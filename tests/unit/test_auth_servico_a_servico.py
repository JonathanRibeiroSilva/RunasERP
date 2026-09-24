"""
Guardas estáticas do INFRA-C: prova de origem interna entre os 8 containers.

O fix tem dois lados e os dois somem calado:
  - o validador, se alguém remover o `app.middleware(...)` de um main.py;
  - o carimbo, se um call site interno novo nascer sem `auth_interno(...)`.

E tem um terceiro modo de falha, o caro: carimbar o segredo numa chamada a
terceiro. `mercadopago_service.py` fala com a API do Mercado Pago, `entrega_service`
com o viacep e `notificacao_service` com a Evolution API do lojista — mandar o
segredo interno para qualquer um deles é vazar credencial para fora.

Asserções sobre a janela do código, no molde de
`test_headers_internos_nao_vem_do_cliente.py`.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SERVICOS = ["clientes", "empresas", "estoque", "financeiro",
            "notificacoes", "produtos", "vendas"]

CHAMADA = re.compile(r"await client\.(get|post|put|patch|delete|request)\(")

# Marcas de destino externo. Uma chamada cuja janela contém qualquer uma delas
# NÃO pode levar o segredo interno.
MARCAS_EXTERNAS = (
    "MERCADOPAGO", "MP_API", "googleapis", "microsoftonline",
    "graph.microsoft", "VIACEP", "message/sendText",
)

# `auth_interno()` direto, ou o wrapper do gateway que delega a ele — travado
# por test_wrapper_do_gateway_delega.
CARIMBOS = ("auth_interno", "_internal_headers")


def _arquivos_de_producao():
    for base in ("api-gateway", "services"):
        for p in sorted((RAIZ / base).rglob("*.py")):
            rel = p.relative_to(RAIZ).as_posix()
            if "/tests/" in rel or p.name == "conftest.py" or "/alembic/" in rel:
                continue
            yield rel, p


def _call_sites():
    """(rel, linha, janela) de cada chamada httpx em código de produção."""
    for rel, p in _arquivos_de_producao():
        linhas = p.read_text(encoding="utf-8").splitlines()
        for i, l in enumerate(linhas):
            if CHAMADA.search(l):
                # A montagem dos headers pode estar bem acima (variável) e os
                # argumentos bem abaixo (chamada multilinha).
                yield rel, i + 1, "\n".join(linhas[max(0, i - 40):i + 15])


@pytest.mark.parametrize("servico", SERVICOS)
def test_validador_registrado_no_servico(servico):
    """Sem o middleware no main.py, o serviço volta a aceitar qualquer origem."""
    # Linha comentada não registra nada: `# app.middleware(...)` passaria numa
    # busca por substring no arquivo inteiro.
    ativas = [
        l.strip()
        for l in (RAIZ / "services" / servico / "main.py").read_text(
            encoding="utf-8").splitlines()
        if not l.strip().startswith("#")
    ]
    assert "from interno import validar_token_interno" in ativas, (
        f"{servico}/main.py não importa o validador"
    )
    assert 'app.middleware("http")(validar_token_interno)' in ativas, (
        f"{servico}/main.py não registra o validador"
    )


@pytest.mark.parametrize("servico", SERVICOS)
def test_servico_le_o_segredo(servico):
    """Sem a env no config, o validador fica fail-open para sempre."""
    cfg = (RAIZ / "services" / servico / "config.py").read_text(encoding="utf-8")
    assert "SERVICO_INTERNO_TOKEN" in cfg, f"{servico}/config.py sem o segredo"


@pytest.mark.parametrize("compose", ["docker-compose.prod.yml", "docker-compose.dev.yml"])
def test_segredo_chega_nos_oito_containers(compose):
    """O mesmo valor nos 8. Faltando em um, ele fica fora da malha autenticada."""
    yaml = pytest.importorskip("yaml")
    servicos = yaml.safe_load((RAIZ / compose).read_text(encoding="utf-8"))["services"]
    com_token = {
        nome for nome, spec in servicos.items()
        if isinstance(spec, dict)
        and "SERVICO_INTERNO_TOKEN" in (spec.get("environment") or {})
    }
    assert len(com_token) == 8, (
        f"{compose}: {len(com_token)} containers com o segredo, esperado 8 "
        f"(gateway + 7 serviços). Presentes: {sorted(com_token)}"
    )


def test_segredo_interno_nao_vai_para_terceiro():
    """
    O modo de falha caro. Um hook global no httpx carimbaria estas chamadas —
    é por isso que `auth_interno()` é opt-in, uma chamada por vez.
    """
    vazados = [
        f"{rel}:{linha}"
        for rel, linha, janela in _call_sites()
        if any(m in janela for m in MARCAS_EXTERNAS)
        and any(c in janela for c in CARIMBOS)
    ]
    assert not vazados, (
        "segredo interno carimbado em chamada a terceiro: " + ", ".join(vazados)
    )


def test_todo_call_site_interno_carimba():
    """
    Um call site interno novo sem carimbo é invisível enquanto o validador
    estiver fail-open: ele loga e deixa passar. Vira 403 no dia em que fechar.

    /health é isento de propósito: o healthcheck do Docker bate direto em
    localhost, sem passar pelo gateway (ver ISENTOS em services/*/interno.py).
    """
    sem_carimbo = [
        f"{rel}:{linha}"
        for rel, linha, janela in _call_sites()
        if not any(m in janela for m in MARCAS_EXTERNAS)
        and "/health" not in janela
        and not any(c in janela for c in CARIMBOS)
    ]
    assert not sem_carimbo, (
        "chamada interna sem prova de origem: " + ", ".join(sem_carimbo)
    )


def test_wrapper_do_gateway_delega():
    """
    `_internal_headers` conta como carimbo nos testes acima. Se ele parar de
    delegar, os 3 call sites que dependem dele passam a mentir calados.
    """
    fonte = (RAIZ / "api-gateway" / "routers" / "auth_cliente.py").read_text(
        encoding="utf-8")
    corpo = fonte[fonte.index("def _internal_headers"):]
    corpo = corpo[:corpo.index("\n\n\n")]
    assert "auth_interno(" in corpo, (
        "_internal_headers parou de carimbar a prova de origem interna"
    )
