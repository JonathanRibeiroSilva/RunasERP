"""
Repository de Estoque.
"""
from datetime import datetime, date, timedelta
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.estoque import (
    Estoque,
    Movimentacao,
    Lote,
    Inventario,
    ItemInventario,
    TipoMovimentacao,
    StatusLote
)


def campos_gravaveis(modelo, campos: dict) -> dict:
    """Descarta `null` que o banco não aceita.

    Todo campo de um schema de PATCH aceita None, porque é assim que ele fica
    opcional — mas a coluna por trás pode ser obrigatória. Sem este filtro,
    apagar um campo obrigatório viraria um IntegrityError vindo do flush, sem
    dizer qual campo. Em coluna anulável o None passa, e é ele que apaga o
    valor.

    Cópia da mesma regra de services/produtos/repositories/produtos.py. Os
    serviços não compartilham código (`shared/` está morto, zero imports) e
    cada um é uma imagem própria — duplicar quatro linhas é mais barato que
    inventar um pacote comum para elas.
    """
    colunas = modelo.__table__.columns
    return {
        campo: valor
        for campo, valor in campos.items()
        if not (valor is None and campo in colunas and not colunas[campo].nullable)
    }



class EstoqueRepository:
    """Repository para operações de Estoque."""

    @staticmethod
    async def criar(db: AsyncSession, **kwargs) -> Estoque:
        """Cria um novo registro de estoque.

        Defaults de coluna (quantidade/quantidade_reservada) só são aplicados no flush;
        normalizamos aqui para calcular quantidade_disponivel sem estourar quando o caller
        não informa esses campos.
        """
        estoque = Estoque(**kwargs)
        if estoque.quantidade is None:
            estoque.quantidade = 0.0
        if estoque.quantidade_reservada is None:
            estoque.quantidade_reservada = 0.0
        estoque.quantidade_disponivel = estoque.quantidade - estoque.quantidade_reservada
        db.add(estoque)
        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return estoque

    @staticmethod
    async def buscar_por_id(
        db: AsyncSession, empresa_id: int, estoque_id: UUID, for_update: bool = False
    ) -> Optional[Estoque]:
        """Busca estoque por ID. for_update: mesmo lock de linha de buscar_por_produto."""
        query = (
            select(Estoque)
            .where(Estoque.empresa_id == empresa_id)
            .where(Estoque.id == estoque_id)
        )
        if for_update:
            query = query.with_for_update()
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def buscar_por_produto(
        db: AsyncSession,
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID] = None,
        for_update: bool = False
    ) -> Optional[Estoque]:
        """
        Busca estoque por produto e variante.

        for_update=True adquire um lock de linha (SELECT ... FOR UPDATE) para
        serializar baixas concorrentes do mesmo produto e impedir overselling.
        """
        query = select(Estoque).where(
            and_(
                Estoque.empresa_id == empresa_id,
                Estoque.produto_id == produto_id
            )
        )

        if variante_id:
            query = query.where(Estoque.variante_id == variante_id)
        else:
            query = query.where(Estoque.variante_id.is_(None))

        if for_update:
            query = query.with_for_update()

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def listar(
        db: AsyncSession,
        empresa_id: int,
        skip: int = 0,
        limit: int = 100,
        apenas_ativos: bool = True,
        apenas_baixo: bool = False,
        apenas_zerado: bool = False
    ) -> List[Estoque]:
        """Lista estoques com filtros."""
        query = select(Estoque).where(Estoque.empresa_id == empresa_id)
        
        if apenas_ativos:
            query = query.where(Estoque.ativo == True)
        
        if apenas_baixo:
            query = query.where(Estoque.quantidade <= Estoque.estoque_minimo)
        
        if apenas_zerado:
            query = query.where(Estoque.quantidade == 0)
        
        query = query.offset(skip).limit(limit).order_by(Estoque.produto_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def atualizar(
        db: AsyncSession,
        empresa_id: int,
        estoque_id: UUID,
        **kwargs
    ) -> Optional[Estoque]:
        """Atualiza um estoque."""
        estoque = await EstoqueRepository.buscar_por_id(db, empresa_id, estoque_id)
        if not estoque:
            return None
        
        # Grava vazio também: `if value is not None` tratava "não mandou o
        # campo" e "mandou vazio" como a mesma coisa, então limpar a
        # localização ou o estoque máximo nunca chegava ao banco. O
        # exclude_unset do service já separa as duas; campos_gravaveis só
        # segura o null que a coluna recusa (estoque_minimo é NOT NULL).
        for key, value in campos_gravaveis(Estoque, kwargs).items():
            if hasattr(estoque, key):
                setattr(estoque, key, value)

        estoque.updated_at = datetime.utcnow()
        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return estoque

    @staticmethod
    async def atualizar_quantidade(
        db: AsyncSession,
        empresa_id: int,
        estoque_id: UUID,
        quantidade: float
    ) -> Optional[Estoque]:
        """Atualiza a quantidade de estoque.

        Entrada, saída e ajuste passam todos por aqui, e só o ajuste escrevia uma
        quantidade que não vem de uma conta sobre a anterior: ele grava a contagem
        do inventário. Contar 2 com 4 unidades reservadas deixava
        quantidade_disponivel = -2 — o estoque passava a prometer o que não tinha,
        e agora seria o CHECK derrubando a requisição com um 500 sem explicação.
        A recusa mora aqui, no ponto por onde os três caminhos passam, e vira 400
        com o motivo: as reservas precisam ser liberadas antes de baixar a contagem.
        """
        estoque = await EstoqueRepository.buscar_por_id(db, empresa_id, estoque_id)
        if not estoque:
            return None

        if quantidade < estoque.quantidade_reservada:
            raise ValueError(
                f"Quantidade ({quantidade}) menor que a reservada "
                f"({estoque.quantidade_reservada}). Libere as reservas antes."
            )

        estoque.quantidade = quantidade
        estoque.quantidade_disponivel = quantidade - estoque.quantidade_reservada
        estoque.updated_at = datetime.utcnow()

        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return estoque

    @staticmethod
    async def reservar(
        db: AsyncSession,
        empresa_id: int,
        estoque_id: UUID,
        quantidade: float
    ) -> Optional[Estoque]:
        """Reserva quantidade de estoque."""
        estoque = await EstoqueRepository.buscar_por_id(db, empresa_id, estoque_id)
        if not estoque:
            return None
        
        # A checagem é sobre a reserva que vai ser gravada, não sobre o
        # quantidade_disponivel lido. Os dois só diferem por um ulp de Float, mas
        # é esse ulp que faria o CHECK recusar uma reserva legítima com um 500:
        # comparando o valor que de fato vai para a coluna, a subtração abaixo
        # nunca sai negativa (IEEE 754 preserva o sinal de a - b com a >= b).
        reservada = estoque.quantidade_reservada + quantidade
        if reservada > estoque.quantidade:
            raise ValueError("Quantidade disponível insuficiente para reserva")

        estoque.quantidade_reservada = reservada
        estoque.quantidade_disponivel = estoque.quantidade - reservada
        estoque.updated_at = datetime.utcnow()

        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return estoque

    @staticmethod
    async def liberar_reserva(
        db: AsyncSession,
        empresa_id: int,
        estoque_id: UUID,
        quantidade: float
    ) -> Optional[Estoque]:
        """Libera reserva de estoque."""
        estoque = await EstoqueRepository.buscar_por_id(db, empresa_id, estoque_id)
        if not estoque:
            return None
        
        if estoque.quantidade_reservada < quantidade:
            raise ValueError("Quantidade reservada insuficiente")
        
        estoque.quantidade_reservada -= quantidade
        estoque.quantidade_disponivel = estoque.quantidade - estoque.quantidade_reservada
        estoque.updated_at = datetime.utcnow()

        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return estoque

    @staticmethod
    async def contar_total(db: AsyncSession, empresa_id: int) -> int:
        """Conta total de estoques."""
        result = await db.execute(
            select(func.count(Estoque.id)).where(Estoque.empresa_id == empresa_id)
        )
        return result.scalar_one()

    @staticmethod
    async def contar_estoque_baixo(db: AsyncSession, empresa_id: int) -> int:
        """Conta estoques abaixo do mínimo."""
        result = await db.execute(
            select(func.count(Estoque.id)).where(
                and_(
                    Estoque.empresa_id == empresa_id,
                    Estoque.ativo == True,
                    Estoque.quantidade <= Estoque.estoque_minimo,
                    Estoque.quantidade > 0
                )
            )
        )
        return result.scalar_one()

    @staticmethod
    async def contar_estoque_zerado(db: AsyncSession, empresa_id: int) -> int:
        """Conta estoques zerados."""
        result = await db.execute(
            select(func.count(Estoque.id)).where(
                and_(
                    Estoque.empresa_id == empresa_id,
                    Estoque.ativo == True,
                    Estoque.quantidade == 0
                )
            )
        )
        return result.scalar_one()


class MovimentacaoRepository:
    """Repository para operações de Movimentação."""

    @staticmethod
    async def criar(db: AsyncSession, **kwargs) -> Movimentacao:
        """Cria uma nova movimentação."""
        # Calcular custo total se tiver custo unitário
        if kwargs.get('custo_unitario'):
            kwargs['custo_total'] = kwargs['custo_unitario'] * kwargs['quantidade']
        
        movimentacao = Movimentacao(**kwargs)
        db.add(movimentacao)
        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return movimentacao

    @staticmethod
    async def buscar_por_id(db: AsyncSession, movimentacao_id: UUID) -> Optional[Movimentacao]:
        """Busca movimentação por ID."""
        result = await db.execute(
            select(Movimentacao).where(Movimentacao.id == movimentacao_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def listar(
        db: AsyncSession,
        empresa_id: Optional[int] = None,
        estoque_id: Optional[UUID] = None,
        tipo: Optional[TipoMovimentacao] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Movimentacao]:
        """Lista movimentações com filtros.

        Movimentacao não tem empresa_id próprio; quando informado, o isolamento de
        tenant é garantido por join no estoque dono da movimentação.
        """
        query = select(Movimentacao)

        if empresa_id is not None:
            query = query.join(Estoque, Movimentacao.estoque_id == Estoque.id).where(
                Estoque.empresa_id == empresa_id
            )

        if estoque_id:
            query = query.where(Movimentacao.estoque_id == estoque_id)
        
        if tipo:
            query = query.where(Movimentacao.tipo == tipo.value)
        
        if data_inicio:
            query = query.where(Movimentacao.created_at >= data_inicio)
        
        if data_fim:
            query = query.where(Movimentacao.created_at <= data_fim)
        
        query = query.offset(skip).limit(limit).order_by(Movimentacao.created_at.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def contar_por_tipo(
        db: AsyncSession,
        tipo: TipoMovimentacao,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> int:
        """Conta movimentações por tipo."""
        query = select(func.count(Movimentacao.id)).where(Movimentacao.tipo == tipo.value)
        
        if data_inicio:
            query = query.where(Movimentacao.created_at >= data_inicio)
        
        if data_fim:
            query = query.where(Movimentacao.created_at <= data_fim)
        
        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def somar_quantidade_por_tipo(
        db: AsyncSession,
        tipo: TipoMovimentacao,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> float:
        """Soma quantidade movimentada por tipo."""
        query = select(func.sum(Movimentacao.quantidade)).where(Movimentacao.tipo == tipo.value)
        
        if data_inicio:
            query = query.where(Movimentacao.created_at >= data_inicio)
        
        if data_fim:
            query = query.where(Movimentacao.created_at <= data_fim)
        
        result = await db.execute(query)
        return result.scalar_one() or 0.0


class LoteRepository:
    """Repository para operações de Lote."""

    @staticmethod
    async def criar(db: AsyncSession, **kwargs) -> Lote:
        """Cria um novo lote."""
        kwargs['quantidade_inicial'] = kwargs['quantidade']
        lote = Lote(**kwargs)
        db.add(lote)
        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return lote

    @staticmethod
    async def buscar_por_id(db: AsyncSession, empresa_id: int, lote_id: UUID) -> Optional[Lote]:
        """Busca lote por ID."""
        result = await db.execute(
            select(Lote)
            .where(Lote.empresa_id == empresa_id)
            .where(Lote.id == lote_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def buscar_por_codigo(db: AsyncSession, empresa_id: int, codigo: str) -> Optional[Lote]:
        """Busca lote por código."""
        result = await db.execute(
            select(Lote)
            .where(Lote.empresa_id == empresa_id)
            .where(Lote.codigo == codigo)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def listar(
        db: AsyncSession,
        empresa_id: int,
        estoque_id: Optional[UUID] = None,
        status: Optional[StatusLote] = None,
        vencendo: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Lote]:
        """Lista lotes com filtros."""
        query = select(Lote).where(Lote.empresa_id == empresa_id)
        
        if estoque_id:
            query = query.where(Lote.estoque_id == estoque_id)
        
        if status:
            query = query.where(Lote.status == status.value)
        
        if vencendo:
            data_limite = date.today() + timedelta(days=30)
            query = query.where(
                and_(
                    Lote.data_validade.isnot(None),
                    Lote.data_validade <= data_limite,
                    Lote.status == StatusLote.ATIVO.value
                )
            )
        
        query = query.offset(skip).limit(limit).order_by(Lote.data_validade)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def atualizar(db: AsyncSession, empresa_id: int, lote_id: UUID, **kwargs) -> Optional[Lote]:
        """Atualiza um lote."""
        lote = await LoteRepository.buscar_por_id(db, empresa_id, lote_id)
        if not lote:
            return None
        
        for key, value in kwargs.items():
            if hasattr(lote, key) and value is not None:
                setattr(lote, key, value)
        
        lote.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(lote)
        return lote

    @staticmethod
    async def atualizar_quantidade(db: AsyncSession, empresa_id: int, lote_id: UUID, quantidade: float) -> Optional[Lote]:
        """Atualiza quantidade do lote."""
        lote = await LoteRepository.buscar_por_id(db, empresa_id, lote_id)
        if not lote:
            return None
        
        lote.quantidade = quantidade
        lote.updated_at = datetime.utcnow()
        
        # Se quantidade zerou, marcar como inativo
        if quantidade == 0:
            lote.status = StatusLote.BLOQUEADO.value

        # flush only — the calling service owns the transaction (begin_nested + commit).
        await db.flush()
        return lote

    @staticmethod
    async def marcar_vencidos(db: AsyncSession, empresa_id: int) -> int:
        """
        Marca lotes vencidos (E4, Onda 6).

        Não comita — o chamador controla a transação, mesma convenção do resto
        do repository (`atualizar_quantidade` acima). O job que chama isto por
        todos os tenants (`jobs/marcar_lotes_vencidos.py`) precisa do commit do
        lado de fora para poder seguir para o próximo tenant mesmo se um falhar.
        """
        hoje = date.today()
        result = await db.execute(
            select(Lote).where(
                and_(
                    Lote.empresa_id == empresa_id,
                    Lote.data_validade < hoje,
                    Lote.status == StatusLote.ATIVO.value
                )
            )
        )
        lotes = result.scalars().all()

        count = 0
        for lote in lotes:
            lote.status = StatusLote.VENCIDO.value
            lote.updated_at = datetime.utcnow()
            count += 1

        if count > 0:
            await db.flush()

        return count

    @staticmethod
    async def empresas_com_lote_vencido(db: AsyncSession) -> List[int]:
        """IDs de empresa com ao menos um lote ATIVO vencido — para o job cross-tenant."""
        hoje = date.today()
        result = await db.execute(
            select(Lote.empresa_id).where(
                and_(
                    Lote.data_validade < hoje,
                    Lote.status == StatusLote.ATIVO.value
                )
            ).distinct()
        )
        return [row[0] for row in result.all()]


class InventarioRepository:
    """Repository para operações de Inventário."""

    @staticmethod
    async def criar(db: AsyncSession, **kwargs) -> Inventario:
        """Cria um novo inventário."""
        inventario = Inventario(**kwargs)
        db.add(inventario)
        await db.commit()
        await db.refresh(inventario)
        return inventario

    @staticmethod
    async def buscar_por_id(db: AsyncSession, empresa_id: int, inventario_id: UUID) -> Optional[Inventario]:
        """Busca inventário por ID."""
        result = await db.execute(
            select(Inventario)
            .options(selectinload(Inventario.itens))
            .where(Inventario.empresa_id == empresa_id)
            .where(Inventario.id == inventario_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def listar(
        db: AsyncSession,
        empresa_id: int,
        apenas_abertos: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Inventario]:
        """Lista inventários."""
        query = select(Inventario).where(Inventario.empresa_id == empresa_id)
        
        if apenas_abertos:
            query = query.where(Inventario.finalizado == False)
        
        query = query.offset(skip).limit(limit).order_by(Inventario.data_inventario.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def finalizar(db: AsyncSession, empresa_id: int, inventario_id: UUID) -> Optional[Inventario]:
        """Finaliza um inventário."""
        inventario = await InventarioRepository.buscar_por_id(db, empresa_id, inventario_id)
        if not inventario:
            return None
        
        inventario.finalizado = True
        inventario.data_finalizacao = datetime.utcnow()
        inventario.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(inventario)
        return inventario

    @staticmethod
    async def adicionar_item(db: AsyncSession, **kwargs) -> ItemInventario:
        """Adiciona item ao inventário."""
        item = ItemInventario(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def marcar_item_ajustado(db: AsyncSession, item_id: UUID) -> Optional[ItemInventario]:
        """Marca item como ajustado."""
        result = await db.execute(
            select(ItemInventario).where(ItemInventario.id == item_id)
        )
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        item.ajustado = True
        await db.commit()
        await db.refresh(item)
        return item
