"""
Router de autenticação.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import structlog

from database import get_db
from repositories.usuario_repository import UsuarioRepository
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.oauth2 import get_current_user
from auth.redis_client import get_redis
from schemas.usuario import Token, RefreshTokenRequest, UsuarioCreate, UsuarioResponse
from models.usuario import Usuario
from config import settings


router = APIRouter(prefix="/auth", tags=["Autenticação"])
log = structlog.get_logger()


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Registra um novo usuário.
    
    Por padrão, cria usuários com role OPERADOR.
    Para criar ADMIN, use role: "ADMIN" no body.
    """
    repo = UsuarioRepository(db)
    
    # Verificar se email já existe
    existing = await repo.buscar_por_email(data.email)
    if existing:
        log.warning("register.email_exists", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Criar usuário
    usuario = await repo.criar(data)
    
    log.info("register.success", user_id=str(usuario.id), email=usuario.email, role=usuario.role.value)
    
    return usuario


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Retorna informações do usuário logado.
    """
    return current_user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Login com OAuth2 password flow.
    
    Retorna access_token e refresh_token.
    """
    repo = UsuarioRepository(db)
    
    # Buscar usuário
    usuario = await repo.buscar_por_email(form_data.username)
    
    if not usuario or not repo.verify_password(form_data.password, usuario.senha_hash):
        log.warning("login.failed", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not usuario.ativo:
        log.warning("login.inactive_user", user_id=str(usuario.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    # Gerar tokens
    access_token = create_access_token(usuario.id, usuario.role)
    refresh_token = create_refresh_token(usuario.id)
    
    # Salvar refresh token no Redis
    await redis.setex(
        f"refresh:{usuario.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    log.info("login.success", user_id=str(usuario.id), role=usuario.role.value)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Renova access_token usando refresh_token.
    """
    # Verificar refresh token
    payload = verify_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )
    
    user_id = payload.get("sub")
    
    # Verificar se refresh token está salvo no Redis
    stored_token = await redis.get(f"refresh:{user_id}")
    if stored_token != request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )
    
    # Buscar usuário
    repo = UsuarioRepository(db)
    usuario = await repo.buscar_por_id(user_id)
    
    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )
    
    # Gerar novo access token
    access_token = create_access_token(usuario.id, usuario.role)
    
    log.info("token.refreshed", user_id=str(usuario.id))
    
    return Token(
        access_token=access_token,
        refresh_token=request.refresh_token
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: Annotated[Usuario, Depends(get_current_user)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Logout: invalida refresh_token.
    """
    # Remover refresh token do Redis
    await redis.delete(f"refresh:{current_user.id}")
    
    log.info("logout.success", user_id=str(current_user.id))
    
    return None
