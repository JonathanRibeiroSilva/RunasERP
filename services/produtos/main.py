"""
Serviço Produtos - Runas
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from routers.produtos import (
    router_categorias,
    router_produtos,
    router_variantes,
    router_catalogo,
    router_fornecedores,
    router_fornecedor_produtos,
)


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
    log.info("produtos.starting")
    await init_db()
    log.info("produtos.started")
    
    yield
    
    log.info("produtos.stopped")


app = FastAPI(
    title="Runas - Produtos",
    description="Microsserviço de produtos",
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "produtos"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )


# ======================== INCLUIR ROUTERS ========================

app.include_router(router_categorias)
app.include_router(router_produtos)
app.include_router(router_variantes)
app.include_router(router_catalogo)
app.include_router(router_fornecedores)
app.include_router(router_fornecedor_produtos)
