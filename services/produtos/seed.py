"""
Script para popular banco com dados de teste.
"""
import asyncio
from decimal import Decimal
from database import AsyncSessionLocal
from models.categoria import Categoria
from models.produto import Produto
from models.variante import Variante, AtributoVariante
from models.fornecedor import Fornecedor, FornecedorProduto
from models.loja_online import LojaOnlineConfig, LojaOnlineFoto


async def seed_data():
    """Popula banco com dados de teste."""
    async with AsyncSessionLocal() as session:
        try:
            print("🌱 Iniciando seed de dados de teste...")
            
            empresa_id = 1  # Empresa padrão para testes
            
            # ========== CATEGORIAS ==========
            print("  → Criando categorias...")
            cat_eletronicos = Categoria(
                empresa_id=empresa_id,
                nome="Eletrônicos",
                descricao="Produtos eletrônicos e tecnologia"
            )
            cat_vestuario = Categoria(
                empresa_id=empresa_id,
                nome="Vestuário",
                descricao="Roupas e acessórios"
            )
            cat_alimentos = Categoria(
                empresa_id=empresa_id,
                nome="Alimentos",
                descricao="Produtos alimentícios"
            )
            session.add_all([cat_eletronicos, cat_vestuario, cat_alimentos])
            await session.flush()
            
            # ========== PRODUTOS ==========
            print("  → Criando produtos...")
            prod_notebook = Produto(
                empresa_id=empresa_id,
                categoria_id=cat_eletronicos.id,
                nome="Notebook Dell Inspiron 15",
                descricao="Notebook com Intel i5, 8GB RAM, 256GB SSD",
                ativo=True
            )
            prod_mouse = Produto(
                empresa_id=empresa_id,
                categoria_id=cat_eletronicos.id,
                nome="Mouse Logitech MX Master 3",
                descricao="Mouse wireless ergonômico",
                ativo=True
            )
            prod_camiseta = Produto(
                empresa_id=empresa_id,
                categoria_id=cat_vestuario.id,
                nome="Camiseta Básica",
                descricao="Camiseta 100% algodão",
                ativo=True
            )
            session.add_all([prod_notebook, prod_mouse, prod_camiseta])
            await session.flush()
            
            # ========== VARIANTES ==========
            print("  → Criando variantes...")
            var_notebook = Variante(
                empresa_id=empresa_id,
                produto_id=prod_notebook.id,
                sku="DELL-INSP15-I5-8GB-256",
                preco_custo=Decimal("2500.00"),
                markup_pct=Decimal("40.00"),
                preco_venda=Decimal("3500.00"),
                ativo=True
            )
            var_mouse = Variante(
                empresa_id=empresa_id,
                produto_id=prod_mouse.id,
                sku="LOGI-MX3-BLACK",
                preco_custo=Decimal("250.00"),
                markup_pct=Decimal("50.00"),
                preco_venda=Decimal("375.00"),
                ativo=True
            )
            var_camiseta_p = Variante(
                empresa_id=empresa_id,
                produto_id=prod_camiseta.id,
                sku="CAM-BASIC-WHITE-P",
                preco_custo=Decimal("15.00"),
                markup_pct=Decimal("100.00"),
                preco_venda=Decimal("30.00"),
                ativo=True
            )
            var_camiseta_m = Variante(
                empresa_id=empresa_id,
                produto_id=prod_camiseta.id,
                sku="CAM-BASIC-WHITE-M",
                preco_custo=Decimal("15.00"),
                markup_pct=Decimal("100.00"),
                preco_venda=Decimal("30.00"),
                ativo=True
            )
            session.add_all([var_notebook, var_mouse, var_camiseta_p, var_camiseta_m])
            await session.flush()
            
            # ========== ATRIBUTOS VARIANTES ==========
            print("  → Criando atributos de variantes...")
            session.add_all([
                AtributoVariante(variante_id=var_camiseta_p.id, chave="tamanho", valor="P"),
                AtributoVariante(variante_id=var_camiseta_p.id, chave="cor", valor="Branco"),
                AtributoVariante(variante_id=var_camiseta_m.id, chave="tamanho", valor="M"),
                AtributoVariante(variante_id=var_camiseta_m.id, chave="cor", valor="Branco"),
            ])
            await session.flush()
            
            # ========== FORNECEDORES ==========
            print("  → Criando fornecedores...")
            forn_dell = Fornecedor(
                empresa_id=empresa_id,
                nome="Dell Computadores Brasil",
                cnpj="12.345.678/0001-90",
                email="vendas@dell.com.br",
                telefone="(11) 3000-1000",
                cidade="São Paulo",
                uf="SP",
                ativo=True
            )
            forn_logitech = Fornecedor(
                empresa_id=empresa_id,
                nome="Logitech do Brasil",
                cnpj="98.765.432/0001-10",
                email="contato@logitech.com.br",
                telefone="(11) 4000-2000",
                cidade="São Paulo",
                uf="SP",
                ativo=True
            )
            session.add_all([forn_dell, forn_logitech])
            await session.flush()
            
            # ========== FORNECEDOR PRODUTOS ==========
            print("  → Vinculando fornecedores a produtos...")
            session.add_all([
                FornecedorProduto(
                    fornecedor_id=forn_dell.id,
                    produto_id=prod_notebook.id,
                    codigo_fornecedor="DELL-INS15-2024",
                    preco_fornecedor=Decimal("2500.00"),
                    prazo_entrega_dias=5,
                    quantidade_minima=1,
                    ativo=True
                ),
                FornecedorProduto(
                    fornecedor_id=forn_logitech.id,
                    produto_id=prod_mouse.id,
                    codigo_fornecedor="MX3-BLK",
                    preco_fornecedor=Decimal("250.00"),
                    prazo_entrega_dias=3,
                    quantidade_minima=5,
                    ativo=True
                ),
            ])
            await session.flush()
            
            # ========== LOJA ONLINE CONFIG ==========
            print("  → Criando configurações de loja online...")
            session.add_all([
                LojaOnlineConfig(
                    produto_id=prod_notebook.id,
                    visivel=True,
                    destaque=True,
                    ordem_exibicao=1,
                    descricao_publica="Notebook potente para trabalho e estudos"
                ),
                LojaOnlineConfig(
                    produto_id=prod_mouse.id,
                    visivel=True,
                    destaque=False,
                    ordem_exibicao=2,
                    descricao_publica="Mouse ergonômico de alta precisão"
                ),
                LojaOnlineConfig(
                    produto_id=prod_camiseta.id,
                    visivel=True,
                    destaque=False,
                    ordem_exibicao=3,
                    descricao_publica="Camiseta básica confortável"
                ),
            ])
            await session.flush()
            
            # ========== LOJA ONLINE FOTOS ==========
            print("  → Adicionando fotos de loja online...")
            session.add_all([
                LojaOnlineFoto(
                    produto_id=prod_notebook.id,
                    url="https://picsum.photos/800/600?random=1",
                    ordem=1
                ),
                LojaOnlineFoto(
                    produto_id=prod_mouse.id,
                    url="https://picsum.photos/800/600?random=2",
                    ordem=1
                ),
            ])
            
            await session.commit()
            print("✅ Seed concluído com sucesso!")
            print(f"   • 3 categorias")
            print(f"   • 3 produtos")
            print(f"   • 4 variantes")
            print(f"   • 4 atributos")
            print(f"   • 2 fornecedores")
            print(f"   • 2 vínculos fornecedor-produto")
            print(f"   • 3 configurações de catálogo")
            print(f"   • 2 fotos de catálogo")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Erro ao executar seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())
