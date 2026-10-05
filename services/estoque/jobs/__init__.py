"""
Jobs de automação do serviço de estoque.

Agendado no lifespan de main.py, como loop asyncio dentro do próprio processo:
- marcar_lotes_vencidos.py - marca VENCIDO todo lote ATIVO com data_validade passada (a cada 1h)
"""
