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
    ClienteCreateOAuth,
    ClienteUpdate,
    CreditoUpdate,
    CreditoDelta,
    EnderecoCreate,
    EnderecoUpdate
)
from models.cliente import Cliente, Endereco, TipoMovimentoCredito

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
        - CPF deve ser único por empresa (multi-tenancy)
        - CPF já validado no schema
        - Telefone já normalizado no schema
        """
        try:
            # Verificar se CPF já existe para esta empresa
            cliente_existente = await self.cliente_repo.buscar_por_cpf(data.cpf, data.empresa_id)
            if cliente_existente:
                if cliente_existente.ativo:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="CPF já cadastrado para esta empresa"
                    )
                else:
                    # Cliente inativo: reativar e atualizar dados
                    log.info("cliente.reativando", cliente_id=str(cliente_existente.id), cpf=data.cpf)
                    cliente_existente.ativo = True
                    cliente_existente.nome = data.nome
                    cliente_existente.telefone = data.telefone
                    cliente_existente.email = data.email
                    cliente_existente.data_nasc = data.data_nasc
                    await self.db.commit()
                    await self.db.refresh(cliente_existente)
                    return cliente_existente
            
            cliente = await self.cliente_repo.criar(data)
            await self.db.commit()
            await self.db.refresh(cliente)
            
            log.info("cliente.criado", cliente_id=str(cliente.id), cpf=data.cpf, empresa_id=data.empresa_id)
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_criar_cliente", error=str(e))
            raise
    
    async def criar_cliente_oauth(self, data: ClienteCreateOAuth) -> Cliente:
        """
        Cria um novo cliente via OAuth (Google/Microsoft).
        
        Regras:
        - Email deve ser único por empresa (OAuth usa email, não CPF)
        - CPF e telefone são opcionais (podem ser preenchidos depois pelo cliente)
        - Se CPF fornecido, deve ser válido
        """
        try:
            # Verificar se email já existe para esta empresa
            if data.email:
                cliente_existente = await self.cliente_repo.buscar_por_email(data.email, data.empresa_id)
                if cliente_existente:
                    if cliente_existente.ativo:
                        # Cliente ativo já existe: retornar o existente
                        log.info("cliente.oauth.already_exists", cliente_id=str(cliente_existente.id), email=data.email)
                        return cliente_existente
                    else:
                        # Cliente inativo: reativar e atualizar dados
                        log.info("cliente.oauth.reativando", cliente_id=str(cliente_existente.id), email=data.email)
                        cliente_existente.ativo = True
                        cliente_existente.nome = data.nome
                        if data.cpf:
                            cliente_existente.cpf = data.cpf
                        if data.telefone:
                            cliente_existente.telefone = data.telefone
                        cliente_existente.data_nasc = data.data_nasc
                        await self.db.commit()
                        await self.db.refresh(cliente_existente)
                        return cliente_existente
            
            cliente = await self.cliente_repo.criar_oauth(data)
            await self.db.commit()
            await self.db.refresh(cliente)
            
            log.info("cliente.oauth.criado", cliente_id=str(cliente.id), email=data.email, empresa_id=data.empresa_id)
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_criar_cliente_oauth", error=str(e))
            raise
    
    async def buscar_cliente(self, cliente_id: UUID, empresa_id: int) -> Cliente:
        """Busca cliente por ID (filtrado por empresa)."""
        cliente = await self.cliente_repo.buscar_por_id(cliente_id, empresa_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )
        return cliente
    
    async def buscar_por_cpf(self, cpf: str, empresa_id: int) -> Cliente:
        """Busca cliente por CPF (filtrado por empresa)."""
        cliente = await self.cliente_repo.buscar_por_cpf(cpf, empresa_id)
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado"
            )
        return cliente
    
    async def listar_clientes(
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
        return await self.cliente_repo.listar(empresa_id, skip, limit, nome, cpf, bloqueado, ativo)
    
    async def atualizar_cliente(
        self,
        cliente_id: UUID,
        empresa_id: int,
        data: ClienteUpdate
    ) -> Cliente:
        """Atualiza dados do cliente com transação atômica (filtrado por empresa)."""
        try:
            cliente = await self.cliente_repo.atualizar(cliente_id, empresa_id, data)
            if not cliente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado"
                )
            
            await self.db.commit()
            await self.db.refresh(cliente)
            log.info("cliente.atualizado", cliente_id=str(cliente_id), empresa_id=empresa_id)
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_atualizar_cliente", error=str(e))
            raise
    
    async def desativar_cliente(self, cliente_id: UUID, empresa_id: int) -> None:
        """
        Desativa um cliente (soft delete) com transação atômica (filtrado por empresa).
        
        Regras:
        - Não pode desativar se tiver pedidos em aberto
        - Não pode desativar se tiver contas pendentes
        """
        try:
            cliente = await self.buscar_cliente(cliente_id, empresa_id)

            # TODO: Verificar pedidos em aberto (integração com serviço de vendas)
            # TODO: Verificar contas pendentes (integração com serviço financeiro)

            sucesso = await self.cliente_repo.soft_delete(cliente_id, empresa_id)
            if not sucesso:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao desativar cliente"
                )

            await self.db.commit()
            log.info("cliente.desativado", cliente_id=str(cliente_id), empresa_id=empresa_id)
            
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
        empresa_id: int,
        data: CreditoUpdate
    ) -> Cliente:
        """
        Define limite de crédito e dia de vencimento com transação atômica (filtrado por empresa).
        
        Regras:
        - limite_credito >= 0
        - dia_vencimento entre 1 e 28
        - credito_disponivel = limite_credito - saldo_devedor
        """
        try:
            cliente = await self.buscar_cliente(cliente_id, empresa_id)

            cliente_atualizado = await self.cliente_repo.atualizar_credito(
                cliente_id,
                empresa_id,
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
                empresa_id=empresa_id,
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
        empresa_id: int,
        delta: Decimal,
        documento: str
    ) -> Cliente:
        """
        Ajusta crédito disponível via ledger, com transação atômica (filtrado por empresa).

        Args:
            cliente_id: ID do cliente
            empresa_id: ID da empresa
            delta: Valor a ajustar (positivo = crédito, negativo = débito)
            documento: numero_venda — chave de idempotência (repete a mesma
                chamada para o mesmo documento não debita/credita de novo)

        Regras:
        - credito_disponivel nunca pode ficar negativo (teto de crédito, C3)
        - idempotente por (empresa_id, documento, tipo) — retry e webhook
          duplicado não duplicam o efeito (C2)
        """
        tipo = TipoMovimentoCredito.CREDITO if delta >= 0 else TipoMovimentoCredito.DEBITO
        try:
            cliente = await self.buscar_cliente(cliente_id, empresa_id)

            try:
                cliente_atualizado = await self.cliente_repo.registrar_movimento_credito(
                    cliente_id,
                    empresa_id,
                    tipo,
                    delta,
                    documento
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
                empresa_id=empresa_id,
                delta=str(delta),
                documento=documento
            )

            return cliente_atualizado

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_ajustar_credito", error=str(e))
            raise
    
    async def bloquear_cliente(self, cliente_id: UUID, empresa_id: int) -> Cliente:
        """
        Bloqueia um cliente manualmente com transação atômica (filtrado por empresa).
        
        Regras:
        - Cliente bloqueado não pode fazer compras fiadas
        """
        try:
            cliente = await self.cliente_repo.bloquear(cliente_id, empresa_id)
            if not cliente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado"
                )

            await self.db.commit()
            log.warning("cliente.bloqueado_manual", cliente_id=str(cliente_id), empresa_id=empresa_id)
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_bloquear_cliente", error=str(e))
            raise
    
    async def desbloquear_cliente(self, cliente_id: UUID, empresa_id: int) -> Cliente:
        """Desbloqueia um cliente com transação atômica (filtrado por empresa)."""
        try:
            cliente = await self.cliente_repo.desbloquear(cliente_id, empresa_id)
            if not cliente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado"
                )

            await self.db.commit()
            log.info("cliente.desbloqueado", cliente_id=str(cliente_id), empresa_id=empresa_id)
            return cliente
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_desbloquear_cliente", error=str(e))
            raise

    async def reativar_cliente(self, cliente_id: UUID, empresa_id: int) -> Cliente:
        """Reativa um cliente desativado com transação atômica (filtrado por empresa)."""
        try:
            cliente = await self.cliente_repo.reativar(cliente_id, empresa_id)
            if not cliente:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado"
                )

            await self.db.commit()
            log.info("cliente.reativado", cliente_id=str(cliente_id), empresa_id=empresa_id)
            return cliente

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_reativar_cliente", error=str(e))
            raise

    # Métodos de Endereço
    
    async def adicionar_endereco(
        self,
        cliente_id: UUID,
        empresa_id: int,
        data: EnderecoCreate
    ) -> Endereco:
        """Adiciona um endereço ao cliente (filtrado por empresa)."""
        try:
            # Verificar se cliente existe e pertence à empresa
            await self.buscar_cliente(cliente_id, empresa_id)
            
            endereco = await self.endereco_repo.criar(cliente_id, data)
            await self.db.commit()
            await self.db.refresh(endereco)
            
            log.info("endereco.criado", cliente_id=str(cliente_id), endereco_id=str(endereco.id), empresa_id=empresa_id)
            return endereco
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_adicionar_endereco", error=str(e))
            raise
    
    async def listar_enderecos(self, cliente_id: UUID, empresa_id: int) -> list[Endereco]:
        """Lista endereços de um cliente (filtrado por empresa)."""
        # Verificar se cliente existe e pertence à empresa
        await self.buscar_cliente(cliente_id, empresa_id)
        
        return await self.endereco_repo.listar_por_cliente(cliente_id)
    
    async def atualizar_endereco(
        self,
        cliente_id: UUID,
        empresa_id: int,
        endereco_id: UUID,
        data: EnderecoUpdate
    ) -> Endereco:
        """Atualiza um endereço com transação atômica (filtrado por empresa)."""
        try:
            # Verificar se cliente existe e pertence à empresa
            await self.buscar_cliente(cliente_id, empresa_id)
            
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
            log.info("endereco.atualizado", endereco_id=str(endereco_id), empresa_id=empresa_id)
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
        empresa_id: int,
        endereco_id: UUID
    ) -> None:
        """Remove um endereço com transação atômica (filtrado por empresa)."""
        try:
            # Verificar se cliente existe e pertence à empresa
            await self.buscar_cliente(cliente_id, empresa_id)
            
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
            log.info("endereco.removido", endereco_id=str(endereco_id), empresa_id=empresa_id)
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            log.error("erro_remover_endereco", error=str(e))
            raise
