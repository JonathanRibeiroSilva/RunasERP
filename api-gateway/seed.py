"""
Seed para criar o usuário administrador padrão.
Executado automaticamente no startup se não existir admin.
"""
import os
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import AsyncSessionLocal
from models.usuario import Usuario, RoleEnum
from repositories.usuario_repository import UsuarioRepository

log = structlog.get_logger()


async def seed_admin():
    """
    Cria o usuário administrador padrão se não existir.
    
    Usa as variáveis de ambiente:
    - ADMIN_EMAIL (default: admin@runas.com)
    - ADMIN_PASSWORD (default: Admin@123)
    - ADMIN_NAME (default: Administrador)
    """
    admin_email = os.getenv("ADMIN_EMAIL", "admin@runas.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123")[:72]  # Bcrypt limita a 72 bytes
    admin_name = os.getenv("ADMIN_NAME", "Administrador")
    
    async with AsyncSessionLocal() as db:
        try:
            # Verificar se já existe admin
            result = await db.execute(
                select(Usuario).where(Usuario.email == admin_email)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                log.info("seed.admin_exists", email=admin_email)
                return
            
            # Criar admin
            senha_hash = UsuarioRepository.hash_password(admin_password)
            admin = Usuario(
                nome=admin_name,
                email=admin_email,
                senha_hash=senha_hash,
                role=RoleEnum.ADMIN,
                ativo=True
            )
            db.add(admin)
            await db.commit()
            
            log.info(
                "seed.admin_created",
                email=admin_email,
                role="ADMIN"
            )
        except Exception as e:
            log.error("seed.admin_error", error=str(e))
            await db.rollback()
