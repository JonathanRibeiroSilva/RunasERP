"""
Script para popular banco com dados de teste.
"""
import asyncio
from uuid import uuid4
from datetime import datetime, date, timedelta
from database import AsyncSessionLocal
from models.estoque import Estoque, Lote, Movimentacao, Inventario, ItemInventario, TipoMovimentacao, StatusLote


async def seed_data():
    """Popula banco com dados de teste."""
    async with AsyncSessionLocal() as session:
        try:
            # IDs de exemplo (assumindo que produtos existem no serviço de produtos)
            produto_id_1 = uuid4()
            produto_id_2 = uuid4()
            produto_id_3 = uuid4()
            variante_id_1 = uuid4()
            
            empresa_id = 1  # Empresa de teste
            
            print("Criando registros de estoque...")
            
            # ========== ESTOQUE ==========
            
            estoque_1 = Estoque(
                id=uuid4(),
                empresa_id=empresa_id,
                produto_id=produto_id_1,
                variante_id=None,
                quantidade=100.0,
                quantidade_reservada=10.0,
                quantidade_disponivel=90.0,
                estoque_minimo=20.0,
                estoque_maximo=200.0,
                localizacao="Prateleira A1",
                ativo=True
            )
            
            estoque_2 = Estoque(
                id=uuid4(),
                empresa_id=empresa_id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                quantidade=15.0,
                quantidade_reservada=5.0,
                quantidade_disponivel=10.0,
                estoque_minimo=30.0,  # Abaixo do mínimo
                estoque_maximo=100.0,
                localizacao="Prateleira B2",
                ativo=True
            )
            
            estoque_3 = Estoque(
                id=uuid4(),
                empresa_id=empresa_id,
                produto_id=produto_id_3,
                variante_id=None,
                quantidade=0.0,
                quantidade_reservada=0.0,
                quantidade_disponivel=0.0,
                estoque_minimo=10.0,  # Zerado
                estoque_maximo=50.0,
                localizacao="Prateleira C3",
                ativo=True
            )
            
            session.add_all([estoque_1, estoque_2, estoque_3])
            await session.flush()
            
            print(f"✓ 3 registros de estoque criados")
            
            # ========== LOTES ==========
            
            hoje = date.today()
            
            lote_1 = Lote(
                id=uuid4(),
                empresa_id=empresa_id,
                estoque_id=estoque_1.id,
                codigo="LOTE-2026-001",
                quantidade=50.0,
                quantidade_inicial=50.0,
                data_fabricacao=hoje - timedelta(days=30),
                data_validade=hoje + timedelta(days=60),  # Vence em 60 dias
                fornecedor="Fornecedor ABC Ltda",
                nota_fiscal="NF-12345",
                custo_unitario=10.50,
                status=StatusLote.ATIVO.value
            )
            
            lote_2 = Lote(
                id=uuid4(),
                empresa_id=empresa_id,
                estoque_id=estoque_1.id,
                codigo="LOTE-2026-002",
                quantidade=50.0,
                quantidade_inicial=50.0,
                data_fabricacao=hoje - timedelta(days=60),
                data_validade=hoje + timedelta(days=20),  # Vencendo (< 30 dias)
                fornecedor="Fornecedor ABC Ltda",
                nota_fiscal="NF-12346",
                custo_unitario=10.00,
                status=StatusLote.ATIVO.value
            )
            
            lote_3 = Lote(
                id=uuid4(),
                empresa_id=empresa_id,
                estoque_id=estoque_2.id,
                codigo="LOTE-2026-003",
                quantidade=15.0,
                quantidade_inicial=20.0,
                data_fabricacao=hoje - timedelta(days=10),
                data_validade=hoje + timedelta(days=90),
                fornecedor="Fornecedor XYZ S.A.",
                nota_fiscal="NF-67890",
                custo_unitario=25.00,
                status=StatusLote.ATIVO.value
            )
            
            session.add_all([lote_1, lote_2, lote_3])
            await session.flush()
            
            print(f"✓ 3 lotes criados")
            
            # ========== MOVIMENTAÇÕES ==========
            
            # Entrada estoque_1
            mov_1 = Movimentacao(
                id=uuid4(),
                estoque_id=estoque_1.id,
                lote_id=lote_1.id,
                tipo=TipoMovimentacao.ENTRADA.value,
                quantidade=50.0,
                quantidade_anterior=50.0,
                quantidade_posterior=100.0,
                motivo="Compra",
                observacao="Entrada inicial do lote 001",
                documento="NF-12345",
                custo_unitario=10.50,
                custo_total=525.00,
                created_at=datetime.utcnow() - timedelta(days=30)
            )
            
            # Entrada estoque_1 (lote 2)
            mov_2 = Movimentacao(
                id=uuid4(),
                estoque_id=estoque_1.id,
                lote_id=lote_2.id,
                tipo=TipoMovimentacao.ENTRADA.value,
                quantidade=50.0,
                quantidade_anterior=0.0,
                quantidade_posterior=50.0,
                motivo="Compra",
                observacao="Entrada inicial do lote 002",
                documento="NF-12346",
                custo_unitario=10.00,
                custo_total=500.00,
                created_at=datetime.utcnow() - timedelta(days=60)
            )
            
            # Saída estoque_2
            mov_3 = Movimentacao(
                id=uuid4(),
                estoque_id=estoque_2.id,
                lote_id=lote_3.id,
                tipo=TipoMovimentacao.SAIDA.value,
                quantidade=5.0,
                quantidade_anterior=20.0,
                quantidade_posterior=15.0,
                motivo="Venda",
                observacao="Venda para cliente",
                documento="PEDIDO-001",
                created_at=datetime.utcnow() - timedelta(days=5)
            )
            
            # Ajuste estoque_3
            mov_4 = Movimentacao(
                id=uuid4(),
                estoque_id=estoque_3.id,
                lote_id=None,
                tipo=TipoMovimentacao.AJUSTE.value,
                quantidade=10.0,
                quantidade_anterior=10.0,
                quantidade_posterior=0.0,
                motivo="Inventário",
                observacao="Ajuste após contagem física - perda identificada",
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            
            session.add_all([mov_1, mov_2, mov_3, mov_4])
            await session.flush()
            
            print(f"✓ 4 movimentações criadas")
            
            # ========== INVENTÁRIO ==========
            
            inventario = Inventario(
                id=uuid4(),
                empresa_id=empresa_id,
                data_inventario=datetime.utcnow() - timedelta(days=2),
                responsavel="João Silva",
                observacao="Inventário mensal - Janeiro 2026",
                finalizado=True,
                data_finalizacao=datetime.utcnow() - timedelta(days=2, hours=2)
            )
            
            session.add(inventario)
            await session.flush()
            
            # Itens do inventário
            item_inv_1 = ItemInventario(
                id=uuid4(),
                inventario_id=inventario.id,
                estoque_id=estoque_1.id,
                quantidade_sistema=100.0,
                quantidade_contada=100.0,
                diferenca=0.0,
                observacao="Conferido - OK",
                ajustado=False
            )
            
            item_inv_2 = ItemInventario(
                id=uuid4(),
                inventario_id=inventario.id,
                estoque_id=estoque_2.id,
                quantidade_sistema=20.0,
                quantidade_contada=15.0,
                diferenca=-5.0,
                observacao="Diferença encontrada - ajuste necessário",
                ajustado=True
            )
            
            item_inv_3 = ItemInventario(
                id=uuid4(),
                inventario_id=inventario.id,
                estoque_id=estoque_3.id,
                quantidade_sistema=10.0,
                quantidade_contada=0.0,
                diferenca=-10.0,
                observacao="Perda total do estoque",
                ajustado=True
            )
            
            session.add_all([item_inv_1, item_inv_2, item_inv_3])
            
            print(f"✓ 1 inventário criado com 3 itens")
            
            # Commit
            await session.commit()
            
            print("\n" + "="*50)
            print("✓ Dados de teste inseridos com sucesso!")
            print("="*50)
            print(f"\nResumo:")
            print(f"  - Empresa ID: {empresa_id}")
            print(f"  - 3 Estoques (1 normal, 1 abaixo mínimo, 1 zerado)")
            print(f"  - 3 Lotes (1 normal, 1 vencendo, 1 recente)")
            print(f"  - 4 Movimentações (2 entradas, 1 saída, 1 ajuste)")
            print(f"  - 1 Inventário com 3 itens")
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Erro ao inserir dados: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())
