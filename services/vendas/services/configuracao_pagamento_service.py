"""
Service de Configuração de Pagamento.
Gerencia credenciais do Mercado Pago por empresa (multi-tenant).
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models.venda import ConfiguracaoPagamento

log = structlog.get_logger()


class ConfiguracaoPagamentoService:
    """
    Service para gerenciar configurações de pagamento (Mercado Pago) por empresa.
    """
    
    @staticmethod
    async def obter_por_empresa(
        db: AsyncSession,
        empresa_id: int
    ) -> Optional[ConfiguracaoPagamento]:
        """
        Obtém configuração de pagamento da empresa.
        
        Returns:
            ConfiguracaoPagamento ou None se não existe
        """
        stmt = select(ConfiguracaoPagamento).where(
            ConfiguracaoPagamento.empresa_id == empresa_id
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def criar_ou_atualizar(
        db: AsyncSession,
        empresa_id: int,
        access_token: str,
        public_key: str,
        ativo: bool = True,
        webhook_secret: str | None = None
    ) -> ConfiguracaoPagamento:
        """
        Cria ou atualiza configuração de pagamento.

        `webhook_secret` vazio significa "mantém o que está gravado" — o form
        não devolve segredo já salvo. Para remover, apague a configuração.

        Returns:
            ConfiguracaoPagamento: Configuração criada/atualizada
        """
        # Verificar se já existe
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)

        if config:
            # Atualizar
            config.mercadopago_access_token = access_token
            config.mercadopago_public_key = public_key
            config.ativo = ativo
            if webhook_secret:
                config.mercadopago_webhook_secret = webhook_secret

            log.info(
                "config_pagamento_atualizada",
                empresa_id=empresa_id
            )
        else:
            # Criar
            config = ConfiguracaoPagamento(
                empresa_id=empresa_id,
                mercadopago_access_token=access_token,
                mercadopago_public_key=public_key,
                mercadopago_webhook_secret=webhook_secret,
                ativo=ativo
            )
            db.add(config)
            
            log.info(
                "config_pagamento_criada",
                empresa_id=empresa_id
            )
        
        await db.commit()
        await db.refresh(config)
        
        return config
    
    @staticmethod
    async def ativar_desativar(
        db: AsyncSession,
        empresa_id: int,
        ativo: bool
    ) -> Optional[ConfiguracaoPagamento]:
        """
        Ativa ou desativa configuração de pagamento.
        
        Returns:
            ConfiguracaoPagamento ou None se não existe
        """
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)
        
        if not config:
            log.warning(
                "config_pagamento_nao_encontrada",
                empresa_id=empresa_id
            )
            return None
        
        config.ativo = ativo
        await db.commit()
        await db.refresh(config)
        
        log.info(
            "config_pagamento_alterada",
            empresa_id=empresa_id,
            ativo=ativo
        )
        
        return config
    
    @staticmethod
    async def remover(
        db: AsyncSession,
        empresa_id: int
    ) -> bool:
        """
        Remove configuração de pagamento.
        
        Returns:
            bool: True se removeu, False se não encontrou
        """
        config = await ConfiguracaoPagamentoService.obter_por_empresa(db, empresa_id)
        
        if not config:
            return False
        
        await db.delete(config)
        await db.commit()
        
        log.info(
            "config_pagamento_removida",
            empresa_id=empresa_id
        )
        
        return True
