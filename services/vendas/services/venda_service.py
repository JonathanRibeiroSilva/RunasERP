"""
Service de Vendas.
Contém a lógica de negócio para gestão de vendas.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import structlog

from models.venda import (
    StatusVenda,
    TipoDesconto,
    FormaPagamento,
    StatusReserva
)
from repositories.venda_repository import (
    VendaRepository,
    ItemVendaRepository,
    PagamentoVendaRepository,
    ReservaEstoqueVendaRepository
)
from schemas.venda import (
    VendaCreate,
    VendaUpdate,
    VendaDetalhada,
    ItemVendaCreate,
    PagamentoVendaCreate,
    ConfirmarVendaRequest,
    CancelarVendaRequest,
    RelatorioVendas
)
from config import settings
from utils.numero_venda import gerar_numero_venda

log = structlog.get_logger()


class VendaService:
    """Service para operações de venda."""

    @staticmethod
    async def verificar_produto_existe(produto_id: UUID, variante_id: Optional[UUID] = None) -> dict:
        """
        Verifica se produto/variante existe no serviço de produtos.
        Retorna dados do produto se existir.
        """
        try:
            async with httpx.AsyncClient() as client:
                if variante_id:
                    url = f"{settings.PRODUTOS_URL}/produtos/{produto_id}/variantes/{variante_id}"
                else:
                    url = f"{settings.PRODUTOS_URL}/produtos/{produto_id}"
                
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            log.error("erro_verificar_produto", error=str(e), produto_id=str(produto_id))
            return None

    @staticmethod
    async def verificar_cliente_existe(empresa_id: int, cliente_id: UUID) -> dict:
        """Verifica se cliente existe e está ativo no serviço de clientes."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.CLIENTES_URL}/clientes/{cliente_id}"
                headers = {"X-Empresa-Id": str(empresa_id)}
                
                response = await client.get(url, headers=headers, timeout=5.0)
                if response.status_code == 200:
                    cliente = response.json()
                    if not cliente.get("ativo"):
                        raise ValueError("Cliente está inativo")
                    if cliente.get("bloqueado"):
                        raise ValueError("Cliente está bloqueado")
                    return cliente
                return None
        except ValueError:
            raise
        except Exception as e:
            log.error("erro_verificar_cliente", error=str(e), cliente_id=str(cliente_id))
            return None

    @staticmethod
    async def reservar_estoque(
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID],
        quantidade: Decimal,
        documento: str
    ) -> bool:
        """Reserva estoque no serviço de estoque."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.ESTOQUE_URL}/estoque/reservar"
                headers = {"X-Empresa-Id": str(empresa_id)}
                payload = {
                    "empresa_id": empresa_id,
                    "produto_id": str(produto_id),
                    "variante_id": str(variante_id) if variante_id else None,
                    "quantidade": float(quantidade),
                    "documento": documento
                }
                
                response = await client.post(url, json=payload, headers=headers, timeout=5.0)
                return response.status_code in [200, 201]
        except Exception as e:
            log.error("erro_reservar_estoque", error=str(e), produto_id=str(produto_id))
            return False

    @staticmethod
    async def liberar_reserva_estoque(
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID],
        quantidade: Decimal,
        documento: str
    ) -> bool:
        """Libera reserva de estoque no serviço de estoque."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.ESTOQUE_URL}/estoque/liberar-reserva"
                headers = {"X-Empresa-Id": str(empresa_id)}
                payload = {
                    "empresa_id": empresa_id,
                    "produto_id": str(produto_id),
                    "variante_id": str(variante_id) if variante_id else None,
                    "quantidade": float(quantidade),
                    "documento": documento
                }
                
                response = await client.post(url, json=payload, headers=headers, timeout=5.0)
                return response.status_code in [200, 201]
        except Exception as e:
            log.error("erro_liberar_reserva", error=str(e), produto_id=str(produto_id))
            return False

    @staticmethod
    async def baixar_estoque(
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID],
        quantidade: Decimal,
        documento: str
    ) -> bool:
        """Baixa estoque definitivamente no serviço de estoque."""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.ESTOQUE_URL}/estoque/saida"
                headers = {"X-Empresa-Id": str(empresa_id)}
                payload = {
                    "empresa_id": empresa_id,
                    "produto_id": str(produto_id),
                    "variante_id": str(variante_id) if variante_id else None,
                    "quantidade": float(quantidade),
                    "motivo": "Venda",
                    "documento": documento
                }
                
                response = await client.post(url, json=payload, headers=headers, timeout=5.0)
                return response.status_code in [200, 201]
        except Exception as e:
            log.error("erro_baixar_estoque", error=str(e), produto_id=str(produto_id))
            return False

    @staticmethod
    def calcular_totais(
        itens: List[dict],
        desconto_tipo: Optional[TipoDesconto],
        desconto_valor: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """
        Calcula subtotal e total da venda.
        
        Returns:
            Tuple[Decimal, Decimal]: (subtotal, valor_total)
        """
        subtotal = sum(Decimal(str(item['subtotal'])) for item in itens)
        
        valor_desconto = Decimal('0.0')
        if desconto_tipo == TipoDesconto.PERCENTUAL:
            valor_desconto = subtotal * (desconto_valor / Decimal('100'))
        elif desconto_tipo == TipoDesconto.VALOR_FIXO:
            valor_desconto = desconto_valor
        
        valor_total = subtotal - valor_desconto
        
        if valor_total < 0:
            valor_total = Decimal('0.0')
        
        return subtotal, valor_total

    @staticmethod
    async def criar_venda(
        db: AsyncSession,
        empresa_id: int,
        data: VendaCreate
    ) -> VendaDetalhada:
        """
        Cria uma nova venda com itens e reserva de estoque.
        Status inicial: PEDIDO
        """
        try:
            async with db.begin_nested():
                # 1. Validar cliente se fornecido
                if data.cliente_id:
                    cliente = await VendaService.verificar_cliente_existe(empresa_id, data.cliente_id)
                    if not cliente:
                        raise ValueError("Cliente não encontrado ou inválido")
                
                # 2. Validar produtos e buscar dados
                itens_dados = []
                for item in data.itens:
                    produto = await VendaService.verificar_produto_existe(
                        item.produto_id,
                        item.variante_id
                    )
                    if not produto:
                        raise ValueError(f"Produto {item.produto_id} não encontrado")
                    
                    # Usar preço do produto se não fornecido
                    preco_unitario = item.preco_unitario if item.preco_unitario else Decimal(str(produto.get('preco_venda', 0)))
                    subtotal = item.quantidade * preco_unitario
                    
                    itens_dados.append({
                        'produto_id': item.produto_id,
                        'variante_id': item.variante_id,
                        'codigo_produto': produto.get('codigo', produto.get('sku')),
                        'descricao_produto': produto.get('nome'),
                        'quantidade': item.quantidade,
                        'preco_unitario': preco_unitario,
                        'subtotal': subtotal
                    })
                
                # 3. Calcular totais
                subtotal, valor_total = VendaService.calcular_totais(
                    itens_dados,
                    data.desconto_tipo,
                    data.desconto_valor
                )
                
                # 4. Gerar número da venda
                sequencia = await VendaRepository.obter_proxima_sequencia(db, empresa_id)
                numero_venda = gerar_numero_venda(empresa_id, sequencia)
                
                # 5. Criar venda
                venda = await VendaRepository.criar(
                    db,
                    empresa_id=empresa_id,
                    numero_venda=numero_venda,
                    cliente_id=data.cliente_id,
                    tipo_entrega=data.tipo_entrega.value,
                    observacao=data.observacao,
                    subtotal=subtotal,
                    desconto_tipo=data.desconto_tipo.value if data.desconto_tipo else None,
                    desconto_valor=data.desconto_valor,
                    valor_total=valor_total,
                    status=StatusVenda.PEDIDO.value
                )
                
                # 6. Criar itens
                itens_criados = []
                reservas_dados = []
                
                for item_data in itens_dados:
                    item_data['venda_id'] = venda.id
                    item = await ItemVendaRepository.criar(db, **item_data)
                    itens_criados.append(item)
                    
                    # Preparar reserva
                    reservas_dados.append({
                        'venda_id': venda.id,
                        'item_venda_id': item.id,
                        'produto_id': item.produto_id,
                        'variante_id': item.variante_id,
                        'quantidade_reservada': item.quantidade,
                        'status': StatusReserva.RESERVADA.value
                    })
                
                # 7. RESERVAR ESTOQUE
                for item in itens_criados:
                    sucesso = await VendaService.reservar_estoque(
                        empresa_id,
                        item.produto_id,
                        item.variante_id,
                        item.quantidade,
                        numero_venda
                    )
                    if not sucesso:
                        raise ValueError(f"Erro ao reservar estoque para produto {item.descricao_produto}")
                    
                    # Marcar item como reservado
                    await ItemVendaRepository.atualizar(db, item.id, estoque_reservado=True)
                
                # 8. Criar reservas no banco
                await ReservaEstoqueVendaRepository.criar_varias(db, reservas_dados)
            
            await db.commit()
            
            log.info(
                "venda_criada",
                venda_id=venda.id,
                numero_venda=numero_venda,
                empresa_id=empresa_id,
                valor_total=float(valor_total)
            )
            
            # Buscar venda completa
            return await VendaService.buscar_venda(db, empresa_id, venda.id)
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_criar_venda", error=str(e))
            raise

    @staticmethod
    async def buscar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID
    ) -> Optional[VendaDetalhada]:
        """Busca venda por ID com todos relacionamentos."""
        venda = await VendaRepository.buscar_por_id(
            db,
            empresa_id,
            venda_id,
            com_relacionamentos=True
        )
        if not venda:
            return None
        
        return VendaDetalhada.model_validate(venda)

    @staticmethod
    async def listar_vendas(
        db: AsyncSession,
        empresa_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StatusVenda] = None,
        cliente_id: Optional[UUID] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> Tuple[List[VendaDetalhada], int]:
        """Lista vendas isoladas por empresa."""
        vendas, total = await VendaRepository.listar(
            db,
            empresa_id=empresa_id,
            skip=skip,
            limit=limit,
            status=status,
            cliente_id=cliente_id,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        vendas_response = []
        for venda in vendas:
            # Buscar com relacionamentos
            venda_completa = await VendaRepository.buscar_por_id(
                db,
                empresa_id,
                venda.id,
                com_relacionamentos=True
            )
            vendas_response.append(VendaDetalhada.model_validate(venda_completa))
        
        return vendas_response, total

    @staticmethod
    async def atualizar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID,
        data: VendaUpdate
    ) -> Optional[VendaDetalhada]:
        """Atualiza venda (apenas se status=PEDIDO)."""
        try:
            async with db.begin_nested():
                venda = await VendaRepository.buscar_por_id(db, empresa_id, venda_id)
                if not venda:
                    return None
                
                if venda.status != StatusVenda.PEDIDO.value:
                    raise ValueError("Só é possível editar vendas com status PEDIDO")
                
                # Validar cliente se alterado
                if data.cliente_id:
                    cliente = await VendaService.verificar_cliente_existe(empresa_id, data.cliente_id)
                    if not cliente:
                        raise ValueError("Cliente não encontrado ou inválido")
                
                venda = await VendaRepository.atualizar(
                    db,
                    empresa_id,
                    venda_id,
                    **data.model_dump(exclude_unset=True)
                )
            
            await db.commit()
            log.info("venda_atualizada", venda_id=str(venda_id), empresa_id=empresa_id)
            
            return await VendaService.buscar_venda(db, empresa_id, venda_id)
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_atualizar_venda", error=str(e))
            raise

    @staticmethod
    async def confirmar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID,
        data: ConfirmarVendaRequest
    ) -> VendaDetalhada:
        """
        Confirma venda e registra pagamentos.
        Status: PEDIDO → CONFIRMADA
        """
        try:
            async with db.begin_nested():
                venda = await VendaRepository.buscar_por_id(db, empresa_id, venda_id)
                if not venda:
                    raise ValueError("Venda não encontrada")
                
                if venda.status != StatusVenda.PEDIDO.value:
                    raise ValueError(f"Venda não pode ser confirmada. Status atual: {venda.status}")
                
                # Validar soma dos pagamentos
                total_pago = sum(Decimal(str(p.valor_pago)) for p in data.pagamentos)
                if total_pago < venda.valor_total:
                    raise ValueError(
                        f"Valor pago (R$ {total_pago}) é menor que o total da venda (R$ {venda.valor_total})"
                    )
                
                # Se tem FIADO, validar cliente
                tem_fiado = any(p.forma_pagamento == FormaPagamento.FIADO for p in data.pagamentos)
                if tem_fiado and not venda.cliente_id:
                    raise ValueError("Venda fiada requer cliente identificado")
                
                # Criar pagamentos
                for pag in data.pagamentos:
                    pag_data = {
                        'venda_id': venda.id,
                        'forma_pagamento': pag.forma_pagamento.value,
                        'valor_pago': pag.valor_pago,
                        'comprovante': pag.comprovante,
                        'gera_conta_receber': pag.forma_pagamento == FormaPagamento.FIADO
                    }
                    
                    # Calcular troco se DINHEIRO
                    if pag.forma_pagamento == FormaPagamento.DINHEIRO and pag.valor_recebido:
                        pag_data['valor_recebido'] = pag.valor_recebido
                        pag_data['valor_troco'] = pag.valor_recebido - pag.valor_pago
                    
                    await PagamentoVendaRepository.criar(db, **pag_data)
                
                # Atualizar status
                venda = await VendaRepository.atualizar(
                    db,
                    empresa_id,
                    venda_id,
                    status=StatusVenda.CONFIRMADA.value,
                    data_confirmacao=datetime.utcnow()
                )
            
            await db.commit()
            
            log.info(
                "venda_confirmada",
                venda_id=str(venda_id),
                empresa_id=empresa_id,
                total_pago=float(total_pago)
            )
            
            return await VendaService.buscar_venda(db, empresa_id, venda_id)
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_confirmar_venda", error=str(e))
            raise

    @staticmethod
    async def separar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID
    ) -> VendaDetalhada:
        """
        Marca venda como separada.
        Status: CONFIRMADA → SEPARADA
        """
        try:
            async with db.begin_nested():
                venda = await VendaRepository.buscar_por_id(db, empresa_id, venda_id)
                if not venda:
                    raise ValueError("Venda não encontrada")
                
                if venda.status != StatusVenda.CONFIRMADA.value:
                    raise ValueError(f"Venda deve estar CONFIRMADA. Status atual: {venda.status}")
                
                venda = await VendaRepository.atualizar(
                    db,
                    empresa_id,
                    venda_id,
                    status=StatusVenda.SEPARADA.value,
                    data_separacao=datetime.utcnow()
                )
            
            await db.commit()
            log.info("venda_separada", venda_id=str(venda_id), empresa_id=empresa_id)
            
            return await VendaService.buscar_venda(db, empresa_id, venda_id)
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_separar_venda", error=str(e))
            raise

    @staticmethod
    async def entregar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID
    ) -> VendaDetalhada:
        """
        Marca venda como entregue e BAIXA ESTOQUE definitivamente.
        Status: SEPARADA → ENTREGUE
        """
        try:
            async with db.begin_nested():
                venda = await VendaRepository.buscar_por_id(
                    db,
                    empresa_id,
                    venda_id,
                    com_relacionamentos=True
                )
                if not venda:
                    raise ValueError("Venda não encontrada")
                
                if venda.status != StatusVenda.SEPARADA.value:
                    raise ValueError(f"Venda deve estar SEPARADA. Status atual: {venda.status}")
                
                # BAIXAR ESTOQUE definitivamente
                for item in venda.itens:
                    if not item.estoque_baixado:
                        sucesso = await VendaService.baixar_estoque(
                            empresa_id,
                            item.produto_id,
                            item.variante_id,
                            item.quantidade,
                            venda.numero_venda
                        )
                        if not sucesso:
                            raise ValueError(f"Erro ao baixar estoque do produto {item.descricao_produto}")
                        
                        # Marcar item como baixado
                        await ItemVendaRepository.atualizar(db, item.id, estoque_baixado=True)
                
                # Liberar reservas (já foram baixadas)
                reservas = await ReservaEstoqueVendaRepository.listar_por_venda(db, venda_id)
                for reserva in reservas:
                    await ReservaEstoqueVendaRepository.atualizar(
                        db,
                        reserva.id,
                        status=StatusReserva.BAIXADA.value,
                        baixada_em=datetime.utcnow()
                    )
                
                # Atualizar status
                venda = await VendaRepository.atualizar(
                    db,
                    empresa_id,
                    venda_id,
                    status=StatusVenda.ENTREGUE.value,
                    data_entregue=datetime.utcnow()
                )
            
            await db.commit()
            log.info("venda_entregue", venda_id=str(venda_id), empresa_id=empresa_id)
            
            return await VendaService.buscar_venda(db, empresa_id, venda_id)
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_entregar_venda", error=str(e))
            raise

    @staticmethod
    async def finalizar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID
    ) -> VendaDetalhada:
        """
        Finaliza venda e cria conta a receber se FIADO.
        Status: ENTREGUE → FINALIZADA
        """
        try:
            async with db.begin_nested():
                venda = await VendaRepository.buscar_por_id(
                    db,
                    empresa_id,
                    venda_id,
                    com_relacionamentos=True
                )
                if not venda:
                    raise ValueError("Venda não encontrada")
                
                if venda.status != StatusVenda.ENTREGUE.value:
                    raise ValueError(f"Venda deve estar ENTREGUE. Status atual: {venda.status}")
                
                # TODO: Criar conta a receber se tem pagamento FIADO
                # (Integração com serviço Financeiro quando estiver implementado)
                
                # Atualizar status
                venda = await VendaRepository.atualizar(
                    db,
                    empresa_id,
                    venda_id,
                    status=StatusVenda.FINALIZADA.value,
                    data_finalizada=datetime.utcnow()
                )
            
            await db.commit()
            log.info("venda_finalizada", venda_id=str(venda_id), empresa_id=empresa_id)
            
            return await VendaService.buscar_venda(db, empresa_id, venda_id)
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_finalizar_venda", error=str(e))
            raise

    @staticmethod
    async def cancelar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID,
        data: CancelarVendaRequest
    ) -> VendaDetalhada:
        """
        Cancela venda e LIBERA RESERVAS de estoque.
        Permitido apenas nos status: PEDIDO, CONFIRMADA, SEPARADA
        """
        try:
            async with db.begin_nested():
                venda = await VendaRepository.buscar_por_id(
                    db,
                    empresa_id,
                    venda_id,
                    com_relacionamentos=True
                )
                if not venda:
                    raise ValueError("Venda não encontrada")
                
                # Validar status
                status_permitidos = [
                    StatusVenda.PEDIDO.value,
                    StatusVenda.CONFIRMADA.value,
                    StatusVenda.SEPARADA.value
                ]
                if venda.status not in status_permitidos:
                    raise ValueError(
                        f"Não é possível cancelar venda com status {venda.status}. "
                        "Use devolução para vendas ENTREGUE ou FINALIZADA."
                    )
                
                # LIBERAR RESERVAS de estoque
                for item in venda.itens:
                    if item.estoque_reservado and not item.estoque_baixado:
                        sucesso = await VendaService.liberar_reserva_estoque(
                            empresa_id,
                            item.produto_id,
                            item.variante_id,
                            item.quantidade,
                            venda.numero_venda
                        )
                        if not sucesso:
                            log.warning(
                                "falha_liberar_reserva",
                                produto_id=str(item.produto_id),
                                venda_id=str(venda_id)
                            )
                
                # Atualizar reservas
                reservas = await ReservaEstoqueVendaRepository.listar_por_venda(db, venda_id)
                for reserva in reservas:
                    if reserva.status == StatusReserva.RESERVADA.value:
                        await ReservaEstoqueVendaRepository.atualizar(
                            db,
                            reserva.id,
                            status=StatusReserva.LIBERADA.value,
                            liberada_em=datetime.utcnow()
                        )
                
                # Atualizar venda
                venda = await VendaRepository.atualizar(
                    db,
                    empresa_id,
                    venda_id,
                    status=StatusVenda.CANCELADA.value,
                    data_cancelada=datetime.utcnow(),
                    motivo_cancelamento=data.motivo,
                    cancelada_por=data.usuario_id
                )
            
            await db.commit()
            
            log.info(
                "venda_cancelada",
                venda_id=str(venda_id),
                empresa_id=empresa_id,
                motivo=data.motivo
            )
            
            return await VendaService.buscar_venda(db, empresa_id, venda_id)
            
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_cancelar_venda", error=str(e))
            raise
