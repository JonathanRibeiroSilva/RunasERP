"""
Serviço Estoque - Runas
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from interno import validar_token_interno
from routers import conferencia_visual_router, estoque_router
from jobs.marcar_lotes_vencidos import marcar_lotes_vencidos


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

log = structlog.get_logger()

MARCAR_VENCIDOS_INTERVALO_SEGUNDOS = 3600


async def _loop_periodico(nome: str, tarefa, intervalo_segundos: int):
    """Executa uma corotina periodicamente, sem deixar exceções derrubarem o loop."""
    while True:
        try:
            await tarefa()
        except Exception as e:
            log.error("loop_periodico_erro", job=nome, error=str(e))
        await asyncio.sleep(intervalo_segundos)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    log.info("estoque.starting")
    await init_db()

    tarefas = [
        asyncio.create_task(_loop_periodico(
            "marcar_lotes_vencidos",
            marcar_lotes_vencidos,
            MARCAR_VENCIDOS_INTERVALO_SEGUNDOS,
        )),
    ]
    log.info("estoque.started")

    yield

    for tarefa in tarefas:
        tarefa.cancel()
    log.info("estoque.stopped")


app = FastAPI(
    title="Runas - Estoque",
    description="Microsserviço de gestão de estoque",
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
app.include_router(conferencia_visual_router)
app.include_router(estoque_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "estoque"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )
