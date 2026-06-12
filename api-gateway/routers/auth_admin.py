"""
Router de autenticação ADMIN - para criar usuários operadores.
Requer permissão de ADMIN.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from database import get_db
from repositories.usuario_repository import UsuarioRepository
from auth.oauth2 import get_current_user
from schemas.usuario import UsuarioCreate, UsuarioResponse
from models.usuario import Usuario, RoleEnum


router = APIRouter(prefix="/auth/admin", tags=["Autenticação Admin"])
log = structlog.get_logger()


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependency para verificar se o usuário é ADMIN.
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas ADMIN pode criar usuários."
        )
    return current_user


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario_operador(
    data: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Usuario, Depends(require_admin)]
):
    """
    Cria um novo usuário operador (ADMIN ou OPERADOR).
    
    Apenas usuários ADMIN podem criar novos operadores.
    O novo usuário será vinculado à mesma empresa do ADMIN.
    """
    repo = UsuarioRepository(db)
    
    # Verificar se email já existe
    existing = await repo.buscar_por_email(data.email)
    if existing:
        log.warning("admin.criar_usuario.email_exists", 
                   email=data.email, 
                   admin_id=str(admin.id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Forçar empresa_id do admin (não confiar no body)
    data.empresa_id = admin.empresa_id
    
    # Criar usuário
    usuario = await repo.criar(data)
    
    log.info("admin.criar_usuario.success", 
             user_id=str(usuario.id), 
             email=usuario.email, 
             role=usuario.role.value,
             empresa_id=usuario.empresa_id,
             created_by=str(admin.id))
    
    return usuario
