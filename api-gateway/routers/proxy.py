"""
Router de proxy para microsserviços.
"""
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from auth.oauth2 import (
    get_current_active_user, 
    require_admin,
    get_current_active_cliente
)
from models.usuario import Usuario
from models.cliente_auth import ClienteAuth
from proxy.service_proxy import ServiceProxy


router = APIRouter()


# Rotas públicas (sem autenticação)
@router.api_route(
    "/catalogo/{path:path}",
    methods=["GET"],
    tags=["Catálogo Público"]
)
async def proxy_catalogo_publico(request: Request, path: str):
    """Proxy para catálogo público (sem autenticação)."""
    full_path = f"/catalogo/{path}" if path else "/catalogo"
    return await ServiceProxy.proxy_request(request, full_path)


@router.api_route(
    "/empresas/publico/{path:path}",
    methods=["GET"],
    tags=["Empresas Público"]
)
async def proxy_empresas_publico(request: Request, path: str):
    """Proxy para informações públicas de empresas (sem autenticação)."""
    full_path = f"/empresas/publico/{path}" if path else "/empresas/publico"
    return await ServiceProxy.proxy_request(request, full_path)


@router.api_route(
    "/loja-online/publico/{path:path}",
    methods=["GET"],
    tags=["Loja Online Público"]
)
async def proxy_loja_online_publico(
    request: Request,
    path: str,
    empresaSlug: str | None = None
):
    """Proxy para loja online pública - produtos e categorias (sem autenticação)."""
    full_path = f"/loja-online/publico/{path}" if path else "/loja-online/publico"
    return await ServiceProxy.proxy_request(request, full_path, empresa_slug=empresaSlug)


@router.api_route(
    "/loja/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Loja Online"]
)
async def proxy_loja_publico(
    request: Request,
    path: str,
    empresaSlug: str | None = None
):
    """Proxy para loja online - carrinho e checkout (sem autenticação)."""
    full_path = f"/loja/{path}" if path else "/loja"
    return await ServiceProxy.proxy_request(request, full_path, empresa_slug=empresaSlug)


@router.api_route(
    "/carrinho/{path:path}",
    methods=["GET", "POST", "PATCH", "DELETE"],
    tags=["Carrinho Público"]
)
async def proxy_carrinho_publico(
    request: Request,
    path: str,
    empresaSlug: str | None = None
):
    """Proxy para carrinho (sem autenticação)."""
    full_path = f"/carrinho/{path}" if path else "/carrinho"
    return await ServiceProxy.proxy_request(request, full_path, empresa_slug=empresaSlug)


# Rotas protegidas (requerem autenticação)

# ============================================================
# ROTAS DE CLIENTES (PÚBLICO - CLIENTE AUTENTICADO)
# ============================================================

@router.get(
    "/clientes/me",
    tags=["Clientes Público"],
    summary="Cliente busca seus próprios dados"
)
async def proxy_cliente_me(
    request: Request,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)]
):
    """
    Rota para cliente autenticado buscar seus próprios dados.
    
    Usa o cliente_id do token JWT automaticamente.
    Não requer passar ID na URL (mais seguro e simples).
    
    Exemplo: GET /clientes/me
    """
    cliente_id = str(current_cliente.cliente_id)
    full_path = f"/clientes/{cliente_id}"
    return await ServiceProxy.proxy_request(request, full_path)


@router.patch(
    "/clientes/me",
    tags=["Clientes Público"],
    summary="Cliente atualiza seus próprios dados"
)
async def proxy_cliente_me_update(
    request: Request,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)]
):
    """
    Rota para cliente autenticado atualizar seus próprios dados.
    
    Usa o cliente_id do token JWT automaticamente.
    Cliente só pode atualizar seus próprios dados.
    
    Exemplo: PATCH /clientes/me
    """
    cliente_id = str(current_cliente.cliente_id)
    full_path = f"/clientes/{cliente_id}"
    return await ServiceProxy.proxy_request(request, full_path)


# ============================================================
# ROTAS DE CLIENTES (ADMIN)
# ============================================================

# Rota específica para listar/criar clientes (ADMIN)
@router.api_route(
    "/clientes",
    methods=["GET", "POST"],
    tags=["Clientes"],
    summary="Listar ou criar clientes"
)
async def proxy_clientes_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    """
    Proxy para serviço de clientes (autenticado admin).
    
    - GET: Lista clientes com filtros opcionais
    - POST: Cria novo cliente
    """
    return await ServiceProxy.proxy_request(request, "/clientes", current_user)


# Rota para operações administrativas com clientes (path genérico - ADMIN)
@router.api_route(
    "/clientes/admin/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Clientes"],
    summary="Operações administrativas com clientes"
)
async def proxy_clientes_admin_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    """
    Proxy para serviço de clientes - operações admin (autenticado).
    
    Movido para /clientes/admin/{path} para evitar conflito com rota pública.
    """
    full_path = f"/clientes/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


# Rota específica para listar/criar produtos
@router.api_route(
    "/produtos",
    methods=["GET", "POST"],
    tags=["Produtos"],
    summary="Listar ou criar produtos"
)
async def proxy_produtos_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    return await ServiceProxy.proxy_request(request, "/produtos", current_user)


