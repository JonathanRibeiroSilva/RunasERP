"""Um cliente, uma conta de login.

`email` sempre foi único; `cliente_id` não era. Duas contas com emails
diferentes apontando para o mesmo cliente passam a enxergar os mesmos pedidos,
os mesmos endereços e o mesmo crédito — e qualquer uma das duas senhas abre a
porta da outra.

O teste vai no banco de verdade porque é lá que a regra mora: a garantia é a
UNIQUE da revision 20260919_cli_unico, não uma checagem no Python que o próximo
caminho de criação esquece de repetir.
"""
import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models.cliente_auth import ClienteAuth


def _conta(cliente_id, empresa_id: int = 1) -> ClienteAuth:
    return ClienteAuth(
        email=f"{uuid4().hex}@exemplo.com",
        senha_hash="hash-irrelevante-para-esta-regra",
        cliente_id=cliente_id,
        empresa_id=empresa_id,
    )


@pytest.mark.asyncio
async def test_segunda_conta_no_mesmo_cliente_e_recusada(db):
    cliente_id = uuid4()
    primeira = _conta(cliente_id)
    db.add(primeira)
    await db.flush()

    # Savepoint próprio: o erro aborta a transação, e sem ele a asserção
    # seguinte não teria banco para rodar.
    with pytest.raises(IntegrityError):
        async with db.begin_nested():
            db.add(_conta(cliente_id))
            await db.flush()

    # Recusa, não sobrescrita: a conta original continua de pé.
    sobreviventes = (await db.execute(
        select(ClienteAuth.id).where(ClienteAuth.cliente_id == cliente_id)
    )).scalars().all()
    assert sobreviventes == [primeira.id]


@pytest.mark.asyncio
async def test_clientes_diferentes_continuam_cabendo(db):
    """A constraint fecha a duplicata, não a loja: cada cliente tem a sua."""
    db.add(_conta(uuid4()))
    db.add(_conta(uuid4()))
    await db.flush()
