"""
Script para popular banco com dados de teste.
"""
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from database import AsyncSessionLocal
from models.venda import (
    Venda,
    ItemVenda,
    PagamentoVenda,
    ReservaEstoqueVenda,
    StatusVenda,
    TipoEntrega,
    TipoDesconto,
    FormaPagamento,
    StatusReserva
)


async def seed_data():
    """Popula banco com dados de teste."""
    async with AsyncSessionLocal() as session:
        try:
            # IDs de exemplo (assumindo que existem nos outros serviços)
            empresa_id = 1
            cliente_id_1 = uuid4()
            cliente_id_2 = uuid4()
            produto_id_1 = uuid4()
            produto_id_2 = uuid4()
            produto_id_3 = uuid4()
            variante_id_1 = uuid4()
            
            hoje = datetime.utcnow()
            
            print("Criando vendas de teste...")
            
            # ========== VENDA 1: Pedido Pendente (só criado, sem pagamento) ==========
            
            venda_1 = Venda(
                id=uuid4(),
                empresa_id=empresa_id,
                numero_venda="V-2026-1-00001",
                cliente_id=None,  # Venda balcão sem cliente
                subtotal=Decimal('85.50'),
                desconto_tipo=None,
                desconto_valor=Decimal('0.00'),
                valor_total=Decimal('85.50'),
                status=StatusVenda.PEDIDO.value,
                tipo_entrega=TipoEntrega.RETIRADA.value,
                observacao="Venda balcão - Cliente sem cadastro",
                data_pedido=hoje - timedelta(hours=2)
            )
            session.add(venda_1)
            await session.flush()
            
            # Itens venda 1
            item_1_1 = ItemVenda(
                id=uuid4(),
                venda_id=venda_1.id,
                produto_id=produto_id_1,
                variante_id=None,
                codigo_produto="PROD-001",
                descricao_produto="Refrigerante 2L",
                quantidade=Decimal('3.000'),
                preco_unitario=Decimal('8.50'),
                subtotal=Decimal('25.50'),
                estoque_reservado=True,
                estoque_baixado=False
            )
            
            item_1_2 = ItemVenda(
                id=uuid4(),
                venda_id=venda_1.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                codigo_produto="PROD-002-V1",
                descricao_produto="Cerveja Lata 350ml",
                quantidade=Decimal('12.000'),
                preco_unitario=Decimal('5.00'),
                subtotal=Decimal('60.00'),
                estoque_reservado=True,
                estoque_baixado=False
            )
            
            session.add_all([item_1_1, item_1_2])
            await session.flush()
            
            # Reservas venda 1
            reserva_1_1 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_1.id,
                item_venda_id=item_1_1.id,
                produto_id=produto_id_1,
                variante_id=None,
                quantidade_reservada=Decimal('3.000'),
                status=StatusReserva.RESERVADA.value,
                reservada_em=hoje - timedelta(hours=2)
            )
            
            reserva_1_2 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_1.id,
                item_venda_id=item_1_2.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                quantidade_reservada=Decimal('12.000'),
                status=StatusReserva.RESERVADA.value,
                reservada_em=hoje - timedelta(hours=2)
            )
            
            session.add_all([reserva_1_1, reserva_1_2])
            
            print(f"✓ Venda 1 criada: {venda_1.numero_venda} (PEDIDO)")
            
            # ========== VENDA 2: Confirmada com Pagamento Dinheiro ==========
            
            venda_2 = Venda(
                id=uuid4(),
                empresa_id=empresa_id,
                numero_venda="V-2026-1-00002",
                cliente_id=cliente_id_1,
                subtotal=Decimal('150.00'),
                desconto_tipo=TipoDesconto.PERCENTUAL.value,
                desconto_valor=Decimal('10.00'),  # 10%
                valor_total=Decimal('135.00'),  # 150 - 15
                status=StatusVenda.CONFIRMADA.value,
                tipo_entrega=TipoEntrega.DELIVERY.value,
                observacao="Cliente solicitou entrega urgente",
                data_pedido=hoje - timedelta(hours=5),
                data_confirmacao=hoje - timedelta(hours=4, minutes=30)
            )
            session.add(venda_2)
            await session.flush()
            
            # Itens venda 2
            item_2_1 = ItemVenda(
                id=uuid4(),
                venda_id=venda_2.id,
                produto_id=produto_id_3,
                variante_id=None,
                codigo_produto="PROD-003",
                descricao_produto="Carvão 5kg",
                quantidade=Decimal('3.000'),
                preco_unitario=Decimal('50.00'),
                subtotal=Decimal('150.00'),
                estoque_reservado=True,
                estoque_baixado=False
            )
            session.add(item_2_1)
            await session.flush()
            
            # Pagamento venda 2 (Dinheiro com troco)
            pag_2_1 = PagamentoVenda(
                id=uuid4(),
                venda_id=venda_2.id,
                forma_pagamento=FormaPagamento.DINHEIRO.value,
                valor_pago=Decimal('135.00'),
                valor_recebido=Decimal('200.00'),
                valor_troco=Decimal('65.00'),
                gera_conta_receber=False,
                data_pagamento=hoje - timedelta(hours=4, minutes=30)
            )
            session.add(pag_2_1)
            
            # Reserva venda 2
            reserva_2_1 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_2.id,
                item_venda_id=item_2_1.id,
                produto_id=produto_id_3,
                variante_id=None,
                quantidade_reservada=Decimal('3.000'),
                status=StatusReserva.RESERVADA.value,
                reservada_em=hoje - timedelta(hours=5)
            )
            session.add(reserva_2_1)
            
            print(f"✓ Venda 2 criada: {venda_2.numero_venda} (CONFIRMADA)")
            
            # ========== VENDA 3: Separada ==========
            
            venda_3 = Venda(
                id=uuid4(),
                empresa_id=empresa_id,
                numero_venda="V-2026-1-00003",
                cliente_id=cliente_id_2,
                subtotal=Decimal('250.00'),
                desconto_tipo=TipoDesconto.VALOR_FIXO.value,
                desconto_valor=Decimal('20.00'),
                valor_total=Decimal('230.00'),
                status=StatusVenda.SEPARADA.value,
                tipo_entrega=TipoEntrega.RETIRADA.value,
                observacao="Cliente vai retirar hoje à tarde",
                data_pedido=hoje - timedelta(days=1),
                data_confirmacao=hoje - timedelta(days=1, hours=-1),
                data_separacao=hoje - timedelta(hours=2)
            )
            session.add(venda_3)
            await session.flush()
            
            # Itens venda 3
            item_3_1 = ItemVenda(
                id=uuid4(),
                venda_id=venda_3.id,
                produto_id=produto_id_1,
                variante_id=None,
                codigo_produto="PROD-001",
                descricao_produto="Refrigerante 2L",
                quantidade=Decimal('10.000'),
                preco_unitario=Decimal('8.50'),
                subtotal=Decimal('85.00'),
                estoque_reservado=True,
                estoque_baixado=False
            )
            
            item_3_2 = ItemVenda(
                id=uuid4(),
                venda_id=venda_3.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                codigo_produto="PROD-002-V1",
                descricao_produto="Cerveja Lata 350ml",
                quantidade=Decimal('33.000'),
                preco_unitario=Decimal('5.00'),
                subtotal=Decimal('165.00'),
                estoque_reservado=True,
                estoque_baixado=False
            )
            
            session.add_all([item_3_1, item_3_2])
            await session.flush()
            
            # Pagamento venda 3 (PIX)
            pag_3_1 = PagamentoVenda(
                id=uuid4(),
                venda_id=venda_3.id,
                forma_pagamento=FormaPagamento.PIX.value,
                valor_pago=Decimal('230.00'),
                comprovante="PIX123456789",
                gera_conta_receber=False,
                data_pagamento=hoje - timedelta(days=1, hours=-1)
            )
            session.add(pag_3_1)
            
            # Reservas venda 3
            reserva_3_1 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_3.id,
                item_venda_id=item_3_1.id,
                produto_id=produto_id_1,
                variante_id=None,
                quantidade_reservada=Decimal('10.000'),
                status=StatusReserva.RESERVADA.value,
                reservada_em=hoje - timedelta(days=1)
            )
            
            reserva_3_2 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_3.id,
                item_venda_id=item_3_2.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                quantidade_reservada=Decimal('33.000'),
                status=StatusReserva.RESERVADA.value,
                reservada_em=hoje - timedelta(days=1)
            )
            
            session.add_all([reserva_3_1, reserva_3_2])
            
            print(f"✓ Venda 3 criada: {venda_3.numero_venda} (SEPARADA)")
            
            # ========== VENDA 4: Entregue (estoque baixado) ==========
            
            venda_4 = Venda(
                id=uuid4(),
                empresa_id=empresa_id,
                numero_venda="V-2026-1-00004",
                cliente_id=None,
                subtotal=Decimal('42.50'),
                desconto_tipo=None,
                desconto_valor=Decimal('0.00'),
                valor_total=Decimal('42.50'),
                status=StatusVenda.ENTREGUE.value,
                tipo_entrega=TipoEntrega.RETIRADA.value,
                data_pedido=hoje - timedelta(days=2),
                data_confirmacao=hoje - timedelta(days=2, hours=-1),
                data_separacao=hoje - timedelta(days=2, hours=-2),
                data_entregue=hoje - timedelta(days=2, hours=-3)
            )
            session.add(venda_4)
            await session.flush()
            
            # Itens venda 4
            item_4_1 = ItemVenda(
                id=uuid4(),
                venda_id=venda_4.id,
                produto_id=produto_id_1,
                variante_id=None,
                codigo_produto="PROD-001",
                descricao_produto="Refrigerante 2L",
                quantidade=Decimal('5.000'),
                preco_unitario=Decimal('8.50'),
                subtotal=Decimal('42.50'),
                estoque_reservado=True,
                estoque_baixado=True  # JÁ BAIXADO
            )
            session.add(item_4_1)
            await session.flush()
            
            # Pagamento venda 4 (Cartão Débito)
            pag_4_1 = PagamentoVenda(
                id=uuid4(),
                venda_id=venda_4.id,
                forma_pagamento=FormaPagamento.DEBITO.value,
                valor_pago=Decimal('42.50'),
                comprovante="DEBITO987654321",
                gera_conta_receber=False,
                data_pagamento=hoje - timedelta(days=2, hours=-1)
            )
            session.add(pag_4_1)
            
            # Reserva venda 4 (BAIXADA)
            reserva_4_1 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_4.id,
                item_venda_id=item_4_1.id,
                produto_id=produto_id_1,
                variante_id=None,
                quantidade_reservada=Decimal('5.000'),
                status=StatusReserva.BAIXADA.value,
                reservada_em=hoje - timedelta(days=2),
                baixada_em=hoje - timedelta(days=2, hours=-3)
            )
            session.add(reserva_4_1)
            
            print(f"✓ Venda 4 criada: {venda_4.numero_venda} (ENTREGUE)")
            
            # ========== VENDA 5: Finalizada com Fiado ==========
            
            venda_5 = Venda(
                id=uuid4(),
                empresa_id=empresa_id,
                numero_venda="V-2026-1-00005",
                cliente_id=cliente_id_1,
                subtotal=Decimal('320.00'),
                desconto_tipo=TipoDesconto.PERCENTUAL.value,
                desconto_valor=Decimal('5.00'),  # 5%
                valor_total=Decimal('304.00'),
                status=StatusVenda.FINALIZADA.value,
                tipo_entrega=TipoEntrega.DELIVERY.value,
                observacao="Cliente preferencial - Fiado aprovado",
                data_pedido=hoje - timedelta(days=3),
                data_confirmacao=hoje - timedelta(days=3, hours=-1),
                data_separacao=hoje - timedelta(days=3, hours=-2),
                data_entregue=hoje - timedelta(days=3, hours=-3),
                data_finalizada=hoje - timedelta(days=3, hours=-4)
            )
            session.add(venda_5)
            await session.flush()
            
            # Itens venda 5
            item_5_1 = ItemVenda(
                id=uuid4(),
                venda_id=venda_5.id,
                produto_id=produto_id_3,
                variante_id=None,
                codigo_produto="PROD-003",
                descricao_produto="Carvão 5kg",
                quantidade=Decimal('4.000'),
                preco_unitario=Decimal('50.00'),
                subtotal=Decimal('200.00'),
                estoque_reservado=True,
                estoque_baixado=True
            )
            
            item_5_2 = ItemVenda(
                id=uuid4(),
                venda_id=venda_5.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                codigo_produto="PROD-002-V1",
                descricao_produto="Cerveja Lata 350ml",
                quantidade=Decimal('24.000'),
                preco_unitario=Decimal('5.00'),
                subtotal=Decimal('120.00'),
                estoque_reservado=True,
                estoque_baixado=True
            )
            
            session.add_all([item_5_1, item_5_2])
            await session.flush()
            
            # Pagamento venda 5 (Parcial Dinheiro + FIADO)
            pag_5_1 = PagamentoVenda(
                id=uuid4(),
                venda_id=venda_5.id,
                forma_pagamento=FormaPagamento.DINHEIRO.value,
                valor_pago=Decimal('100.00'),
                valor_recebido=Decimal('100.00'),
                valor_troco=Decimal('0.00'),
                gera_conta_receber=False,
                data_pagamento=hoje - timedelta(days=3, hours=-1)
            )
            
            pag_5_2 = PagamentoVenda(
                id=uuid4(),
                venda_id=venda_5.id,
                forma_pagamento=FormaPagamento.FIADO.value,
                valor_pago=Decimal('204.00'),
                gera_conta_receber=True,
                data_pagamento=hoje - timedelta(days=3, hours=-1)
            )
            
            session.add_all([pag_5_1, pag_5_2])
            
            # Reservas venda 5 (BAIXADAS)
            reserva_5_1 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_5.id,
                item_venda_id=item_5_1.id,
                produto_id=produto_id_3,
                variante_id=None,
                quantidade_reservada=Decimal('4.000'),
                status=StatusReserva.BAIXADA.value,
                reservada_em=hoje - timedelta(days=3),
                baixada_em=hoje - timedelta(days=3, hours=-3)
            )
            
            reserva_5_2 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_5.id,
                item_venda_id=item_5_2.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                quantidade_reservada=Decimal('24.000'),
                status=StatusReserva.BAIXADA.value,
                reservada_em=hoje - timedelta(days=3),
                baixada_em=hoje - timedelta(days=3, hours=-3)
            )
            
            session.add_all([reserva_5_1, reserva_5_2])
            
            print(f"✓ Venda 5 criada: {venda_5.numero_venda} (FINALIZADA)")
            
            # ========== VENDA 6: Cancelada ==========
            
            venda_6 = Venda(
                id=uuid4(),
                empresa_id=empresa_id,
                numero_venda="V-2026-1-00006",
                cliente_id=None,
                subtotal=Decimal('170.00'),
                desconto_tipo=None,
                desconto_valor=Decimal('0.00'),
                valor_total=Decimal('170.00'),
                status=StatusVenda.CANCELADA.value,
                tipo_entrega=TipoEntrega.RETIRADA.value,
                observacao="Cliente desistiu da compra",
                motivo_cancelamento="Cliente solicitou cancelamento - produto não disponível na cor desejada",
                data_pedido=hoje - timedelta(hours=10),
                data_cancelada=hoje - timedelta(hours=9)
            )
            session.add(venda_6)
            await session.flush()
            
            # Itens venda 6
            item_6_1 = ItemVenda(
                id=uuid4(),
                venda_id=venda_6.id,
                produto_id=produto_id_3,
                variante_id=None,
                codigo_produto="PROD-003",
                descricao_produto="Carvão 5kg",
                quantidade=Decimal('2.000'),
                preco_unitario=Decimal('50.00'),
                subtotal=Decimal('100.00'),
                estoque_reservado=False,  # Reserva foi liberada
                estoque_baixado=False
            )
            
            item_6_2 = ItemVenda(
                id=uuid4(),
                venda_id=venda_6.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                codigo_produto="PROD-002-V1",
                descricao_produto="Cerveja Lata 350ml",
                quantidade=Decimal('14.000'),
                preco_unitario=Decimal('5.00'),
                subtotal=Decimal('70.00'),
                estoque_reservado=False,
                estoque_baixado=False
            )
            
            session.add_all([item_6_1, item_6_2])
            await session.flush()
            
            # Reservas venda 6 (LIBERADAS)
            reserva_6_1 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_6.id,
                item_venda_id=item_6_1.id,
                produto_id=produto_id_3,
                variante_id=None,
                quantidade_reservada=Decimal('2.000'),
                status=StatusReserva.LIBERADA.value,
                reservada_em=hoje - timedelta(hours=10),
                liberada_em=hoje - timedelta(hours=9)
            )
            
            reserva_6_2 = ReservaEstoqueVenda(
                id=uuid4(),
                venda_id=venda_6.id,
                item_venda_id=item_6_2.id,
                produto_id=produto_id_2,
                variante_id=variante_id_1,
                quantidade_reservada=Decimal('14.000'),
                status=StatusReserva.LIBERADA.value,
                reservada_em=hoje - timedelta(hours=10),
                liberada_em=hoje - timedelta(hours=9)
            )
            
            session.add_all([reserva_6_1, reserva_6_2])
            
            print(f"✓ Venda 6 criada: {venda_6.numero_venda} (CANCELADA)")
            
            # Commit
            await session.commit()
            
            print("\n" + "="*60)
            print("✓ Dados de teste inseridos com sucesso!")
            print("="*60)
            print(f"\nResumo:")
            print(f"  - Empresa ID: {empresa_id}")
            print(f"  - 6 Vendas criadas:")
            print(f"    • 1 PEDIDO (aguardando confirmação)")
            print(f"    • 1 CONFIRMADA (paga, aguardando separação)")
            print(f"    • 1 SEPARADA (aguardando entrega)")
            print(f"    • 1 ENTREGUE (estoque baixado)")
            print(f"    • 1 FINALIZADA (com fiado)")
            print(f"    • 1 CANCELADA (reservas liberadas)")
            print(f"\n  - Total de 11 itens")
            print(f"  - 7 pagamentos (Dinheiro, PIX, Débito, Fiado)")
            print(f"  - 11 reservas de estoque")
            print(f"\n  - Formas de pagamento testadas: Dinheiro, PIX, Débito, Fiado")
            print(f"  - Tipos de entrega: Retirada e Delivery")
            print(f"  - Descontos: Percentual e Valor Fixo")
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Erro ao inserir dados: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_data())
