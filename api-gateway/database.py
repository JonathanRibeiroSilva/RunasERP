"""
Configuração do banco de dados para o API Gateway.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings


# Engine assíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    connect_args={"server_settings": {"search_path": "gateway,public"}}
)

# Session factory
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
    """
    Inicializa o banco de dados.
    
    IMPORTANTE: Este método não cria mais as tabelas automaticamente.
    Use Alembic migrations para gerenciar o schema do banco:
    
    ```bash
    # Criar migration
    alembic revision --autogenerate -m "descrição"
    
    # Aplicar migration
    alembic upgrade head
    ```
    """
    # Apenas log - tabelas são criadas via Alembic migrations
    pass
