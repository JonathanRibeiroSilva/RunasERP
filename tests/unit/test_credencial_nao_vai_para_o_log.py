"""Credencial não vai para o log.

`mercadopago_service.py` gravava, a cada preferência criada, um evento
`mercadopago_payload_completo` com `access_token_inicio=...[:20]` — os vinte
primeiros caracteres do access token do lojista, em log de produção, para
sempre. Junto ia o `preference_data` inteiro, que carrega o e-mail e o nome do
comprador convidado.

Era log de debug que ficou. O evento `mercadopago_preferencia_montada`, logo
acima, já diz o que interessa sem carregar nada disso.

A guarda é estática e vale para o repositório todo: varre as chamadas de log
por AST (não por texto, senão um comentário citando a regra reprovaria) e
recusa qualquer argumento que nomeie uma credencial. Passam `len(...)`,
`bool(...)` e literais — o tamanho do token é diagnóstico útil e não é o
segredo, e uma string constante não carrega valor de runtime.
"""
import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RAIZES = ("services", "api-gateway")

NIVEIS = {"debug", "info", "warning", "error", "critical", "exception"}
CREDENCIAIS = ("access_token", "refresh_token", "webhook_secret", "secret", "senha", "password")
# Envelopes que provam que o segredo não sai: não dá para reconstruí-lo do resultado.
SEGUROS = ("len(", "bool(")


def _fontes():
    for raiz in RAIZES:
        for arquivo in (REPO / raiz).rglob("*.py"):
            if "alembic" in arquivo.parts or "tests" in arquivo.parts:
                continue
            yield arquivo


def _chamadas_de_log(arvore):
    for no in ast.walk(arvore):
        if (
            isinstance(no, ast.Call)
            and isinstance(no.func, ast.Attribute)
            and no.func.attr in NIVEIS
            and isinstance(no.func.value, ast.Name)
            and no.func.value.id in ("log", "logger")
        ):
            yield no


def _vazamentos(arquivo: Path):
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    for chamada in _chamadas_de_log(arvore):
        for kw in chamada.keywords:
            if isinstance(kw.value, ast.Constant):
                continue  # literal não carrega segredo em runtime (f-string é JoinedStr)
            valor = ast.unparse(kw.value)
            if valor.startswith(SEGUROS):
                continue
            alvo = f"{kw.arg or ''} {valor}".lower()
            achado = [c for c in CREDENCIAIS if c in alvo]
            if achado:
                yield f"{arquivo.relative_to(REPO)}:{chamada.lineno} {kw.arg}={valor} ({achado[0]})"


def test_nenhum_log_carrega_credencial():
    vazamentos = [v for arquivo in _fontes() for v in _vazamentos(arquivo)]
    assert not vazamentos, "credencial em log:\n" + "\n".join(vazamentos)


def test_o_corpo_da_preferencia_nao_vai_para_o_log():
    """O payload leva o e-mail e o nome do comprador convidado."""
    arquivo = REPO / "services" / "vendas" / "services" / "mercadopago_service.py"
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))

    despejos = [
        f"linha {c.lineno}"
        for c in _chamadas_de_log(arvore)
        for kw in c.keywords
        if ast.unparse(kw.value) == "preference_data"
    ]
    assert not despejos, f"corpo da preferência no log: {despejos}"
