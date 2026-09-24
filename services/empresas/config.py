"""
Configurações do serviço empresas.
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
    
    # Segredo compartilhado pelos 8 containers: prova que a requisicao veio
    # de dentro da malha. Vazio = fail-open (ver interno.py).
    SERVICO_INTERNO_TOKEN: str = ""

    # Segredo de escopo MENOR, so no gateway e aqui: prova que o X-Plataforma
    # saiu do router /plataforma do gateway, depois do require_super_admin.
    # O SERVICO_INTERNO_TOKEN acima nao serve para isso -- ele e o mesmo nos 8
    # containers, entao provaria apenas que a chamada veio de algum deles, e as
    # rotas de plataforma apagam tenant. Vazio = fail-open (ver empresas.py).
    PLATAFORMA_INTERNO_TOKEN: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
