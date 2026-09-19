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
from services.webhook_assinatura import assinatura_valida
from utils.tenant import get_empresa_id_by_slug

router = APIRouter(prefix="/loja", tags=["Webhooks"])
log = structlog.get_logger()


async def _conferir_assinatura(
    db: AsyncSession, empresa_id: int, empresa_slug: str, request: Request, recurso_id
) -> None:
    """
    Recusa a notificação se ela vier assinada errado.

    Duas janelas deliberadamente abertas, ambas com warning para medir antes de
    fechar (uma linha cada, quando o log de prod mostrar que não há tráfego
    legítimo passando por elas):

    - lojista sem segredo gravado: era assim para todo mundo até agora, e
      fechar de imediato pararia o pagamento de quem não colou o segredo;
    - notificação sem cabeçalho `x-signature`: o IPN legado (`?topic=`), que é
      como o cartão com 3DS chega, não assina. Até saber que ninguém depende
      dele, negar aqui é perder venda.
    """
    config = await MercadoPagoService.obter_credenciais(db, empresa_id)
    segredo = config.mercadopago_webhook_secret if config else None
    if not segredo:
        log.warning("webhook_sem_segredo_configurado", empresa_slug=empresa_slug)
        return

    x_signature = request.headers.get("x-signature")
    if not x_signature:
        log.warning("webhook_sem_assinatura", empresa_slug=empresa_slug, recurso_id=recurso_id)
        return

    if not assinatura_valida(
        x_signature, request.headers.get("x-request-id"), str(recurso_id), segredo
    ):
        log.error(
            "webhook_assinatura_invalida",
            empresa_slug=empresa_slug,
            recurso_id=recurso_id,
            client_host=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Assinatura do webhook inválida"
        )


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

        # 4. Conferir a assinatura antes de gastar qualquer chamada à API do MP.
        await _conferir_assinatura(db, empresa_id, empresa_slug, request, recurso_id)

        # 5. Resolver o(s) payment_id(s) a processar.
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

        # 6. Processar cada pagamento com idempotência.
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
