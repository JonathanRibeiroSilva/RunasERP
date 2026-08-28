"""
Router de proxy para microsserviços.
"""
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from auth.oauth2 import (
    get_current_active_user,
    require_admin,
    require_admin_or_operador,
    get_current_active_cliente
)
from models.usuario import Usuario
from models.cliente_auth import ClienteAuth
from proxy.service_proxy import ServiceProxy


router = APIRouter()


# Rotas públicas (sem autenticação)
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
    # Encaminha o cliente autenticado para que o proxy injete X-Empresa-Id
    # (e X-Cliente-Id) — sem isso o serviço de clientes rejeita com 400.
    return await ServiceProxy.proxy_request(request, full_path, current_cliente)  # type: ignore[arg-type]


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
    # Encaminha o cliente autenticado para que o proxy injete X-Empresa-Id
    # (e X-Cliente-Id) — sem isso o serviço de clientes rejeita com 400.
    return await ServiceProxy.proxy_request(request, full_path, current_cliente)  # type: ignore[arg-type]


@router.get(
    "/loja/meus-pedidos",
    tags=["Loja Online - Cliente"],
    summary="Listar pedidos do cliente autenticado"
)
async def proxy_loja_meus_pedidos(
    request: Request,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)],
    empresaSlug: str | None = None
):
    """
    Rota para cliente autenticado listar seus próprios pedidos.
    
    Usa o cliente_id do token JWT automaticamente via header X-Cliente-Id.
    
    Exemplo: GET /loja/meus-pedidos?empresaSlug=minha-loja
    """
    full_path = "/loja/meus-pedidos"

    # current_cliente (ClienteAuth) já expõe empresa_id/cliente_id; o ServiceProxy
    # injeta X-Empresa-Id/X-Cliente-Id a partir dele.
    return await ServiceProxy.proxy_request(
        request,
        full_path,
        current_user=current_cliente,  # type: ignore[arg-type]
        empresa_slug=empresaSlug
    )


@router.post(
    "/loja/pedidos/{numero_venda}/retry-payment",
    tags=["Loja Online - Cliente"],
    summary="Gerar novo link de pagamento"
)
async def proxy_loja_retry_payment(
    request: Request,
    numero_venda: str,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)],
    empresaSlug: str | None = None
):
    """
    Rota para cliente autenticado gerar novo link de pagamento para pedido pendente.
    
    Usa o cliente_id do token JWT automaticamente via header X-Cliente-Id.
    
    Exemplo: POST /loja/pedidos/V-2024-001/retry-payment?empresaSlug=minha-loja
    """
    full_path = f"/loja/pedidos/{numero_venda}/retry-payment"
    
    # current_cliente (ClienteAuth) já expõe empresa_id/cliente_id; o ServiceProxy
    # injeta X-Empresa-Id/X-Cliente-Id a partir dele.
    return await ServiceProxy.proxy_request(
        request,
        full_path,
        current_user=current_cliente,  # type: ignore[arg-type]
        empresa_slug=empresaSlug
    )


@router.post(
    "/loja/pedidos/{numero_venda}/recuperar-carrinho",
    tags=["Loja Online - Cliente"],
    summary="Recuperar carrinho de pedido não pago"
)
async def proxy_loja_recuperar_carrinho(
    request: Request,
    numero_venda: str,
    current_cliente: Annotated[ClienteAuth, Depends(get_current_active_cliente)],
    empresaSlug: str | None = None
):
    """
    Rota para cliente autenticado recuperar carrinho a partir de pedido pendente.
    
    Reconstrói carrinho com itens do pedido para permitir edição antes de pagar.
    Usa o cliente_id do token JWT automaticamente via header X-Cliente-Id.
    
    Exemplo: POST /loja/pedidos/V-2024-001/recuperar-carrinho?empresaSlug=minha-loja
    """
    full_path = f"/loja/pedidos/{numero_venda}/recuperar-carrinho"
    
    # current_cliente (ClienteAuth) já expõe empresa_id/cliente_id; o ServiceProxy
    # injeta X-Empresa-Id/X-Cliente-Id a partir dele.
    return await ServiceProxy.proxy_request(
        request,
        full_path,
        current_user=current_cliente,  # type: ignore[arg-type]
        empresa_slug=empresaSlug
    )


# Catch-all da loja (carrinho, checkout, rastreamento — sem autenticação).
# Registrado DEPOIS das rotas /loja/* autenticadas acima: o Starlette casa rotas
# na ordem de registro, e este {path:path} capturaria /loja/meus-pedidos etc.
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


# Rota para operações com cliente específico (path genérico - ADMIN)
# Registrada após /clientes/me e /clientes para que aquelas rotas tenham precedência.
@router.api_route(
    "/clientes/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Clientes"],
    summary="Operações administrativas com clientes"
)
async def proxy_clientes_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    """
    Proxy para serviço de clientes - operações admin (autenticado).

    Mesma convenção de /produtos/{path}, /categorias/{path}, etc.
    A rota pública /clientes/me é declarada antes e mantém precedência.
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


# Rotas de administração da loja online (config, fotos, status de publicação de produtos)
# Nota: a rota pública "/loja-online/publico/{path:path}" é registrada antes desta
# (sem autenticação) e tem precedência no roteamento do FastAPI.
@router.api_route(
    "/loja-online/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["Loja Online"],
    summary="Operações de administração da loja online"
)
async def proxy_loja_online_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
):
    full_path = f"/loja-online/{path}"
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
    current_user: Annotated[Usuario, Depends(require_admin_or_operador)]
):
    """
    Proxy para serviço de estoque (ADMIN ou OPERADOR).

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
    current_user: Annotated[Usuario, Depends(require_admin_or_operador)]
):
    """
    Proxy para serviço de estoque (ADMIN ou OPERADOR).

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


# Integrações do tenant (WhatsApp/Evolution e SMTP) — só admin configura
@router.api_route(
    "/integracoes",
    methods=["GET", "PUT", "DELETE"],
    tags=["Integrações"],
    summary="Integrações do tenant"
)
async def proxy_integracoes(
    request: Request,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """Proxy para as integrações em vendas (apenas admin)."""
    return await ServiceProxy.proxy_request(request, "/integracoes", current_user)


# Rotas de empresas (admin)
@router.api_route(
    "/empresas",
    methods=["GET"],
    tags=["Empresas"],
    summary="Listar a própria empresa"
)
async def proxy_empresas_root(
    request: Request,
    current_user: Annotated[Usuario, Depends(require_admin)]
):
    """Proxy para serviço de empresas (apenas admin). Criação vive em /plataforma."""
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
