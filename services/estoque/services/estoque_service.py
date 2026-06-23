"""
Service de Estoque.
Contém a lógica de negócio para gestão de estoque.
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import structlog

from models.estoque import TipoMovimentacao, StatusLote
from repositories.estoque_repository import (
    EstoqueRepository,
    MovimentacaoRepository,
    LoteRepository,
    InventarioRepository
)
from schemas.estoque import (
    EstoqueCreate,
    EstoqueUpdate,
    EstoqueResponse,
    EstoqueComAlerta,
    MovimentacaoCreate,
    LoteCreate,
    EntradaEstoqueRequest,
    SaidaEstoqueRequest,
    AjusteEstoqueRequest,
    ReservaEstoqueRequest,
    LiberarReservaRequest,
    RelatorioEstoque,
    RelatorioMovimentacoes,
)
from config import settings

log = structlog.get_logger()


class EstoqueService:
    """Service para operações de estoque."""

    @staticmethod
    async def verificar_produto_existe(produto_id: UUID, variante_id: Optional[UUID] = None) -> bool:
        """Verifica se produto/variante existe no serviço de produtos."""
        try:
            async with httpx.AsyncClient() as client:
                if variante_id:
                    url = f"{settings.PRODUTOS_URL}/produtos/{produto_id}/variantes/{variante_id}"
                else:
                    url = f"{settings.PRODUTOS_URL}/produtos/{produto_id}"
                
                response = await client.get(url, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            log.error("erro_verificar_produto", error=str(e), produto_id=str(produto_id))
            return False

    @staticmethod
    async def criar_estoque(db: AsyncSession, empresa_id: int, data: EstoqueCreate) -> EstoqueResponse:
        """Cria um novo registro de estoque."""
        # Verificar se produto existe
        if not await EstoqueService.verificar_produto_existe(data.produto_id, data.variante_id):
            raise ValueError("Produto ou variante não encontrado")
        
        try:
            async with db.begin_nested():
                # Verificar se já existe estoque para este produto/variante
                estoque_existente = await EstoqueRepository.buscar_por_produto(
                    db, empresa_id, data.produto_id, data.variante_id
                )
                if estoque_existente:
                    raise ValueError("Já existe estoque cadastrado para este produto/variante")
                
                # Criar estoque
                estoque = await EstoqueRepository.criar(db, **data.model_dump())
                
            await db.commit()
            log.info("estoque_criado", estoque_id=estoque.id, produto_id=data.produto_id, empresa_id=empresa_id)
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_criar_estoque", error=str(e))
            raise

    @staticmethod
    async def buscar_estoque(db: AsyncSession, empresa_id: int, estoque_id: UUID) -> Optional[EstoqueComAlerta]:
        """Busca estoque por ID com alertas."""
        estoque = await EstoqueRepository.buscar_por_id(db, empresa_id, estoque_id)
        if not estoque:
            return None
        
        # Adicionar alertas
        response = EstoqueComAlerta.model_validate(estoque)
        response.alerta_estoque_baixo = estoque.quantidade <= estoque.estoque_minimo and estoque.quantidade > 0
        response.alerta_estoque_zerado = estoque.quantidade == 0
        
        return response

    @staticmethod
    async def listar_estoques(
        db: AsyncSession,
        empresa_id: int,
        skip: int = 0,
        limit: int = 100,
        apenas_baixo: bool = False,
        apenas_zerado: bool = False
    ) -> List[EstoqueComAlerta]:
        """Lista estoques com alertas."""
        estoques = await EstoqueRepository.listar(
            db, empresa_id=empresa_id, skip=skip, limit=limit,
            apenas_baixo=apenas_baixo,
            apenas_zerado=apenas_zerado
        )
        
        result = []
        for estoque in estoques:
            response = EstoqueComAlerta.model_validate(estoque)
            response.alerta_estoque_baixo = estoque.quantidade <= estoque.estoque_minimo and estoque.quantidade > 0
            response.alerta_estoque_zerado = estoque.quantidade == 0
            result.append(response)
        
        return result

    @staticmethod
    async def atualizar_estoque(
        db: AsyncSession,
        empresa_id: int,
        estoque_id: UUID,
        data: EstoqueUpdate
    ) -> Optional[EstoqueResponse]:
        """Atualiza configurações de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                estoque = await EstoqueRepository.atualizar(db, empresa_id, estoque_id, **data.model_dump(exclude_unset=True))
                if not estoque:
                    return None
            
            await db.commit()
            log.info("estoque_atualizado", estoque_id=str(estoque_id), empresa_id=empresa_id)
            
            return EstoqueResponse.model_validate(estoque)
        except Exception as e:
            await db.rollback()
            log.error("erro_atualizar_estoque", error=str(e))
            raise

    @staticmethod
    async def entrada_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: EntradaEstoqueRequest,
        usuario_id: Optional[UUID] = None
    ) -> Tuple[EstoqueResponse, Optional[UUID]]:
        """Registra entrada de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                # Buscar ou criar estoque
                estoque = await EstoqueRepository.buscar_por_produto(db, empresa_id, data.produto_id, data.variante_id)
                
                if not estoque:
                    # Verificar se produto existe
                    if not await EstoqueService.verificar_produto_existe(data.produto_id, data.variante_id):
                        raise ValueError("Produto ou variante não encontrado")
                    
                    # Criar estoque
                    estoque = await EstoqueRepository.criar(
                        db,
                        empresa_id=empresa_id,
                        produto_id=data.produto_id,
                        variante_id=data.variante_id,
                        quantidade=0.0,
                        estoque_minimo=0.0
                    )
                
                # Registrar movimentação
                quantidade_anterior = estoque.quantidade
                quantidade_posterior = quantidade_anterior + data.quantidade
                
                movimentacao = await MovimentacaoRepository.criar(
                    db,
                    estoque_id=estoque.id,
                    tipo=TipoMovimentacao.ENTRADA.value,
                    quantidade=data.quantidade,
                    quantidade_anterior=quantidade_anterior,
                    quantidade_posterior=quantidade_posterior,
                    motivo=data.motivo,
                    observacao=data.observacao,
                    documento=data.documento,
                    custo_unitario=data.custo_unitario,
                    usuario_id=usuario_id
                )
                
                # Atualizar quantidade
                estoque = await EstoqueRepository.atualizar_quantidade(db, empresa_id, estoque.id, quantidade_posterior)
                
                # Criar lote se solicitado
                lote_id = None
                if data.criar_lote and data.codigo_lote:
                    lote = await LoteRepository.criar(
                        db,
                        empresa_id=empresa_id,
                        estoque_id=estoque.id,
                        codigo=data.codigo_lote,
                        quantidade=data.quantidade,
                        data_fabricacao=data.data_fabricacao,
                        data_validade=data.data_validade,
                        fornecedor=data.fornecedor,
                        nota_fiscal=data.nota_fiscal,
                        custo_unitario=data.custo_unitario
                    )
                    lote_id = lote.id
                    
                    # Atualizar movimentação com lote
                    movimentacao.lote_id = lote_id
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "entrada_estoque",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                lote_id=lote_id,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque), lote_id
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_entrada_estoque", error=str(e))
            raise

    @staticmethod
    async def saida_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: SaidaEstoqueRequest,
        usuario_id: Optional[UUID] = None
    ) -> EstoqueResponse:
        """Registra saída de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                # Buscar estoque
                estoque = await EstoqueRepository.buscar_por_produto(db, empresa_id, data.produto_id, data.variante_id)
                if not estoque:
                    raise ValueError("Estoque não encontrado para este produto/variante")
                
                # Verificar disponibilidade
                if estoque.quantidade_disponivel < data.quantidade:
                    raise ValueError(
                        f"Quantidade disponível insuficiente. "
                        f"Disponível: {estoque.quantidade_disponivel}, Solicitado: {data.quantidade}"
                    )
                
                # Se especificou lote, verificar e atualizar
                if data.lote_id:
                    lote = await LoteRepository.buscar_por_id(db, empresa_id, data.lote_id)
                    if not lote or lote.estoque_id != estoque.id:
                        raise ValueError("Lote não encontrado ou não pertence a este estoque")
                    
                    if lote.quantidade < data.quantidade:
                        raise ValueError(f"Quantidade insuficiente no lote. Disponível: {lote.quantidade}")
                    
                    # Atualizar quantidade do lote
                    await LoteRepository.atualizar_quantidade(db, empresa_id, lote.id, lote.quantidade - data.quantidade)
                
                # Registrar movimentação
                quantidade_anterior = estoque.quantidade
                quantidade_posterior = quantidade_anterior - data.quantidade
                
                await MovimentacaoRepository.criar(
                    db,
                    estoque_id=estoque.id,
                    lote_id=data.lote_id,
                    tipo=TipoMovimentacao.SAIDA.value,
                    quantidade=data.quantidade,
                    quantidade_anterior=quantidade_anterior,
                    quantidade_posterior=quantidade_posterior,
                    motivo=data.motivo,
                    observacao=data.observacao,
                    documento=data.documento,
                    usuario_id=usuario_id
                )
                
                # Atualizar quantidade
                estoque = await EstoqueRepository.atualizar_quantidade(db, empresa_id, estoque.id, quantidade_posterior)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "saida_estoque",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                lote_id=data.lote_id,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_saida_estoque", error=str(e))
            raise

    @staticmethod
    async def ajustar_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: AjusteEstoqueRequest,
        usuario_id: Optional[UUID] = None
    ) -> EstoqueResponse:
        """Ajusta estoque (inventário) com transação atômica."""
        try:
            async with db.begin_nested():
                estoque = await EstoqueRepository.buscar_por_id(db, empresa_id, data.estoque_id)
                if not estoque:
                    raise ValueError("Estoque não encontrado")
                
                quantidade_anterior = estoque.quantidade
                quantidade_posterior = data.quantidade_nova
                quantidade_ajuste = quantidade_posterior - quantidade_anterior
                
                # Registrar movimentação
                await MovimentacaoRepository.criar(
                    db,
                    estoque_id=estoque.id,
                    tipo=TipoMovimentacao.AJUSTE.value,
                    quantidade=abs(quantidade_ajuste),
                    quantidade_anterior=quantidade_anterior,
                    quantidade_posterior=quantidade_posterior,
                    motivo=data.motivo,
                    observacao=data.observacao,
                    usuario_id=usuario_id
                )
                
                # Atualizar quantidade
                estoque = await EstoqueRepository.atualizar_quantidade(db, empresa_id, estoque.id, quantidade_posterior)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "ajuste_estoque",
                estoque_id=estoque.id,
                quantidade_anterior=quantidade_anterior,
                quantidade_posterior=quantidade_posterior,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_ajuste_estoque", error=str(e))
            raise

    @staticmethod
    async def reservar_estoque(
        db: AsyncSession,
        empresa_id: int,
        data: ReservaEstoqueRequest
    ) -> EstoqueResponse:
        """Reserva estoque para venda com transação atômica."""
        try:
            async with db.begin_nested():
                estoque = await EstoqueRepository.buscar_por_produto(db, empresa_id, data.produto_id, data.variante_id)
                if not estoque:
                    raise ValueError("Estoque não encontrado para este produto/variante")
                
                estoque = await EstoqueRepository.reservar(db, empresa_id, estoque.id, data.quantidade)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "estoque_reservado",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                documento=data.documento,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_reservar_estoque", error=str(e))
            raise

    @staticmethod
    async def liberar_reserva(
        db: AsyncSession,
        empresa_id: int,
        data: LiberarReservaRequest
    ) -> EstoqueResponse:
        """Libera reserva de estoque com transação atômica."""
        try:
            async with db.begin_nested():
                estoque = await EstoqueRepository.buscar_por_produto(db, empresa_id, data.produto_id, data.variante_id)
                if not estoque:
                    raise ValueError("Estoque não encontrado para este produto/variante")
                
                estoque = await EstoqueRepository.liberar_reserva(db, empresa_id, estoque.id, data.quantidade)
            
            # Commit da transação principal
            await db.commit()
            
            log.info(
                "reserva_liberada",
                estoque_id=estoque.id,
                quantidade=data.quantidade,
                documento=data.documento,
                empresa_id=empresa_id
            )
            
            return EstoqueResponse.model_validate(estoque)
        except ValueError:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            log.error("erro_liberar_reserva", error=str(e))
            raise

    @staticmethod
    async def gerar_relatorio(db: AsyncSession, empresa_id: int) -> RelatorioEstoque:
        """Gera relatório geral de estoque."""
        total_produtos = await EstoqueRepository.contar_total(db, empresa_id)
        produtos_estoque_baixo = await EstoqueRepository.contar_estoque_baixo(db, empresa_id)
        produtos_sem_estoque = await EstoqueRepository.contar_estoque_zerado(db, empresa_id)
        
        # Calcular total em estoque
        estoques = await EstoqueRepository.listar(db, empresa_id=empresa_id, limit=10000)
        total_em_estoque = sum(e.quantidade for e in estoques)
        
        return RelatorioEstoque(
            total_produtos=total_produtos,
            total_em_estoque=total_em_estoque,
            produtos_estoque_baixo=produtos_estoque_baixo,
            produtos_sem_estoque=produtos_sem_estoque
        )

    @staticmethod
    async def gerar_relatorio_movimentacoes(
        db: AsyncSession,
        empresa_id: int,
        data_inicio: datetime,
        data_fim: datetime
    ) -> RelatorioMovimentacoes:
        """Gera relatório de movimentações."""
        total_entradas = await MovimentacaoRepository.contar_por_tipo(
            db, empresa_id, TipoMovimentacao.ENTRADA, data_inicio, data_fim
        )
        total_saidas = await MovimentacaoRepository.contar_por_tipo(
            db, empresa_id, TipoMovimentacao.SAIDA, data_inicio, data_fim
        )
        
        quantidade_entrada = await MovimentacaoRepository.somar_quantidade_por_tipo(
            db, empresa_id, TipoMovimentacao.ENTRADA, data_inicio, data_fim
        )
        quantidade_saida = await MovimentacaoRepository.somar_quantidade_por_tipo(
            db, empresa_id, TipoMovimentacao.SAIDA, data_inicio, data_fim
        )
        
        return RelatorioMovimentacoes(
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            total_entradas=total_entradas,
            total_saidas=total_saidas,
            quantidade_entrada=quantidade_entrada,
            quantidade_saida=quantidade_saida
        )
