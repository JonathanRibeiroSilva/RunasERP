"""
Service de Notificações via WhatsApp (Evolution API).
Envia notificações para clientes sobre status de pedidos.
"""
from typing import Optional
from uuid import UUID
from decimal import Decimal
import httpx
import structlog

from config import settings

log = structlog.get_logger()


class NotificacaoService:
    """Service para envio de notificações via WhatsApp."""
    
    @staticmethod
    def _formatar_telefone(telefone: str) -> str:
        """
        Formata telefone para envio (remove caracteres especiais).
        
        Args:
            telefone: Telefone com ou sem formatação
        
        Returns:
            str: Telefone apenas números (5511999999999)
        """
        # Remove tudo que não é número
        apenas_numeros = ''.join(filter(str.isdigit, telefone))
        
        # Se não tem código do país (55), adiciona
        if not apenas_numeros.startswith('55'):
            apenas_numeros = '55' + apenas_numeros
        
        return apenas_numeros
    
    @staticmethod
    def _formatar_valor(valor: Decimal) -> str:
        """
        Formata valor monetário para exibição.
        
        Args:
            valor: Valor decimal
        
        Returns:
            str: Valor formatado (R$ 123,45)
        """
        valor_str = f"{valor:.2f}".replace('.', ',')
        return f"R$ {valor_str}"
    
    @staticmethod
    async def enviar_confirmacao_pedido(
        telefone: str,
        numero_venda: str,
        valor_total: Decimal,
        tipo_entrega: str,
        empresa_id: int | None = None
    ) -> bool:
        """
        Envia notificação de confirmação de pedido.
        
        Args:
            telefone: Telefone do cliente
            numero_venda: Número do pedido
            valor_total: Valor total do pedido
            tipo_entrega: DELIVERY ou RETIRADA
        
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            telefone_formatado = NotificacaoService._formatar_telefone(telefone)
            valor_formatado = NotificacaoService._formatar_valor(valor_total)
            
            tipo_entrega_texto = "Entrega" if tipo_entrega == "DELIVERY" else "Retirada"
            
            mensagem = (
                f"🎉 *Pedido Confirmado!*\n\n"
                f"📦 Pedido: *{numero_venda}*\n"
                f"💰 Valor: *{valor_formatado}*\n"
                f"🚚 Tipo: *{tipo_entrega_texto}*\n\n"
                f"Aguarde a confirmação do pagamento!\n"
                f"Você pode rastrear seu pedido usando o número acima."
            )
            
            sucesso = await NotificacaoService._enviar_mensagem(
                telefone_formatado,
                mensagem,
                empresa_id
            )
            
            if sucesso:
                log.info(
                    "notificacao_pedido_enviada",
                    numero_venda=numero_venda,
                    telefone=telefone_formatado[:8] + "****"  # Masked
                )
            
            return sucesso
            
        except Exception as e:
            log.error(
                "erro_enviar_confirmacao_pedido",
                numero_venda=numero_venda,
                error=str(e)
            )
            return False
    
    @staticmethod
    async def enviar_pagamento_confirmado(
        telefone: str,
        numero_venda: str,
        nome_cliente: Optional[str] = None,
        empresa_id: int | None = None
    ) -> bool:
        """
        Envia notificação de pagamento confirmado.
        
        Args:
            telefone: Telefone do cliente
            numero_venda: Número do pedido
            nome_cliente: Nome do cliente (opcional)
        
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            telefone_formatado = NotificacaoService._formatar_telefone(telefone)
            
            saudacao = f"Olá{', ' + nome_cliente if nome_cliente else ''}! "
            
            mensagem = (
                f"✅ *Pagamento Confirmado!*\n\n"
                f"{saudacao}Seu pagamento foi aprovado!\n\n"
                f"📦 Pedido: *{numero_venda}*\n\n"
                f"Agora vamos preparar seu pedido! 📋"
            )
            
            sucesso = await NotificacaoService._enviar_mensagem(
                telefone_formatado,
                mensagem,
                empresa_id
            )
            
            if sucesso:
                log.info(
                    "notificacao_pagamento_enviada",
                    numero_venda=numero_venda,
                    telefone=telefone_formatado[:8] + "****"
                )
            
            return sucesso
            
        except Exception as e:
            log.error(
                "erro_enviar_pagamento_confirmado",
                numero_venda=numero_venda,
                error=str(e)
            )
            return False
    
    @staticmethod
    async def enviar_pedido_separado(
        telefone: str,
        numero_venda: str,
        tipo_entrega: str,
        empresa_id: int | None = None
    ) -> bool:
        """
        Envia notificação de pedido separado.
        
        Args:
            telefone: Telefone do cliente
            numero_venda: Número do pedido
            tipo_entrega: DELIVERY ou RETIRADA
        
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            telefone_formatado = NotificacaoService._formatar_telefone(telefone)
            
            if tipo_entrega == "DELIVERY":
                mensagem = (
                    f"📦 *Pedido Pronto para Envio!*\n\n"
                    f"Pedido: *{numero_venda}*\n\n"
                    f"Seu pedido foi separado e está pronto para envio! 🚚\n"
                    f"Em breve estará a caminho!"
                )
            else:
                mensagem = (
                    f"📦 *Pedido Pronto para Retirada!*\n\n"
                    f"Pedido: *{numero_venda}*\n\n"
                    f"Seu pedido está pronto! ✅\n"
                    f"Você já pode retirar na loja! 🏪"
                )
            
            sucesso = await NotificacaoService._enviar_mensagem(
                telefone_formatado,
                mensagem,
                empresa_id
            )
            
            if sucesso:
                log.info(
                    "notificacao_separado_enviada",
                    numero_venda=numero_venda,
                    telefone=telefone_formatado[:8] + "****"
                )
            
            return sucesso
            
        except Exception as e:
            log.error(
                "erro_enviar_pedido_separado",
                numero_venda=numero_venda,
                error=str(e)
            )
            return False
    
    @staticmethod
    async def enviar_pedido_entregue(
        telefone: str,
        numero_venda: str,
        tipo_entrega: str,
        empresa_id: int | None = None
    ) -> bool:
        """
        Envia notificação de pedido entregue.
        
        Args:
            telefone: Telefone do cliente
            numero_venda: Número do pedido
            tipo_entrega: DELIVERY ou RETIRADA
        
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            telefone_formatado = NotificacaoService._formatar_telefone(telefone)
            
            if tipo_entrega == "DELIVERY":
                mensagem = (
                    f"✅ *Pedido Entregue!*\n\n"
                    f"Pedido: *{numero_venda}*\n\n"
                    f"Seu pedido foi entregue com sucesso! 🎉\n"
                    f"Esperamos que goste! 😊"
                )
            else:
                mensagem = (
                    f"✅ *Pedido Retirado!*\n\n"
                    f"Pedido: *{numero_venda}*\n\n"
                    f"Obrigado pela retirada! 🎉\n"
                    f"Esperamos que goste! 😊"
                )
            
            sucesso = await NotificacaoService._enviar_mensagem(
                telefone_formatado,
                mensagem,
                empresa_id
            )
            
            if sucesso:
                log.info(
                    "notificacao_entregue_enviada",
                    numero_venda=numero_venda,
                    telefone=telefone_formatado[:8] + "****"
                )
            
            return sucesso
            
        except Exception as e:
            log.error(
                "erro_enviar_pedido_entregue",
                numero_venda=numero_venda,
                error=str(e)
            )
            return False
    
    @staticmethod
    async def enviar_pedido_cancelado(
        telefone: str,
        numero_venda: str,
        motivo: Optional[str] = None,
        empresa_id: int | None = None
    ) -> bool:
        """
        Envia notificação de pedido cancelado.
        
        Args:
            telefone: Telefone do cliente
            numero_venda: Número do pedido
            motivo: Motivo do cancelamento (opcional)
        
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            telefone_formatado = NotificacaoService._formatar_telefone(telefone)
            
            mensagem = (
                f"❌ *Pedido Cancelado*\n\n"
                f"Pedido: *{numero_venda}*\n\n"
                f"Seu pedido foi cancelado.\n"
            )
            
            if motivo:
                mensagem += f"\nMotivo: _{motivo}_\n"
            
            mensagem += "\nSe tiver dúvidas, entre em contato conosco!"
            
            sucesso = await NotificacaoService._enviar_mensagem(
                telefone_formatado,
                mensagem,
                empresa_id
            )
            
            if sucesso:
                log.info(
                    "notificacao_cancelado_enviada",
                    numero_venda=numero_venda,
                    telefone=telefone_formatado[:8] + "****"
                )
            
            return sucesso
            
        except Exception as e:
            log.error(
                "erro_enviar_pedido_cancelado",
                numero_venda=numero_venda,
                error=str(e)
            )
            return False
    
    @staticmethod
    async def _enviar_mensagem(
        telefone: str, mensagem: str, empresa_id: int | None = None
    ) -> bool:
        """
        Envia mensagem via Evolution API.
        
        Args:
            telefone: Telefone do destinatário (apenas números)
            mensagem: Mensagem a enviar
        
        Returns:
            bool: True se enviado com sucesso
        """
        try:
            # Evolution do próprio tenant; sem ela, o env global (comportamento antigo)
            from services.configuracao_integracao_service import credenciais_whatsapp
            cred = await credenciais_whatsapp(empresa_id)
            if not cred:
                log.warning("evolution_api_nao_configurada", empresa_id=empresa_id)
                return False
            
            async with httpx.AsyncClient() as client:
                url = f"{cred['url']}/message/sendText/{cred['instance']}"
                headers = {
                    "Content-Type": "application/json",
                    "apikey": cred["api_key"]
                }
                payload = {
                    "number": telefone,
                    "text": mensagem
                }
                
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    return True
                
                log.warning(
                    "evolution_api_erro",
                    status_code=response.status_code,
                    response=response.text
                )
                return False
                
        except Exception as e:
            log.error("erro_enviar_mensagem_evolution", error=str(e))
            return False
