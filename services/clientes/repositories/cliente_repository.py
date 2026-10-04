"""
Repository para operações de Cliente no banco de dados.
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, update, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from models.cliente import Cliente, Endereco, MovimentoCredito, TipoMovimentoCredito
from schemas.cliente import ClienteCreate, ClienteCreateOAuth, ClienteUpdate, EnderecoCreate, EnderecoUpdate
import structlog

log = structlog.get_logger()


class ClienteRepository:
    """Repository de Cliente."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def criar(self, data: ClienteCreate) -> Cliente:
        """Cria um novo cliente."""
        cliente = Cliente(
            empresa_id=data.empresa_id,
            cpf=data.cpf,
            nome=data.nome,
            telefone=data.telefone,
            email=data.email,
            data_nasc=data.data_nasc
        )
        self.db.add(cliente)
        await self.db.flush()
        log.info("cliente.criado", cliente_id=str(cliente.id), empresa_id=data.empresa_id)
        return cliente
    
    async def buscar_por_id(
        self, cliente_id: UUID, empresa_id: int, for_update: bool = False
    ) -> Cliente | None:
        """
        Busca cliente por ID (filtrado por empresa).

        for_update: SELECT ... FOR UPDATE — trava a linha para serializar
        débitos/créditos concorrentes do mesmo cliente (mesmo lock de
        `estoque.EstoqueRepository.buscar_por_produto`).
        """
        query = select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.empresa_id == empresa_id
        )
        if for_update:
            query = query.with_for_update()
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def buscar_por_cpf(self, cpf: str, empresa_id: int) -> Cliente | None:
        """Busca cliente por CPF (filtrado por empresa)."""
        result = await self.db.execute(
            select(Cliente).where(
                Cliente.cpf == cpf,
                Cliente.empresa_id == empresa_id
            )
        )
        return result.scalar_one_or_none()
    
    async def criar_oauth(self, data: ClienteCreateOAuth) -> Cliente:
        """Cria um novo cliente via OAuth (CPF e telefone opcionais)."""
        cliente = Cliente(
            empresa_id=data.empresa_id,
            cpf=data.cpf,  # Pode ser None
            nome=data.nome,
            telefone=data.telefone,  # Pode ser None
            email=data.email,
            data_nasc=data.data_nasc
        )
        self.db.add(cliente)
        await self.db.flush()
        log.info("cliente.oauth.criado", cliente_id=str(cliente.id), empresa_id=data.empresa_id, email=data.email)
        return cliente
    
    async def buscar_por_email(self, email: str, empresa_id: int) -> Cliente | None:
        """Busca cliente por email (filtrado por empresa)."""
        result = await self.db.execute(
            select(Cliente).where(
                Cliente.email == email,
                Cliente.empresa_id == empresa_id
            )
        )
        return result.scalar_one_or_none()
    
    async def listar(
        self,
        empresa_id: int,
        skip: int = 0,
        limit: int = 100,
        nome: str | None = None,
        cpf: str | None = None,
        bloqueado: bool | None = None,
        ativo: bool | None = None
    ) -> tuple[list[Cliente], int]:
        """Lista clientes com filtros (filtrado por empresa)."""
        query = select(Cliente).where(Cliente.empresa_id == empresa_id)
        
        # Filtro de ativo (padrão: apenas ativos)
        if ativo is not None:
            query = query.where(Cliente.ativo == ativo)
        else:
            query = query.where(Cliente.ativo == True)
        
        if nome:
            # Tentar detectar se é CPF (apenas números)
            nome_limpo = ''.join(filter(str.isdigit, nome))
            if len(nome_limpo) >= 3:  # Se tem pelo menos 3 dígitos, buscar por CPF também
                query = query.where(
                    (Cliente.nome.ilike(f"%{nome}%")) | 
                    (Cliente.cpf.like(f"%{nome_limpo}%"))
                )
            else:
                query = query.where(Cliente.nome.ilike(f"%{nome}%"))
        
        if cpf:
            # Remover formatação do CPF
            cpf_limpo = ''.join(filter(str.isdigit, cpf))
            query = query.where(Cliente.cpf == cpf_limpo)
        
        if bloqueado is not None:
            query = query.where(Cliente.bloqueado == bloqueado)
        
        # Total
        count_result = await self.db.execute(query)
        total = len(count_result.all())
        
        # Itens paginados
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        clientes = list(result.scalars().all())
        
        return clientes, total
    
    async def atualizar(self, cliente_id: UUID, empresa_id: int, data: ClienteUpdate) -> Cliente | None:
        """Atualiza um cliente (filtrado por empresa)."""
        cliente = await self.buscar_por_id(cliente_id, empresa_id)
        if not cliente:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cliente, field, value)

        await self.db.flush()
        log.info("cliente.atualizado", cliente_id=str(cliente_id), empresa_id=empresa_id)
        return cliente
    
    async def soft_delete(self, cliente_id: UUID, empresa_id: int) -> bool:
        """Soft delete de um cliente (filtrado por empresa)."""
        cliente = await self.buscar_por_id(cliente_id, empresa_id)
        if not cliente:
            return False
        
        cliente.ativo = False
        await self.db.flush()
        log.info("cliente.desativado", cliente_id=str(cliente_id), empresa_id=empresa_id)
        return True

    async def reativar(self, cliente_id: UUID, empresa_id: int) -> Cliente | None:
        """Reativa um cliente desativado (filtrado por empresa)."""
        cliente = await self.buscar_por_id(cliente_id, empresa_id)
        if not cliente:
            return None

        cliente.ativo = True
        await self.db.flush()
        log.info("cliente.reativado", cliente_id=str(cliente_id), empresa_id=empresa_id)
        return cliente

    async def atualizar_credito(
        self,
        cliente_id: UUID,
        empresa_id: int,
        limite_credito: Decimal,
        dia_vencimento: int | None
    ) -> Cliente | None:
        """
        Atualiza limite de crédito e dia de vencimento (filtrado por empresa).

        C1: trocar o limite não pode apagar o saldo devedor. `credito_disponivel`
        é recalculado como `novo_limite - saldo_devedor_atual`, não reposto para o
        limite cheio — senão um cliente com fiado em aberto "quita" a dívida
        sozinho só porque o lojista editou o limite dele.
        """
        cliente = await self.buscar_por_id(cliente_id, empresa_id)
        if not cliente:
            return None

        saldo_devedor = cliente.limite_credito - cliente.credito_disponivel
        cliente.limite_credito = limite_credito
        cliente.dia_vencimento = dia_vencimento
        cliente.credito_disponivel = limite_credito - saldo_devedor

        await self.db.flush()
        log.info(
            "cliente.credito_atualizado", cliente_id=str(cliente_id), empresa_id=empresa_id,
            saldo_devedor=str(saldo_devedor)
        )
        return cliente

    async def registrar_movimento_credito(
        self,
        cliente_id: UUID,
        empresa_id: int,
        tipo: TipoMovimentoCredito,
        valor: Decimal,
        documento: str
    ) -> Cliente | None:
        """
        Debita (`valor` negativo) ou credita (`valor` positivo) o cliente via ledger.

        C2+C3: idempotente e com lock de linha — mesmo desenho de
        `EstoqueService._baixar_venda_once`. `documento` é a chave de idempotência
        (numero_venda); a unique constraint em `movimentos_credito` (empresa_id,
        documento, tipo) serializa chamadas concorrentes do mesmo evento e faz
        retry/webhook duplicado não debitar/creditar duas vezes.

        Levanta ValueError se o débito deixaria `credito_disponivel` negativo —
        é o teto de crédito que C3 pedia e `vendas` nunca checava.
        """
        existente = await self.db.execute(
            select(MovimentoCredito.id).where(
                MovimentoCredito.empresa_id == empresa_id,
                MovimentoCredito.documento == documento,
                MovimentoCredito.tipo == tipo.value,
            )
        )
        if existente.first() is not None:
            log.info(
                "cliente.credito_movimento_idempotente", cliente_id=str(cliente_id),
                empresa_id=empresa_id, documento=documento, tipo=tipo.value
            )
            return await self.buscar_por_id(cliente_id, empresa_id)

        # Trava a linha do cliente antes de ler o saldo: duas requisições concorrentes
        # para o mesmo cliente serializam aqui, a segunda só lê depois que a primeira
        # já gravou (ou deu rollback).
        cliente = await self.buscar_por_id(cliente_id, empresa_id, for_update=True)
        if not cliente:
            return None

        novo_credito = cliente.credito_disponivel + valor
        if novo_credito < 0:
            raise ValueError(
                f"Crédito insuficiente: disponível {cliente.credito_disponivel}, "
                f"solicitado {-valor}"
            )

        self.db.add(MovimentoCredito(
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            tipo=tipo.value,
            valor=valor,
            documento=documento,
        ))
        try:
            await self.db.flush()
        except IntegrityError:
            # Corrida: outra transação registrou o mesmo (empresa_id, documento, tipo)
            # entre o SELECT de cima e este flush. Idempotente — não é erro.
            await self.db.rollback()
            log.info(
                "cliente.credito_movimento_idempotente_corrida", cliente_id=str(cliente_id),
                empresa_id=empresa_id, documento=documento, tipo=tipo.value
            )
            return await self.buscar_por_id(cliente_id, empresa_id)

        cliente.credito_disponivel = novo_credito
        await self.db.flush()
        log.info(
            "cliente.credito_movimento", cliente_id=str(cliente_id), empresa_id=empresa_id,
            tipo=tipo.value, valor=str(valor), documento=documento
        )
        return cliente
    
    async def bloquear(self, cliente_id: UUID, empresa_id: int) -> Cliente | None:
        """Bloqueia um cliente (filtrado por empresa)."""
        cliente = await self.buscar_por_id(cliente_id, empresa_id)
        if not cliente:
            return None
        
        cliente.bloqueado = True
        await self.db.flush()
        log.info("cliente.bloqueado", cliente_id=str(cliente_id), empresa_id=empresa_id)
        return cliente
    
    async def desbloquear(self, cliente_id: UUID, empresa_id: int) -> Cliente | None:
        """Desbloqueia um cliente (filtrado por empresa)."""
        cliente = await self.buscar_por_id(cliente_id, empresa_id)
        if not cliente:
            return None
        
        cliente.bloqueado = False
        await self.db.flush()
        log.info("cliente.desbloqueado", cliente_id=str(cliente_id), empresa_id=empresa_id)
        return cliente


