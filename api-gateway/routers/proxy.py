"""
Router de proxy para microsserviços.
"""
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from auth.oauth2 import get_current_active_user, require_admin
from models.usuario import Usuario
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
    "/carrinho/{path:path}",
    methods=["GET", "POST", "PATCH", "DELETE"],
    tags=["Carrinho Público"]
)
async def proxy_carrinho_publico(request: Request, path: str):
    """Proxy para carrinho (sem autenticação)."""
    full_path = f"/carrinho/{path}" if path else "/carrinho"
    return await ServiceProxy.proxy_request(request, full_path)


# Rotas protegidas (requerem autenticação)

# Rota específica para listar/criar clientes
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
    Proxy para serviço de clientes (autenticado).
    
    - GET: Lista clientes com filtros opcionais
    - POST: Cria novo cliente
    """
    return await ServiceProxy.proxy_request(request, "/clientes")


# Rota para operações com ID específico
@router.api_route(
    "/clientes/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Clientes"],
    summary="Operações com cliente específico"
)
async def proxy_clientes_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    """
    Proxy para serviço de clientes (autenticado).
    
    - GET /clientes/{id}: Busca cliente por ID
    - PUT /clientes/{id}: Atualiza cliente
    - DELETE /clientes/{id}: Desativa cliente
    - POST /clientes/{id}/enderecos: Adiciona endereço
    """
    full_path = f"/clientes/{path}"
    return await ServiceProxy.proxy_request(request, full_path)


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
    """
    Proxy para serviço de produtos (autenticado).
    
    - GET: Lista produtos com filtros opcionais
    - POST: Cria novo produto
    """
    return await ServiceProxy.proxy_request(request, "/produtos")


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
    """
    Proxy para serviço de produtos (autenticado).
    
    - GET /produtos/{id}: Busca produto por ID
    - PUT /produtos/{id}: Atualiza produto
    - DELETE /produtos/{id}: Desativa produto
    - POST /produtos/{id}/variantes: Adiciona variante
    """
    full_path = f"/produtos/{path}"
    return await ServiceProxy.proxy_request(request, full_path)


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
    return await ServiceProxy.proxy_request(request, "/estoque")


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
    return await ServiceProxy.proxy_request(request, full_path)


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
    return await ServiceProxy.proxy_request(request, full_path)


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
    return await ServiceProxy.proxy_request(request, full_path)


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
    return await ServiceProxy.proxy_request(request, full_path)


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
    return await ServiceProxy.proxy_request(request, full_path)


# Webhook público (sem autenticação)
@router.post(
    "/pagamentos/webhook/mercadopago",
    tags=["Webhooks"]
)
async def proxy_webhook_mercadopago(request: Request):
    """Proxy para webhook do Mercado Pago (público)."""
    return await ServiceProxy.proxy_request(request, "/pagamentos/webhook/mercadopago")
