"""
Seed de estoque.

Cria um registro de estoque para cada produto/variante real cadastrado no serviço
de produtos, garantindo que a loja online consiga reservar estoque ao adicionar itens
ao carrinho.

Nota de arquitetura: o serviço de estoque não conhece os models de produtos, então os
IDs reais são lidos via query cross-schema (mesmo banco). É o mesmo padrão já usado pelo
serviço de produtos para resolver `empresas.empresas`. Restrito a scripts de seed/dev.
"""
import asyncio
from uuid import uuid4

from sqlalchemy import select, text

from database import AsyncSessionLocal
from models.estoque import Estoque

# Quantidade inicial padrão por produto (dev). Suficiente para validar o fluxo da loja.
QUANTIDADE_INICIAL = 100.0


async def seed_data():
    """Cria estoque para todos os produtos/variantes ativos existentes."""
    async with AsyncSessionLocal() as session:
        try:
            # IDs reais dos produtos/variantes (query cross-schema no mesmo banco).
            rows = (await session.execute(text("""
                SELECT p.id AS produto_id,
                       p.empresa_id AS empresa_id,
                       COALESCE(p.estoque_minimo, 0) AS estoque_minimo,
                       v.id AS variante_id
                FROM produtos.produtos p
                LEFT JOIN produtos.variantes v
                       ON v.produto_id = p.id AND v.ativo = TRUE
                WHERE p.ativo = TRUE AND p.deletado_em IS NULL
                ORDER BY p.empresa_id, p.id
            """))).mappings().all()

            if not rows:
                print("⚠️  Nenhum produto ativo encontrado. Rode o seed de produtos primeiro.")
                return

            # Chaves já existentes para tornar o seed idempotente.
            existentes = {
                (e.empresa_id, e.produto_id, e.variante_id)
                for e in (await session.execute(select(Estoque))).scalars().all()
            }

            criados = 0
            for row in rows:
                chave = (row["empresa_id"], row["produto_id"], row["variante_id"])
                if chave in existentes:
                    continue

                session.add(Estoque(
                    id=uuid4(),
                    empresa_id=row["empresa_id"],
                    produto_id=row["produto_id"],
                    variante_id=row["variante_id"],
                    quantidade=QUANTIDADE_INICIAL,
                    quantidade_reservada=0.0,
                    quantidade_disponivel=QUANTIDADE_INICIAL,
                    estoque_minimo=float(row["estoque_minimo"] or 0),
                    localizacao="Estoque Geral",
                    ativo=True,
                ))
                existentes.add(chave)
                criados += 1

            await session.commit()

            print(f"✓ {criados} registros de estoque criados ({len(rows)} produtos/variantes; "
                  f"{len(rows) - criados} já existiam).")

        except Exception as e:
            await session.rollback()
            print(f"✗ Erro ao inserir dados: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())
