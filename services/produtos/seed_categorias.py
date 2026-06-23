"""
Seed de categorias de produtos.
"""
import asyncio
from sqlalchemy import select, func

from database import AsyncSessionLocal
from models.categoria import Categoria


async def seed_categorias():
    """Cria categorias de exemplo."""
    async with AsyncSessionLocal() as session:
        # Verificar se já existem categorias
        stmt = select(func.count()).select_from(Categoria).where(Categoria.empresa_id == 1)
        result = await session.execute(stmt)
        count = result.scalar_one()
        
        if count > 0:
            print(f"⚠️  Já existem {count} categorias para empresa_id=1. Pulando seed.")
            return
        
        print("🌱 Criando categorias de produtos...")
        
        categorias = [
            {
                "nome": "Alimentos",
                "descricao": "Alimentos em geral, secos e não perecíveis",
                "empresa_id": 1
            },
            {
                "nome": "Bebidas",
                "descricao": "Bebidas alcoólicas e não alcoólicas",
                "empresa_id": 1
            },
            {
                "nome": "Higiene e Limpeza",
                "descricao": "Produtos de higiene pessoal e limpeza doméstica",
                "empresa_id": 1
            },
            {
                "nome": "Mercearia",
                "descricao": "Arroz, feijão, massas, temperos",
                "empresa_id": 1
            },
            {
                "nome": "Frios e Laticínios",
                "descricao": "Queijos, presuntos, iogurtes, leites",
                "empresa_id": 1
            },
            {
                "nome": "Padaria",
                "descricao": "Pães, bolos, tortas e massas",
                "empresa_id": 1
            },
            {
                "nome": "Hortifruti",
                "descricao": "Frutas, verduras e legumes frescos",
                "empresa_id": 1
            },
            {
                "nome": "Açougue",
                "descricao": "Carnes bovinas, suínas, aves e peixes",
                "empresa_id": 1
            },
        ]
        
        for cat_data in categorias:
            categoria = Categoria(**cat_data)
            session.add(categoria)
        
        await session.commit()
        
        print(f"✅ {len(categorias)} categorias criadas com sucesso!")


async def main():
    """Função principal."""
    print("=" * 60)
    print("🌱 SEED - Categorias de Produtos")
    print("=" * 60)
    
    try:
        await seed_categorias()
        print("\n✅ Seed concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao executar seed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
