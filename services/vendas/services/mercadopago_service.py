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

from models.venda import Venda, ConfiguracaoPagamento, WebhookProcessado, StatusVenda
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
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Cria preferência de pagamento no Mercado Pago.
        
        Args:
            venda: Venda criada
            empresa_id: ID da empresa
            empresa_slug: Slug da empresa (para webhook URL)
            valor_credito_usado: Valor do crédito usado (pagamento misto)
        
        Returns:
            tuple: (preference_id, init_point, sandbox_init_point, erro)
                - preference_id: ID da preferência criada
                - init_point: URL de produção para redirecionar cliente
                - sandbox_init_point: URL de teste (sandbox) para redirecionar cliente
                - erro: mensagem de erro se falhou
        """
        # Obter credenciais
        config = await MercadoPagoService.obter_credenciais(db, empresa_id)
        if not config:
            return (None, None, None, "Mercado Pago não configurado para esta empresa")
        
        # Calcular valor a pagar (total - crédito usado)
        valor_a_pagar = venda.valor_total
        if valor_credito_usado and valor_credito_usado > 0:
            valor_a_pagar = venda.valor_total - valor_credito_usado
        
        if valor_a_pagar <= 0:
            return (None, None, None, "Valor a pagar deve ser maior que zero")
        
        # Montar itens da preferência
        items = []
        for item in venda.itens:
            item_mp = {
                "title": item.descricao_produto,
                "description": f"Código: {item.codigo_produto}" if item.codigo_produto else None,
                "quantity": int(item.quantidade),
                "unit_price": float(item.preco_unitario),
                "currency_id": "BRL"
            }
            items.append(item_mp)
            
            # 🔍 Log detalhado de cada item
            log.info(
                "item_montado_para_mercadopago",
                venda_id=str(venda.id),
                produto_id=str(item.produto_id),
                descricao_produto_original=item.descricao_produto,
                title_enviado=item_mp["title"],
                codigo=item.codigo_produto,
                quantidade=item.quantidade,
                preco=float(item.preco_unitario)
            )
        
        # Webhook URL (por empresa)
        webhook_url = f"{settings.API_BASE_URL}/loja/{empresa_slug}/webhook/mercadopago"
        
        # Log das URLs configuradas
        log.info(
            "mercadopago_urls_configuradas",
            venda_id=str(venda.id),
            webhook_url=webhook_url,
            frontend_url=settings.FRONTEND_URL,
            api_base_url=settings.API_BASE_URL
        )
        
        # Corrigir rotas de back_urls para /c/ (loja pública)
        success_url = f"{settings.FRONTEND_URL}/c/{empresa_slug}/pedido/{venda.numero_venda}?status=success"
        failure_url = f"{settings.FRONTEND_URL}/c/{empresa_slug}/pedido/{venda.numero_venda}?status=failure"
        pending_url = f"{settings.FRONTEND_URL}/c/{empresa_slug}/pedido/{venda.numero_venda}?status=pending"
        
        log.info(
            "mercadopago_back_urls_geradas",
            venda_id=str(venda.id),
            success_url=success_url,
            failure_url=failure_url,
            pending_url=pending_url
        )
        
        # Montar payload da preferência
        preference_data = {
            "items": items,
            "payer": {},
            "back_urls": {
                "success": success_url,
                "failure": failure_url,
                "pending": pending_url
            },
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
            # Configurações adicionais
            "binary_mode": False,  # False permite pagamentos pendentes (necessário para PIX)
            # NÃO definir "purpose": "wallet_purchase". Esse valor restringe o Checkout Pro a
            # usuários logados no Mercado Pago e DESABILITA o pagamento como convidado — bloqueando
            # o fluxo de cartão de crédito da loja (checkout guest). Sem o campo, o convidado
            # paga com cartão/PIX/boleto sem precisar de conta Mercado Pago.
        }

        # auto_return exige back_urls públicas HTTPS — o MP rejeita localhost com
        # "auto_return invalid". Em dev local o comprador volta pelo botão do checkout;
        # a confirmação do pagamento é feita pelo job verificar_pagamentos_pendentes.
        if success_url.startswith("https://"):
            preference_data["auto_return"] = "approved"
        
        # Adicionar dados do pagador se disponível
        if venda.cliente_id:
            # TODO: Buscar dados do cliente via HTTP
            pass
        elif venda.cliente_convidado_email:
            preference_data["payer"]["email"] = venda.cliente_convidado_email
            if venda.cliente_convidado_nome:
                preference_data["payer"]["name"] = venda.cliente_convidado_nome
        
        log.info(
            "mercadopago_preferencia_montada",
            venda_id=str(venda.id),
            binary_mode=preference_data["binary_mode"],
            auto_return=preference_data.get("auto_return")
        )
        
        # Log do payload COMPLETO que será enviado
        log.info(
            "mercadopago_payload_completo",
            venda_id=str(venda.id),
            payload=preference_data,  # Payload completo para debug
            access_token_length=len(config.mercadopago_access_token),
            access_token_inicio=config.mercadopago_access_token[:20]
        )
        
        try:
            # Log ANTES de fazer a requisição
            log.info(
                "mercadopago_enviando_requisicao",
                venda_id=str(venda.id),
                url=f"{MercadoPagoService.MERCADOPAGO_API_BASE}/checkout/preferences",
                timeout=10.0
            )
            
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
                
                log.info(
                    "mercadopago_resposta_recebida",
                    venda_id=str(venda.id),
                    status_code=response.status_code,
                    headers_count=len(response.headers)
                )
                
                # Se não for 2xx, logar corpo da resposta de erro
                if response.status_code >= 400:
                    error_body = response.text
                    log.error(
                        "mercadopago_erro_resposta",
                        venda_id=str(venda.id),
                        status_code=response.status_code,
                        error_body=error_body[:500]  # Primeiros 500 chars
                    )
                
                response.raise_for_status()
                data = response.json()
                
                preference_id = data.get("id")
                init_point = data.get("init_point")
                sandbox_init_point = data.get("sandbox_init_point")
                
                # Log detalhado da resposta
                log.info(
                    "mercadopago_resposta_completa",
                    venda_id=str(venda.id),
                    preference_id=preference_id,
                    init_point=init_point,
                    sandbox_init_point=sandbox_init_point,
                    has_back_urls=bool(data.get("back_urls")),
                    notification_url=data.get("notification_url"),
                    back_urls_retornadas=data.get("back_urls")  # ✅ Ver se volta correto
                )
                
                if not preference_id or not init_point:
                    log.error(
                        "mercadopago_resposta_invalida",
                        data=data
                    )
                    return (None, None, None, "Resposta inválida do Mercado Pago")
                
                # Salvar preference_id na venda (sem commit - será feito pelo caller)
                venda.mercadopago_preference_id = preference_id
                # NÃO fazer commit aqui - deixar para o fluxo principal fazer
                
                log.info(
                    "mercadopago_preferencia_criada_sucesso",
                    venda_id=str(venda.id),
                    preference_id=preference_id,
                    valor=float(valor_a_pagar),
                    init_point_comeca_com=init_point[:50] if init_point else None,
                    sandbox_init_point_comeca_com=sandbox_init_point[:50] if sandbox_init_point else None
                )
                
                return (preference_id, init_point, sandbox_init_point, None)
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            log.error(
                "mercadopago_erro_http",
                status_code=e.response.status_code,
                detail=error_detail,
                venda_id=str(venda.id)
            )
            return (None, None, None, f"Erro ao criar preferência: {error_detail}")
        
        except Exception as e:
            log.error(
                "mercadopago_erro",
                error=str(e),
                venda_id=str(venda.id)
            )
            return (None, None, None, f"Erro ao criar preferência: {str(e)}")
    
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
    ) -> None:
        """
        Registra o webhook como processado (idempotência por payment_id).

        Não faz commit — o chamador controla a transação para que o marcador e a transição
        de status da venda comitem juntos (atomicidade). A unique constraint em
        payment_id é o gate real contra processamento duplicado concorrente.
        """
        db.add(WebhookProcessado(
            payment_id=payment_id,
            tipo_evento=tipo_evento,
            venda_id=venda_id,
            payload=str(payload) if payload else None
        ))
        await db.flush()

    @staticmethod
    async def _commit_idempotente(db: AsyncSession) -> None:
        """
        Commit que tolera corrida de webhook duplicado.

        Se a unique constraint de payment_id estourar (outra instância marcou o mesmo
        webhook concorrentemente), faz rollback e segue — o evento já foi processado.
        """
        from sqlalchemy.exc import IntegrityError
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            log.info("webhook_marcar_corrida_idempotente")

    @staticmethod
    def _mapear_forma_pagamento(payment_data: Dict[str, Any]):
        """Mapeia o payment_type_id do Mercado Pago para a FormaPagamento interna."""
        from models.venda import FormaPagamento
        mp_type_to_forma = {
            "credit_card": FormaPagamento.CREDITO,
            "debit_card": FormaPagamento.DEBITO,
            "bank_transfer": FormaPagamento.PIX,
            "account_money": FormaPagamento.PIX,
            "ticket": FormaPagamento.PIX,
        }
        return mp_type_to_forma.get(payment_data.get("payment_type_id"), FormaPagamento.PIX)

    @staticmethod
    async def buscar_pagamento_aprovado_por_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Busca na API do Mercado Pago um pagamento APROVADO para a venda (external_reference).

        Revalidação usada antes de cancelar por timeout (C3): evita cancelar uma venda que
        já foi paga mas cujo webhook ainda não chegou.

        Returns:
            dict do pagamento aprovado, ou None se a consulta foi conclusiva e não há
            pagamento aprovado (incluindo quando não há credenciais para revalidar).

        Raises:
            httpx.HTTPError / Exception: se a consulta ao Mercado Pago for inconclusiva
            (API indisponível). O caller NÃO deve cancelar nesse caso — resultado incerto.
        """
        config = await MercadoPagoService.obter_credenciais(db, empresa_id)
        if not config:
            return None  # sem credenciais → impossível revalidar; trata como "sem aprovado"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MercadoPagoService.MERCADOPAGO_API_BASE}/v1/payments/search",
                headers={"Authorization": f"Bearer {config.mercadopago_access_token}"},
                params={"external_reference": str(venda_id), "status": "approved"},
                timeout=10.0,
            )
            response.raise_for_status()
            resultados = response.json().get("results") or []
            for pagamento in resultados:
                if pagamento.get("status") == "approved":
                    return pagamento
            return None
    
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
    async def obter_merchant_order(
        db: AsyncSession,
        empresa_id: int,
        merchant_order_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém uma merchant_order via API do Mercado Pago.

        Notificações IPN de Checkout Pro (incluindo cartão de crédito 3DS) chegam como
        topic=merchant_order; a ordem contém o array `payments` com os pagamentos vinculados.

        Returns:
            dict: Dados da merchant_order ou None se erro.
        """
        config = await MercadoPagoService.obter_credenciais(db, empresa_id)
        if not config:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{MercadoPagoService.MERCADOPAGO_API_BASE}/merchant_orders/{merchant_order_id}",
                    headers={
                        "Authorization": f"Bearer {config.mercadopago_access_token}"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            log.error(
                "mercadopago_obter_merchant_order_erro",
                error=str(e),
                merchant_order_id=merchant_order_id
            )
            return None

    @staticmethod
    async def obter_payment_ids_de_merchant_order(
        db: AsyncSession,
        empresa_id: int,
        merchant_order_id: str
    ) -> list[str]:
        """
        Extrai os payment_ids de uma merchant_order, priorizando pagamentos aprovados.

        A ordenação (aprovados primeiro) garante que uma tentativa rejeitada anterior
        não sobrescreva o status de uma tentativa aprovada da mesma ordem.

        Returns:
            list[str]: payment_ids vinculados à ordem (pode ser vazia).
        """
        order = await MercadoPagoService.obter_merchant_order(
            db, empresa_id, merchant_order_id
        )
        if not order:
            return []

        pagamentos = order.get("payments") or []
        pagamentos.sort(key=lambda p: p.get("status") != "approved")
        return [str(p["id"]) for p in pagamentos if p.get("id")]

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
        from services.venda_service import VendaService, EstoqueIndeterminadoError
        from services.historico_status_service import HistoricoStatusService
        from schemas.venda import ConfirmarVendaRequest, PagamentoVendaCreate
        from repositories.venda_repository import VendaRepository
        from services.webhook_politica import AcaoWebhook, decidir_acao_webhook, eh_cobranca_duplicada

        # 1. Obter detalhes do pagamento (o status real está aqui, não no action do webhook).
        payment_data = await MercadoPagoService.obter_detalhes_pagamento(
            db, empresa_id, payment_id
        )
        if not payment_data:
            return (False, "Não foi possível obter detalhes do pagamento")

        status_pagamento = payment_data.get("status")

        # 2. Idempotência por payment_id (fast path). Reembolsos/chargebacks compartilham o
        #    payment_id do pagamento aprovado (já marcado como processado), por isso NÃO podem
        #    ser curto-circuitados aqui — sua idempotência vem do status REEMBOLSADA da venda e
        #    do ledger idempotente de estorno do serviço de estoque (D2).
        eh_reembolso = status_pagamento in ("refunded", "charged_back")
        if not eh_reembolso and await MercadoPagoService.webhook_ja_processado(db, payment_id):
            log.info("webhook_ja_processado_ignorando", payment_id=payment_id)
            return (True, None)

        # 3. Resolver a venda pelo external_reference.
        external_reference = payment_data.get("external_reference")
        if not external_reference:
            log.warning("webhook_sem_external_reference", payment_id=payment_id)
            return (False, "Webhook sem external_reference")
        try:
            venda_id = UUID(external_reference)
        except ValueError:
            log.error("webhook_external_reference_invalido", external_reference=external_reference)
            return (False, "external_reference inválido")

        try:
            # 4. Travar a venda ANTES de qualquer transição de status (C2). O lock serializa
            #    webhooks concorrentes/fora de ordem do mesmo pedido.
            venda = await VendaRepository.buscar_por_id(
                db, empresa_id, venda_id, com_relacionamentos=True, com_lock=True
            )
            if not venda:
                log.error("webhook_venda_nao_encontrada", venda_id=str(venda_id), payment_id=payment_id)
                return (False, "Venda não encontrada")

            acao = decidir_acao_webhook(venda.status, status_pagamento)

            # 5a. Pagamento não-final → aguardar o webhook final. NÃO marca processado
            #     (senão a idempotência por payment_id bloquearia a aprovação subsequente).
            if acao is AcaoWebhook.AGUARDAR:
                if not venda.mercadopago_payment_id:
                    venda.mercadopago_payment_id = payment_id
                await db.commit()
                log.info(
                    "webhook_pagamento_status_nao_final",
                    payment_id=payment_id, status=status_pagamento, venda_id=str(venda_id)
                )
                return (True, None)

            # 5b. Ignorar: anti-downgrade, idempotente (já confirmada) ou pago-após-terminal.
            #     NUNCA sobrescreve o payment_id aprovado nem rebaixa o status.
            if acao is AcaoWebhook.IGNORAR:
                if status_pagamento == "approved" and venda.status in (
                    StatusVenda.CANCELADA.value, StatusVenda.REEMBOLSADA.value
                ):
                    log.critical(
                        "webhook_pago_apos_cancelamento_revisar_manual",
                        venda_id=str(venda_id), payment_id=payment_id, status_venda=venda.status
                    )
                elif eh_cobranca_duplicada(
                    venda.status, status_pagamento, payment_id, venda.mercadopago_payment_id
                ):
                    # Não sobrescreve o payment_id da venda: ele é o pagamento que a
                    # confirmou. Este é o que precisa ser devolvido.
                    log.critical(
                        "pagamento_duplicado_reembolso_necessario",
                        venda_id=str(venda_id),
                        empresa_id=empresa_id,
                        payment_id=str(payment_id),
                        payment_id_da_venda=venda.mercadopago_payment_id,
                        valor=payment_data.get("transaction_amount"),
                    )
                    await HistoricoStatusService.registrar_mudanca(
                        db, venda.id, venda.status, venda.status, None,
                        f"Segundo pagamento aprovado ({payment_id}) para venda já confirmada "
                        f"pelo pagamento {venda.mercadopago_payment_id or 'fora do Mercado Pago'}"
                        " — cobrança em duplicidade, reembolso manual necessário.",
                    )
                else:
                    log.info(
                        "webhook_ignorado_anti_downgrade",
                        venda_id=str(venda_id), payment_id=payment_id,
                        status_venda=venda.status, status_pagamento=status_pagamento
                    )
                await MercadoPagoService.marcar_webhook_processado(
                    db, payment_id, tipo_evento, venda_id, payment_data
                )
                await MercadoPagoService._commit_idempotente(db)
                return (True, None)

            # 5c. Confirmar: aprovado e venda ainda não confirmada.
            if acao is AcaoWebhook.CONFIRMAR:
                venda.mercadopago_payment_id = payment_id
                await db.flush()  # garante que confirmar_venda enxergue o payment_id
                confirmar_data = ConfirmarVendaRequest(
                    pagamentos=[
                        PagamentoVendaCreate(
                            forma_pagamento=MercadoPagoService._mapear_forma_pagamento(payment_data),
                            valor_pago=venda.valor_total,
                            comprovante=str(payment_id),
                        )
                    ]
                )
                # confirmar_venda gerencia o próprio commit (idempotente; baixa de estoque
                # idempotente + 3 estados; pode lançar EstoqueIndeterminadoError).
                await VendaService.confirmar_venda(db, empresa_id, venda_id, confirmar_data)

                # Limpar carrinho (best-effort, não falha o webhook).
                if venda.sessao_carrinho_id:
                    try:
                        from services.carrinho_service import CarrinhoService
                        await CarrinhoService.limpar_carrinho(venda.sessao_carrinho_id, empresa_id)
                    except Exception as e:
                        log.warning("erro_limpar_carrinho_webhook", venda_id=str(venda_id), error=str(e))

                await MercadoPagoService.marcar_webhook_processado(
                    db, payment_id, tipo_evento, venda_id, payment_data
                )
                await MercadoPagoService._commit_idempotente(db)
                log.info(
                    "webhook_payment_approved",
                    venda_id=str(venda_id), payment_id=payment_id, valor=float(venda.valor_total)
                )
                return (True, None)

            # 5d. Marcar pendente: negado em venda ainda não paga → mantém p/ nova tentativa.
            if acao is AcaoWebhook.MARCAR_PENDENTE:
                status_anterior = venda.status
                venda.mercadopago_payment_id = payment_id
                if venda.status != StatusVenda.PENDENTE_PAGAMENTO.value:
                    venda.status = StatusVenda.PENDENTE_PAGAMENTO.value
                    await HistoricoStatusService.registrar_mudanca(
                        db, venda.id, status_anterior, StatusVenda.PENDENTE_PAGAMENTO.value,
                        None, f"Pagamento {status_pagamento} — aguardando nova tentativa"
                    )
                log.warning(
                    "webhook_payment_rejected_cancelled",
                    venda_id=str(venda_id), payment_id=payment_id, tipo=tipo_evento
                )
                await MercadoPagoService.marcar_webhook_processado(
                    db, payment_id, tipo_evento, venda_id, payment_data
                )
                await MercadoPagoService._commit_idempotente(db)
                return (True, None)

            # 5e. Reembolso: devolve o estoque baixado (idempotente — D2) e marca a venda
            #     REEMBOLSADA. NÃO insere WebhookProcessado: o payment_id já foi marcado na
            #     aprovação (a unique constraint colidiria); a idempotência do reembolso vem do
            #     status REEMBOLSADA da venda + ledger de estorno do estoque. Solta o lock atual
            #     (nenhuma escrita feita) e delega para reembolsar_venda, que reabre com lock próprio.
            if acao is AcaoWebhook.REEMBOLSO:
                await db.rollback()
                await VendaService.reembolsar_venda(db, empresa_id, venda_id)
                log.info(
                    "webhook_payment_refunded_estornado",
                    venda_id=str(venda_id), payment_id=payment_id
                )
                return (True, None)

            return (True, None)

        except EstoqueIndeterminadoError as e:
            # Venda paga, baixa de estoque indeterminada: já marcada p/ reconciliação e
            # comitada em confirmar_venda. Responde erro → Mercado Pago reentrega o webhook.
            log.warning(
                "webhook_estoque_indeterminado",
                venda_id=str(venda_id), payment_id=payment_id, motivo=str(e)
            )
            return (False, f"Baixa de estoque indeterminada: {e}")
        except Exception as e:
            await db.rollback()
            log.error(
                "webhook_processar_erro",
                error=str(e), venda_id=str(venda_id), payment_id=payment_id
            )
            return (False, str(e))
