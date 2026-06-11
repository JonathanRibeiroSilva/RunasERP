"""
Router de Webhooks (Mercado Pago).
Recebe notificações de pagamento do Mercado Pago.
"""
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from database import get_db
from services.mercadopago_service import MercadoPagoService

router = APIRouter(prefix="/loja", tags=["Webhooks"])
log = structlog.get_logger()


@router.post("/{empresa_slug}/webhook/mercadopago")
async def webhook_mercadopago(
    empresa_slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook do Mercado Pago.
    
    Recebe notificações de mudança de status de pagamento.
    
    **URL de configuração no Mercado Pago:**
    ```
    https://seu-dominio.com/loja/{empresa_slug}/webhook/mercadopago
    ```
    
    **Eventos suportados:**
    - payment.created: Pagamento criado
    - payment.approved: Pagamento aprovado ✅
    - payment.rejected: Pagamento rejeitado ❌
    - payment.cancelled: Pagamento cancelado ❌
    - payment.refunded: Pagamento reembolsado 💰
    
    **Idempotência:**
    Sistema garante que mesmo webhook não é processado duas vezes.
    """
    try:
        # 1. Parsear body
        body = await request.json()
        
        log.info(
            "webhook_recebido",
            empresa_slug=empresa_slug,
            body=body
        )
        
        # 2. Extrair dados do webhook
        tipo = body.get("type")
        action = body.get("action")
        
        # Mercado Pago envia: {"type": "payment", "action": "payment.approved", "data": {"id": "123"}}
        if tipo != "payment":
            log.warning(
                "webhook_tipo_nao_suportado",
                tipo=tipo
            )
            return {"status": "ignored", "reason": "Tipo não suportado"}
        
        # 3. Extrair payment_id
        data = body.get("data", {})
        payment_id = data.get("id")
        
        if not payment_id:
            log.error(
                "webhook_sem_payment_id",
                body=body
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook sem payment_id"
            )
        
        # 4. Determinar tipo de evento
        tipo_evento = action or "payment.created"
        
        # 5. Buscar empresa_id pelo slug
        # TODO: Implementar busca de empresa por slug via HTTP
        empresa_id = 1  # Mock por enquanto
        
        # 6. Processar webhook com idempotência
        sucesso, erro = await MercadoPagoService.processar_webhook_payment(
            db=db,
            empresa_id=empresa_id,
            payment_id=str(payment_id),
            tipo_evento=tipo_evento
        )
        
        if not sucesso:
            log.error(
                "webhook_processar_falhou",
                erro=erro,
                payment_id=payment_id
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=erro or "Erro ao processar webhook"
            )
        
        log.info(
            "webhook_processado_sucesso",
            payment_id=payment_id,
            tipo_evento=tipo_evento
        )
        
        return {"status": "ok", "payment_id": payment_id}
        
    except HTTPException:
        raise
    
    except Exception as e:
        log.error(
            "webhook_erro_geral",
            error=str(e),
            empresa_slug=empresa_slug
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar webhook"
        )


@router.get("/{empresa_slug}/webhook/mercadopago/test")
async def test_webhook(empresa_slug: str):
    """
    Endpoint de teste para verificar se webhook está acessível.
    """
    return {
        "status": "ok",
        "message": "Webhook do Mercado Pago está acessível",
        "empresa_slug": empresa_slug
    }