# Rota para operações com ID específico
@router.api_route(
    "/produtos/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Produtos"],
    summary="Operações com produto específico"
)
async def proxy_produtos_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    full_path = f"/produtos/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


# Rotas de categorias
@router.api_route(
    "/categorias",
    methods=["GET", "POST"],
    tags=["Produtos"],
    summary="Listar ou criar categorias"
)
async def proxy_categorias_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    return await ServiceProxy.proxy_request(request, "/categorias", current_user)


@router.api_route(
    "/categorias/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Produtos"],
    summary="Operações com categoria específica"
)
async def proxy_categorias_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    full_path = f"/categorias/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


# Rotas de variantes
@router.api_route(
    "/variantes",
    methods=["GET", "POST"],
    tags=["Produtos"],
    summary="Listar ou criar variantes"
)
async def proxy_variantes_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    return await ServiceProxy.proxy_request(request, "/variantes", current_user)


@router.api_route(
    "/variantes/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Produtos"],
    summary="Operações com variante específica"
)
async def proxy_variantes_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    full_path = f"/variantes/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


# Rotas de fornecedores
@router.api_route(
    "/fornecedores",
    methods=["GET", "POST"],
    tags=["Produtos"],
    summary="Listar ou criar fornecedores"
)
async def proxy_fornecedores_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    return await ServiceProxy.proxy_request(request, "/fornecedores", current_user)


@router.api_route(
    "/fornecedores/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Produtos"],
    summary="Operações com fornecedor específico"
)
async def proxy_fornecedores_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    full_path = f"/fornecedores/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


# Rota específica para listar/criar estoque
@router.api_route(
    "/estoque",
    methods=["GET", "POST"],
    tags=["Estoque"],
    summary="Listar ou criar registros de estoque"
)
async def proxy_estoque_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """
    Proxy para serviço de estoque (apenas admin).
    
    - GET: Lista registros de estoque
    - POST: Cria novo registro de estoque
    """
    return await ServiceProxy.proxy_request(request, "/estoque", current_user)


# Rota para operações com ID específico
@router.api_route(
    "/estoque/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Estoque"],
    summary="Operações de estoque"
)
async def proxy_estoque_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """
    Proxy para serviço de estoque (apenas admin).
    
    - GET /estoque/{id}: Busca estoque por ID
    - POST /estoque/entrada: Entrada de mercadoria
    - POST /estoque/saida: Saída de mercadoria
    - POST /estoque/reservar: Reservar estoque
    - POST /estoque/confirmar-reserva: Confirmar reserva
    - POST /estoque/liberar-reserva: Liberar reserva
    """
    full_path = f"/estoque/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


@router.api_route(
    "/pedidos/{path:path}",
    methods=["GET", "POST", "PATCH", "DELETE"],
    tags=["Pedidos"]
)
async def proxy_pedidos(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    """Proxy para serviço de vendas - pedidos (autenticado)."""
    full_path = f"/pedidos/{path}" if path else "/pedidos"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


@router.api_route(
    "/pagamentos/{path:path}",
    methods=["GET", "POST", "PATCH"],
    tags=["Pagamentos"]
)
async def proxy_pagamentos(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    """Proxy para serviço de vendas - pagamentos (autenticado)."""
    full_path = f"/pagamentos/{path}" if path else "/pagamentos"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


@router.api_route(
    "/contas/{path:path}",
    methods=["GET", "POST", "PATCH"],
    tags=["Financeiro"]
)
async def proxy_contas(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """Proxy para serviço financeiro (apenas admin)."""
    full_path = f"/contas/{path}" if path else "/contas"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


@router.api_route(
    "/notificacoes/{path:path}",
    methods=["GET", "POST"],
    tags=["Notificações"]
)
async def proxy_notificacoes(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """Proxy para serviço de notificações (apenas admin)."""
    full_path = f"/notificacoes/{path}" if path else "/notificacoes"
    return await ServiceProxy.proxy_request(request, full_path, current_user)


# Webhook público (sem autenticação)
@router.post(
    "/pagamentos/webhook/mercadopago",
    tags=["Webhooks"]
)
async def proxy_webhook_mercadopago(request: Request):
    """Proxy para webhook do Mercado Pago (público)."""
    return await ServiceProxy.proxy_request(request, "/pagamentos/webhook/mercadopago")


# Rotas de empresas (admin)
@router.api_route(
    "/empresas",
    methods=["GET", "POST"],
    tags=["Empresas"],
    summary="Listar ou criar empresas"
)
async def proxy_empresas_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """Proxy para serviço de empresas (apenas admin)."""
    return await ServiceProxy.proxy_request(request, "/empresas", current_user)


@router.api_route(
    "/empresas/{path:path}",
    methods=["GET", "PUT", "DELETE"],
    tags=["Empresas"],
    summary="Operações com empresa específica"
)
async def proxy_empresas_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """Proxy para serviço de empresas (apenas admin)."""
    full_path = f"/empresas/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)
