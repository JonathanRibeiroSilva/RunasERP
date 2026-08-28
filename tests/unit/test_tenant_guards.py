"""Every business route in a service must scope itself to a tenant.

`GET /empresas` listed every tenant in production because nothing forced the
route to declare a tenant dependency. Services never check role — the gateway
injects `X-Empresa-Id` and the route is the only place that reads it. So a
route function without `exigir_tenant`/`get_empresa_id` in its signature is,
by construction, cross-tenant. Public routes are opt-in, listed below.
"""
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TENANT_DEPS = ("exigir_tenant", "get_empresa_id", "get_empresa_id_from_slug", "exigir_plataforma")

# Rotas deliberadamente públicas: catálogo da loja online e webhooks externos,
# que se identificam por slug/assinatura e não por header do gateway.
PUBLICAS = {
    "empresas/routers/empresas.py::buscar_info_publica",
    # catálogo público: o tenant vem do ?empresaSlug, resolvido dentro do handler
    "produtos/routers/produtos.py::listar_produtos_loja_online_publico",
    "produtos/routers/produtos.py::listar_categorias_loja_online_publico",
    "produtos/routers/produtos.py::obter_produto_catalogo_publico",
    "produtos/routers/produtos.py::obter_produto_loja_online_publico",
    # webhook externo: tenant vem do path /{empresa_slug}, autenticado pela assinatura do MP
    "vendas/routers/webhook.py::webhook_mercadopago",
    "vendas/routers/webhook.py::test_webhook",
}


def _decorators_are_routes(fn: ast.AST) -> bool:
    return any(
        isinstance(d, ast.Call)
        and isinstance(d.func, ast.Attribute)
        and d.func.attr in ("get", "post", "put", "patch", "delete", "api_route")
        for d in getattr(fn, "decorator_list", [])
    )


def _dependency_names(fn: ast.AST) -> set:
    names = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "Depends":
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    names.add(arg.id)
                elif isinstance(arg, ast.Attribute):
                    names.add(arg.attr)
    return names


def test_every_service_route_declares_a_tenant_dependency():
    offenders = []
    for path in REPO.glob("services/*/routers/*.py"):
        rel = "/".join(path.parts[path.parts.index("services") + 1:])
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in tree.body:
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _decorators_are_routes(fn):
                continue
            if f"{rel}::{fn.name}" in PUBLICAS:
                continue
            # o dep de tenant pode estar no default de qualquer parâmetro
            if not (_dependency_names(fn) & set(TENANT_DEPS)):
                offenders.append(f"{rel}::{fn.name}")
    assert not offenders, (
        "rotas sem isolamento por tenant (adicione Depends(exigir_tenant) ou "
        f"Depends(get_empresa_id), ou liste em PUBLICAS): {offenders}"
    )
