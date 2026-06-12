"""
Configurações do API Gateway.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # URLs dos serviços internos
    EMPRESAS_URL: str
    CLIENTES_URL: str
    PRODUTOS_URL: str
    ESTOQUE_URL: str
    VENDAS_URL: str
    FINANCEIRO_URL: str
    NOTIFICACOES_URL: str

    # OAuth Google
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # OAuth Microsoft
    MICROSOFT_CLIENT_ID: str | None = None
    MICROSOFT_CLIENT_SECRET: str | None = None
    MICROSOFT_TENANT_ID: str = "common"

    # Email SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str = "Runas ERP"

    # Frontend URL
    # Usado para: links de reset de senha, detecção de HTTPS para cookies
    # Em produção/ngrok: https://pretty-dissuade-brunette.ngrok-free.dev
    # Em desenvolvimento local: http://localhost:3000
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
