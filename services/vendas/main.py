"""
Serviço Vendas - Runas
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from routers import vendas_router
from routers.loja import router as loja_router


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
    log.info("vendas.starting")
    await init_db()
    log.info("vendas.started")
    
    yield
    
    log.info("vendas.stopped")


app = FastAPI(
    title="Runas - Vendas",
    description="Microsserviço de vendas",
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

# Registrar routers
app.include_router(vendas_router)
app.include_router(loja_router)  # Loja Online (E-commerce)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vendas"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )
