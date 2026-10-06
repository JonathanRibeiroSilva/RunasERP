"""
Serviço Vendas - Runas
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from interno import validar_token_interno
from routers import vendas_router
from routers.loja import router as loja_router
from routers.webhook import router as webhook_router
from routers.admin_entrega import router as admin_entrega_router
from routers.admin_pagamento import router as admin_pagamento_router
from routers.admin_integracao import router as admin_integracao_router
from jobs.verificar_pagamentos_pendentes import verificar_pagamentos_pendentes
from jobs.reconciliar_estoque_vendas import reconciliar_estoque_vendas


structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

log = structlog.get_logger()


PAGAMENTOS_PENDENTES_INTERVALO_SEGUNDOS = 60
RECONCILIACAO_ESTOQUE_INTERVALO_SEGUNDOS = 120


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
    log.info("vendas.starting")
    await init_db()

    tarefas = [
        asyncio.create_task(_loop_periodico(
            "verificar_pagamentos_pendentes",
            verificar_pagamentos_pendentes,
            PAGAMENTOS_PENDENTES_INTERVALO_SEGUNDOS,
        )),
        asyncio.create_task(_loop_periodico(
            "reconciliar_estoque_vendas",
            reconciliar_estoque_vendas,
            RECONCILIACAO_ESTOQUE_INTERVALO_SEGUNDOS,
        )),
    ]
    log.info("vendas.started")

    yield

    for tarefa in tarefas:
        tarefa.cancel()
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

# Prova de origem interna. Fail-closed desde o #124 -- ver interno.py.
app.middleware("http")(validar_token_interno)

# Registrar routers
app.include_router(vendas_router)
app.include_router(loja_router)  # Loja Online (E-commerce)
app.include_router(webhook_router)  # Webhooks (Mercado Pago)
app.include_router(admin_entrega_router)  # Admin - Configuração de Entrega
app.include_router(admin_pagamento_router)  # Admin - Configuração de Pagamento
app.include_router(admin_integracao_router)  # Admin - Integrações (WhatsApp/SMTP)


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
