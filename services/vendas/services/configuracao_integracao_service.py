"""
Service de Configuração de Integrações.
Gerencia credenciais de WhatsApp (Evolution) e SMTP por empresa (multi-tenant).
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from config import settings
from database import AsyncSessionLocal
from models.venda import ConfiguracaoIntegracao
from utils.crypto import decrypt, encrypt

log = structlog.get_logger()

# Campos que chegam em claro e vão cifrados para a coluna de mesmo nome + "_enc".
SEGREDOS = ("evolution_api_key", "smtp_password")


class ConfiguracaoIntegracaoService:
    """Service para gerenciar integrações por empresa."""

    @staticmethod
    async def obter_por_empresa(
        db: AsyncSession,
        empresa_id: int
    ) -> Optional[ConfiguracaoIntegracao]:
        """Obtém a configuração de integrações da empresa, ou None."""
        result = await db.execute(
            select(ConfiguracaoIntegracao).where(
                ConfiguracaoIntegracao.empresa_id == empresa_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def criar_ou_atualizar(
        db: AsyncSession,
        empresa_id: int,
        **campos
    ) -> ConfiguracaoIntegracao:
        """
        Cria ou atualiza a configuração do tenant.

        Só grava o que veio: um segredo ausente ou vazio significa "não mexi
        neste campo", porque a tela mostra •••••• em vez do valor real e um
        salvamento parcial não pode apagar a senha que o admin não digitou.
        """
        config = await ConfiguracaoIntegracaoService.obter_por_empresa(db, empresa_id)
        if not config:
            config = ConfiguracaoIntegracao(empresa_id=empresa_id)
            db.add(config)

        for campo, valor in campos.items():
            if valor is None:
                continue
            if campo in SEGREDOS:
                if valor:  # string vazia = manter o segredo atual
                    setattr(config, f"{campo}_enc", encrypt(valor))
            else:
                setattr(config, campo, valor)

        await db.commit()
        await db.refresh(config)

        log.info("config_integracao_salva", empresa_id=empresa_id, campos=sorted(campos))
        return config

    @staticmethod
    async def remover(db: AsyncSession, empresa_id: int) -> bool:
        """Remove a configuração da empresa. Retorna False se não existia."""
        config = await ConfiguracaoIntegracaoService.obter_por_empresa(db, empresa_id)
        if not config:
            return False

        await db.delete(config)
        await db.commit()

        log.info("config_integracao_removida", empresa_id=empresa_id)
        return True


async def credenciais_whatsapp(empresa_id: int | None) -> dict | None:
    """
    Evolution API efetiva do tenant, com fallback no env global.

    O env global é o comportamento de hoje — um único WhatsApp para todos os
    tenants. Ele continua valendo para quem não configurou o próprio, senão
    esta mudança silenciaria as notificações de todo mundo no deploy.
    Retorna None quando não há credencial em lugar nenhum.
    """
    if empresa_id is not None:
        async with AsyncSessionLocal() as db:
            config = await ConfiguracaoIntegracaoService.obter_por_empresa(db, empresa_id)
        if config and config.whatsapp_ativo and config.evolution_url and config.evolution_api_key_enc:
            return {
                "url": config.evolution_url,
                "api_key": decrypt(config.evolution_api_key_enc),
                "instance": config.evolution_instance or "",
            }

    if settings.EVOLUTION_API_URL and settings.EVOLUTION_API_KEY:
        return {
            "url": settings.EVOLUTION_API_URL,
            "api_key": settings.EVOLUTION_API_KEY,
            "instance": settings.EVOLUTION_INSTANCE,
        }
    return None


async def credenciais_smtp(empresa_id: int | None) -> dict | None:
    """SMTP efetivo do tenant, mesma regra de fallback do WhatsApp."""
    if empresa_id is not None:
        async with AsyncSessionLocal() as db:
            config = await ConfiguracaoIntegracaoService.obter_por_empresa(db, empresa_id)
        if config and config.email_ativo and config.smtp_host and config.smtp_password_enc:
            return {
                "host": config.smtp_host,
                "port": config.smtp_port or 587,
                "user": config.smtp_user or "",
                "password": decrypt(config.smtp_password_enc),
                "from_name": config.smtp_from_name or settings.SMTP_FROM_NAME,
            }

    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        return {
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "from_name": settings.SMTP_FROM_NAME,
        }
    return None
