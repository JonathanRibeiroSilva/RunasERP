"""
Router de autenticação.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import structlog
import secrets

from database import get_db
from repositories.usuario_repository import UsuarioRepository
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.oauth2 import get_current_user
from auth.redis_client import get_redis
from schemas.usuario import Token, RefreshTokenRequest, UsuarioResponse, LoginResponse, ForgotPasswordRequest, ResetPasswordRequest, AlterarSenhaRequest
from models.usuario import Usuario
from config import settings
from services.email_service import send_reset_password_email
from proxy.service_proxy import ServiceProxy
from middleware.rate_limit import limiter


router = APIRouter(prefix="/auth", tags=["Autenticação"])
log = structlog.get_logger()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """
    Define cookies HTTP-only para os tokens de autenticação.
    
    Args:
        response: Response object do FastAPI
        access_token: JWT access token
        refresh_token: JWT refresh token
    """
    # Detectar se está em HTTPS (ngrok, produção) ou HTTP (desenvolvimento local)
    is_https = settings.FRONTEND_URL.startswith("https://")
    
    # Access token - expira em 30 minutos
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_https,   # True em HTTPS (ngrok/produção), False em HTTP local
        samesite="lax",
        max_age=30 * 60,
        path="/"
    )
    
    # Refresh token - expira em 7 dias
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_https,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Remove os cookies de autenticação.
    
    Args:
        response: Response object do FastAPI
    """
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


async def _usuario_response_com_slug(usuario: Usuario) -> UsuarioResponse:
    """Serializa o usuário incluindo o slug da empresa (multi-tenancy).

    SUPER_ADMIN não tem tenant — empresa_id nulo, e nenhum slug a resolver.
    """
    empresa_slug = (
        None if usuario.empresa_id is None
        else await ServiceProxy.get_empresa_slug_from_id(usuario.empresa_id)
    )
    return UsuarioResponse.model_validate(usuario).model_copy(
        update={"empresa_slug": empresa_slug}
    )


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(
    current_user: Annotated[Usuario, Depends(get_current_user)]
):
    """
    Retorna informações do usuário logado.
    """
    return await _usuario_response_com_slug(current_user)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Login com OAuth2 password flow.
    
    Retorna access_token, refresh_token e dados do usuário.
    Os tokens também são definidos como HTTP-only cookies.
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
    
    # Definir cookies HTTP-only
    set_auth_cookies(response, access_token, refresh_token)
    
    log.info("login.success", user_id=str(usuario.id), role=usuario.role.value)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=await _usuario_response_com_slug(usuario)
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    response: Response,
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Renova access_token usando refresh_token.
    Também atualiza os cookies HTTP-only.
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
    
    # Atualizar cookies HTTP-only
    set_auth_cookies(response, access_token, request.refresh_token)
    
    log.info("token.refreshed", user_id=str(usuario.id))
    
    return Token(
        access_token=access_token,
        refresh_token=request.refresh_token
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Logout: invalida refresh_token e remove cookies.
    """
    # Remover refresh token do Redis
    await redis.delete(f"refresh:{current_user.id}")
    
    # Limpar cookies
    clear_auth_cookies(response)
    
    log.info("logout.success", user_id=str(current_user.id))
    
    return None


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Solicita reset de senha. Gera um token, salva no Redis e envia email.
    Sempre retorna sucesso para evitar enumeration attacks.
    """
    repo = UsuarioRepository(db)
    usuario = await repo.buscar_por_email(payload.email)

    if usuario and usuario.ativo:
        # Gerar token aleatório
        reset_token = secrets.token_urlsafe(32)

        # Salvar token no Redis (expira em 1 hora)
        await redis.setex(
            f"password_reset:{reset_token}",
            3600,
            str(usuario.id)
        )

        # Enviar email com link de reset
        await send_reset_password_email(
            to_email=usuario.email,
            reset_token=reset_token,
            nome=usuario.nome
        )

        log.info("forgot_password.email_sent",
                 user_id=str(usuario.id),
                 email=usuario.email)
    else:
        log.warning("forgot_password.user_not_found", email=payload.email)

    return {
        "message": "Se o email existir, você receberá instruções para resetar sua senha."
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Reseta a senha usando o token recebido por email.
    """
    user_id_str = await redis.get(f"password_reset:{payload.token}")

    if not user_id_str:
        log.warning("reset_password.invalid_token", token=payload.token[:10] + "...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )

    if isinstance(user_id_str, bytes):
        user_id_str = user_id_str.decode('utf-8')

    repo = UsuarioRepository(db)
    success = await repo.atualizar_senha(user_id_str, payload.nova_senha)

    if not success:
        log.error("reset_password.user_not_found", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao resetar senha"
        )

    # Token de uso único — remover do Redis
    await redis.delete(f"password_reset:{payload.token}")

    # Invalidar refresh tokens (forçar novo login)
    await redis.delete(f"refresh:{user_id_str}")

    log.info("reset_password.success", user_id=user_id_str)

    return {
        "message": "Senha resetada com sucesso. Faça login com sua nova senha."
    }


@router.post("/alterar-senha", status_code=status.HTTP_200_OK)
async def alterar_senha(
    request: AlterarSenhaRequest,
    current_user: Annotated[Usuario, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """Altera a senha do usuário autenticado, exigindo a senha atual."""
    repo = UsuarioRepository(db)

    if not current_user.senha_hash or not repo.verify_password(request.senha_atual, current_user.senha_hash):
        log.warning("alterar_senha.senha_atual_incorreta", user_id=str(current_user.id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )

    await repo.atualizar_senha(current_user.id, request.nova_senha)

    # Invalidar refresh tokens (forçar novo login nas outras sessões)
    await redis.delete(f"refresh:{current_user.id}")

    log.info("alterar_senha.success", user_id=str(current_user.id))
    return {"message": "Senha alterada com sucesso"}
