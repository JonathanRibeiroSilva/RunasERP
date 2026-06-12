"""
Seed de variantes para produtos existentes.
Cria uma variante padrão para cada produto que não tem variantes.
"""
import asyncio
from decimal import Decimal
from sqlalchemy import select

from database import AsyncSessionLocal
from models.produto import Produto
from models.variante import Variante


async def seed_variantes():
    """Cria variantes padrão para produtos sem variantes."""
    async with AsyncSessionLocal() as session:
        print("🔍 Buscando produtos sem variantes...")
        
        # Buscar produtos que não têm variantes
        stmt = select(Produto).where(Produto.empresa_id == 4, Produto.deletado_em == None)
        result = await session.execute(stmt)
        produtos = result.scalars().all()
        
        produtos_sem_variantes = []
        
        for produto in produtos:
            # Verificar se produto já tem variantes
            stmt_var = select(Variante).where(Variante.produto_id == produto.id)
            result_var = await session.execute(stmt_var)
            variantes_existentes = result_var.scalars().all()
            
            if not variantes_existentes:
                produtos_sem_variantes.append(produto)
        
        if not produtos_sem_variantes:
            print("✅ Todos os produtos já possuem variantes!")
            return
        
        print(f"📦 Criando variantes para {len(produtos_sem_variantes)} produtos...")
        
        for produto in produtos_sem_variantes:
            # Gerar SKU baseado no código de barras ou ID
            sku = produto.codigo_barras if produto.codigo_barras else f"SKU-{str(produto.id)[:8]}"
            
            # Usar preços do produto (se existirem) ou valores padrão
            preco_custo = produto.custo if hasattr(produto, 'custo') and produto.custo else Decimal("10.00")
            preco_venda = produto.preco if hasattr(produto, 'preco') and produto.preco else Decimal("15.00")
            
            # Calcular markup
            if preco_custo > 0:
                markup_pct = ((preco_venda - preco_custo) / preco_custo * 100).quantize(Decimal("0.01"))
            else:
                markup_pct = Decimal("50.00")
            
            # Criar variante padrão
            variante = Variante(
                empresa_id=produto.empresa_id,
                produto_id=produto.id,
                sku=sku,
                preco_custo=preco_custo,
                markup_pct=markup_pct,
                preco_venda=preco_venda,
                ativo=True
            )
            
            session.add(variante)
            print(f"  ✓ {produto.nome} - SKU: {sku} - R$ {preco_venda}")
        
        await session.commit()
        
        print(f"\n✅ {len(produtos_sem_variantes)} variantes criadas com sucesso!")


async def main():
    """Função principal."""
    print("=" * 60)
    print("🌱 SEED - Variantes de Produtos")
    print("=" * 60)
    
    try:
        await seed_variantes()
        print("\n✅ Seed concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao executar seed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
