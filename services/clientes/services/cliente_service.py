"""
Service de Cliente com regras de negócio.
"""
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
import structlog

from repositories.cliente_repository import ClienteRepository, EnderecoRepository
from schemas.cliente import (
    ClienteCreate,
    ClienteUpdate,
    CreditoUpdate,
    CreditoDelta,
    EnderecoCreate,
    EnderecoUpdate
)
from models.cliente import Cliente, Endereco

log = structlog.get_logger()


class ClienteService:
    """Service de Cliente."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cliente_repo = ClienteRepository(db)
        self.endereco_repo = EnderecoRepository(db)
    
    async def criar_cliente(self, data: ClienteCreate) -> Cliente:
        """
        Cria um novo cliente com transação atômica.
        
        Regras:
        - CPF deve ser único
        - CPF já validado no schema
        - Telefone já normalizado no schema
        """
        try:
            # Verificar se CPF já existe
            cliente_existente = await self.cliente_repo.buscar_por_cpf(data.cpf)
            if cliente_existente:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="CPF já cadastrado"
                )
            
            cliente = await self.cliente_repo.criar(data)
            await self.db.commit()
            await self.db.refresh(cliente)
            
            log.info("cliente.criado", cliente_id=str(cliente.id), cpf=data.cpf)
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_criar_cliente", error=str(e))
            raise
    
    async def buscar_cliente(self, cliente_id: UUID) -> Cliente:
        """Busca cliente por ID."""
        cliente = await self.cliente_repo.buscar_por_id(cliente_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )
        return cliente
    
    async def buscar_por_cpf(self, cpf: str) -> Cliente:
        """Busca cliente por CPF."""
        cliente = await self.cliente_repo.buscar_por_cpf(cpf)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )
        return cliente
    
    async def listar_clientes(
        self,
        skip: int = 0,
        limit: int = 100,
        nome: str | None = None,
        cpf: str | None = None,
        bloqueado: bool | None = None,
        ativo: bool | None = None
    ) -> tuple[list[Cliente], int]:
        """Lista clientes com filtros."""
        return await self.cliente_repo.listar(skip, limit, nome, cpf, bloqueado, ativo)
    
    async def atualizar_cliente(
        self,
        cliente_id: UUID,
        data: ClienteUpdate
    ) -> Cliente:
        """Atualiza dados do cliente com transação atômica."""
        try:
            cliente = await self.cliente_repo.atualizar(cliente_id, data)
            if not cliente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado"
                )
            
            await self.db.commit()
            await self.db.refresh(cliente)
            log.info("cliente.atualizado", cliente_id=str(cliente_id))
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_atualizar_cliente", error=str(e))
            raise
    
    async def desativar_cliente(self, cliente_id: UUID) -> None:
        """
        Desativa um cliente (soft delete) com transação atômica.
        
        Regras:
        - Não pode desativar se tiver pedidos em aberto
        - Não pode desativar se tiver contas pendentes
        """
        try:
            async with self.db.begin_nested():
                cliente = await self.buscar_cliente(cliente_id)
                
                # TODO: Verificar pedidos em aberto (integração com serviço de vendas)
                # TODO: Verificar contas pendentes (integração com serviço financeiro)
                
                sucesso = await self.cliente_repo.soft_delete(cliente_id)
                if not sucesso:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao desativar cliente"
                    )
            
            await self.db.commit()
            log.info("cliente.desativado", cliente_id=str(cliente_id))
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_desativar_cliente", error=str(e))
            raise
    
    async def definir_credito(
        self,
        cliente_id: UUID,
        data: CreditoUpdate
    ) -> Cliente:
        """
        Define limite de crédito e dia de vencimento com transação atômica.
        
        Regras:
        - limite_credito >= 0
        - dia_vencimento entre 1 e 28
        - credito_disponivel = limite_credito - saldo_devedor
        """
        try:
            async with self.db.begin_nested():
                cliente = await self.buscar_cliente(cliente_id)
                
                # TODO: Buscar saldo devedor do serviço financeiro
                saldo_devedor = Decimal("0.00")  # Por enquanto
                
                cliente_atualizado = await self.cliente_repo.atualizar_credito(
                    cliente_id,
                    data.limite_credito,
                    data.dia_vencimento
                )
                
                if not cliente_atualizado:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cliente não encontrado"
                    )
            
            await self.db.commit()
            log.info(
                "cliente.credito_definido",
                cliente_id=str(cliente_id),
                limite=str(data.limite_credito)
            )
            
            return cliente_atualizado
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_definir_credito", error=str(e))
            raise
    
    async def ajustar_credito(
        self,
        cliente_id: UUID,
        delta: Decimal
    ) -> Cliente:
        """
        Ajusta crédito disponível com transação atômica.
        
        Args:
            cliente_id: ID do cliente
            delta: Valor a ajustar (positivo = crédito, negativo = débito)
            
        Regras:
        - credito_disponivel nunca pode ser negativo
        """
        try:
            async with self.db.begin_nested():
                cliente = await self.buscar_cliente(cliente_id)
                
                try:
                    cliente_atualizado = await self.cliente_repo.ajustar_credito_disponivel(
                        cliente_id,
                        delta
                    )
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=str(e)
                    )
                
                if not cliente_atualizado:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cliente não encontrado"
                    )
            
            await self.db.commit()
            log.info(
                "cliente.credito_ajustado",
                cliente_id=str(cliente_id),
                delta=str(delta)
            )
            
            return cliente_atualizado
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_ajustar_credito", error=str(e))
            raise
    
    async def bloquear_cliente(self, cliente_id: UUID) -> Cliente:
        """
        Bloqueia um cliente manualmente com transação atômica.
        
        Regras:
        - Cliente bloqueado não pode fazer compras fiadas
        """
        try:
            async with self.db.begin_nested():
                cliente = await self.cliente_repo.bloquear(cliente_id)
                if not cliente:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cliente não encontrado"
                    )
            
            await self.db.commit()
            log.warning("cliente.bloqueado_manual", cliente_id=str(cliente_id))
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_bloquear_cliente", error=str(e))
            raise
    
    async def desbloquear_cliente(self, cliente_id: UUID) -> Cliente:
        """Desbloqueia um cliente com transação atômica."""
        try:
            async with self.db.begin_nested():
                cliente = await self.cliente_repo.desbloquear(cliente_id)
                if not cliente:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Cliente não encontrado"
                    )
            
            await self.db.commit()
            log.info("cliente.desbloqueado", cliente_id=str(cliente_id))
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_desbloquear_cliente", error=str(e))
            raise
    
    # Métodos de Endereço
    
    async def adicionar_endereco(
        self,
        cliente_id: UUID,
        data: EnderecoCreate
    ) -> Endereco:
        """Adiciona um endereço ao cliente."""
        try:
            # Verificar se cliente existe
            await self.buscar_cliente(cliente_id)
            
            endereco = await self.endereco_repo.criar(cliente_id, data)
            await self.db.commit()
            await self.db.refresh(endereco)
            
            log.info("endereco.criado", cliente_id=str(cliente_id), endereco_id=str(endereco.id))
            return endereco
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_adicionar_endereco", error=str(e))
            raise
    
    async def listar_enderecos(self, cliente_id: UUID) -> list[Endereco]:
        """Lista endereços de um cliente."""
        # Verificar se cliente existe
        await self.buscar_cliente(cliente_id)
        
        return await self.endereco_repo.listar_por_cliente(cliente_id)
    
    async def atualizar_endereco(
        self,
        cliente_id: UUID,
        endereco_id: UUID,
        data: EnderecoUpdate
    ) -> Endereco:
        """Atualiza um endereço com transação atômica."""
        try:
            # Verificar se cliente existe
            await self.buscar_cliente(cliente_id)
            
            # Verificar se endereço pertence ao cliente
            endereco = await self.endereco_repo.buscar_por_id(endereco_id)
            if not endereco or endereco.cliente_id != cliente_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Endereço não encontrado"
                )
            
            endereco_atualizado = await self.endereco_repo.atualizar(endereco_id, data)
            if not endereco_atualizado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Endereço não encontrado"
                )
            
            await self.db.commit()
            await self.db.refresh(endereco_atualizado)
            log.info("endereco.atualizado", endereco_id=str(endereco_id))
            return endereco_atualizado
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_atualizar_endereco", error=str(e))
            raise
    
    async def remover_endereco(
        self,
        cliente_id: UUID,
        endereco_id: UUID
    ) -> None:
        """Remove um endereço com transação atômica."""
        try:
            # Verificar se cliente existe
            await self.buscar_cliente(cliente_id)
            
            # Verificar se endereço pertence ao cliente
            endereco = await self.endereco_repo.buscar_por_id(endereco_id)
            if not endereco or endereco.cliente_id != cliente_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Endereço não encontrado"
                )
            
            sucesso = await self.endereco_repo.deletar(endereco_id)
            if not sucesso:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao remover endereço"
                )
            
            await self.db.commit()
            log.info("endereco.removido", endereco_id=str(endereco_id))
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_remover_endereco", error=str(e))
            raise
