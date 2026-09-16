"""A rota de billing da plataforma não aceita dict cru nem sobrescreve o que não foi pedido.

`alterar_plano` recebia `plano: dict` e repassava o corpo inteiro para
`PATCH /empresas/{id}/plano`. Era o único ponto do router de plataforma sem
validação própria: a única coisa entre um corpo arbitrário e a tabela era o
schema do serviço downstream.

O segundo assert guarda a armadilha de consertar o primeiro sem pensar. Do outro
lado, `EmpresaService.atualizar_plano` faz `setattr` de cada campo que chega
(`model_dump(exclude_unset=True)` sobre o que o JSON trouxe). Um `model_dump()`
sem `exclude_unset` no gateway manda os cinco campos como null, o Pydantic do
empresas lê null como valor informado, e quem só queria suspender um tenant
zera plano, max_usuarios e max_produtos junto.
"""
import re
from pathlib import Path

GATEWAY = Path(__file__).resolve().parents[2] / "api-gateway"


def _corpo_da_rota(fonte: str, decorador: str) -> str:
    """O texto de uma rota, do decorador até a próxima."""
    corpo = fonte[fonte.index(decorador):]
    return corpo[: corpo.index("\n@router.")] if "\n@router." in corpo else corpo


def test_alterar_plano_declara_schema():
    fonte = (GATEWAY / "routers" / "plataforma.py").read_text(encoding="utf-8")
    corpo = _corpo_da_rota(fonte, '@router.patch("/tenants/{empresa_id}/plano"')

    assert not re.search(r"plano:\s*dict", corpo), (
        "alterar_plano voltou a aceitar dict cru — corpo arbitrário chega à rota de billing"
    )
    assert re.search(r"plano:\s*PlanoUpdate", corpo), "schema do corpo sumiu"


def test_alterar_plano_nao_sobrescreve_campo_nao_informado():
    fonte = (GATEWAY / "routers" / "plataforma.py").read_text(encoding="utf-8")
    corpo = _corpo_da_rota(fonte, '@router.patch("/tenants/{empresa_id}/plano"')

    assert "model_dump(exclude_unset=True)" in corpo, (
        "sem exclude_unset, suspender um tenant manda plano/limites como null "
        "e o empresas grava null em cima"
    )


def test_schema_do_plano_recusa_campo_desconhecido():
    fonte = (GATEWAY / "routers" / "plataforma.py").read_text(encoding="utf-8")
    classe = fonte[fonte.index("class PlanoUpdate"):]
    classe = classe[: classe.index("\n@router.")]

    assert 'extra="forbid"' in classe, "PlanoUpdate voltou a ignorar campo desconhecido"
