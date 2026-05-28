"""
Router de autenticação.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import structlog
import httpx
import secrets
from pydantic import BaseModel

from database import get_db
from repositories.usuario_repository import UsuarioRepository
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.oauth2 import get_current_user
from auth.redis_client import get_redis
from schemas.usuario import Token, RefreshTokenRequest, UsuarioCreate, UsuarioResponse, LoginResponse, ForgotPasswordRequest, ResetPasswordRequest
from models.usuario import Usuario, RoleEnum
from config import settings
from services.email_service import send_reset_password_email


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
    # Em produção com ngrok, sempre usar secure=True
    secure = True  # Sempre True para ngrok/produção
    
    # Access token - expira em 30 minutos
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,  # Não acessível via JavaScript
        secure=secure,  # True em produção/ngrok (HTTPS only)
        samesite="lax",  # Proteção CSRF
        max_age=30 * 60,  # 30 minutos em segundos
        path="/"
    )
    
    # Refresh token - expira em 7 dias
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 dias em segundos
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


class OAuthInitRequest(BaseModel):
    """Request para iniciar OAuth flow."""
    redirect_uri: str


class OAuthCallbackRequest(BaseModel):
    """Request para callback OAuth."""
    code: str
    state: str


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


@router.post("/login", response_model=LoginResponse)
async def login(
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
        user=usuario
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
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Solicita reset de senha. Gera um token, salva no Redis e envia email.
    Sempre retorna sucesso para evitar enumeration attacks.
    """
    repo = UsuarioRepository(db)
    usuario = await repo.buscar_por_email(request.email)

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
        log.warning("forgot_password.user_not_found", email=request.email)

    return {
        "message": "Se o email existir, você receberá instruções para resetar sua senha."
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Reseta a senha usando o token recebido por email.
    """
    user_id_str = await redis.get(f"password_reset:{request.token}")

    if not user_id_str:
        log.warning("reset_password.invalid_token", token=request.token[:10] + "...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )

    if isinstance(user_id_str, bytes):
        user_id_str = user_id_str.decode('utf-8')

    repo = UsuarioRepository(db)
    success = await repo.atualizar_senha(user_id_str, request.nova_senha)

    if not success:
        log.error("reset_password.user_not_found", user_id=user_id_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao resetar senha"
        )

    # Token de uso único — remover do Redis
    await redis.delete(f"password_reset:{request.token}")

    # Invalidar refresh tokens (forçar novo login)
    await redis.delete(f"refresh:{user_id_str}")

    log.info("reset_password.success", user_id=user_id_str)

    return {
        "message": "Senha resetada com sucesso. Faça login com sua nova senha."
    }
    
    # Invalidar todos os refresh tokens do usuário (forçar novo login)
    await redis.delete(f"refresh:{user_id_str}")
    
    log.info("reset_password.success", user_id=user_id_str)
    
    return {
        "message": "Senha resetada com sucesso. Faça login com sua nova senha."
    }


# ==================== OAUTH ROUTES ====================

@router.post("/oauth/google")
async def oauth_google_init(
    request: OAuthInitRequest,
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Inicia o fluxo OAuth com Google.
    Retorna a URL de autorização.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth Google não configurado"
        )
    
    # Gerar state aleatório para CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Salvar state no Redis (expira em 10 minutos)
    await redis.setex(f"oauth:state:{state}", 600, request.redirect_uri)
    
    # Construir URL de autorização do Google
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={request.redirect_uri}"
        "&response_type=code"
        "&scope=openid email profile"
        f"&state={state}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    log.info("oauth.google.init", state=state)
    
    return {"auth_url": auth_url, "state": state}


@router.post("/oauth/google/callback")
async def oauth_google_callback(
    response: Response,
    callback: OAuthCallbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Processa o callback do Google OAuth.
    Retorna tokens de acesso e define cookies HTTP-only.
    """
    log.info("oauth.google.callback.start", code=callback.code[:20] + "...", state=callback.state)
    
    # Verificar state (CSRF protection)
    redirect_uri = await redis.get(f"oauth:state:{callback.state}")
    
    log.info("oauth.google.callback.state_check", 
             state=callback.state, 
             redirect_uri=redirect_uri,
             found=redirect_uri is not None)
    
    if not redirect_uri:
        log.error("oauth.google.callback.invalid_state", state=callback.state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido ou expirado"
        )
    
    # Converter bytes para string se necessário
    if isinstance(redirect_uri, bytes):
        redirect_uri = redirect_uri.decode('utf-8')
    
    log.info("oauth.google.callback.state_valid", redirect_uri=redirect_uri)
    
    # Remover state do Redis
    await redis.delete(f"oauth:state:{callback.state}")
    
    # Trocar code por access token
    async with httpx.AsyncClient() as client:
        log.info("oauth.google.callback.exchanging_code")
        
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": callback.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            log.error("oauth.google.token_error", 
                     status=token_response.status_code,
                     response=token_response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao obter token do Google"
            )
        
        token_data = token_response.json()
        google_access_token = token_data.get("access_token")
        
        log.info("oauth.google.callback.token_received")
        
        # Obter informações do usuário
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"}
        )
        
        if user_response.status_code != 200:
            log.error("oauth.google.userinfo_error", 
                     status=user_response.status_code,
                     response=user_response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao obter informações do usuário"
            )
        
        user_data = user_response.json()
        log.info("oauth.google.callback.user_data", user_data=user_data)
    
    # Buscar ou criar usuário
    repo = UsuarioRepository(db)
    email = user_data.get("email")
    nome = user_data.get("name", email.split("@")[0])
    
    log.info("oauth.google.callback.processing_user", email=email, nome=nome)
    
    usuario = await repo.buscar_por_email(email)
    
    if not usuario:
        # Criar novo usuário
        log.info("oauth.google.callback.creating_user", email=email)
        usuario_create = UsuarioCreate(
            email=email,
            nome=nome,
            senha="",  # OAuth users não têm senha
            role=RoleEnum.OPERADOR
        )
        usuario = await repo.criar(usuario_create)
        log.info("oauth.google.user_created", user_id=str(usuario.id), email=email)
    else:
        log.info("oauth.google.user_login", user_id=str(usuario.id), email=email)
    
    # Gerar tokens
    access_token = create_access_token(usuario.id, usuario.role)
    refresh_token = create_refresh_token(usuario.id)
    
    log.info("oauth.google.callback.tokens_generated")
    
    # Salvar refresh token no Redis
    await redis.setex(
        f"refresh:{usuario.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    # Definir cookies HTTP-only
    set_auth_cookies(response, access_token, refresh_token)
    
    response_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(usuario.id),
            "email": usuario.email,
            "nome": usuario.nome,
            "role": usuario.role.value
        }
    }
    
    log.info("oauth.google.callback.success", 
             user_id=str(usuario.id), 
             email=usuario.email,
             response_keys=list(response_data.keys()))
    
    return response_data


