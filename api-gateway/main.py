"""
API Gateway - Ponto de entrada único para todos os microsserviços.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import structlog
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from database import engine, init_db
from health import SERVICE_NAMES, summarize
from auth.redis_client import close_redis, get_redis
from seed import seed_admin
from routers import auth, auth_cliente, auth_admin, plataforma
from routers import proxy
from middleware.auditoria_middleware import AuditoriaMiddleware
from middleware.inadimplencia_middleware import InadimplenciaMiddleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.rate_limit import limiter


# Configurar structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    log.info("gateway.starting")
    await init_db()
    await seed_admin()
    log.info("gateway.started")
    
    yield
    
    # Shutdown
    log.info("gateway.stopping")
    await close_redis()
    log.info("gateway.stopped")


app = FastAPI(
    title="ERP Runas - API Gateway",
    description="Gateway de autenticação e roteamento para o ERP Runas",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,
)

# Rate limiting — registrado antes do CORS de propósito. add_middleware()
# empilha por fora a cada chamada nova, então o último adicionado aqui embrulha
# o anterior: com o CORS vindo depois, uma resposta 429 do SlowAPIMiddleware
# ainda passa pelo CORSMiddleware no caminho de volta e sai com os headers —
# na ordem inversa, o browser veria a resposta como falha de CORS, não como
# 429. Limite geral em rate_limit.py; login/registro/reset usam @limiter.limit
# direto na rota.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Sem isto o browser não enxerga o marcador de replay idempotente
    expose_headers=["X-Idempotent-Replay"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuditoriaMiddleware)  # trilha de intenção (auditoria nível 1)
app.add_middleware(InadimplenciaMiddleware)  # 402 na escrita de tenant em atraso

# Routers
app.include_router(auth.router)
app.include_router(auth_cliente.router)
app.include_router(auth_admin.router)
# Antes do proxy: Starlette casa por ordem de registro e o proxy tem catch-all.
app.include_router(plataforma.router)
app.include_router(plataforma.router_publico)  # webhook do MP e job do cron
app.include_router(proxy.router)


@app.get("/health")
@limiter.exempt
async def health_check():
    """Liveness: prova apenas que o processo responde.

    Fica raso de propósito — é o que o healthcheck do Docker lê, e um blip no
    Redis não pode marcar o container do gateway como morto. Quem precisa saber
    se a stack inteira está de pé usa /health/ready.
    """
    return {"status": "healthy", "service": "api-gateway"}


# 2s: a sonda externa tenta 3 vezes com --max-time 10, então uma dependência
# lenta precisa reprovar bem antes de o curl desistir.
HEALTH_TIMEOUT = 2.0


async def _check(nome: str, sonda) -> dict:
    """Roda uma sonda e traduz qualquer falha em status "down".

    O erro real vai para o log, nunca para o corpo: /health/ready é público
    através do Cloudflare, e mensagem de SQLAlchemy carrega host e usuário do
    banco. O tipo da exceção basta para separar timeout de conexão recusada.
    """
    try:
        await asyncio.wait_for(sonda(), HEALTH_TIMEOUT)
        return {"name": nome, "status": "up"}
    except Exception as erro:  # noqa: BLE001 — qualquer falha é "down"
        log.warning("health.check_failed", check=nome, error=str(erro))
        return {"name": nome, "status": "down", "error": type(erro).__name__}


async def _sonda_postgres():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _sonda_redis():
    await (await get_redis()).ping()


def _sonda_servico(url: str):
    async def sonda():
        async with httpx.AsyncClient(timeout=HEALTH_TIMEOUT) as client:
            resposta = await client.get(f"{url}/health")
            resposta.raise_for_status()

    return sonda


@app.get("/health/ready")
@limiter.exempt
async def readiness_check():
    """Readiness: Postgres, Redis e os sete serviços, sondados em paralelo.

    É este que a sonda externa consome. Devolve 503 nomeando quem caiu, para o
    alarme no Telegram dizer "financeiro não responde" em vez de "fora do ar".
    """
    checks = await asyncio.gather(
        _check("postgres", _sonda_postgres),
        _check("redis", _sonda_redis),
        *[
            _check(nome, _sonda_servico(getattr(settings, f"{nome.upper()}_URL")))
            for nome in SERVICE_NAMES
        ],
    )
    codigo, corpo = summarize(checks)
    return JSONResponse(status_code=codigo, content=corpo)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )
