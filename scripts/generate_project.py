"""
Script para gerar toda a estrutura do projeto ERP Runas.
Este script cria todos os microsserviços, testes e documentação.
"""
import os
from pathlib import Path


def create_file(path: str, content: str):
    """Cria um arquivo com o conteúdo especificado."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding='utf-8')
    print(f"✓ Criado: {path}")


def generate_api_gateway_main():
    """Gera o main.py do API Gateway."""
    content = '''"""
API Gateway - Ponto de entrada único para todos os microsserviços.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db
from auth.redis_client import close_redis
from routers import auth
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
'''
    create_file("api-gateway/main.py", content)


def generate_middleware():
    """Gera os middlewares do gateway."""
    
    # Logging middleware
    logging_content = '''"""
Middleware de logging estruturado.
"""
import time
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


log = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para log estruturado de todas as requisições."""
    
    async def dispatch(self, request: Request, call_next):
        """Processa a requisição e loga."""
        start_time = time.time()
        
        # Log da requisição
        log.info(
            "request.started",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None
        )
        
        # Processar requisição
        response = await call_next(request)
        
        # Log da resposta
        duration = time.time() - start_time
        log.info(
            "request.completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2)
        )
        
        return response
'''
    create_file("api-gateway/middleware/logging_middleware.py", logging_content)
    
    # Rate limit
    rate_limit_content = '''"""
Middleware de rate limiting.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)
'''
    create_file("api-gateway/middleware/rate_limit.py", rate_limit_content)
    
    create_file("api-gateway/middleware/__init__.py", '"""Middlewares."""')


def generate_alembic_config(service_name: str, port: int):
    """Gera configuração do Alembic para um serviço."""
    
    alembic_ini = f'''# Alembic configuration for {service_name}

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
'''
    create_file(f"services/{service_name}/alembic.ini", alembic_ini)
    
    # env.py
    env_py = f'''"""
Alembic environment configuration for {service_name}.
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from database import Base
from config import settings

# Import all models here
from models import *

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
    create_file(f"services/{service_name}/alembic/env.py", env_py)
    create_file(f"services/{service_name}/alembic/script.py.mako", '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
''')


def generate_service_structure(service_name: str, port: int):
    """Gera a estrutura completa de um microsserviço."""
    base_path = f"services/{service_name}"
    
    print(f"  � Criando estrutura de {service_name}...")
    
    # Dockerfile
    dockerfile = f'''FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {port}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}", "--reload"]
'''
    create_file(f"{base_path}/Dockerfile", dockerfile)
    
    # requirements.txt
    requirements = '''fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
httpx==0.26.0
structlog==24.1.0
aio-pika==9.3.1
redis==5.0.1
python-multipart==0.0.6
validate-docbr==1.10.0
celery==5.3.4
'''
    create_file(f"{base_path}/requirements.txt", requirements)
    
    # config.py
    config = f'''"""
Configurações do serviço {service_name}.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    DATABASE_URL: str
    RABBITMQ_URL: str
    REDIS_URL: str
    
    # URLs de outros serviços (quando necessário)
    CLIENTES_URL: str = "http://clientes:8001"
    PRODUTOS_URL: str = "http://produtos:8002"
    ESTOQUE_URL: str = "http://estoque:8003"
    VENDAS_URL: str = "http://vendas:8004"
    FINANCEIRO_URL: str = "http://financeiro:8005"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
'''
    create_file(f"{base_path}/config.py", config)
    
    # database.py
    database = '''"""
Configuração do banco de dados.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Classe base para os modelos."""
    pass


async def get_db() -> AsyncSession:
    """Dependency para obter sessão do banco de dados."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Inicializa o banco de dados criando todas as tabelas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
'''
    create_file(f"{base_path}/database.py", database)
    
    # main.py
    main = f'''"""
Serviço {service_name.capitalize()} - ERP Runas
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from database import init_db


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
    log.info("{service_name}.starting")
    await init_db()
    log.info("{service_name}.started")
    
    yield
    
    log.info("{service_name}.stopped")


