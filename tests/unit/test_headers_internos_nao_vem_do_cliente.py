"""Headers de contexto são identidade: o cliente não pode fornecê-los.

O gateway copiava `dict(request.headers)` inteiro antes de encaminhar. X-Plataforma
nunca era sobrescrito, e ele é o único portão de `exigir_plataforma` no serviço de
empresas — que protege criar_empresa, atualizar_plano e listar_todas_plataforma.
Com o proxy catch-all `/empresas/{path:path}`, qualquer admin de tenant mandava
`X-Plataforma: 1` e virava administrador da plataforma.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INTERNOS = ("x-empresa-id", "x-cliente-id", "x-plataforma")


def test_gateway_descarta_headers_internos_antes_de_injetar_contexto():
    fonte = (REPO / "api-gateway" / "proxy" / "service_proxy.py").read_text(encoding="utf-8")

    copia = fonte.index("headers = dict(request.headers)")
    injecao = fonte.index("_inject_context_headers(headers", copia)
    saneamento = fonte[copia:injecao]

    faltando = [h for h in INTERNOS if h not in saneamento]
    assert not faltando, f"header interno não é descartado antes da injeção: {faltando}"


def test_exigir_plataforma_continua_sendo_o_portao_das_rotas_de_plataforma():
    """Se o portão mudar de nome, o saneamento acima precisa acompanhar."""
    empresas = (REPO / "services" / "empresas" / "routers" / "empresas.py").read_text(encoding="utf-8")
    assert 'Header(None, alias="X-Plataforma")' in empresas, "portão da plataforma mudou"
