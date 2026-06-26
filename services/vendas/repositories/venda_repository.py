"""
Repository de Vendas.
Responsável pelas queries no banco de dados.
"""
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.venda import (
    Venda,
    ItemVenda,
    PagamentoVenda,
    ReservaEstoqueVenda,
    StatusVenda,
    FormaPagamento,
    ConfiguracaoLoja,
    FaixaEntrega
)


class VendaRepository:
    """Repository para operações de Venda."""

    @staticmethod
    async def criar(db: AsyncSession, **dados) -> Venda:
        """Cria uma nova venda."""
        venda = Venda(**dados)
        db.add(venda)
        await db.flush()
        return venda

    @staticmethod
    async def buscar_por_id(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID,
        com_relacionamentos: bool = False
    ) -> Optional[Venda]:
        """Busca venda por ID isolada por empresa."""
        query = select(Venda).where(
            and_(
                Venda.empresa_id == empresa_id,
                Venda.id == venda_id
            )
        )
        
        if com_relacionamentos:
            query = query.options(
                selectinload(Venda.itens),
                selectinload(Venda.pagamentos),
                selectinload(Venda.reservas)
            )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def buscar_por_numero(
        db: AsyncSession,
        empresa_id: int,
        numero_venda: str
    ) -> Optional[Venda]:
        """Busca venda por número isolada por empresa."""
        query = select(Venda).where(
            and_(
                Venda.empresa_id == empresa_id,
                Venda.numero_venda == numero_venda
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def listar(
        db: AsyncSession,
        empresa_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StatusVenda] = None,
        cliente_id: Optional[UUID] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> Tuple[List[Venda], int]:
        """Lista vendas isoladas por empresa com filtros."""
        # Query base
        conditions = [Venda.empresa_id == empresa_id]
        
        # Filtros opcionais
        if status:
            conditions.append(Venda.status == status.value)
        if cliente_id:
            conditions.append(Venda.cliente_id == cliente_id)
        if data_inicio:
            conditions.append(Venda.data_pedido >= data_inicio)
        if data_fim:
            conditions.append(Venda.data_pedido <= data_fim)
        
        # Query de vendas
        query = select(Venda).where(and_(*conditions)).order_by(desc(Venda.data_pedido))
        
        # Total
        count_query = select(func.count()).select_from(Venda).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Paginação
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        vendas = result.scalars().all()
        
        return list(vendas), total

    @staticmethod
    async def atualizar(
        db: AsyncSession,
        empresa_id: int,
        venda_id: UUID,
        **dados
    ) -> Optional[Venda]:
        """Atualiza uma venda."""
        venda = await VendaRepository.buscar_por_id(db, empresa_id, venda_id)
        if not venda:
            return None
        
        for key, value in dados.items():
            if value is not None:
                setattr(venda, key, value)
        
        venda.updated_at = datetime.utcnow()
        await db.flush()
        return venda

    @staticmethod
    async def contar_por_empresa(db: AsyncSession, empresa_id: int) -> int:
        """Conta total de vendas da empresa."""
        query = select(func.count()).select_from(Venda).where(Venda.empresa_id == empresa_id)
        result = await db.execute(query)
        return result.scalar()

    @staticmethod
    async def obter_proxima_sequencia(db: AsyncSession, empresa_id: int) -> int:
        """Obtém a próxima sequência de número de venda para a empresa."""
        count = await VendaRepository.contar_por_empresa(db, empresa_id)
        return count + 1

    @staticmethod
    async def buscar_por_sessao_carrinho(
        db: AsyncSession,
        empresa_id: int,
        sessao_carrinho_id: str
    ) -> Optional[Venda]:
        """
        Busca venda por sessao_carrinho_id.
        
        Retorna a venda mais recente se houver múltiplas com mesmo sessao_id
        (caso de bug onde mesmo carrinho foi usado em múltiplas vendas).
        """
        query = select(Venda).where(
            and_(
                Venda.empresa_id == empresa_id,
                Venda.sessao_carrinho_id == sessao_carrinho_id
            )
        ).order_by(desc(Venda.created_at))
        
        result = await db.execute(query)
        return result.scalars().first()  # Retorna a mais recente


class ItemVendaRepository:
    """Repository para operações de Item de Venda."""

    @staticmethod
    async def criar(db: AsyncSession, **dados) -> ItemVenda:
        """Cria um novo item de venda."""
        item = ItemVenda(**dados)
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def criar_varios(db: AsyncSession, itens: List[dict]) -> List[ItemVenda]:
        """Cria múltiplos itens de venda."""
        itens_criados = []
        for item_data in itens:
            item = ItemVenda(**item_data)
            db.add(item)
            itens_criados.append(item)
        
        await db.flush()
        return itens_criados

    @staticmethod
    async def listar_por_venda(db: AsyncSession, venda_id: UUID) -> List[ItemVenda]:
        """Lista itens de uma venda."""
        query = select(ItemVenda).where(ItemVenda.venda_id == venda_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def atualizar(db: AsyncSession, item_id: UUID, **dados) -> Optional[ItemVenda]:
        """Atualiza um item de venda."""
        query = select(ItemVenda).where(ItemVenda.id == item_id)
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        for key, value in dados.items():
            if value is not None:
                setattr(item, key, value)
        
        await db.flush()
        return item


class PagamentoVendaRepository:
    """Repository para operações de Pagamento de Venda."""

    @staticmethod
    async def criar(db: AsyncSession, **dados) -> PagamentoVenda:
        """Cria um novo pagamento de venda."""
        pagamento = PagamentoVenda(**dados)
        db.add(pagamento)
        await db.flush()
        return pagamento

    @staticmethod
    async def criar_varios(db: AsyncSession, pagamentos: List[dict]) -> List[PagamentoVenda]:
        """Cria múltiplos pagamentos de venda."""
        pagamentos_criados = []
        for pag_data in pagamentos:
            pagamento = PagamentoVenda(**pag_data)
            db.add(pagamento)
            pagamentos_criados.append(pagamento)
        
        await db.flush()
        return pagamentos_criados

    @staticmethod
    async def listar_por_venda(db: AsyncSession, venda_id: UUID) -> List[PagamentoVenda]:
        """Lista pagamentos de uma venda."""
        query = select(PagamentoVenda).where(PagamentoVenda.venda_id == venda_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def somar_pagamentos(db: AsyncSession, venda_id: UUID) -> Decimal:
        """Soma total de pagamentos de uma venda."""
        query = select(func.sum(PagamentoVenda.valor_pago)).where(
            PagamentoVenda.venda_id == venda_id
        )
        result = await db.execute(query)
        total = result.scalar()
        return Decimal(total) if total else Decimal('0.0')


class ReservaEstoqueVendaRepository:
    """Repository para operações de Reserva de Estoque."""

    @staticmethod
    async def criar(db: AsyncSession, **dados) -> ReservaEstoqueVenda:
        """Cria uma nova reserva de estoque."""
        reserva = ReservaEstoqueVenda(**dados)
        db.add(reserva)
        await db.flush()
        return reserva

    @staticmethod
    async def criar_varias(db: AsyncSession, reservas: List[dict]) -> List[ReservaEstoqueVenda]:
        """Cria múltiplas reservas de estoque."""
        reservas_criadas = []
        for reserva_data in reservas:
            reserva = ReservaEstoqueVenda(**reserva_data)
            db.add(reserva)
            reservas_criadas.append(reserva)
        
        await db.flush()
        return reservas_criadas

    @staticmethod
    async def listar_por_venda(db: AsyncSession, venda_id: UUID) -> List[ReservaEstoqueVenda]:
        """Lista reservas de uma venda."""
        query = select(ReservaEstoqueVenda).where(ReservaEstoqueVenda.venda_id == venda_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def atualizar(
        db: AsyncSession,
        reserva_id: UUID,
        **dados
    ) -> Optional[ReservaEstoqueVenda]:
        """Atualiza uma reserva de estoque."""
        query = select(ReservaEstoqueVenda).where(ReservaEstoqueVenda.id == reserva_id)
        result = await db.execute(query)
        reserva = result.scalar_one_or_none()
        
        if not reserva:
            return None
        
        for key, value in dados.items():
            if value is not None:
                setattr(reserva, key, value)
        
        reserva.updated_at = datetime.utcnow()
        await db.flush()
        return reserva



class ConfiguracaoLojaRepository:
    """Repository para operações de ConfiguracaoLoja."""
    
    @staticmethod
    async def criar(db: AsyncSession, **dados) -> ConfiguracaoLoja:
        """Cria uma nova configuração de loja."""
        config = ConfiguracaoLoja(**dados)
        db.add(config)
        await db.flush()
        return config
    
    @staticmethod
    async def buscar_por_empresa(
        db: AsyncSession,
        empresa_id: int
    ) -> Optional[ConfiguracaoLoja]:
        """Busca configuração da loja por empresa."""
        query = select(ConfiguracaoLoja).where(
            ConfiguracaoLoja.empresa_id == empresa_id
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def atualizar(
        db: AsyncSession,
        config_id: UUID,
        **dados
    ) -> ConfiguracaoLoja:
        """Atualiza configuração da loja."""
        query = select(ConfiguracaoLoja).where(
            ConfiguracaoLoja.id == config_id
        )
        
        result = await db.execute(query)
        config = result.scalar_one()
        
        for key, value in dados.items():
            setattr(config, key, value)
        
        await db.flush()
        return config


class FaixaEntregaRepository:
    """Repository para operações de FaixaEntrega."""
    
    @staticmethod
    async def criar(db: AsyncSession, **dados) -> FaixaEntrega:
        """Cria uma nova faixa de entrega."""
        faixa = FaixaEntrega(**dados)
        db.add(faixa)
        await db.flush()
        return faixa
    
    @staticmethod
    async def buscar_por_id(
        db: AsyncSession,
        faixa_id: UUID
    ) -> Optional[FaixaEntrega]:
        """Busca faixa de entrega por ID."""
        query = select(FaixaEntrega).where(
            FaixaEntrega.id == faixa_id
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def buscar_por_bairro(
        db: AsyncSession,
        empresa_id: int,
        bairro: str
    ) -> Optional[FaixaEntrega]:
        """Busca faixa de entrega por empresa e bairro."""
        query = select(FaixaEntrega).where(
            and_(
                FaixaEntrega.empresa_id == empresa_id,
                FaixaEntrega.bairro.ilike(bairro),  # Case-insensitive
                FaixaEntrega.ativo == True
            )
        )
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def listar(
        db: AsyncSession,
        empresa_id: int,
        apenas_ativas: bool = False
    ) -> List[FaixaEntrega]:
        """Lista faixas de entrega por empresa."""
        query = select(FaixaEntrega).where(
            FaixaEntrega.empresa_id == empresa_id
        )
        
        if apenas_ativas:
            query = query.where(FaixaEntrega.ativo == True)
        
        query = query.order_by(FaixaEntrega.bairro)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def atualizar(
        db: AsyncSession,
        faixa_id: UUID,
        **dados
    ) -> FaixaEntrega:
        """Atualiza faixa de entrega."""
        query = select(FaixaEntrega).where(
            FaixaEntrega.id == faixa_id
        )
        
        result = await db.execute(query)
        faixa = result.scalar_one()
        
        for key, value in dados.items():
            setattr(faixa, key, value)
        
        await db.flush()
        return faixa
    
    @staticmethod
    async def deletar(
        db: AsyncSession,
        faixa_id: UUID
    ) -> None:
        """Deleta faixa de entrega."""
        query = select(FaixaEntrega).where(
            FaixaEntrega.id == faixa_id
        )
        
        result = await db.execute(query)
        faixa = result.scalar_one()
        
        await db.delete(faixa)
        await db.flush()
