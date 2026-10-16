"""
Utilitários para geração e validação de tokens JWT.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID
import jwt
from jwt import PyJWTError
from config import settings
from models.usuario import RoleEnum


def create_access_token(
    user_id: UUID, 
    role: RoleEnum | str, 
    user_type: str = "usuario", 
    empresa_id: int | None = None,
    cliente_id: UUID | None = None
) -> str:
    """
    Cria um access token JWT.
    
    Args:
        user_id: ID do usuário ou cliente_auth
        role: Role do usuário (RoleEnum) ou "CLIENTE"
        user_type: Tipo de usuário ("usuario" ou "cliente")
        empresa_id: ID da empresa (opcional, usado para clientes)
        cliente_id: ID do cliente (opcional, usado para clientes OAuth)
        
    Returns:
        Token JWT codificado
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": str(user_id),
        "role": role.value if isinstance(role, RoleEnum) else role,
        "user_type": user_type,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    }
    
    # Adicionar empresa_id para clientes
    if empresa_id is not None:
        payload["empresa_id"] = empresa_id
    
    # Adicionar cliente_id para clientes (necessário para buscar dados)
    if cliente_id is not None:
        payload["cliente_id"] = str(cliente_id)
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    """
    Cria um refresh token JWT.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Refresh token JWT codificado
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT
        
    Returns:
        Payload do token
        
    Raises:
        PyJWTError: Se o token for inválido
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Verifica se um token é válido.
    
    Args:
        token: Token JWT
        
    Returns:
        Payload do token se válido, None caso contrário
    """
    try:
        return decode_token(token)
    except PyJWTError:
        return None
