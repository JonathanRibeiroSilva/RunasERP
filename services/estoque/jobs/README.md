# Jobs de Automação - Serviço de Estoque

Um job, agendado como loop `asyncio` dentro do próprio processo do estoque, no
`lifespan` de `services/estoque/main.py`, pelo mesmo `_loop_periodico` usado em
`services/vendas/main.py`.

| Job | Função | Intervalo | Constante (`main.py`) |
|---|---|---|---|
| `marcar_lotes_vencidos.py` | `marcar_lotes_vencidos()` | 3600s (1h) | `MARCAR_VENCIDOS_INTERVALO_SEGUNDOS` |

### `marcar_lotes_vencidos.py`
**Propósito**: marcar `VENCIDO` todo lote `ATIVO` com `data_validade` no passado. `LoteRepository.marcar_vencidos` existia desde antes deste job e não tinha nenhum chamador — um lote vencido ficava `ATIVO` para sempre.

**Cross-tenant de propósito**: o job roda sem contexto de request, sem um `empresa_id` "do pedido". `LoteRepository.empresas_com_lote_vencido` faz uma query sem filtro de tenant para achar quem tem lote vencido; o job então chama `marcar_vencidos` (tenant-scoped, como o resto do repository) uma vez por empresa encontrada, comitando cada uma isoladamente — uma falha numa empresa não derruba as outras.

**Log final**: `job_marcar_lotes_vencidos_concluido`, com `empresas` e `lotes_marcados`.
