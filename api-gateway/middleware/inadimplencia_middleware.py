"""
Corte de escrita por inadimplência — 402 no gateway, zero nos 7 serviços.

O gateway é o único caminho público e a tabela gateway.assinaturas mora no
banco dele: a consulta é local. Nenhum serviço aprende o que é inadimplência,
e não há chamada cross-serviço no caminho quente.

Só POST/PUT/PATCH/DELETE são barrados. GET passa sempre — cortar leitura
transformaria um atraso de dois dias em cancelamento, e o lojista precisa
continuar entrando para ver a própria fatura.
"""
import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from auth.jwt import verify_token
from auth.redis_client import get_redis
from database import AsyncSessionLocal

log = structlog.get_logger()

METODOS_DE_ESCRITA = {"POST", "PUT", "PATCH", "DELETE"}

# Sem estas, o tenant inadimplente não consegue nem entrar para pagar.
LIBERADAS = ("/auth/", "/health", "/plataforma/", "/docs", "/openapi.json")

CACHE_TTL = 60  # segundos: a régua muda uma vez por dia, não por request


class InadimplenciaMiddleware(BaseHTTPMiddleware):
    """Rejeita escrita com 402 enquanto o tenant está em somente leitura."""

    async def dispatch(self, request: Request, call_next):
        if request.method not in METODOS_DE_ESCRITA or request.url.path.startswith(LIBERADAS):
            return await call_next(request)

        empresa_id = await self._empresa_do_request(request)
        if empresa_id and await self._somente_leitura(empresa_id):
            log.info("inadimplencia.escrita_bloqueada", empresa_id=empresa_id,
                     rota=request.url.path)
            return JSONResponse(
                status_code=402,
                content={
                    "detail": "Fatura em aberto: a conta está em modo somente leitura. "
                              "Regularize o pagamento para voltar a salvar alterações."
                },
            )

        return await call_next(request)

    @staticmethod
    async def _empresa_do_request(request: Request) -> int | None:
        """
        Tenant do portador. O JWT de usuário não carrega empresa_id, então o
        caminho normal é a consulta por sub; o claim cobre o token de cliente.
        """
        token = request.cookies.get("access_token") or ""
        if not token:
            auth = request.headers.get("authorization", "")
            if not auth.lower().startswith("bearer "):
                return None
            token = auth.split(None, 1)[1]

        claims = verify_token(token) or {}
        if claims.get("empresa_id"):
            return int(claims["empresa_id"])

        sub = claims.get("sub")
        if not sub:
            return None
        async with AsyncSessionLocal() as db:
            return await db.scalar(
                text("SELECT empresa_id FROM gateway.usuarios WHERE id = CAST(:s AS UUID)"),
                {"s": sub},
            )

    @staticmethod
    async def _somente_leitura(empresa_id: int) -> bool:
        """
        Estado da assinatura, com cache curto no Redis que já existe.

        Redis fora do ar não pode travar as vendas de todo mundo: cai para a
        consulta direta, que é local e barata.
        """
        chave = f"inadimplencia:{empresa_id}"
        try:
            redis = await get_redis()
            cache = await redis.get(chave)
            if cache is not None:
                return cache == "1"
        except Exception:
            redis = None

        async with AsyncSessionLocal() as db:
            estado = await db.scalar(
                text(
                    "SELECT somente_leitura_desde IS NOT NULL FROM gateway.assinaturas "
                    "WHERE empresa_id = :e"
                ),
                {"e": empresa_id},
            )
        # Sem linha de assinatura o tenant não é cobrado ainda: não bloquear.
        bloqueado = bool(estado)

        if redis is not None:
            try:
                await redis.setex(chave, CACHE_TTL, "1" if bloqueado else "0")
            except Exception:
                pass
        return bloqueado
