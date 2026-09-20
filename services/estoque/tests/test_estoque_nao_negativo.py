"""O estoque jamais aceita negativo, e a recusa chega como 400, não como 500.

Duas metades, e as duas importam.

O CHECK no banco é a última linha de defesa: vale para o caminho que ainda não
existe e para o UPDATE feito à mão no psql, que nenhuma validação em Python
alcança. Sem ele, um -3 entra em silêncio e o sistema passa a vender o que já
saiu.

Mas defesa de última linha que dispara no uso normal é um 500 sem explicação. O
ajuste de inventário é o caminho que hoje escrevia disponível negativo: contar 2
numa prateleira com 4 unidades reservadas. Quem recusa isso é o repositório,
antes do banco, com o motivo — e é esse teste que garante que o CHECK fique
sendo rede de segurança em vez de virar o validador do dia a dia.
"""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from models.estoque import Estoque
from schemas.estoque import AjusteEstoqueRequest
from services.estoque_service import EstoqueService

EMPRESA = 990_003


@pytest.mark.parametrize(
    "coluna", ["quantidade", "quantidade_reservada", "quantidade_disponivel"]
)
@pytest.mark.asyncio
async def test_o_banco_recusa_quantidade_negativa(db, coluna):
    valores = {
        "quantidade": 5.0,
        "quantidade_reservada": 0.0,
        "quantidade_disponivel": 5.0,
    }
    valores[coluna] = -3.0

    # Savepoint próprio: a violação aborta a transação, e sem ele o erro levaria
    # junto a sessão do teste.
    with pytest.raises(IntegrityError, match="ck_estoque_quantidades_nao_negativas"):
        async with db.begin_nested():
            db.add(Estoque(empresa_id=EMPRESA, produto_id=uuid.uuid4(), **valores))
            await db.flush()


@pytest.mark.asyncio
async def test_ajuste_abaixo_do_reservado_e_recusado_com_motivo(db):
    estoque = Estoque(
        empresa_id=EMPRESA, produto_id=uuid.uuid4(),
        quantidade=10.0, quantidade_reservada=4.0, quantidade_disponivel=6.0,
    )
    db.add(estoque)
    # commit: o serviço dá rollback no erro, e sem isto o rollback levaria junto
    # o que o teste montou. A fixture `db` desfaz tudo no fim de qualquer jeito.
    await db.commit()

    with pytest.raises(ValueError, match="reservada"):
        await EstoqueService.ajustar_estoque(
            db, EMPRESA,
            AjusteEstoqueRequest(
                estoque_id=estoque.id, quantidade_nova=2.0, motivo="contagem"
            ),
        )

    await db.refresh(estoque)
    assert (estoque.quantidade, estoque.quantidade_disponivel) == (10.0, 6.0), (
        "o ajuste recusado mexeu no estoque"
    )


@pytest.mark.asyncio
async def test_ajuste_ate_o_reservado_continua_passando(db):
    """A guarda não pode fechar a porta do inventário legítimo.

    Contar exatamente o que está reservado é o caso de borda que separa "recusa o
    que vira negativo" de "recusa qualquer ajuste para baixo".
    """
    estoque = Estoque(
        empresa_id=EMPRESA, produto_id=uuid.uuid4(),
        quantidade=10.0, quantidade_reservada=4.0, quantidade_disponivel=6.0,
    )
    db.add(estoque)
    await db.commit()

    resposta = await EstoqueService.ajustar_estoque(
        db, EMPRESA,
        AjusteEstoqueRequest(
            estoque_id=estoque.id, quantidade_nova=4.0, motivo="contagem"
        ),
    )

    assert (resposta.quantidade, resposta.quantidade_disponivel) == (4.0, 0.0)
