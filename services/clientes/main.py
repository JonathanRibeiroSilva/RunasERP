"""
Serviço Clientes - Runas
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from interno import validar_token_interno
from routers import clientes_router, enderecos_router


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
    log.info("clientes.starting")
    await init_db()
    log.info("clientes.started")
    
    yield
    
    log.info("clientes.stopped")


app = FastAPI(
    title="Runas - Clientes",
    description="Microsserviço de clientes",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prova de origem interna. Fail-closed desde o #124 -- ver interno.py.
app.middleware("http")(validar_token_interno)

# Incluir routers
app.include_router(clientes_router)
app.include_router(enderecos_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "clientes"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )
