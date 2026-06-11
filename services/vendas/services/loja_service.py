"""
Service de Loja Online (E-commerce).
Gerencia checkout e pedidos online.
"""
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import httpx

from models.venda import StatusVenda, FormaPagamento, TipoEntrega
from schemas.loja import (
    CheckoutRequest,
    CheckoutResponse,
    PedidoClienteResumido,
    RastreamentoPedido
)
from schemas.venda import (
    VendaCreate,
    ItemVendaCreate
)
from services.carrinho_service import CarrinhoService
from services.venda_service import VendaService
from services.reserva_temporaria_service import ReservaTemporariaService
from services.entrega_service import EntregaService
from services.cliente_validacao_service import ClienteValidacaoService
from services.mercadopago_service import MercadoPagoService
from services.historico_status_service import HistoricoStatusService
from services.notificacao_service import NotificacaoService
from services.cache_service import CacheService
from repositories.venda_repository import VendaRepository
from config import settings

log = structlog.get_logger()


class LojaService:
    """Service para operações de loja online."""
    
    @staticmethod
    async def processar_checkout(
        db: AsyncSession,
        sessao_id: str,
        empresa_id: int,
        data: CheckoutRequest
    ) -> CheckoutResponse:
        """
        Processa checkout completo: converte carrinho em venda.
        
        Fluxo completo:
        1. Obtém e valida carrinho do Redis
        2. Valida cliente (existente ou convidado)
        3. Se cliente cadastrado com FIADO, verifica permite_fiado_online
        4. Calcula taxa de entrega (se DELIVERY)
        5. Valida estoque com reserva de 5min (checkout)
        6. Cria venda com status apropriado (PEDIDO ou PENDENTE_PAGAMENTO)
        7. Se pagamento online, cria preferência Mercado Pago
        8. Registra histórico de status
        9. Envia notificação WhatsApp
        10. Libera reservas temporárias do carrinho
        11. Limpa carrinho
        12. Retorna dados da venda
        """
        try:
            # 1. Obter carrinho
            carrinho = await CarrinhoService.obter_ou_criar_carrinho(sessao_id, empresa_id)
            
            if not carrinho.itens:
                raise ValueError("Carrinho está vazio")
            
            # 2. Determinar e validar cliente
            cliente_id = data.cliente_id
            cliente_info = None
            
            # 2.1 Cliente convidado (guest)
            if data.cliente_novo and not cliente_id:
                # Validar dados do cliente convidado
                cliente_validado = await ClienteValidacaoService.validar_cliente_convidado(
                    nome=data.cliente_novo.nome,
                    telefone=data.cliente_novo.telefone,
                    email=data.cliente_novo.email if hasattr(data.cliente_novo, 'email') else None,
                    cpf=data.cliente_novo.cpf if hasattr(data.cliente_novo, 'cpf') else None
                )
                
                cliente_info = {
                    'nome': cliente_validado['nome'],
                    'telefone': cliente_validado['telefone'],
                    'email': cliente_validado.get('email'),
                    'cpf': cliente_validado.get('cpf')
                }
                
                log.info(
                    "checkout_cliente_convidado",
                    nome=cliente_info['nome'],
                    telefone_masked=cliente_info['telefone'][:8] + "****"
                )
            
            # 2.2 Cliente cadastrado
            elif cliente_id:
                # Buscar cliente no serviço de clientes
                cliente_info = await VendaService.verificar_cliente_existe(empresa_id, cliente_id)
                if not cliente_info:
                    raise ValueError("Cliente não encontrado ou inválido")
                
                # Se tem FIADO nos pagamentos, verificar permite_fiado_online
                tem_fiado = any(
                    p.forma_pagamento == FormaPagamento.FIADO 
                    for p in data.pagamentos
                )
                
                if tem_fiado and not cliente_info.get('permite_fiado_online', False):
                    raise ValueError(
                        "Cliente não autorizado para compras fiadas online. "
                        "Entre em contato com a loja."
                    )
            
            # 3. Calcular taxa de entrega
            valor_frete = Decimal('0.0')
            if data.tipo_entrega == TipoEntrega.DELIVERY:
                if not data.endereco_entrega:
                    raise ValueError("Endereço de entrega obrigatório para DELIVERY")
                
                # Calcular taxa via EntregaService
                valor_frete = await EntregaService.calcular_taxa_entrega(
                    db,
                    empresa_id,
                    data.endereco_entrega.cep,
                    data.endereco_entrega.bairro
                )
            
            # 4. Validar estoque e criar reservas de checkout (5min)
            # Liberar reservas temporárias do carrinho (15min) e criar reservas de checkout (5min)
            for item in carrinho.itens:
                # Liberar reserva do carrinho
                await ReservaTemporariaService.liberar_reserva(
                    db,
                    sessao_id,
                    empresa_id,
                    item.produto_id,
                    item.variante_id
                )
                
                # Criar reserva de checkout (5min)
                disponivel = await ReservaTemporariaService.obter_estoque_disponivel(
                    db,
                    empresa_id,
                    item.produto_id,
                    item.variante_id
                )
                
                if disponivel < item.quantidade:
                    raise ValueError(
                        f"Estoque insuficiente para {item.descricao_produto}. "
                        f"Disponível: {disponivel}, Solicitado: {item.quantidade}"
                    )
                
                # Reservar com TTL de 5min (checkout)
                await ReservaTemporariaService.reservar(
                    db,
                    sessao_id,
                    empresa_id,
                    item.produto_id,
                    item.variante_id,
                    item.quantidade,
                    ttl_minutos=5
                )
            
            # 5. Calcular total dos pagamentos
            total_pagamentos = sum(p.valor for p in data.pagamentos)
            subtotal_carrinho = carrinho.subtotal + valor_frete
            
            if total_pagamentos < subtotal_carrinho:
                raise ValueError(
                    f"Total dos pagamentos (R$ {total_pagamentos}) é menor que o total do pedido (R$ {subtotal_carrinho})"
                )
            
            # 6. Converter itens do carrinho para ItemVendaCreate
            itens_venda = [
                ItemVendaCreate(
                    produto_id=item.produto_id,
                    variante_id=item.variante_id,
                    quantidade=item.quantidade,
                    preco_unitario=item.preco_unitario
                )
                for item in carrinho.itens
            ]
            
            # 7. Determinar status inicial
            tem_pagamento_online = any(
                p.forma_pagamento in [FormaPagamento.PIX, FormaPagamento.DEBITO, FormaPagamento.CREDITO]
                for p in data.pagamentos
            )
            
            status_inicial = StatusVenda.PENDENTE_PAGAMENTO if tem_pagamento_online else StatusVenda.PEDIDO
            
            # 8. Criar venda
            venda_data = VendaCreate(
                empresa_id=empresa_id,
                cliente_id=cliente_id,
                tipo_entrega=data.tipo_entrega,
                observacao=data.observacao,
                itens=itens_venda,
                desconto_tipo=None,
                desconto_valor=Decimal('0.0')
            )
            
            venda = await VendaService.criar_venda(db, empresa_id, venda_data)
            
            # 8.1 Atualizar campos adicionais da venda
            updates = {
                'status': status_inicial.value,
                'valor_frete': valor_frete
            }
            
            # Se cliente convidado, salvar dados
            if cliente_info and not cliente_id:
                updates.update({
                    'cliente_convidado_nome': cliente_info['nome'],
                    'cliente_convidado_telefone': cliente_info['telefone'],
                    'cliente_convidado_email': cliente_info.get('email'),
                    'cliente_convidado_cpf': cliente_info.get('cpf')
                })
            
            # Se DELIVERY, salvar endereço
            if data.tipo_entrega == TipoEntrega.DELIVERY and data.endereco_entrega:
                updates.update({
                    'endereco_logradouro': data.endereco_entrega.logradouro,
                    'endereco_numero': data.endereco_entrega.numero,
                    'endereco_complemento': data.endereco_entrega.complemento,
                    'endereco_bairro': data.endereco_entrega.bairro,
                    'endereco_cidade': data.endereco_entrega.cidade,
                    'endereco_estado': data.endereco_entrega.estado,
                    'endereco_cep': data.endereco_entrega.cep
                })
            
            venda = await VendaRepository.atualizar(
                db,
                empresa_id,
                venda.id,
                **updates
            )
            
            # 9. Registrar histórico de status
            await HistoricoStatusService.registrar_mudanca(
                db,
                venda.id,
                None,  # Status anterior (primeira mudança)
                status_inicial.value,
                None,  # Sistema
                f"Pedido criado via loja online com {'pagamento online pendente' if tem_pagamento_online else 'pagamento offline'}"
            )
            
            # 10. Se pagamento online, criar preferência Mercado Pago
            mercadopago_init_point = None
            if tem_pagamento_online:
                pagamento_online = next(
                    p for p in data.pagamentos
                    if p.forma_pagamento in [FormaPagamento.PIX, FormaPagamento.DEBITO, FormaPagamento.CREDITO]
                )
                
                try:
                    preferencia = await MercadoPagoService.criar_preferencia(
                        db,
                        empresa_id,
                        venda.id,
                        venda.numero_venda,
                        carrinho.itens,
                        pagamento_online.valor,
                        valor_frete
                    )
                    
                    mercadopago_init_point = preferencia.get('init_point')
                    
                    # Salvar preference_id na venda
                    await VendaRepository.atualizar(
                        db,
                        empresa_id,
                        venda.id,
                        mercadopago_preference_id=preferencia.get('id')
                    )
                    
                except Exception as e:
                    log.error(
                        "erro_criar_preferencia_mercadopago",
                        venda_id=str(venda.id),
                        error=str(e)
                    )
                    # Não falhar o checkout por erro no Mercado Pago
                    # Cliente pode pagar depois manualmente
            
            # 11. Enviar notificação WhatsApp (não bloquear checkout se falhar)
            try:
                telefone = None
                if cliente_info:
                    telefone = cliente_info.get('telefone')
                
                if telefone:
                    await NotificacaoService.enviar_confirmacao_pedido(
                        telefone,
                        venda.numero_venda,
                        venda.valor_total,
                        venda.tipo_entrega
                    )
            except Exception as e:
                log.warning(
                    "erro_enviar_notificacao_checkout",
                    venda_id=str(venda.id),
                    error=str(e)
                )
            
            # 12. Limpar carrinho
            await CarrinhoService.limpar_carrinho(sessao_id, empresa_id)
            
            await db.commit()
            
            log.info(
                "checkout_processado",
                sessao_id=sessao_id,
                venda_id=str(venda.id),
                numero_venda=venda.numero_venda,
                valor_total=float(venda.valor_total),
                status=status_inicial.value
            )
            
            # 13. Retornar resposta
            mensagem = f"Pedido {venda.numero_venda} criado com sucesso! "
            
            if tem_pagamento_online:
                mensagem += "Complete o pagamento para confirmar seu pedido."
            else:
                mensagem += "Aguarde a confirmação do pagamento."
            
            return CheckoutResponse(
                venda_id=venda.id,
                numero_venda=venda.numero_venda,
                status=status_inicial.value,
                valor_total=venda.valor_total,
                mercadopago_init_point=mercadopago_init_point,
                mensagem=mensagem
            )
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_processar_checkout", error=str(e))
            raise
    
    @staticmethod
    async def listar_pedidos_cliente(
        db: AsyncSession,
        empresa_id: int,
        cliente_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[PedidoClienteResumido]:
        """
        Lista pedidos de um cliente específico (área do cliente).
        """
        vendas, _ = await VendaService.listar_vendas(
            db,
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            skip=skip,
            limit=limit
        )
        
        pedidos = []
        for venda in vendas:
            pedidos.append(
                PedidoClienteResumido(
                    id=venda.id,
                    numero_venda=venda.numero_venda,
                    data_pedido=venda.data_pedido,
                    status=venda.status.value,
                    valor_total=venda.valor_total,
                    quantidade_itens=len(venda.itens)
                )
            )
        
        return pedidos
    
    @staticmethod
    async def rastrear_pedido(
        db: AsyncSession,
        empresa_id: int,
        numero_venda: str
    ) -> Optional[RastreamentoPedido]:
        """
        Rastreia pedido pelo número da venda.
        Retorna histórico completo e próxima etapa esperada.
        
        Usa dados do `historico_status_venda` para timeline completa.
        """
        from services.historico_status_service import HistoricoStatusService
        
        # Buscar venda
        venda = await VendaRepository.buscar_por_numero(
            db,
            empresa_id,
            numero_venda
        )
        
        if not venda:
            return None
        
        # Buscar histórico de status
        historico_db = await HistoricoStatusService.listar_por_venda(db, venda.id)
        
        # Montar timeline do histórico
        historico = []
        
        for h in historico_db:
            historico.append({
                "etapa": h.status_novo,
                "descricao": h.observacao or self._get_descricao_status(h.status_novo),
                "data": h.alterado_em.isoformat(),
                "concluido": True,
                "alterado_por": "sistema" if not h.alterado_por else "usuario"
            })
        
        # Se não tem histórico, usar dados das datas da venda (backward compatibility)
        if not historico:
            historico = self._montar_historico_legado(venda)
        
        # Determinar próxima etapa
        proxima_etapa = None
        previsao_entrega = None
        
        if venda.status == StatusVenda.PEDIDO.value:
            proxima_etapa = "Aguardando confirmação de pagamento"
        elif venda.status == StatusVenda.PENDENTE_PAGAMENTO.value:
            proxima_etapa = "Aguardando pagamento online (5 minutos)"
        elif venda.status == StatusVenda.CONFIRMADA.value:
            proxima_etapa = "Seu pedido será separado em breve"
        elif venda.status == StatusVenda.SEPARADA.value:
            if venda.tipo_entrega == "DELIVERY":
                proxima_etapa = "Seu pedido está pronto para envio"
                previsao_entrega = "Entrega em até 2 dias úteis"
            else:
                proxima_etapa = "Seu pedido está pronto para retirada"
        elif venda.status == StatusVenda.ENTREGUE.value:
            proxima_etapa = "Aguardando confirmação final"
        elif venda.status == StatusVenda.FINALIZADA.value:
            proxima_etapa = "Pedido concluído"
        elif venda.status == StatusVenda.CANCELADA.value:
            proxima_etapa = "Pedido cancelado"
            if venda.motivo_cancelamento:
                proxima_etapa += f" - {venda.motivo_cancelamento}"
        elif venda.status == StatusVenda.REEMBOLSADA.value:
            proxima_etapa = "Pedido reembolsado"
        
        return RastreamentoPedido(
            numero_venda=venda.numero_venda,
            status_atual=venda.status,
            data_pedido=venda.data_pedido,
            data_confirmacao=venda.data_confirmacao,
            data_separacao=venda.data_separacao,
            data_entregue=venda.data_entregue,
            data_finalizada=venda.data_finalizada,
            data_cancelada=venda.data_cancelada,
            tipo_entrega=venda.tipo_entrega,
            valor_total=venda.valor_total,
            historico=historico,
            proxima_etapa=proxima_etapa,
            previsao_entrega=previsao_entrega
        )
    
    @staticmethod
    def _get_descricao_status(status: str) -> str:
        """Retorna descrição amigável do status."""
        descricoes = {
            StatusVenda.PEDIDO.value: "Pedido criado",
            StatusVenda.PENDENTE_PAGAMENTO.value: "Aguardando pagamento online",
            StatusVenda.CONFIRMADA.value: "Pagamento confirmado",
            StatusVenda.SEPARADA.value: "Pedido separado",
            StatusVenda.EM_ENTREGA.value: "Pedido em entrega",
            StatusVenda.ENTREGUE.value: "Pedido entregue/retirado",
            StatusVenda.FINALIZADA.value: "Pedido finalizado",
            StatusVenda.CANCELADA.value: "Pedido cancelado",
            StatusVenda.REEMBOLSADA.value: "Pedido reembolsado"
        }
        return descricoes.get(status, status)
    
    @staticmethod
    def _montar_historico_legado(venda) -> list:
        """Monta histórico usando datas da venda (backward compatibility)."""
        historico = []
        
        if venda.data_pedido:
            historico.append({
                "etapa": "PEDIDO",
                "descricao": "Pedido criado",
                "data": venda.data_pedido.isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_confirmacao:
            historico.append({
                "etapa": "CONFIRMADA",
                "descricao": "Pagamento confirmado",
                "data": venda.data_confirmacao.isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_separacao:
            historico.append({
                "etapa": "SEPARADA",
                "descricao": "Pedido separado",
                "data": venda.data_separacao.isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_entregue:
            historico.append({
                "etapa": "ENTREGUE",
                "descricao": "Pedido entregue/retirado",
                "data": venda.data_entregue.isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_finalizada:
            historico.append({
                "etapa": "FINALIZADA",
                "descricao": "Pedido finalizado",
                "data": venda.data_finalizada.isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        if venda.data_cancelada:
            descricao = "Pedido cancelado"
            if venda.motivo_cancelamento:
                descricao += f": {venda.motivo_cancelamento}"
            
            historico.append({
                "etapa": "CANCELADA",
                "descricao": descricao,
                "data": venda.data_cancelada.isoformat(),
                "concluido": True,
                "alterado_por": "sistema"
            })
        
        return historico
