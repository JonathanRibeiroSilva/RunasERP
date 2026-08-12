"""
Configuração OAuth2 e dependências de autenticação.
"""
from typing import Annotated, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from database import get_db
from repositories.usuario_repository import UsuarioRepository
from repositories.cliente_auth_repository import ClienteAuthRepository
from auth.jwt import verify_token
from models.usuario import Usuario, RoleEnum
from models.cliente_auth import ClienteAuth
from auth.redis_client import get_redis


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_token_from_cookie_or_header(
    request: Request,
    token_from_header: Annotated[Optional[str], Depends(oauth2_scheme)]
) -> str:
    """
    Obtém o token do cookie HTTP-only ou do header Authorization.
    Prioriza o cookie para maior segurança.
    
    Args:
        request: Request object do FastAPI
        token_from_header: Token do header Authorization (opcional)
        
    Returns:
        Token JWT
        
    Raises:
        HTTPException: Se nenhum token for encontrado
    """
    # Tentar obter do cookie primeiro (mais seguro)
    token = request.cookies.get("access_token")
    
    # Se não tiver no cookie, tentar do header (para compatibilidade)
    if not token:
        token = token_from_header
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


async def get_current_user(
    request: Request,
    token_from_header: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
) -> Usuario:
    """
    Obtém o usuário atual a partir do token JWT (cookie ou header).

    Raises:
        HTTPException: Se o token for inválido ou usuário não encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("access_token") or token_from_header
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar se token está na blacklist
    is_blacklisted = await redis.get(f"blacklist:{token}")
    if is_blacklisted:
        raise credentials_exception
    
    # Decodificar token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Buscar usuário no banco
    repo = UsuarioRepository(db)
    usuario = await repo.buscar_por_id(UUID(user_id))
    
    if usuario is None or not usuario.ativo:
        raise credentials_exception
    
    return usuario


async def get_current_active_user(
    current_user: Annotated[Usuario, Depends(get_current_user)]
) -> Usuario:
    """
    Verifica se o usuário está ativo.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Usuário ativo
        
    Raises:
        HTTPException: Se o usuário estiver inativo
    """
    if not current_user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user


async def require_admin(
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
) -> Usuario:
    """
    Verifica se o usuário tem role ADMIN.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Usuário admin
        
    Raises:
        HTTPException: Se o usuário não for admin
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: apenas administradores"
        )
    return current_user


async def require_admin_or_operador(
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
) -> Usuario:
    """
    Verifica se o usuário tem role ADMIN ou OPERADOR.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Usuário autenticado
        
    Raises:
        HTTPException: Se o usuário não tiver permissão
    """
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.OPERADOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )
    return current_user


# ============================================================
# AUTENTICAÇÃO DE CLIENTES (LOJA ONLINE)
# ============================================================

async def get_current_cliente(
    token: Annotated[str, Depends(get_token_from_cookie_or_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
) -> ClienteAuth:
    """
    Obtém o cliente atual a partir do token JWT.
    
    Valida que o token é de um CLIENTE (não de usuário operador).
    
    Args:
        token: Token JWT
        db: Sessão do banco de dados
        redis: Cliente Redis
        
    Returns:
        ClienteAuth autenticado
        
    Raises:
        HTTPException: Se o token for inválido, não for de cliente, ou cliente não encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verificar se token está na blacklist
    is_blacklisted = await redis.get(f"blacklist:{token}")
    if is_blacklisted:
        raise credentials_exception
    
    # Decodificar token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    # Validar que é token de CLIENTE
    user_type = payload.get("user_type")
    if user_type != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token de cliente requerido"
        )
    
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Buscar cliente_auth no banco
    repo = ClienteAuthRepository(db)
    cliente_auth = await repo.buscar_por_id(UUID(user_id))
    
    if cliente_auth is None or not cliente_auth.ativo:
        raise credentials_exception
    
    return cliente_auth


async def get_current_active_cliente(
    current_cliente: Annotated[ClienteAuth, Depends(get_current_cliente)]
) -> ClienteAuth:
    """
    Verifica se o cliente está ativo.
    
    Args:
        current_cliente: Cliente atual
        
    Returns:
        Cliente ativo
        
    Raises:
        HTTPException: Se o cliente estiver inativo
    """
    if not current_cliente.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente inativo"
        )
    return current_cliente
