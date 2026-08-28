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
from services.estoque_resultado import ResultadoBaixaEstoque, classificar_status_http

log = structlog.get_logger()


class EstoqueIndeterminadoError(Exception):
    """
    Resultado da baixa de estoque desconhecido (timeout/erro) para uma venda paga.

    Sinaliza que a venda NÃO foi confirmada nem cancelada: foi marcada para reconciliação
    assíncrona. O caller (webhook) deve responder erro para que o Mercado Pago reentregue,
    e o job de reconciliação retenta a baixa idempotente.
    """


class VendaService:
    """Service para operações de venda."""

    @staticmethod
    async def verificar_produto_existe(produto_id: UUID, variante_id: Optional[UUID] = None, empresa_id: Optional[int] = None) -> dict:
        """
        Verifica se produto/variante existe no serviço de produtos.
        Retorna dados do produto se existir.
        
        Usa o endpoint público do catálogo para não depender de autenticação.
        """
        try:
            async with httpx.AsyncClient() as client:
                # Buscar slug da empresa a partir do ID
                # TODO: Implementar cache de slug ou passar slug diretamente
                
                # Por enquanto, usar endpoint administrativo com header
                headers = {}
                if empresa_id:
                    headers["X-Empresa-Id"] = str(empresa_id)
                
                # Endpoint administrativo de produto
                url = f"{settings.PRODUTOS_URL}/produtos/{produto_id}"
                
                response = await client.get(url, headers=headers, timeout=5.0)
                if response.status_code == 200:
                    produto = response.json()
                    
                    # Log para debug: ver estrutura do produto
                    log.info(
                        "produto_buscado_sucesso",
                        produto_id=str(produto_id),
                        tem_nome=bool(produto.get('nome')),
                        nome_valor=produto.get('nome'),  # ✅ Ver o valor real
                        nome_tipo=type(produto.get('nome')).__name__,  # ✅ Ver o tipo
                        chaves_produto=list(produto.keys())[:10]  # Primeiras 10 chaves
                    )
                    
                    # Se tem variante, validar se ela existe no produto
                    if variante_id and produto.get('variantes'):
                        variantes = produto.get('variantes', [])
                        variante_encontrada = None
                        for v in variantes:
                            if str(v.get('id')) == str(variante_id):
                                variante_encontrada = v
                                break
                        
                        if variante_encontrada:
                            return variante_encontrada
                        else:
                            log.warning("variante_nao_encontrada", 
                                       produto_id=str(produto_id), 
                                       variante_id=str(variante_id))
                            return None
                    
                    return produto
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
    async def baixar_estoque_venda(
        empresa_id: int, venda
    ) -> Tuple[ResultadoBaixaEstoque, Optional[str]]:
        """
        Baixa o estoque de TODOS os itens da venda de forma atômica e idempotente.

        Usado no momento da confirmação do pagamento: é o gate real de estoque. O serviço de
        estoque valida a disponibilidade física sob lock de linha (e é idempotente por
        numero_venda — C1), respondendo 409 se faltar estoque para qualquer item.

        Distingue (C4) três resultados, pois exigem tratamentos diferentes:
            - SUCESSO       : estoque baixado (ou já baixado). Pode confirmar.
            - SEM_ESTOQUE   : 409 definitivo, nada baixado. Cancelar a venda é seguro.
            - INDETERMINADO : timeout/erro de rede/5xx. Resultado desconhecido — NUNCA
                              cancelar uma venda paga; marcar para reconciliação.

        Returns:
            tuple: (ResultadoBaixaEstoque, mensagem)
        """
        itens = [
            {
                "produto_id": str(item.produto_id),
                "variante_id": str(item.variante_id) if item.variante_id else None,
                "quantidade": float(item.quantidade),
            }
            for item in venda.itens
            if not item.estoque_baixado
        ]
        if not itens:
            return (ResultadoBaixaEstoque.SUCESSO, None)  # Nada a baixar (já baixado)

        url = f"{settings.ESTOQUE_URL}/estoque/baixar-venda"
        headers = {"X-Empresa-Id": str(empresa_id)}
        payload = {
            "empresa_id": empresa_id,
            "documento": venda.numero_venda,
            "itens": itens,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
        except httpx.TimeoutException as e:
            # Timeout: a baixa pode ter ocorrido no estoque ou não. Resultado incerto.
            log.error("baixar_estoque_venda_timeout", error=str(e), venda_id=str(venda.id))
            return (ResultadoBaixaEstoque.INDETERMINADO, f"Timeout ao baixar estoque: {e}")
        except httpx.RequestError as e:
            # Falha de comunicação (conexão recusada, DNS, etc.): resultado incerto.
            log.error("baixar_estoque_venda_falha_comunicacao", error=str(e), venda_id=str(venda.id))
            return (ResultadoBaixaEstoque.INDETERMINADO, f"Falha de comunicação com estoque: {e}")

        resultado = classificar_status_http(response.status_code)

        if resultado is ResultadoBaixaEstoque.SUCESSO:
            return (ResultadoBaixaEstoque.SUCESSO, None)

        if resultado is ResultadoBaixaEstoque.SEM_ESTOQUE:
            detalhe = "Estoque insuficiente"
            try:
                detalhe = response.json().get("detail", detalhe)
            except Exception:
                pass
            return (ResultadoBaixaEstoque.SEM_ESTOQUE, detalhe)

        # INDETERMINADO (5xx ou status inesperado): não se sabe se baixou.
        log.error(
            "baixar_estoque_venda_status_inesperado",
            status=response.status_code,
            body=response.text[:300],
            venda_id=str(venda.id)
        )
        return (
            ResultadoBaixaEstoque.INDETERMINADO,
            f"Resposta inesperada do estoque (HTTP {response.status_code})",
        )

    @staticmethod
    async def estornar_estoque_venda(
        empresa_id: int, venda
    ) -> Tuple[bool, Optional[str]]:
        """
        Devolve ao estoque os itens já baixados da venda (estorno por reembolso).

        Idempotente por numero_venda no serviço de estoque (ledger de estorno — D2): chamadas
        repetidas não devolvem estoque em duplicidade. Devolve (sucesso, mensagem):
            - sucesso=True : estoque devolvido (ou já devolvido), ou nada a devolver.
            - sucesso=False: timeout/erro de comunicação/5xx — resultado incerto. O caller NÃO
                             deve marcar a venda como reembolsada; o webhook é reentregue.
        """
        itens = [
            {
                "produto_id": str(item.produto_id),
                "variante_id": str(item.variante_id) if item.variante_id else None,
                "quantidade": float(item.quantidade),
            }
            for item in venda.itens
            if item.estoque_baixado
        ]
        if not itens:
            return (True, None)  # nada foi baixado → nada a estornar

        url = f"{settings.ESTOQUE_URL}/estoque/estornar-venda"
        headers = {"X-Empresa-Id": str(empresa_id)}
        payload = {
            "empresa_id": empresa_id,
            "documento": venda.numero_venda,
            "itens": itens,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
        except (httpx.TimeoutException, httpx.RequestError) as e:
            log.error("estornar_estoque_venda_falha_comunicacao", error=str(e), venda_id=str(venda.id))
            return (False, f"Falha de comunicação com estoque: {e}")

        if response.status_code in (200, 201):
            return (True, None)

        log.error(
            "estornar_estoque_venda_status_inesperado",
            status=response.status_code,
            body=response.text[:300],
            venda_id=str(venda.id),
        )
        return (False, f"Resposta inesperada do estoque (HTTP {response.status_code})")

    @staticmethod
    async def reembolsar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID
    ) -> VendaDetalhada:
        """
        Reembolsa uma venda: devolve o estoque baixado e marca a venda como REEMBOLSADA.

        Idempotente e atômica:
        - Trava a linha da venda (FOR UPDATE) para serializar webhooks de reembolso concorrentes.
        - Se a venda já está REEMBOLSADA, retorna sem efeito.
        - Devolve o estoque de forma idempotente (ledger de estorno por numero_venda — D2).
        - Se o estorno for indeterminado (timeout/erro), NÃO marca reembolsada e sinaliza
          reentrega do webhook (o estorno idempotente é reexecutado com segurança).
        """
        from services.historico_status_service import HistoricoStatusService

        try:
            venda = await VendaRepository.buscar_por_id(
                db, empresa_id, venda_id, com_relacionamentos=True, com_lock=True
            )
            if not venda:
                raise ValueError("Venda não encontrada")

            # Idempotência: já reembolsada por outro webhook/requisição → não duplica nada.
            if venda.status == StatusVenda.REEMBOLSADA.value:
                status_atual = venda.status
                await db.rollback()
                log.info(
                    "reembolsar_venda_idempotente_ignorada",
                    venda_id=str(venda_id),
                    status_atual=status_atual,
                )
                return await VendaService.buscar_venda(db, empresa_id, venda_id)

            status_anterior = venda.status

            # Devolver o estoque baixado (idempotente por numero_venda).
            sucesso, erro = await VendaService.estornar_estoque_venda(empresa_id, venda)
            if not sucesso:
                await db.rollback()
                log.critical(
                    "reembolso_estorno_estoque_indeterminado_reentregar",
                    venda_id=str(venda_id),
                    empresa_id=empresa_id,
                    motivo=erro,
                )
                raise EstoqueIndeterminadoError(erro or "Estorno de estoque indeterminado")

            # Estoque devolvido → itens não estão mais baixados.
            for item in venda.itens:
                item.estoque_baixado = False

            venda = await VendaRepository.atualizar(
                db, empresa_id, venda_id, status=StatusVenda.REEMBOLSADA.value
            )

            await HistoricoStatusService.registrar_mudanca(
                db,
                venda.id,
                status_anterior,
                StatusVenda.REEMBOLSADA.value,
                None,  # Sistema
                "Pagamento reembolsado — estoque devolvido.",
            )

            await db.commit()

            log.info("venda_reembolsada", venda_id=str(venda_id), empresa_id=empresa_id)

            return await VendaService.buscar_venda(db, empresa_id, venda_id)

        except (ValueError, EstoqueIndeterminadoError):
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_reembolsar_venda", error=str(e))
            raise

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
                        item.variante_id,
                        empresa_id  # Passar empresa_id
                    )
                    if not produto:
                        raise ValueError(f"Produto {item.produto_id} não encontrado")
                    
                    # Usar preço do produto se não fornecido
                    preco_unitario = item.preco_unitario if item.preco_unitario else Decimal(str(produto.get('preco', produto.get('preco_venda', 0))))
                    subtotal = item.quantidade * preco_unitario
                    
                    # 🔧 CORREÇÃO: Se item já vem com codigo/descricao (do carrinho), usar eles
                    # Caso contrário, buscar do produto (para vendas diretas sem carrinho)
                    codigo_produto = item.codigo_produto if item.codigo_produto else produto.get('sku', produto.get('codigo', produto.get('codigo_barras')))
                    descricao_produto = item.descricao_produto if item.descricao_produto else produto.get('nome', 'Produto sem nome')
                    
                    itens_dados.append({
                        'produto_id': item.produto_id,
                        'variante_id': item.variante_id,
                        'codigo_produto': codigo_produto,
                        'descricao_produto': descricao_produto,
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
                
                # 7. RESERVAR ESTOQUE (TODO: Integração com serviço de estoque)
                # Por enquanto, apenas registramos a tentativa mas não bloqueamos
                for item in itens_criados:
                    sucesso = await VendaService.reservar_estoque(
                        empresa_id,
                        item.produto_id,
                        item.variante_id,
                        item.quantidade,
                        numero_venda
                    )
                    if not sucesso:
                        # Log warning mas não bloqueia (estoque já foi validado nas reservas temporárias)
                        log.warning("estoque_reserva_falhou", 
                                   produto=item.descricao_produto,
                                   produto_id=str(item.produto_id))
                    
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
        Confirma venda, baixa o estoque real e registra pagamentos.
        Status: PEDIDO/PENDENTE_PAGAMENTO → CONFIRMADA

        Idempotente e atômica:
        - Trava a linha da venda (FOR UPDATE) para serializar webhooks concorrentes
          (payment + merchant_order do mesmo pedido). A confirmação roda uma única vez.
        - Se a venda já está confirmada (ou em estágio posterior), retorna sem efeitos.
        - Só confirma se houver estoque físico real para TODOS os itens no momento da
          aprovação do pagamento (baixa atômica no serviço de estoque). Sem estoque, a
          venda é cancelada e as reservas liberadas.
        """
        from services.historico_status_service import HistoricoStatusService
        from services.notificacao_service import NotificacaoService

        # Status a partir dos quais a venda já está confirmada (ou além): no-op idempotente.
        STATUS_JA_CONFIRMADA = {
            StatusVenda.CONFIRMADA.value,
            StatusVenda.SEPARADA.value,
            StatusVenda.EM_ENTREGA.value,
            StatusVenda.ENTREGUE.value,
            StatusVenda.FINALIZADA.value,
        }

        try:
            # Lock da venda + itens. A transação fica aberta até o commit, mantendo o lock.
            venda = await VendaRepository.buscar_por_id(
                db, empresa_id, venda_id, com_relacionamentos=True, com_lock=True
            )
            if not venda:
                raise ValueError("Venda não encontrada")

            # Idempotência: já confirmada por outro webhook/requisição → não duplica nada.
            if venda.status in STATUS_JA_CONFIRMADA:
                # Capturar o status ANTES do rollback: o rollback expira os atributos do
                # ORM e acessá-los depois dispararia um lazy-load síncrono (MissingGreenlet).
                status_atual = venda.status
                await db.rollback()  # Libera o lock sem alterações
                log.info(
                    "confirmar_venda_idempotente_ignorada",
                    venda_id=str(venda_id),
                    status_atual=status_atual
                )
                return await VendaService.buscar_venda(db, empresa_id, venda_id)

            status_anterior = venda.status

            if venda.status not in [StatusVenda.PEDIDO.value, StatusVenda.PENDENTE_PAGAMENTO.value]:
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

            # GATE DE ESTOQUE REAL (regra de negócio mandatória):
            # baixa atômica e idempotente de todos os itens.
            resultado_estoque, erro_estoque = await VendaService.baixar_estoque_venda(
                empresa_id, venda
            )

            if resultado_estoque is ResultadoBaixaEstoque.SEM_ESTOQUE:
                # Definitivo: estoque insuficiente, nada foi baixado → cancelar é seguro.
                await VendaService._cancelar_por_falta_estoque(
                    db, empresa_id, venda, status_anterior, erro_estoque
                )
                await db.commit()
                log.error(
                    "venda_cancelada_sem_estoque",
                    venda_id=str(venda_id),
                    empresa_id=empresa_id,
                    motivo=erro_estoque,
                    pago=float(total_pago)
                )
                raise ValueError(erro_estoque or "Estoque insuficiente para confirmar a venda")

            if resultado_estoque is ResultadoBaixaEstoque.INDETERMINADO:
                # Resultado desconhecido (timeout/erro). NUNCA cancelar uma venda paga aqui:
                # marca para reconciliação assíncrona (retry idempotente) e aborta a confirmação.
                await VendaService._marcar_reconciliacao_estoque(
                    db, empresa_id, venda, status_anterior, erro_estoque
                )
                await db.commit()
                log.critical(
                    "venda_paga_estoque_indeterminado_reconciliar",
                    venda_id=str(venda_id),
                    empresa_id=empresa_id,
                    payment_id=venda.mercadopago_payment_id,
                    motivo=erro_estoque,
                    pago=float(total_pago)
                )
                raise EstoqueIndeterminadoError(
                    erro_estoque or "Resultado da baixa de estoque indeterminado"
                )

            # SUCESSO → marcar itens e limpar qualquer marca de reconciliação anterior.
            for item in venda.itens:
                item.estoque_baixado = True
            venda.reconciliacao_estoque_pendente = False
            venda.reconciliacao_motivo = None

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

            # Registrar histórico (entrada única por confirmação)
            await HistoricoStatusService.registrar_mudanca(
                db,
                venda.id,
                status_anterior,
                StatusVenda.CONFIRMADA.value,
                data.usuario_id if hasattr(data, 'usuario_id') else None,
                f"Pagamento confirmado. Total pago: R$ {total_pago}. Estoque baixado."
            )

            await db.commit()

            log.info(
                "venda_confirmada",
                venda_id=str(venda_id),
                empresa_id=empresa_id,
                total_pago=float(total_pago)
            )

            # Enviar notificação WhatsApp
            try:
                telefone = venda.cliente_convidado_telefone if venda.cliente_convidado_telefone else None
                if telefone:
                    nome_cliente = venda.cliente_convidado_nome if venda.cliente_convidado_nome else None
                    await NotificacaoService.enviar_pagamento_confirmado(
                        telefone,
                        venda.numero_venda,
                        nome_cliente,
                        empresa_id=empresa_id
                    )
            except Exception as e:
                log.warning("erro_enviar_notificacao_pagamento", venda_id=str(venda_id), error=str(e))

            return await VendaService.buscar_venda(db, empresa_id, venda_id)

        except ValueError:
            await db.rollback()
            raise
        except EstoqueIndeterminadoError:
            # Já comitado (reconciliação marcada) e logado — apenas propaga p/ o caller
            # responder erro e disparar a reentrega do webhook / reconciliação.
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_confirmar_venda", error=str(e))
            raise

    @staticmethod
    async def _marcar_reconciliacao_estoque(
        db: AsyncSession,
        empresa_id: int,
        venda,
        status_anterior: str,
        motivo: Optional[str]
    ) -> None:
        """
        Marca uma venda paga com resultado de baixa de estoque indeterminado para
        reconciliação assíncrona. Não cancela nem confirma — preserva o status atual e
        sinaliza o retry idempotente. Não faz commit (o chamador controla a transação).
        """
        from services.historico_status_service import HistoricoStatusService

        venda.reconciliacao_estoque_pendente = True
        venda.reconciliacao_motivo = (motivo or "Baixa de estoque indeterminada")[:500]

        await HistoricoStatusService.registrar_mudanca(
            db,
            venda.id,
            status_anterior,
            status_anterior,  # sem transição de status; entrada de auditoria
            None,  # Sistema
            f"Pagamento aprovado; baixa de estoque indeterminada — pendente de "
            f"reconciliação. {motivo or ''}".strip()
        )

    @staticmethod
    async def _cancelar_por_falta_estoque(
        db: AsyncSession,
        empresa_id: int,
        venda,
        status_anterior: str,
        motivo: Optional[str]
    ) -> None:
        """
        Cancela uma venda que não pôde ser confirmada por falta de estoque real e
        libera as reservas. Não faz commit — o chamador controla a transação.

        Para vendas online já pagas, registra evento crítico: requer reembolso manual.
        """
        from services.historico_status_service import HistoricoStatusService

        # Liberar reservas de estoque (best-effort) no serviço de estoque
        for item in venda.itens:
            if item.estoque_reservado and not item.estoque_baixado:
                await VendaService.liberar_reserva_estoque(
                    empresa_id,
                    item.produto_id,
                    item.variante_id,
                    item.quantidade,
                    venda.numero_venda
                )

        # Atualizar reservas da venda → LIBERADA
        reservas = await ReservaEstoqueVendaRepository.listar_por_venda(db, venda.id)
        for reserva in reservas:
            if reserva.status == StatusReserva.RESERVADA.value:
                await ReservaEstoqueVendaRepository.atualizar(
                    db,
                    reserva.id,
                    status=StatusReserva.LIBERADA.value,
                    liberada_em=datetime.utcnow()
                )

        await VendaRepository.atualizar(
            db,
            empresa_id,
            venda.id,
            status=StatusVenda.CANCELADA.value,
            data_cancelada=datetime.utcnow(),
            motivo_cancelamento=f"Estoque insuficiente na aprovação do pagamento: {motivo}"
        )

        await HistoricoStatusService.registrar_mudanca(
            db,
            venda.id,
            status_anterior,
            StatusVenda.CANCELADA.value,
            None,  # Sistema
            f"Venda cancelada por falta de estoque na aprovação do pagamento. {motivo}"
        )

        # Pagamento online aprovado mas sem estoque → reembolso necessário.
        if venda.mercadopago_payment_id:
            log.critical(
                "venda_paga_sem_estoque_reembolso_necessario",
                venda_id=str(venda.id),
                numero_venda=venda.numero_venda,
                empresa_id=empresa_id,
                payment_id=venda.mercadopago_payment_id
            )

    @staticmethod
    async def separar_venda(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> VendaDetalhada:
        """
        Marca venda como separada.
        Status: CONFIRMADA → SEPARADA
        """
        from services.historico_status_service import HistoricoStatusService
        from services.notificacao_service import NotificacaoService
        
        try:
            async with db.begin_nested():
                venda = await VendaRepository.buscar_por_id(db, empresa_id, venda_id)
                if not venda:
                    raise ValueError("Venda não encontrada")
                
                status_anterior = venda.status
                
                if venda.status != StatusVenda.CONFIRMADA.value:
                    raise ValueError(f"Venda deve estar CONFIRMADA. Status atual: {venda.status}")
                
                venda = await VendaRepository.atualizar(
                    db,
                    empresa_id,
                    venda_id,
                    status=StatusVenda.SEPARADA.value,
                    data_separacao=datetime.utcnow()
                )
                
                # Registrar histórico
                await HistoricoStatusService.registrar_mudanca(
                    db,
                    venda.id,
                    status_anterior,
                    StatusVenda.SEPARADA.value,
                    usuario_id,
                    "Pedido separado e pronto para entrega/retirada"
                )
            
            await db.commit()
            log.info("venda_separada", venda_id=str(venda_id), empresa_id=empresa_id)
            
            # Enviar notificação WhatsApp
            try:
                telefone = venda.cliente_convidado_telefone if venda.cliente_convidado_telefone else None
                if telefone:
                    await NotificacaoService.enviar_pedido_separado(
                        telefone,
                        venda.numero_venda,
                        venda.tipo_entrega,
                        empresa_id=empresa_id
                    )
            except Exception as e:
                log.warning("erro_enviar_notificacao_separado", venda_id=str(venda_id), error=str(e))
            
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
        venda_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> VendaDetalhada:
        """
        Marca venda como entregue (logística apenas — NÃO movimenta estoque).
        Status: SEPARADA → ENTREGUE

        O estoque já foi baixado de forma definitiva na confirmação do pagamento.
        A entrega é puramente logística e não altera quantidades de estoque.
        """
        from services.historico_status_service import HistoricoStatusService
        from services.notificacao_service import NotificacaoService

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

                status_anterior = venda.status

                if venda.status != StatusVenda.SEPARADA.value:
                    raise ValueError(f"Venda deve estar SEPARADA. Status atual: {venda.status}")

                # Marcar reservas como BAIXADA (o estoque já saiu na confirmação).
                reservas = await ReservaEstoqueVendaRepository.listar_por_venda(db, venda_id)
                for reserva in reservas:
                    if reserva.status == StatusReserva.RESERVADA.value:
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

                # Registrar histórico
                tipo_entrega_texto = "entregue" if venda.tipo_entrega == "DELIVERY" else "retirado"
                await HistoricoStatusService.registrar_mudanca(
                    db,
                    venda.id,
                    status_anterior,
                    StatusVenda.ENTREGUE.value,
                    usuario_id,
                    f"Pedido {tipo_entrega_texto} (logística — estoque já baixado na confirmação)."
                )
            
            await db.commit()
            log.info("venda_entregue", venda_id=str(venda_id), empresa_id=empresa_id)
            
            # Enviar notificação WhatsApp
            try:
                telefone = venda.cliente_convidado_telefone if venda.cliente_convidado_telefone else None
                if telefone:
                    await NotificacaoService.enviar_pedido_entregue(
                        telefone,
                        venda.numero_venda,
                        venda.tipo_entrega,
                        empresa_id=empresa_id
                    )
            except Exception as e:
                log.warning("erro_enviar_notificacao_entregue", venda_id=str(venda_id), error=str(e))
            
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
        venda_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> VendaDetalhada:
        """
        Finaliza venda e cria conta a receber se FIADO.
        Status: ENTREGUE → FINALIZADA
        """
        from services.historico_status_service import HistoricoStatusService
        
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
                
                status_anterior = venda.status
                
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
                
                # Registrar histórico
                await HistoricoStatusService.registrar_mudanca(
                    db,
                    venda.id,
                    status_anterior,
                    StatusVenda.FINALIZADA.value,
                    usuario_id,
                    "Venda finalizada com sucesso"
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
