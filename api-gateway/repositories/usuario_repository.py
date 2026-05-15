"""
Repository para operações de usuário no banco de dados.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.usuario import Usuario
from schemas.usuario import UsuarioCreate, UsuarioUpdate
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UsuarioRepository:
    """Repository de usuário."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash de senha usando bcrypt."""
        # Bcrypt limita senhas a 72 bytes
        return pwd_context.hash(password[:72])
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha corresponde ao hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    async def criar(self, data: UsuarioCreate) -> Usuario:
        """Cria um novo usuário."""
        usuario = Usuario(
            nome=data.nome,
            email=data.email,
            senha_hash=self.hash_password(data.senha),
            role=data.role
        )
        self.db.add(usuario)
        await self.db.commit()
        await self.db.refresh(usuario)
        return usuario
    
    async def buscar_por_id(self, user_id: UUID) -> Usuario | None:
        """Busca usuário por ID."""
        result = await self.db.execute(
            select(Usuario).where(Usuario.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def buscar_por_email(self, email: str) -> Usuario | None:
        """Busca usuário por email."""
        result = await self.db.execute(
            select(Usuario).where(Usuario.email == email)
        )
        return result.scalar_one_or_none()
    
    async def listar(self, skip: int = 0, limit: int = 100) -> tuple[list[Usuario], int]:
        """Lista usuários com paginação."""
        # Total
        count_result = await self.db.execute(select(Usuario))
        total = len(count_result.all())
        
        # Itens
        result = await self.db.execute(
            select(Usuario).offset(skip).limit(limit)
        )
        usuarios = list(result.scalars().all())
        
        return usuarios, total
    
    async def atualizar(self, user_id: UUID, data: UsuarioUpdate) -> Usuario | None:
        """Atualiza um usuário."""
        usuario = await self.buscar_por_id(user_id)
        if not usuario:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(usuario, field, value)
        
        await self.db.commit()
        await self.db.refresh(usuario)
        return usuario
    
    async def deletar(self, user_id: UUID) -> bool:
        """Deleta um usuário (soft delete)."""
        usuario = await self.buscar_por_id(user_id)
        if not usuario:
            return False
        
        usuario.ativo = False
        await self.db.commit()
        return True
