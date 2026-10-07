"""
Seed de produtos.
"""
import asyncio
from decimal import Decimal
from sqlalchemy import select, func

from database import AsyncSessionLocal
from models.produto import Produto
from models.categoria import Categoria


async def seed_produtos():
    """Cria produtos de exemplo."""
    async with AsyncSessionLocal() as session:
        # Verificar se já existem produtos
        stmt = select(func.count()).select_from(Produto).where(Produto.empresa_id == 1)
        result = await session.execute(stmt)
        count = result.scalar_one()
        
        if count > 0:
            print(f"⚠️  Já existem {count} produtos para empresa_id=1. Pulando seed.")
            return
        
        print("🌱 Criando produtos...")
        
        # Buscar categorias
        stmt = select(Categoria).where(Categoria.empresa_id == 1)
        result = await session.execute(stmt)
        categorias = {cat.nome: cat.id for cat in result.scalars().all()}
        
        if not categorias:
            print("❌ Nenhuma categoria encontrada. Execute seed_categorias.py primeiro!")
            return
        
        produtos = [
            # Alimentos
            {"nome": "Arroz Tio João Tipo 1", "codigo_barras": "7891999000019", "preco": Decimal("22.90"), "custo": Decimal("18.50"), "categoria_id": categorias.get("Mercearia"), "estoque_minimo": 20, "empresa_id": 1},
            {"nome": "Feijão Preto Camil", "codigo_barras": "7896006700012", "preco": Decimal("8.90"), "custo": Decimal("6.50"), "categoria_id": categorias.get("Mercearia"), "estoque_minimo": 30, "empresa_id": 1},
            {"nome": "Macarrão Espaguete Barilla", "codigo_barras": "8076809513012", "preco": Decimal("6.50"), "custo": Decimal("4.80"), "categoria_id": categorias.get("Mercearia"), "estoque_minimo": 40, "empresa_id": 1},
            {"nome": "Óleo de Soja Liza 900ml", "codigo_barras": "7896036095010", "preco": Decimal("7.90"), "custo": Decimal("6.20"), "categoria_id": categorias.get("Alimentos"), "estoque_minimo": 25, "empresa_id": 1},
            {"nome": "Açúcar Cristal União 1kg", "codigo_barras": "7896098900413", "preco": Decimal("4.50"), "custo": Decimal("3.50"), "categoria_id": categorias.get("Mercearia"), "estoque_minimo": 35, "empresa_id": 1},
            
            # Bebidas
            {"nome": "Coca-Cola 2L", "codigo_barras": "7894900011012", "preco": Decimal("8.90"), "custo": Decimal("6.50"), "categoria_id": categorias.get("Bebidas"), "estoque_minimo": 50, "empresa_id": 1},
            {"nome": "Cerveja Skol Lata 350ml", "codigo_barras": "7891991010016", "preco": Decimal("3.50"), "custo": Decimal("2.80"), "categoria_id": categorias.get("Bebidas"), "estoque_minimo": 100, "empresa_id": 1},
            {"nome": "Suco Del Valle Laranja 1L", "codigo_barras": "7894900530018", "preco": Decimal("6.90"), "custo": Decimal("5.20"), "categoria_id": categorias.get("Bebidas"), "estoque_minimo": 30, "empresa_id": 1},
            {"nome": "Água Mineral Crystal 1,5L", "codigo_barras": "7896286604017", "preco": Decimal("2.50"), "custo": Decimal("1.80"), "categoria_id": categorias.get("Bebidas"), "estoque_minimo": 80, "empresa_id": 1},
            {"nome": "Guaraná Antarctica 2L", "codigo_barras": "7894900011111", "preco": Decimal("7.90"), "custo": Decimal("5.80"), "categoria_id": categorias.get("Bebidas"), "estoque_minimo": 40, "empresa_id": 1},
            
            # Higiene e Limpeza
            {"nome": "Sabão em Pó OMO 1kg", "codigo_barras": "7891150013018", "preco": Decimal("15.90"), "custo": Decimal("12.50"), "categoria_id": categorias.get("Higiene e Limpeza"), "estoque_minimo": 20, "empresa_id": 1},
            {"nome": "Detergente Ypê Neutro", "codigo_barras": "7896098900512", "preco": Decimal("2.50"), "custo": Decimal("1.80"), "categoria_id": categorias.get("Higiene e Limpeza"), "estoque_minimo": 50, "empresa_id": 1},
            {"nome": "Papel Higiênico Neve c/12", "codigo_barras": "7896183301019", "preco": Decimal("18.90"), "custo": Decimal("14.50"), "categoria_id": categorias.get("Higiene e Limpeza"), "estoque_minimo": 15, "empresa_id": 1},
            {"nome": "Sabonete Dove 90g", "codigo_barras": "7891150013117", "preco": Decimal("3.90"), "custo": Decimal("2.80"), "categoria_id": categorias.get("Higiene e Limpeza"), "estoque_minimo": 40, "empresa_id": 1},
            {"nome": "Água Sanitária Qboa 1L", "codigo_barras": "7896094918016", "preco": Decimal("3.50"), "custo": Decimal("2.50"), "categoria_id": categorias.get("Higiene e Limpeza"), "estoque_minimo": 30, "empresa_id": 1},
            
            # Frios e Laticínios
            {"nome": "Leite Integral Parmalat 1L", "codigo_barras": "7899080701012", "preco": Decimal("5.90"), "custo": Decimal("4.50"), "categoria_id": categorias.get("Frios e Laticínios"), "estoque_minimo": 30, "empresa_id": 1},
            {"nome": "Queijo Mussarela Tirolez", "codigo_barras": "7896030612015", "preco": Decimal("38.90"), "custo": Decimal("32.50"), "categoria_id": categorias.get("Frios e Laticínios"), "estoque_minimo": 10, "empresa_id": 1},
            {"nome": "Presunto Sadia Fatiado", "codigo_barras": "7897326600013", "preco": Decimal("25.90"), "custo": Decimal("21.50"), "categoria_id": categorias.get("Frios e Laticínios"), "estoque_minimo": 15, "empresa_id": 1},
            {"nome": "Iogurte Danone Morango", "codigo_barras": "7891025100119", "preco": Decimal("4.90"), "custo": Decimal("3.80"), "categoria_id": categorias.get("Frios e Laticínios"), "estoque_minimo": 40, "empresa_id": 1},
            {"nome": "Manteiga Aviação 200g", "codigo_barras": "7896286620017", "preco": Decimal("12.90"), "custo": Decimal("9.80"), "categoria_id": categorias.get("Frios e Laticínios"), "estoque_minimo": 20, "empresa_id": 1},
            
            # Padaria
            {"nome": "Pão Francês kg", "codigo_barras": "2000000000015", "preco": Decimal("18.90"), "custo": Decimal("12.50"), "categoria_id": categorias.get("Padaria"), "estoque_minimo": 0, "empresa_id": 1},
            {"nome": "Pão de Forma Pullman", "codigo_barras": "7896030502019", "preco": Decimal("8.90"), "custo": Decimal("6.50"), "categoria_id": categorias.get("Padaria"), "estoque_minimo": 20, "empresa_id": 1},
            {"nome": "Bolo de Chocolate Fatia", "codigo_barras": "2000000000022", "preco": Decimal("6.50"), "custo": Decimal("4.00"), "categoria_id": categorias.get("Padaria"), "estoque_minimo": 0, "empresa_id": 1},
            
            # Hortifruti
            {"nome": "Banana Prata kg", "codigo_barras": "2000000000039", "preco": Decimal("6.90"), "custo": Decimal("4.50"), "categoria_id": categorias.get("Hortifruti"), "estoque_minimo": 0, "empresa_id": 1},
            {"nome": "Tomate kg", "codigo_barras": "2000000000046", "preco": Decimal("7.90"), "custo": Decimal("5.50"), "categoria_id": categorias.get("Hortifruti"), "estoque_minimo": 0, "empresa_id": 1},
            {"nome": "Alface Crespa un", "codigo_barras": "2000000000053", "preco": Decimal("3.50"), "custo": Decimal("2.00"), "categoria_id": categorias.get("Hortifruti"), "estoque_minimo": 0, "empresa_id": 1},
            
            # Açougue
            {"nome": "Picanha kg", "codigo_barras": "2000000000060", "preco": Decimal("79.90"), "custo": Decimal("65.00"), "categoria_id": categorias.get("Açougue"), "estoque_minimo": 0, "empresa_id": 1},
            {"nome": "Frango Inteiro Congelado kg", "codigo_barras": "2000000000077", "preco": Decimal("12.90"), "custo": Decimal("9.50"), "categoria_id": categorias.get("Açougue"), "estoque_minimo": 0, "empresa_id": 1},
            {"nome": "Linguiça Toscana kg", "codigo_barras": "2000000000084", "preco": Decimal("24.90"), "custo": Decimal("19.50"), "categoria_id": categorias.get("Açougue"), "estoque_minimo": 0, "empresa_id": 1},
        ]
        
        for p in produtos:
            assert _dv_ean13_ok(p["codigo_barras"]), f"EAN com dígito verificador inválido: {p['codigo_barras']}"

        for prod_data in produtos:
            produto = Produto(**prod_data)
            session.add(produto)
        
        await session.commit()
        
        print(f"✅ {len(produtos)} produtos criados com sucesso!")


async def main():
    """Função principal."""
    print("=" * 60)
    print("🌱 SEED - Produtos")
    print("=" * 60)
    
    try:
        await seed_produtos()
        print("\n✅ Seed concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao executar seed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
