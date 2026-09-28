"""
Jobs de automação do serviço de vendas.

Agendados no lifespan de main.py, como loop asyncio dentro do próprio processo:
- verificar_pagamentos_pendentes.py - cancela pagamento online sem aprovação após 5 min (a cada 60s)
- reconciliar_estoque_vendas.py - refaz a baixa de estoque que ficou indeterminada (a cada 120s)

Existem, mas nada os agenda (só rodam à mão):
- limpar_reservas.py, limpar_carrinhos_abandonados.py, verificar_timeouts_separacao.py

Detalhes em README.md.
"""