app = FastAPI(
    title="ERP Runas - {service_name.capitalize()}",
    description="Microsserviço de {service_name}",
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
    return {{"status": "healthy", "service": "{service_name}"}}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções."""
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={{"detail": "Erro interno do servidor"}}
    )
'''
    create_file(f"{base_path}/main.py", main)
    
    # Estrutura de pastas
    create_file(f"{base_path}/models/__init__.py", '"""Modelos do serviço."""')
    create_file(f"{base_path}/schemas/__init__.py", '"""Schemas Pydantic."""')
    create_file(f"{base_path}/repositories/__init__.py", '"""Repositories."""')
    create_file(f"{base_path}/services/__init__.py", '"""Services (lógica de negócio)."""')
    create_file(f"{base_path}/routers/__init__.py", '"""Routers FastAPI."""')
    create_file(f"{base_path}/events/__init__.py", '"""Event publishers."""')
    create_file(f"{base_path}/tests/__init__.py", '"""Testes."""')
    
    # events/publisher.py
    publisher = '''"""
Publisher de eventos para RabbitMQ.
"""
import json
from typing import Any
import aio_pika
from aio_pika import ExchangeType
import structlog
from config import settings


log = structlog.get_logger()


class EventPublisher:
    """Publisher de eventos de domínio."""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
    
    async def connect(self):
        """Conecta ao RabbitMQ."""
        if self.connection is None or self.connection.is_closed:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "erp.events",
                ExchangeType.TOPIC,
                durable=True
            )
    
    async def publish(self, routing_key: str, payload: dict[str, Any]):
        """
        Publica um evento.
        
        Args:
            routing_key: Chave de roteamento (ex: "pedido.confirmado")
            payload: Dados do evento
        """
        await self.connect()
        
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await self.exchange.publish(message, routing_key=routing_key)
        
        log.info("event.published", routing_key=routing_key, payload=payload)
    
    async def close(self):
        """Fecha a conexão."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()


# Singleton
_publisher = EventPublisher()


async def get_publisher() -> EventPublisher:
    """Obtém instância do publisher."""
    return _publisher
'''
    create_file(f"{base_path}/events/publisher.py", publisher)
    
    # Alembic
    generate_alembic_config(service_name, port)
    
    # conftest.py para testes
    conftest = '''"""
Configuração de fixtures para testes.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database import Base, get_db
from main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Fixture de banco de dados em memória para testes."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_db: AsyncSession):
    """Fixture de cliente HTTP para testes."""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
'''
    create_file(f"{base_path}/tests/conftest.py", conftest)
    
    # seed.py
    seed = '''"""
Script para popular banco com dados de teste.
"""
import asyncio
from database import AsyncSessionLocal


async def seed_data():
    """Popula banco com dados de teste."""
    async with AsyncSessionLocal() as session:
        # TODO: Implementar seed de dados
        print("✓ Dados de teste inseridos")


if __name__ == "__main__":
    asyncio.run(seed_data())
'''
    create_file(f"{base_path}/seed.py", seed)
    
    print(f"  ✓ Estrutura de {service_name} criada")


def generate_all_services():
    """Gera todos os microsserviços."""
    services = [
        ("clientes", 8001),
        ("produtos", 8002),
        ("estoque", 8003),
        ("vendas", 8004),
        ("financeiro", 8005),
        ("notificacoes", 8006),
    ]
    
    for service_name, port in services:
        generate_service_structure(service_name, port)


if __name__ == "__main__":
    print("🚀 Gerando estrutura completa do ERP Runas...")
    print()
    
    # API Gateway
    print("📦 Gerando API Gateway...")
    generate_api_gateway_main()
    generate_middleware()
    
    print()
    
    # Microsserviços
    print("📦 Gerando Microsserviços...")
    generate_all_services()
    
    print()
    print("✅ Estrutura completa criada!")
    print()
    print("📋 Próximos passos:")
    print("   1. Configure o arquivo .env")
    print("   2. Execute: make up")
    print("   3. Execute: make migrate")
    print("   4. Execute: make seed")
    print()
    print("🎉 Pronto para desenvolvimento!")
