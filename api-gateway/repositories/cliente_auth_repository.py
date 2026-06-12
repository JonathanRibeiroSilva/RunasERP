"""
Repository para ClienteAuth (autenticação de clientes compradores).
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from models.cliente_auth import ClienteAuth


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ClienteAuthRepository:
    """Repository para gerenciar autenticação de clientes."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def buscar_por_email(self, email: str) -> ClienteAuth | None:
        """
        Busca um cliente de autenticação por email.
        
        Args:
            email: Email do cliente
            
        Returns:
            ClienteAuth ou None se não encontrado
        """
        result = await self.db.execute(
            select(ClienteAuth).where(ClienteAuth.email == email)
        )
        return result.scalar_one_or_none()
    
    async def buscar_por_id(self, cliente_auth_id: UUID) -> ClienteAuth | None:
        """
        Busca um cliente de autenticação por ID.
        
        Args:
            cliente_auth_id: ID do registro de autenticação
            
        Returns:
            ClienteAuth ou None se não encontrado
        """
        result = await self.db.execute(
            select(ClienteAuth).where(ClienteAuth.id == cliente_auth_id)
        )
        return result.scalar_one_or_none()
    
    async def criar(
        self,
        email: str,
        senha: str,
        cliente_id: UUID,
        empresa_id: int
    ) -> ClienteAuth:
        """
        Cria um novo registro de autenticação de cliente.
        
        Args:
            email: Email do cliente
            senha: Senha em texto plano (vazio para OAuth)
            cliente_id: ID do cliente no serviço clientes
            empresa_id: ID da loja
            
        Returns:
            ClienteAuth criado
        """
        # Hash da senha (se fornecida)
        senha_hash = pwd_context.hash(senha) if senha else ""
        
        cliente_auth = ClienteAuth(
            email=email,
            senha_hash=senha_hash,
            cliente_id=cliente_id,
            empresa_id=empresa_id
        )
        
        self.db.add(cliente_auth)
        await self.db.commit()
        await self.db.refresh(cliente_auth)
        
        return cliente_auth
    
    def verificar_senha(self, senha_plana: str, senha_hash: str) -> bool:
        """
        Verifica se a senha corresponde ao hash.
        
        Args:
            senha_plana: Senha em texto plano
            senha_hash: Hash da senha armazenada
            
        Returns:
            True se a senha corresponde, False caso contrário
        """
        return pwd_context.verify(senha_plana, senha_hash)
