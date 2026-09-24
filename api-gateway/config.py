"""
Configurações do API Gateway.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

# Trigger: graphify update after gitignore fix


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

    # Janela em que uma Idempotency-Key devolve a resposta já salva
    IDEMPOTENCY_TTL_SECONDS: int = 86400

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

    # Mercado Pago DA PLATAFORMA — cobra a mensalidade dos lojistas. Nada a ver
    # com vendas.configuracoes_pagamento, que e a conta de cada lojista.
    PLATAFORMA_MP_ACCESS_TOKEN: str = ""
    # Protege o endpoint da varredura diaria, chamado pelo cron do host.
    PLATAFORMA_JOB_TOKEN: str = ""

    # Segredo compartilhado com o servico de vendas. Protege
    # POST /auth/cliente/registrar-interno, que aceita a senha ja hasheada:
    # quem chama define a senha da conta do comprador.
    REGISTRO_INTERNO_TOKEN: str = ""

    # Segredo compartilhado pelos 8 containers: prova que a requisicao veio de
    # dentro da malha. O gateway e o unico que so carimba (nunca valida) --
    # nada interno chama o gateway de volta exceto loja_service, que carimba
    # tambem. Vazio = fail-open (ver services/*/middleware_interno.py).
    SERVICO_INTERNO_TOKEN: str = ""

    # Swagger/ReDoc/openapi.json. Desligado por padrao: o schema completo e um
    # mapa da API pra quem nao deveria ter. Ligue no .env local se precisar.
    DOCS_ENABLED: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
