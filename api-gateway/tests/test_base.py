"""O mínimo que todo serviço prova antes de qualquer teste de regra de negócio.

1. O app importa e responde. Sem isso, nenhum outro teste daqui diz nada.
2. O schema que as migrations constroem num banco vazio serve a todos os models.

O segundo é o que importa. O schema de prod veio de um create_all legado e foi
carimbado: ele reflete os models, não as migrations. Um model com uma coluna que
nenhuma revision cria funciona em prod e quebra no primeiro banco novo — um VPS
novo, um `docker-compose down -v`. Nada construía um banco pelas migrations, então
ninguém via.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError

import models  # noqa: F401 -- registra as tabelas no Base.metadata, como o alembic/env.py
from database import Base


@pytest.mark.asyncio
async def test_app_responde_health(client):
    resposta = await client.get("/health")

    assert resposta.status_code == 200, resposta.text


@pytest.mark.asyncio
async def test_schema_das_migrations_serve_aos_models(db):
    faltando = []
    for tabela in Base.metadata.sorted_tables:
        try:
            # Savepoint por tabela: um erro aborta a transação, e sem ele a
            # primeira tabela quebrada esconderia todas as seguintes.
            async with db.begin_nested():
                await db.execute(select(tabela).limit(0))
        except DBAPIError as erro:
            faltando.append(f"{tabela.fullname}: {str(erro.orig).splitlines()[0]}")

    assert not faltando, (
        "os models pedem o que as migrations não criam — num banco novo estas "
        f"queries quebram: {faltando}"
    )
