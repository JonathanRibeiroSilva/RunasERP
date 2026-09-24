"""
Serviço Financeiro - Runas
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from interno import validar_token_interno


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
    log.info("financeiro.starting")
    await init_db()
    log.info("financeiro.started")
    
    yield
    
    log.info("financeiro.stopped")


app = FastAPI(
    title="Runas - Financeiro",
    description="Microsserviço de financeiro",
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

# Prova de origem interna. Fail-open enquanto SERVICO_INTERNO_TOKEN
# nao estiver nos 8 containers -- ver interno.py.
app.middleware("http")(validar_token_interno)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "financeiro"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )
