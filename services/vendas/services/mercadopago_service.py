"""
Service de integração com Mercado Pago.
Gerencia criação de preferências, links de pagamento e processamento de webhooks.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.venda import Venda, ConfiguracaoPagamento, WebhookProcessado
from config import settings

log = structlog.get_logger()


class MercadoPagoService:
    """
    Service para integração com Mercado Pago.
    
    Funcionalidades:
    - Criar preferência de pagamento
    - Gerar link de checkout
    - Processar webhooks com idempotência
    - Multi-tenant (cada empresa tem suas credenciais)
    """
    
    MERCADOPAGO_API_BASE = "https://api.mercadopago.com"
    
    @staticmethod
    async def obter_credenciais(
        db: AsyncSession,
        empresa_id: int
    ) -> Optional[ConfiguracaoPagamento]:
        """
        Obtém credenciais do Mercado Pago da empresa.
        
        Returns:
            ConfiguracaoPagamento ou None se não configurado
        """
        stmt = select(ConfiguracaoPagamento).where(
            ConfiguracaoPagamento.empresa_id == empresa_id,
            ConfiguracaoPagamento.ativo == True
        )
        
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config or not config.mercadopago_access_token:
            log.warning(
                "mercadopago_credenciais_nao_configuradas",
                empresa_id=empresa_id
            )
            return None
        
        return config
    
    @staticmethod
    async def criar_preferencia(
        db: AsyncSession,
        venda: Venda,
        empresa_id: int,
        empresa_slug: str,
        valor_credito_usado: Optional[Decimal] = None
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Cria preferência de pagamento no Mercado Pago.
        
        Args:
            venda: Venda criada
            empresa_id: ID da empresa
            empresa_slug: Slug da empresa (para webhook URL)
            valor_credito_usado: Valor do crédito usado (pagamento misto)
        
        Returns:
            tuple: (preference_id, init_point, erro)
                - preference_id: ID da preferência criada
                - init_point: URL para redirecionar cliente
                - erro: mensagem de erro se falhou
        """
        # Obter credenciais
        config = await MercadoPagoService.obter_credenciais(db, empresa_id)
        if not config:
            return (None, None, "Mercado Pago não configurado para esta empresa")
        
        # Calcular valor a pagar (total - crédito usado)
        valor_a_pagar = venda.valor_total
        if valor_credito_usado and valor_credito_usado > 0:
            valor_a_pagar = venda.valor_total - valor_credito_usado
        
        if valor_a_pagar <= 0:
            return (None, None, "Valor a pagar deve ser maior que zero")
        
        # Montar itens da preferência
        items = []
        for item in venda.itens:
            items.append({
                "title": item.descricao_produto,
                "description": f"Código: {item.codigo_produto}" if item.codigo_produto else None,
                "quantity": int(item.quantidade),
                "unit_price": float(item.preco_unitario),
                "currency_id": "BRL"
            })
        
        # Webhook URL (por empresa)
        webhook_url = f"{settings.API_BASE_URL}/loja/{empresa_slug}/webhook/mercadopago"
        
        # Montar payload da preferência
        preference_data = {
            "items": items,
            "payer": {},
            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/loja/{empresa_slug}/pedido/{venda.numero_venda}?status=success",
                "failure": f"{settings.FRONTEND_URL}/loja/{empresa_slug}/pedido/{venda.numero_venda}?status=failure",
                "pending": f"{settings.FRONTEND_URL}/loja/{empresa_slug}/pedido/{venda.numero_venda}?status=pending"
            },
            "auto_return": "approved",
            "external_reference": str(venda.id),  # Vincular com venda
            "notification_url": webhook_url,
            "statement_descriptor": f"Pedido {venda.numero_venda}",
            "expires": True,
            "expiration_date_from": None,  # Agora
            "expiration_date_to": None,     # 5 minutos (calculado no momento)
            # Métodos de pagamento permitidos - incluindo PIX explicitamente
            "payment_methods": {
                "excluded_payment_methods": [],  # Não excluir nenhum método
                "excluded_payment_types": [],    # Não excluir nenhum tipo (importante para PIX)
                "installments": 12,              # Até 12 parcelas para cartão
                "default_installments": 1,       # Padrão: à vista
                "default_payment_method_id": None  # Não forçar método padrão
            },
            # Configurações adicionais para garantir PIX
            "binary_mode": False,  # False permite pagamentos pendentes (necessário para PIX)
            "purpose": "onboarding_credits"  # Propósito da transação
        }
        
        # Adicionar dados do cliente se disponível
        if venda.cliente_id:
            # TODO: Buscar dados do cliente via HTTP
            pass
        elif venda.cliente_convidado_email:
            preference_data["payer"]["email"] = venda.cliente_convidado_email
            if venda.cliente_convidado_nome:
                preference_data["payer"]["name"] = venda.cliente_convidado_nome
        
        try:
            # Criar preferência via API do Mercado Pago
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{MercadoPagoService.MERCADOPAGO_API_BASE}/checkout/preferences",
                    headers={
                        "Authorization": f"Bearer {config.mercadopago_access_token}",
                        "Content-Type": "application/json"
                    },
                    json=preference_data,
                    timeout=10.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                preference_id = data.get("id")
                init_point = data.get("init_point")
                
                if not preference_id or not init_point:
                    log.error(
                        "mercadopago_resposta_invalida",
                        data=data
                    )
                    return (None, None, "Resposta inválida do Mercado Pago")
                
                # Salvar preference_id na venda (sem commit - será feito pelo caller)
                venda.mercadopago_preference_id = preference_id
                # NÃO fazer commit aqui - deixar para o fluxo principal fazer
                
                log.info(
                    "mercadopago_preferencia_criada",
                    venda_id=str(venda.id),
                    preference_id=preference_id,
                    valor=float(valor_a_pagar)
                )
                
                return (preference_id, init_point, None)
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            log.error(
                "mercadopago_erro_http",
                status_code=e.response.status_code,
                detail=error_detail,
                venda_id=str(venda.id)
            )
            return (None, None, f"Erro ao criar preferência: {error_detail}")
        
        except Exception as e:
            log.error(
                "mercadopago_erro",
                error=str(e),
                venda_id=str(venda.id)
            )
            return (None, None, f"Erro ao criar preferência: {str(e)}")
    
    @staticmethod
    async def webhook_ja_processado(
        db: AsyncSession,
        payment_id: str
    ) -> bool:
        """
        Verifica se webhook já foi processado (idempotência).
        
        Returns:
            bool: True se já processado, False se é novo
        """
        stmt = select(WebhookProcessado).where(
            WebhookProcessado.payment_id == payment_id
        )
        
        result = await db.execute(stmt)
        webhook = result.scalar_one_or_none()
        
        return webhook is not None
    
    @staticmethod
    async def marcar_webhook_processado(
        db: AsyncSession,
        payment_id: str,
        tipo_evento: str,
        venda_id: Optional[UUID],
        payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Marca webhook como processado para evitar duplicação.
        
        Returns:
            bool: True se marcou, False se já existia
        """
        try:
            # Verificar se já existe
            if await MercadoPagoService.webhook_ja_processado(db, payment_id):
                return False
            
            # Criar registro
            webhook = WebhookProcessado(
                payment_id=payment_id,
                tipo_evento=tipo_evento,
                venda_id=venda_id,
                payload=str(payload) if payload else None
            )
            
            db.add(webhook)
            await db.commit()
            
            log.info(
                "webhook_marcado_processado",
                payment_id=payment_id,
                tipo_evento=tipo_evento
            )
            
            return True
            
        except Exception as e:
            await db.rollback()
            log.error(
                "webhook_marcar_erro",
                error=str(e),
                payment_id=payment_id
            )
            return False
    
    @staticmethod
    async def obter_detalhes_pagamento(
        db: AsyncSession,
        empresa_id: int,
        payment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes do pagamento via API do Mercado Pago.
        
        Returns:
            dict: Dados do pagamento ou None se erro
        """
        config = await MercadoPagoService.obter_credenciais(db, empresa_id)
        if not config:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{MercadoPagoService.MERCADOPAGO_API_BASE}/v1/payments/{payment_id}",
                    headers={
                        "Authorization": f"Bearer {config.mercadopago_access_token}"
                    },
                    timeout=10.0
                )
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            log.error(
                "mercadopago_obter_pagamento_erro",
                error=str(e),
                payment_id=payment_id
            )
            return None
    
    @staticmethod
    async def processar_webhook_payment(
        db: AsyncSession,
        empresa_id: int,
        payment_id: str,
        tipo_evento: str
    ) -> tuple[bool, Optional[str]]:
        """
        Processa webhook de pagamento do Mercado Pago.
        
        Tipos de evento:
        - payment.created: Pagamento criado
        - payment.approved: Pagamento aprovado ✅
        - payment.rejected: Pagamento rejeitado ❌
        - payment.cancelled: Pagamento cancelado ❌
        - payment.refunded: Pagamento reembolsado 💰
        
        Returns:
            tuple: (sucesso, mensagem_erro)
        """
        from services.venda_service import VendaService
        
        # 1. Verificar idempotência
        if await MercadoPagoService.webhook_ja_processado(db, payment_id):
            log.info(
                "webhook_ja_processado_ignorando",
                payment_id=payment_id
            )
            return (True, None)  # Não é erro, apenas já foi processado
        
        # 2. Obter detalhes do pagamento
        payment_data = await MercadoPagoService.obter_detalhes_pagamento(
            db, empresa_id, payment_id
        )
        
        if not payment_data:
            return (False, "Não foi possível obter detalhes do pagamento")
        
        # 3. Buscar venda pelo external_reference
        external_reference = payment_data.get("external_reference")
        if not external_reference:
            log.warning(
                "webhook_sem_external_reference",
                payment_id=payment_id
            )
            return (False, "Webhook sem external_reference")
        
        try:
            venda_id = UUID(external_reference)
        except ValueError:
            log.error(
                "webhook_external_reference_invalido",
                external_reference=external_reference
            )
            return (False, "external_reference inválido")
        
        # Buscar venda
        stmt = select(Venda).where(
            Venda.id == venda_id,
            Venda.empresa_id == empresa_id
        )
        result = await db.execute(stmt)
        venda = result.scalar_one_or_none()
        
        if not venda:
            log.error(
                "webhook_venda_nao_encontrada",
                venda_id=str(venda_id),
                payment_id=payment_id
            )
            return (False, "Venda não encontrada")
        
        # 4. Salvar payment_id na venda
        venda.mercadopago_payment_id = payment_id
        
        # 5. Processar baseado no tipo de evento
        try:
            if tipo_evento == "payment.approved":
                # Pagamento aprovado → CONFIRMAR venda
                await VendaService.confirmar_venda(db, venda_id, empresa_id)
                
                log.info(
                    "webhook_payment_approved",
                    venda_id=str(venda_id),
                    payment_id=payment_id,
                    valor=float(venda.valor_total)
                )
                
            elif tipo_evento in ["payment.rejected", "payment.cancelled"]:
                # Pagamento rejeitado/cancelado → CANCELAR venda
                motivo = f"Pagamento {tipo_evento.split('.')[1]} pelo Mercado Pago"
                await VendaService.cancelar_venda(
                    db, venda_id, empresa_id, motivo=motivo
                )
                
                log.warning(
                    "webhook_payment_rejected_cancelled",
                    venda_id=str(venda_id),
                    payment_id=payment_id,
                    tipo=tipo_evento
                )
                
            elif tipo_evento == "payment.refunded":
                # Reembolso → Futuro (criar lógica de devolução)
                log.info(
                    "webhook_payment_refunded",
                    venda_id=str(venda_id),
                    payment_id=payment_id
                )
                # TODO: Implementar lógica de reembolso
            
            # 6. Marcar webhook como processado
            await MercadoPagoService.marcar_webhook_processado(
                db, payment_id, tipo_evento, venda_id, payment_data
            )
            
            await db.commit()
            
            return (True, None)
            
        except Exception as e:
            await db.rollback()
            log.error(
                "webhook_processar_erro",
                error=str(e),
                venda_id=str(venda_id),
                payment_id=payment_id
            )
            return (False, str(e))
