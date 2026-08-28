"""
Middleware de auditoria — nível 1, a trilha de intenção.

Um arquivo cobre os 7 serviços porque tudo passa pelo gateway. Grava quem
pediu o quê e quando; o "o quê mudou de verdade" é o nível 2, os snapshots
gravados por trigger no banco.
"""
import json

import structlog
from fastapi import Request
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from auth.jwt import verify_token
from database import AsyncSessionLocal

log = structlog.get_logger()

METODOS_AUDITADOS = {"POST", "PUT", "PATCH", "DELETE"}

# Auditar o login gravaria a senha do usuário numa tabela que o suporte lê.
# A trilha de autenticação já existe nos logs estruturados.
ROTAS_IGNORADAS = ("/auth/login", "/auth/refresh", "/auth/register", "/health")

# Redigidas por substring da chave: o payload é de 7 serviços e ninguém vai
# manter uma lista exata de campos por rota.
SENSIVEIS = ("senha", "password", "token", "secret", "api_key", "apikey", "authorization")

LIMITE_PAYLOAD = 16 * 1024  # 16KB: um upload em base64 não vira linha de auditoria


def _redigir(valor):
    """Substitui recursivamente qualquer chave sensível por ***."""
    if isinstance(valor, dict):
        return {
            k: ("***" if any(s in k.lower() for s in SENSIVEIS) else _redigir(v))
            for k, v in valor.items()
        }
    if isinstance(valor, list):
        return [_redigir(v) for v in valor]
    return valor


class AuditoriaMiddleware(BaseHTTPMiddleware):
    """Grava toda escrita que passa pelo gateway em gateway.auditoria."""

    async def dispatch(self, request: Request, call_next):
        if request.method not in METODOS_AUDITADOS or request.url.path.startswith(ROTAS_IGNORADAS):
            return await call_next(request)

        # Ler o corpo antes: call_next consome o stream e o handler precisa dele.
        corpo = await request.body()

        async def receive():
            return {"type": "http.request", "body": corpo, "more_body": False}

        request._receive = receive
        response = await call_next(request)

        try:
            await self._gravar(request, corpo, response.status_code)
        except Exception as e:
            # Auditoria nunca derruba a requisição que ela observa: a escrita do
            # usuário já aconteceu, e falhar aqui transformaria um problema de
            # log num 500 depois do commit.
            log.warning("auditoria.falhou", rota=request.url.path, error=str(e))

        return response

    async def _gravar(self, request: Request, corpo: bytes, status_resposta: int) -> None:
        payload = None
        if corpo and len(corpo) <= LIMITE_PAYLOAD:
            try:
                payload = _redigir(json.loads(corpo))
            except (ValueError, TypeError):
                payload = None  # não-JSON (upload, form): a rota e o status bastam

        usuario_id, empresa_id = self._identificar(request)

        async with AsyncSessionLocal() as db:
            await db.execute(
                text(
                    # O JWT de usuário não carrega empresa_id (só o de cliente),
                    # e sem tenant a trilha não serve para filtrar por lojista.
                    # O subselect resolve na própria escrita, sem roundtrip extra.
                    "INSERT INTO gateway.auditoria "
                    "(usuario_id, empresa_id, metodo, rota, payload, status_resposta) "
                    "VALUES (CAST(:usuario_id AS UUID), COALESCE(:empresa_id, "
                    "(SELECT empresa_id FROM gateway.usuarios WHERE id = CAST(:usuario_id AS UUID))), "
                    ":metodo, :rota, CAST(:payload AS JSONB), :status)"
                ),
                {
                    "usuario_id": usuario_id,
                    "empresa_id": empresa_id,
                    "metodo": request.method,
                    "rota": request.url.path,
                    "payload": json.dumps(payload) if payload is not None else None,
                    "status": status_resposta,
                },
            )
            await db.commit()

    @staticmethod
    def _identificar(request: Request) -> tuple[str | None, int | None]:
        """
        Identifica o autor pelo token, cookie primeiro — mesma ordem de
        get_token_from_cookie_or_header, senão o front, que autentica por
        cookie HTTP-only, gravaria toda a trilha como anônima.

        Token inválido devolve (None, None): a linha ainda vale pela rota e
        pelo status, e recusar a gravar esconderia justamente as tentativas
        que mais interessam.
        """
        token = request.cookies.get("access_token") or ""
        if not token:
            auth = request.headers.get("authorization", "")
            if not auth.lower().startswith("bearer "):
                return None, None
            token = auth.split(None, 1)[1]

        claims = verify_token(token) or {}
        empresa_id = claims.get("empresa_id")
        return claims.get("sub"), int(empresa_id) if empresa_id else None