class EnderecoRepository:
    """Repository de Endereço."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def criar(self, cliente_id: UUID, data: EnderecoCreate) -> Endereco:
        """Cria um novo endereço."""
        # Se for principal, desmarcar outros
        if data.principal:
            await self.db.execute(
                update(Endereco)
                .where(Endereco.cliente_id == cliente_id)
                .values(principal=False)
            )
        
        endereco = Endereco(
            cliente_id=cliente_id,
            **data.model_dump()
        )
        self.db.add(endereco)
        await self.db.flush()
        return endereco

    async def listar_por_cliente(self, cliente_id: UUID) -> list[Endereco]:
        """Lista endereços de um cliente."""
        result = await self.db.execute(
            select(Endereco).where(Endereco.cliente_id == cliente_id)
        )
        return list(result.scalars().all())
    
    async def buscar_por_id(self, endereco_id: UUID) -> Endereco | None:
        """Busca endereço por ID."""
        result = await self.db.execute(
            select(Endereco).where(Endereco.id == endereco_id)
        )
        return result.scalar_one_or_none()
    
    async def atualizar(
        self,
        endereco_id: UUID,
        data: EnderecoUpdate
    ) -> Endereco | None:
        """Atualiza um endereço."""
        endereco = await self.buscar_por_id(endereco_id)
        if not endereco:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Se marcar como principal, desmarcar outros
        if update_data.get('principal'):
            await self.db.execute(
                update(Endereco)
                .where(Endereco.cliente_id == endereco.cliente_id)
                .where(Endereco.id != endereco_id)
                .values(principal=False)
            )
        
        for field, value in update_data.items():
            setattr(endereco, field, value)

        await self.db.flush()
        return endereco

    async def deletar(self, endereco_id: UUID) -> bool:
        """Deleta um endereço."""
        endereco = await self.buscar_por_id(endereco_id)
        if not endereco:
            return False
        
        await self.db.delete(endereco)
        await self.db.flush()
        return True
