"""
API Gateway - Ponto de entrada único para todos os microsserviços.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from auth.redis_client import close_redis
from seed import seed_admin
from routers import auth, auth_cliente, auth_admin
from routers import proxy
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
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configurar adequadamente em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Rate limiting
app.state.limiter = limiter

# Routers
app.include_router(auth.router)
app.include_router(auth_cliente.router)
app.include_router(auth_admin.router)
app.include_router(proxy.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "api-gateway"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )
