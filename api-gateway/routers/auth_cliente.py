"""
Router de autenticação para clientes compradores (loja online).
Separado de auth.py que é para usuários operadores do sistema.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
import structlog
import httpx
import secrets
from pydantic import BaseModel

from database import get_db
from repositories.cliente_auth_repository import ClienteAuthRepository
from auth.jwt import create_access_token, create_refresh_token, verify_token
from auth.redis_client import get_redis
from schemas.cliente import ClienteRegisterRequest, ClienteLoginResponse
from config import settings


router = APIRouter(prefix="/auth/cliente", tags=["Autenticação Cliente"])
log = structlog.get_logger()


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Define cookies HTTP-only para os tokens."""
    is_https = settings.FRONTEND_URL.startswith("https://")
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_https,
        samesite="lax",
        max_age=30 * 60,
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_https,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )


class OAuthInitRequest(BaseModel):
    """Request para iniciar OAuth flow para clientes."""
    redirect_uri: str
    empresa_id: int  # ID da loja onde está se cadastrando


class OAuthCallbackRequest(BaseModel):
    """Request para callback OAuth."""
    code: str
    state: str


@router.post("/register", response_model=ClienteLoginResponse, status_code=status.HTTP_201_CREATED)
async def register_cliente(
    response: Response,
    data: ClienteRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Registra um novo cliente comprador.
    
    1. Cria o cliente no serviço de clientes
    2. Cria registro de autenticação no gateway
    3. Retorna tokens JWT
    """
    repo = ClienteAuthRepository(db)
    
    # Verificar se email já existe
    existing = await repo.buscar_por_email(data.email)
    if existing:
        log.warning("cliente.register.email_exists", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Criar cliente no serviço de clientes
    async with httpx.AsyncClient() as client:
        try:
            cliente_response = await client.post(
                f"{settings.CLIENTES_URL}/clientes",
                json={
                    "cpf": data.cpf,
                    "nome": data.nome,
                    "telefone": data.telefone,
                    "email": data.email
                },
                headers={"X-Empresa-Id": str(data.empresa_id)},
                timeout=10.0
            )
            
            if cliente_response.status_code != 201:
                log.error("cliente.register.service_error", 
                         status=cliente_response.status_code,
                         response=cliente_response.text)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao criar cliente"
                )
            
            cliente_data = cliente_response.json()
            cliente_id = UUID(cliente_data["id"])
            
            log.info("cliente.register.cliente_created", cliente_id=str(cliente_id))
            
        except httpx.RequestError as e:
            log.error("cliente.register.request_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao comunicar com serviço de clientes"
            )
    
    # Criar registro de autenticação
    cliente_auth = await repo.criar(
        email=data.email,
        senha=data.senha,
        cliente_id=cliente_id,
        empresa_id=data.empresa_id
    )
    
    log.info("cliente.register.auth_created", 
             cliente_auth_id=str(cliente_auth.id),
             cliente_id=str(cliente_id),
             empresa_id=data.empresa_id)
    
    # Gerar tokens
    access_token = create_access_token(
        user_id=cliente_auth.id,
        role="CLIENTE",
        user_type="cliente",
        empresa_id=data.empresa_id,
        cliente_id=cliente_id
    )
    refresh_token = create_refresh_token(cliente_auth.id)
    
    # Salvar refresh token no Redis
    await redis.setex(
        f"refresh:cliente:{cliente_auth.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    # Definir cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    log.info("cliente.register.success", cliente_id=str(cliente_id))
    
    return ClienteLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_type="cliente",
        cliente=cliente_data
    )


@router.post("/login", response_model=ClienteLoginResponse)
async def login_cliente(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Login de cliente comprador.
    """
    repo = ClienteAuthRepository(db)
    
    # Buscar cliente
    cliente_auth = await repo.buscar_por_email(form_data.username)
    
    if not cliente_auth or not repo.verificar_senha(form_data.password, cliente_auth.senha_hash):
        log.warning("cliente.login.failed", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not cliente_auth.ativo:
        log.warning("cliente.login.inactive", cliente_auth_id=str(cliente_auth.id))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cliente inativo"
        )
    
    # Buscar dados do cliente no serviço de clientes
    async with httpx.AsyncClient() as client:
        try:
            cliente_response = await client.get(
                f"{settings.CLIENTES_URL}/clientes/{cliente_auth.cliente_id}",
                headers={"X-Empresa-Id": str(cliente_auth.empresa_id)},
                timeout=10.0
            )
            
            if cliente_response.status_code != 200:
                log.error("cliente.login.fetch_error", status=cliente_response.status_code)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao buscar dados do cliente"
                )
            
            cliente_data = cliente_response.json()
            
        except httpx.RequestError as e:
            log.error("cliente.login.request_error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao comunicar com serviço de clientes"
            )
    
    # Gerar tokens
    access_token = create_access_token(
        user_id=cliente_auth.id,
        role="CLIENTE",
        user_type="cliente",
        empresa_id=cliente_auth.empresa_id,
        cliente_id=cliente_auth.cliente_id
    )
    refresh_token = create_refresh_token(cliente_auth.id)
    
    # Salvar refresh token no Redis
    await redis.setex(
        f"refresh:cliente:{cliente_auth.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    # Definir cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    log.info("cliente.login.success", cliente_id=str(cliente_auth.cliente_id))
    
    return ClienteLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_type="cliente",
        cliente=cliente_data
    )


@router.post("/oauth/google/init")
async def oauth_google_init_cliente(
    request: OAuthInitRequest,
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Inicia o fluxo OAuth do Google para clientes.
    """
    state = secrets.token_urlsafe(32)
    
    # Salvar state + redirect_uri + empresa_id no Redis (expira em 10 minutos)
    await redis.setex(
        f"oauth:cliente:state:{state}",
        600,
        f"{request.redirect_uri}|{request.empresa_id}"
    )
    
    log.info("oauth.cliente.google.init", state=state, empresa_id=request.empresa_id)
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={request.redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
        f"&state={state}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    
    return {"auth_url": auth_url, "state": state}


@router.post("/oauth/google/callback", response_model=ClienteLoginResponse)
async def oauth_google_callback_cliente(
    response: Response,
    callback: OAuthCallbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Processa o callback do Google OAuth para clientes.
    """
    log.info("oauth.cliente.google.callback", state=callback.state)
    
    # Verificar state
    state_data = await redis.get(f"oauth:cliente:state:{callback.state}")
    
    if not state_data:
        log.error("oauth.cliente.google.invalid_state", state=callback.state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido ou expirado"
        )
    
    # Converter bytes para string e extrair redirect_uri e empresa_id
    if isinstance(state_data, bytes):
        state_data = state_data.decode('utf-8')
    
    redirect_uri, empresa_id_str = state_data.split("|")
    empresa_id = int(empresa_id_str)
    
    log.info("oauth.cliente.google.state_valid", redirect_uri=redirect_uri, empresa_id=empresa_id)
    
    # Remover state do Redis
    await redis.delete(f"oauth:cliente:state:{callback.state}")
    
    # Trocar code por access token
    async with httpx.AsyncClient() as client:
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
            log.error("oauth.cliente.google.token_error", status=token_response.status_code)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao obter token do Google"
            )
        
        token_data = token_response.json()
        google_access_token = token_data.get("access_token")
        
        # Obter informações do usuário
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"}
        )
        
        if user_response.status_code != 200:
            log.error("oauth.cliente.google.userinfo_error", status=user_response.status_code)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao obter informações do usuário"
            )
        
        user_data = user_response.json()
    
    # Buscar ou criar cliente
    repo = ClienteAuthRepository(db)
    email = user_data.get("email")
    nome = user_data.get("name", email.split("@")[0])
    
    cliente_auth = await repo.buscar_por_email(email)
    
    if not cliente_auth:
        # Criar cliente no serviço de clientes
        async with httpx.AsyncClient() as client:
            try:
                # Tentar buscar cliente existente por email primeiro
                busca_response = await client.get(
                    f"{settings.CLIENTES_URL}/clientes",
                    params={"email": email},
                    headers={"X-Empresa-Id": str(empresa_id)},
                    timeout=10.0
                )
                
                if busca_response.status_code == 200:
                    clientes = busca_response.json().get("itens", [])
                    if clientes:
                        # Cliente já existe
                        cliente_data = clientes[0]
                        cliente_id = UUID(cliente_data["id"])
                        log.info("oauth.cliente.google.existing", cliente_id=str(cliente_id))
                    else:
                        # Criar novo cliente
                        cliente_response = await client.post(
                            f"{settings.CLIENTES_URL}/clientes",
                            json={
                                "cpf": None,  # Opcional para OAuth
                                "nome": nome,
                                "telefone": None,  # Opcional para OAuth
                                "email": email
                            },
                            headers={"X-Empresa-Id": str(empresa_id)},
                            timeout=10.0
                        )
                        
                        if cliente_response.status_code == 201:
                            cliente_data = cliente_response.json()
                            cliente_id = UUID(cliente_data["id"])
                            log.info("oauth.cliente.google.created", cliente_id=str(cliente_id))
                        else:
                            log.error("oauth.cliente.google.create_error", status=cliente_response.status_code, response=cliente_response.text)
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Erro ao criar cliente"
                            )
                else:
                    log.error("oauth.cliente.google.search_error", status=busca_response.status_code)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao buscar cliente"
                    )
                
            except httpx.RequestError as e:
                log.error("oauth.cliente.google.request_error", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao comunicar com serviço de clientes"
                )
        
        # Criar autenticação
        cliente_auth = await repo.criar(
            email=email,
            senha="",  # OAuth não usa senha
            cliente_id=cliente_id,
            empresa_id=empresa_id
        )
        
        log.info("oauth.cliente.google.created", cliente_id=str(cliente_id))
    else:
        # Buscar dados do cliente
        async with httpx.AsyncClient() as client:
            try:
                cliente_response = await client.get(
                    f"{settings.CLIENTES_URL}/clientes/{cliente_auth.cliente_id}",
                    headers={"X-Empresa-Id": str(empresa_id)},
                    timeout=10.0
                )
                
                if cliente_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao buscar cliente"
                    )
                
                cliente_data = cliente_response.json()
                
            except httpx.RequestError as e:
                log.error("oauth.cliente.google.fetch_error", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao comunicar com serviço de clientes"
                )
        
        log.info("oauth.cliente.google.login", cliente_id=str(cliente_auth.cliente_id))
    
    # Gerar tokens
    access_token = create_access_token(
        user_id=cliente_auth.id,
        role="CLIENTE",
        user_type="cliente",
        empresa_id=empresa_id,
        cliente_id=cliente_auth.cliente_id
    )
    refresh_token = create_refresh_token(cliente_auth.id)
    
    # Salvar refresh token
    await redis.setex(
        f"refresh:cliente:{cliente_auth.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    # Definir cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    return ClienteLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_type="cliente",
        cliente=cliente_data
    )


@router.post("/oauth/microsoft/init")
async def oauth_microsoft_init_cliente(
    request: OAuthInitRequest,
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Inicia o fluxo OAuth da Microsoft para clientes.
    """
    state = secrets.token_urlsafe(32)
    
    # Salvar state + redirect_uri + empresa_id no Redis
    await redis.setex(
        f"oauth:cliente:state:{state}",
        600,
        f"{request.redirect_uri}|{request.empresa_id}"
    )
    
    log.info("oauth.cliente.microsoft.init", state=state, empresa_id=request.empresa_id)
    
    tenant = settings.MICROSOFT_TENANT_ID or "common"
    
    auth_url = (
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        f"?client_id={settings.MICROSOFT_CLIENT_ID}"
        f"&redirect_uri={request.redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile User.Read"
        f"&state={state}"
        f"&prompt=consent"
    )
    
    return {"auth_url": auth_url, "state": state}


@router.post("/oauth/microsoft/callback", response_model=ClienteLoginResponse)
async def oauth_microsoft_callback_cliente(
    response: Response,
    callback: OAuthCallbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)]
):
    """
    Processa o callback do Microsoft OAuth para clientes.
    """
    log.info("oauth.cliente.microsoft.callback", state=callback.state)
    
    # Verificar state
    state_data = await redis.get(f"oauth:cliente:state:{callback.state}")
    
    if not state_data:
        log.error("oauth.cliente.microsoft.invalid_state", state=callback.state)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State inválido ou expirado"
        )
    
    # Extrair redirect_uri e empresa_id
    if isinstance(state_data, bytes):
        state_data = state_data.decode('utf-8')
    
    redirect_uri, empresa_id_str = state_data.split("|")
    empresa_id = int(empresa_id_str)
    
    # Remover state
    await redis.delete(f"oauth:cliente:state:{callback.state}")
    
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
            log.error("oauth.cliente.microsoft.token_error", status=token_response.status_code)
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
            log.error("oauth.cliente.microsoft.userinfo_error", status=user_response.status_code)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao obter informações do usuário"
            )
        
        user_data = user_response.json()
    
    # Buscar ou criar cliente
    repo = ClienteAuthRepository(db)
    email = user_data.get("mail") or user_data.get("userPrincipalName")
    nome = user_data.get("displayName", email.split("@")[0])
    
    cliente_auth = await repo.buscar_por_email(email)
    
    if not cliente_auth:
        # Criar cliente no serviço
        async with httpx.AsyncClient() as client:
            try:
                cliente_response = await client.post(
                    f"{settings.CLIENTES_URL}/clientes",
                    json={
                        "cpf": "00000000000",
                        "nome": nome,
                        "telefone": "0000000000",
                        "email": email
                    },
                    headers={"X-Empresa-Id": str(empresa_id)},
                    timeout=10.0
                )
                
                if cliente_response.status_code != 201:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao criar cliente"
                    )
                
                cliente_data = cliente_response.json()
                cliente_id = UUID(cliente_data["id"])
                
            except httpx.RequestError as e:
                log.error("oauth.cliente.microsoft.request_error", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao comunicar com serviço de clientes"
                )
        
        # Criar autenticação
        cliente_auth = await repo.criar(
            email=email,
            senha="",
            cliente_id=cliente_id,
            empresa_id=empresa_id
        )
        
        log.info("oauth.cliente.microsoft.created", cliente_id=str(cliente_id))
    else:
        # Buscar dados
        async with httpx.AsyncClient() as client:
            try:
                cliente_response = await client.get(
                    f"{settings.CLIENTES_URL}/clientes/{cliente_auth.cliente_id}",
                    headers={"X-Empresa-Id": str(empresa_id)},
                    timeout=10.0
                )
                
                if cliente_response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Erro ao buscar cliente"
                    )
                
                cliente_data = cliente_response.json()
                
            except httpx.RequestError as e:
                log.error("oauth.cliente.microsoft.fetch_error", error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao comunicar com serviço de clientes"
                )
        
        log.info("oauth.cliente.microsoft.login", cliente_id=str(cliente_auth.cliente_id))
    
    # Gerar tokens
    access_token = create_access_token(
        user_id=cliente_auth.id,
        role="CLIENTE",
        user_type="cliente",
        empresa_id=empresa_id,
        cliente_id=cliente_auth.cliente_id
    )
    refresh_token = create_refresh_token(cliente_auth.id)
    
    # Salvar refresh token
    await redis.setex(
        f"refresh:cliente:{cliente_auth.id}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token
    )
    
    # Definir cookies
    set_auth_cookies(response, access_token, refresh_token)
    
    return ClienteLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_type="cliente",
        cliente=cliente_data
    )



class InternalRegisterRequest(BaseModel):
    """Request interno para registrar cliente (hash já gerado)."""
    email: str
    senha_hash: str
    cliente_id: str
    empresa_id: int


@router.post("/registrar-interno", status_code=status.HTTP_201_CREATED)
async def registrar_cliente_interno(
    data: InternalRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Endpoint interno para registrar autenticação de cliente.
    Usado quando o cliente é criado durante o checkout.
    
    Não requer hash da senha - já vem hasheado do serviço chamador.
    """
    repo = ClienteAuthRepository(db)
    
    # Verificar se email já existe
    existing = await repo.buscar_por_email(data.email)
    if existing:
        log.warning("cliente.internal_register.email_exists", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Criar registro de autenticação com hash já fornecido
    from models.cliente_auth import ClienteAuth
    cliente_auth = ClienteAuth(
        email=data.email,
        senha_hash=data.senha_hash,
        cliente_id=UUID(data.cliente_id),
        empresa_id=data.empresa_id,
        ativo=True
    )
    
    db.add(cliente_auth)
    await db.commit()
    await db.refresh(cliente_auth)
    
    log.info(
        "cliente.internal_register.success",
        cliente_auth_id=str(cliente_auth.id),
        cliente_id=data.cliente_id,
        empresa_id=data.empresa_id
    )
    
    return {
        "id": str(cliente_auth.id),
        "email": cliente_auth.email,
        "cliente_id": str(cliente_auth.cliente_id),
        "empresa_id": cliente_auth.empresa_id
    }
