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
from utils.tenant import get_empresa_id_by_slug

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
        
        # Log COMPLETO do webhook recebido (incluindo timestamp)
        from datetime import datetime, timezone
        
        log.info(
            "webhook_mercadopago_recebido_completo",
            empresa_slug=empresa_slug,
            timestamp=datetime.now(timezone.utc).isoformat(),
            body=body,
            headers={
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
                "x_request_id": request.headers.get("x-request-id"),
                "x_signature": request.headers.get("x-signature"),
                "x_request_timestamp": request.headers.get("x-request-timestamp")
            },
            client_host=request.client.host if request.client else None,
            method=request.method,
            url=str(request.url)
        )
        
        # 2. Identificar o tipo de notificação.
        #    O Mercado Pago Checkout Pro envia notificações em formatos distintos:
        #      - Webhooks v2: body {"type":"payment","action":"...","data":{"id":...}}
        #      - IPN:         query ?topic=payment|merchant_order&id=...  body {"resource":...,"topic":...}
        #    O cartão de crédito (3DS) é notificado via IPN merchant_order/payment, que antes
        #    caía no "tipo_nao_suportado" e nunca confirmava o pedido.
        query = request.query_params
        topic = body.get("type") or body.get("topic") or query.get("type") or query.get("topic")
        action = body.get("action")
        recurso_id = (
            (body.get("data") or {}).get("id")
            or query.get("id")
            or body.get("id")
        )

        if topic not in ("payment", "merchant_order"):
            log.warning("webhook_tipo_nao_suportado", topic=topic)
            return {"status": "ignored", "reason": "Tipo não suportado"}

        if not recurso_id:
            log.error("webhook_sem_recurso_id", body=body, query=dict(query))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook sem identificador de recurso"
            )

        # 3. Buscar empresa_id pelo slug (resolução multi-tenant via serviço de empresas)
        empresa_id = await get_empresa_id_by_slug(db, empresa_slug)
        if not empresa_id:
            log.error(
                "webhook_empresa_nao_encontrada",
                empresa_slug=empresa_slug,
                recurso_id=recurso_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa com slug '{empresa_slug}' não encontrada"
            )

        # 4. Resolver o(s) payment_id(s) a processar.
        #    payment        -> o próprio id já é o pagamento.
        #    merchant_order -> buscar a ordem e extrair os pagamentos vinculados (cartão 3DS).
        if topic == "payment":
            payment_ids = [str(recurso_id)]
        else:
            payment_ids = await MercadoPagoService.obter_payment_ids_de_merchant_order(
                db, empresa_id, str(recurso_id)
            )

        if not payment_ids:
            log.info(
                "webhook_sem_pagamentos_para_processar",
                recurso_id=recurso_id,
                topic=topic
            )
            return {"status": "ok", "reason": "Sem pagamentos para processar"}

        # 5. Processar cada pagamento com idempotência.
        #    obter_payment_ids_de_merchant_order já ordena aprovados primeiro, evitando que
        #    uma tentativa rejeitada sobrescreva uma aprovada da mesma ordem.
        tipo_evento = action or f"{topic}.notification"
        processados = []
        for payment_id in payment_ids:
            sucesso, erro = await MercadoPagoService.processar_webhook_payment(
                db=db,
                empresa_id=empresa_id,
                payment_id=payment_id,
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
            processados.append(payment_id)

        log.info(
            "webhook_processado_sucesso",
            payment_ids=processados,
            topic=topic,
            tipo_evento=tipo_evento
        )

        return {"status": "ok", "payment_ids": processados}
        
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
