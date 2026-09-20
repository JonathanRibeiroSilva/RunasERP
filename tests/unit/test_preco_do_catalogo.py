"""Vendas lê o preço do catálogo por uma função só.

A regra "promoção ou preço normal" estava escrita duas vezes — no card da loja
em TypeScript e no carrinho em Python — e as duas se desencontraram: a vitrine
anunciava R$ 8 e o carrinho cobrava R$ 10. O conserto foi mover a decisão para
o catálogo (`preco_efetivo`) e deixar vendas com um leitor único.

A metade estática importa tanto quanto a função: se um dos dois pontos de
leitura voltar a montar o preço na mão, as pontas se desencontram de novo sem
nenhum teste de comportamento ficar vermelho.
"""
import ast
import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_RAIZ / "services" / "vendas" / "services"))

from preco_catalogo import preco_do_catalogo  # noqa: E402

from decimal import Decimal  # noqa: E402


def test_promocao_resolvida_pelo_catalogo_ganha_do_preco_de_tabela():
    assert preco_do_catalogo({"preco": "10.00", "preco_efetivo": "8.00"}) == Decimal("8.00")


def test_sem_preco_efetivo_cai_no_preco_de_tabela():
    """Imagem antiga de produtos durante um deploy: cobra cheio, não quebra."""
    assert preco_do_catalogo({"preco": "10.00"}) == Decimal("10.00")


def test_variante_tem_preco_proprio_e_nao_tem_promocao():
    assert preco_do_catalogo({"preco_venda": "15.50"}) == Decimal("15.50")


def test_catalogo_sem_preco_nenhum_devolve_zero():
    """Quem recusa é o chamador, que sabe se zero é venda de graça ou carrinho vazio."""
    assert preco_do_catalogo({"nome": "Produto"}) == Decimal("0")


def test_preco_efetivo_zero_nao_e_ignorado():
    """0 é falsy: um `or` no lugar do `is not None` devolveria o preço de tabela."""
    assert preco_do_catalogo({"preco": "10.00", "preco_efetivo": "0"}) == Decimal("0")


# --------------------- a metade estática ---------------------

ARQUIVOS_QUE_LEEM_PRECO = [
    _RAIZ / "services" / "vendas" / "services" / "carrinho_service.py",
    _RAIZ / "services" / "vendas" / "services" / "venda_service.py",
]


def _chaves_de_preco_lidas_na_mao(caminho: Path) -> list[str]:
    """Acha `algo.get('preco')` e afins fora do preco_catalogo."""
    achados = []
    for no in ast.walk(ast.parse(caminho.read_text(encoding="utf-8"))):
        if not isinstance(no, ast.Call) or not isinstance(no.func, ast.Attribute):
            continue
        if no.func.attr != "get" or not no.args:
            continue
        chave = no.args[0]
        if isinstance(chave, ast.Constant) and chave.value in ("preco", "preco_venda", "preco_efetivo"):
            achados.append(f"{caminho.name}:{no.lineno} -> .get({chave.value!r})")
    return achados


def test_nenhum_ponto_de_venda_monta_o_preco_na_mao():
    na_mao = [achado for caminho in ARQUIVOS_QUE_LEEM_PRECO for achado in _chaves_de_preco_lidas_na_mao(caminho)]

    assert na_mao == [], (
        "preço de catálogo lido fora do preco_do_catalogo — é assim que a "
        f"vitrine e a cobrança voltam a discordar: {na_mao}"
    )
