"""
Service de Loja Online (E-commerce).
Gerencia checkout e pedidos online.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models.venda import StatusVenda
from schemas.loja import (
    CheckoutRequest,
    CheckoutResponse,
    PedidoClienteResumido,
    RastreamentoPedido
)
from schemas.venda import (
    VendaCreate,
    ItemVendaCreate,
    PagamentoVendaCreate
)
from services.carrinho_service import CarrinhoService
from services.venda_service import VendaService
from repositories.venda_repository import VendaRepository

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
        Processa checkout: converte carrinho em venda.
        
        Fluxo:
        1. Obtém carrinho do Redis
        2. Valida cliente (existente ou cria novo - simplificado)
        3. Cria venda com status PEDIDO
        4. Cria pagamento pendente
        5. Limpa carrinho
        6. Retorna dados da venda
        """
        try:
            # 1. Obter carrinho
            carrinho = await CarrinhoService.obter_ou_criar_carrinho(sessao_id, empresa_id)
            
            if not carrinho.itens:
                raise ValueError("Carrinho está vazio")
            
            # 2. Determinar cliente_id
            cliente_id = data.cliente_id
            
            # TODO: Se cliente_novo fornecido, criar cliente (requer integração com serviço Clientes)
            # Por enquanto, permitir venda sem cliente (balcão)
            if data.cliente_novo and not cliente_id:
                log.warning(
                    "cliente_novo_nao_implementado",
                    email=data.cliente_novo.email
                )
                # Futuramente: criar cliente via HTTP call
                # cliente_id = await criar_cliente_rapido(data.cliente_novo)
            
            # 3. Converter itens do carrinho para ItemVendaCreate
            itens_venda = [
                ItemVendaCreate(
                    produto_id=item.produto_id,
                    variante_id=item.variante_id,
                    quantidade=item.quantidade,
                    preco_unitario=item.preco_unitario
                )
                for item in carrinho.itens
            ]
            
            # 4. Criar venda
            venda_data = VendaCreate(
                empresa_id=empresa_id,
                cliente_id=cliente_id,
                tipo_entrega=data.tipo_entrega,
                observacao=data.observacao,
                itens=itens_venda,
                desconto_tipo=None,
                desconto_valor=0
            )
            
            venda = await VendaService.criar_venda(db, empresa_id, venda_data)
            
            # 5. Limpar carrinho
            await CarrinhoService.limpar_carrinho(sessao_id, empresa_id)
            
            log.info(
                "checkout_processado",
                sessao_id=sessao_id,
                venda_id=str(venda.id),
                numero_venda=venda.numero_venda,
                valor_total=float(venda.valor_total)
            )
            
            # 6. Retornar resposta
            return CheckoutResponse(
                venda_id=venda.id,
                numero_venda=venda.numero_venda,
                status=venda.status.value,
                valor_total=venda.valor_total,
                mensagem=f"Pedido {venda.numero_venda} criado com sucesso! "
                        f"Aguarde a confirmação do pagamento. "
                        f"Use o número do pedido para rastreamento."
            )
            
        except ValueError:
            raise
        except Exception as e:
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
        """
        # Buscar venda
        venda = await VendaRepository.buscar_por_numero(
            db,
            empresa_id,
            numero_venda
        )
        
        if not venda:
            return None
        
        # Montar histórico
        historico = []
        
        if venda.data_pedido:
            historico.append({
                "etapa": "PEDIDO",
                "descricao": "Pedido criado",
                "data": venda.data_pedido.isoformat(),
                "concluido": True
            })
        
        if venda.data_confirmacao:
            historico.append({
                "etapa": "CONFIRMADA",
                "descricao": "Pagamento confirmado",
                "data": venda.data_confirmacao.isoformat(),
                "concluido": True
            })
        else:
            historico.append({
                "etapa": "CONFIRMADA",
                "descricao": "Aguardando confirmação de pagamento",
                "data": None,
                "concluido": False
            })
        
        if venda.data_separacao:
            historico.append({
                "etapa": "SEPARADA",
                "descricao": "Pedido separado",
                "data": venda.data_separacao.isoformat(),
                "concluido": True
            })
        elif venda.status == StatusVenda.CONFIRMADA.value:
            historico.append({
                "etapa": "SEPARADA",
                "descricao": "Aguardando separação",
                "data": None,
                "concluido": False
            })
        
        if venda.data_entregue:
            historico.append({
                "etapa": "ENTREGUE",
                "descricao": "Pedido entregue/retirado",
                "data": venda.data_entregue.isoformat(),
                "concluido": True
            })
        elif venda.status in [StatusVenda.CONFIRMADA.value, StatusVenda.SEPARADA.value]:
            historico.append({
                "etapa": "ENTREGUE",
                "descricao": f"Aguardando {'entrega' if venda.tipo_entrega == 'DELIVERY' else 'retirada'}",
                "data": None,
                "concluido": False
            })
        
        if venda.data_finalizada:
            historico.append({
                "etapa": "FINALIZADA",
                "descricao": "Pedido finalizado",
                "data": venda.data_finalizada.isoformat(),
                "concluido": True
            })
        
        if venda.data_cancelada:
            historico.append({
                "etapa": "CANCELADA",
                "descricao": f"Pedido cancelado: {venda.motivo_cancelamento or 'Sem motivo informado'}",
                "data": venda.data_cancelada.isoformat(),
                "concluido": True
            })
        
        # Determinar próxima etapa
        proxima_etapa = None
        previsao_entrega = None
        
        if venda.status == StatusVenda.PEDIDO.value:
            proxima_etapa = "Aguardando confirmação de pagamento"
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
