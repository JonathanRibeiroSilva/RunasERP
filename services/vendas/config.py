"""
Configurações do serviço vendas.
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
    
    # URLs públicas (para Mercado Pago)
    API_BASE_URL: str = "https://api.seudominio.com"  # URL pública da API
    FRONTEND_URL: str = "https://loja.seudominio.com"  # URL pública do frontend
    
    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = ""  # URL da Evolution API (opcional)
    EVOLUTION_API_KEY: str = ""  # API Key da Evolution API (opcional)
    EVOLUTION_INSTANCE: str = ""  # Nome da instância (opcional)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
