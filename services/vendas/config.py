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
    EMPRESAS_URL: str = "http://empresas:8007"
    CLIENTES_URL: str = "http://clientes:8001"
    PRODUTOS_URL: str = "http://produtos:8002"
    ESTOQUE_URL: str = "http://estoque:8003"
    VENDAS_URL: str = "http://vendas:8004"
    FINANCEIRO_URL: str = "http://financeiro:8005"
    
    # URLs públicas (para Mercado Pago, webhooks, redirect)
    # Defaults locais; produção/tunnel definem via environment (docker-compose)
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Evolution API (WhatsApp)
    EVOLUTION_API_URL: str = ""  # URL da Evolution API (opcional)
    EVOLUTION_API_KEY: str = ""  # API Key da Evolution API (opcional)
    EVOLUTION_INSTANCE: str = ""  # Nome da instância (opcional)
    
    # Email SMTP (para enviar credenciais de conta criada)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Email de envio (opcional)
    SMTP_PASSWORD: str = ""  # Senha do email (opcional)
    SMTP_FROM_NAME: str = "Runas ERP"
    
    # JWT (para criar tokens de clientes)
    SECRET_KEY: str
    # Cifra das credenciais de integração por tenant (Fernet.generate_key()).
    # Vazia = escrita de integração falha alto, nunca grava texto plano.
    INTEGRACOES_SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    
    # API Gateway URL
    API_GATEWAY_URL: str = "http://api-gateway:8000"

    # Segredo compartilhado com o gateway. Carimbado em
    # POST /auth/cliente/registrar-interno, a rota que cria a conta do
    # comprador no checkout com a senha já hasheada daqui.
    REGISTRO_INTERNO_TOKEN: str = ""

    # Mercado Pago environment switch.
    # "sandbox" (default) forces the sandbox/test checkout flow; production is only
    # used when MP_ENVIRONMENT is explicitly set to "production". This is the single
    # source of truth — no token-format heuristics.
    MP_ENVIRONMENT: str = "sandbox"

    @property
    def mercadopago_sandbox(self) -> bool:
        """True unless MP_ENVIRONMENT is explicitly 'production'."""
        return self.MP_ENVIRONMENT.strip().lower() != "production"

    # Segredo compartilhado pelos 8 containers: prova que a requisicao veio
    # de dentro da malha. Vazio = fail-open (ver interno.py).
    SERVICO_INTERNO_TOKEN: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
