"""
Qual preço o catálogo diz que vale.

A regra "promoção ou preço normal" estava escrita duas vezes, em duas
linguagens: o card da loja em TypeScript exibia a promoção quando ela existia,
e o carrinho em Python lia `preco` e nunca olhava `preco_promocional`. As duas
se desencontraram — a vitrine anunciava R$ 8 e o carrinho cobrava R$ 10.

Agora quem decide é o serviço de produtos, num campo calculado (`preco_efetivo`),
e este módulo é o único ponto por onde vendas lê preço de catálogo. Dois
leitores, uma fonte: o carrinho, ao adicionar o item, e o criar_venda, ao
fechar o pedido.

Sem ORM e sem HTTP: recebe o dicionário que a API de produtos devolveu.
"""
from decimal import Decimal

# Ordem importa. `preco_efetivo` é o campo novo e já traz a promoção resolvida.
# `preco` é a rede para uma imagem antiga do serviço de produtos ainda no ar
# durante um deploy: cobra o preço cheio, que é o lado seguro. `preco_venda` é
# a variante, que tem preço próprio e não tem promoção.
_CHAVES = ("preco_efetivo", "preco", "preco_venda")


def preco_do_catalogo(item: dict) -> Decimal:
    """Preço de venda de um produto ou variante, como o catálogo respondeu."""
    for chave in _CHAVES:
        valor = item.get(chave)
        if valor is not None:
            return Decimal(str(valor))
    return Decimal("0")