@router.post("/oauth/microsoft")
async def oauth_microsoft_init(
    request: OAuthInitRequest,
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Inicia o fluxo OAuth com Microsoft.
    Retorna a URL de autorização.
    """
    if not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth Microsoft não configurado"
        )
    
    # Gerar state aleatório para CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Salvar state no Redis (expira em 10 minutos)
    await redis.setex(f"oauth:state:{state}", 600, request.redirect_uri)
    
    tenant = settings.MICROSOFT_TENANT_ID or "common"
    
    # Construir URL de autorização da Microsoft
    # Scope User.Read é necessário para acessar o Microsoft Graph API
    auth_url = (
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        f"?client_id={settings.MICROSOFT_CLIENT_ID}"
        f"&redirect_uri={request.redirect_uri}"
        "&response_type=code"
        "&scope=openid email profile User.Read"
        f"&state={state}"
        "&response_mode=query"
    )
    
    log.info("oauth.microsoft.init", state=state)
    
    return {"auth_url": auth_url, "state": state}


@router.post("/oauth/microsoft/callback")
async def oauth_microsoft_callback(
    response: Response,
    callback: OAuthCallbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Processa o callback do Microsoft OAuth.
    Retorna tokens de acesso e define cookies HTTP-only.
    """
    # Verificar state (CSRF protection)
    redirect_uri = await redis.get(f"oauth:state:{callback.state}")
    if not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido ou expirado"
        )
    
    # Converter bytes para string se necessário
    if isinstance(redirect_uri, bytes):
        redirect_uri = redirect_uri.decode('utf-8')
    
    # Remover state do Redis
    await redis.delete(f"oauth:state:{callback.state}")
    
    tenant = settings.MICROSOFT_TENANT_ID or "common"
    
    # Trocar code por access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "code": callback.code,
                "client_id": settings.MICROSOFT_CLIENT_ID,
                "client_secret": settings.MICROSOFT_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "scope": "openid email profile User.Read"
            }
        )
        
        if token_response.status_code != 200:
            log.error("oauth.microsoft.token_error", response=token_response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao obter token da Microsoft"
            )
        
        token_data = token_response.json()
        ms_access_token = token_data.get("access_token")
        
        # Obter informações do usuário
        user_response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {ms_access_token}"}
        )
        
        if user_response.status_code != 200:
            log.error("oauth.microsoft.userinfo_error", response=user_response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao obter informações do usuário"
            )
        
        user_data = user_response.json()
    
    # Buscar ou criar usuário
    repo = UsuarioRepository(db)
    email = user_data.get("mail") or user_data.get("userPrincipalName")
    nome = user_data.get("displayName", email.split("@")[0])
    
    usuario = await repo.buscar_por_email(email)
    
    if not usuario:
        # Criar novo usuário
        usuario_create = UsuarioCreate(
            email=email,
            nome=nome,
            senha="",  # OAuth users não têm senha
            role=RoleEnum.OPERADOR
        )
        usuario = await repo.criar(usuario_create)
        log.info("oauth.microsoft.user_created", user_id=str(usuario.id), email=email)
    else:
        log.info("oauth.microsoft.user_login", user_id=str(usuario.id), email=email)
    
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
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(usuario.id),
            "email": usuario.email,
            "nome": usuario.nome,
            "role": usuario.role.value
        }
    }

