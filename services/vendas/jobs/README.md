# Jobs de Automação - Serviço de Vendas

Este diretório tem cinco scripts de job. **Só dois rodam de fato.** Eles são agendados como loops `asyncio` dentro do próprio processo do vendas. Os outros três existem, mas nada os agenda.

Não há Celery, cron, Supervisor nem Task Scheduler configurado no repositório. O `celery` aparece em `requirements.txt`, mas nenhum arquivo `.py` o importa.

---

## ⏱️ Jobs agendados (rodam sozinhos)

Os dois são iniciados no `lifespan` de `services/vendas/main.py` (linhas 47-71) por `_loop_periodico` (linhas 37-44). O loop executa o job, registra `loop_periodico_erro` se ele lançar exceção e dorme o intervalo. O intervalo, portanto, conta a partir do **fim** de cada execução. Cada réplica do vendas roda os seus próprios loops. Os dois jobs usam lock de linha (`FOR UPDATE SKIP LOCKED`) para não processar a mesma venda em paralelo.

| Job | Função | Intervalo | Constante (`main.py`) |
|---|---|---|---|
| `verificar_pagamentos_pendentes.py` | `verificar_pagamentos_pendentes()` | 60s | `PAGAMENTOS_PENDENTES_INTERVALO_SEGUNDOS` (linha 33) |
| `reconciliar_estoque_vendas.py` | `reconciliar_estoque_vendas()` | 120s | `RECONCILIACAO_ESTOQUE_INTERVALO_SEGUNDOS` (linha 34) |

### 1. `verificar_pagamentos_pendentes.py`
**Propósito**: cancelar vendas de pagamento online que passaram do prazo sem pagamento aprovado.

**Candidatas**: vendas `PENDENTE_PAGAMENTO` com `mercadopago_preference_id` preenchido e `data_pedido` mais antiga que `TIMEOUT_PAGAMENTO`. O prazo é de 5 minutos (`services/mercadopago_service.py:24`), o mesmo usado em `expiration_date_to` da preferência do Mercado Pago.

**Para cada candidata**, sob lock:
- relê o status e o prazo; se a venda já foi resolvida, pula;
- revalida no Mercado Pago. Se há pagamento aprovado, **confirma** a venda em vez de cancelar. Se o Mercado Pago está indisponível, **adia** para a próxima rodada;
- sem pagamento aprovado: libera as reservas de estoque, marca a venda como `CANCELADA`, registra o histórico, restaura o carrinho no Redis (best-effort) e envia o WhatsApp de cancelamento se houver `cliente_convidado_telefone`. A chamada não passa `empresa_id`, então só a credencial global da Evolution é tentada (ver [evolution-api.md](../../../docs/04-backend/integracao/evolution-api.md)).

**Log final**: `job_verificar_pagamentos_pendentes_concluido`, com `candidatos` e `resultados`. `resultados` conta rótulos como `cancelada`, `ja_resolvida`, `ainda_no_prazo`, `ignorada_lock`, `revalidacao_indisponivel`, `confirmada_na_revalidacao`, `reconciliacao_pendente`, `cancelada_sem_estoque_na_revalidacao` e `erro`.

### 2. `reconciliar_estoque_vendas.py`
**Propósito**: resolver vendas pagas cuja baixa de estoque terminou com resultado indeterminado (timeout ou erro ao falar com o serviço de estoque).

**Candidatas**: vendas com `reconciliacao_estoque_pendente = true` e `mercadopago_payment_id` preenchido.

**Para cada candidata**, sob lock: busca os detalhes do pagamento no Mercado Pago e reexecuta `VendaService.confirmar_venda`, cuja baixa de estoque é idempotente. Os resultados possíveis são:
- `confirmada`;
- `cancelada_sem_estoque`: estoque insuficiente; `confirmar_venda` cancela e registra o reembolso necessário;
- `ainda_indeterminada`: a venda continua marcada para a próxima rodada.

Também aparecem na contagem `ignorada_lock` (outra instância segura a linha), `ja_reconciliada` (a flag já foi limpa) e `erro`.

**Log final**: `job_reconciliar_estoque_concluido`, com `candidatos` e `resultados`.

---

## 💤 Scripts que existem mas nada agenda

Nenhum arquivo versionado importa ou chama estes scripts; `main.py` importa só os dois jobs acima. Eles só rodam se alguém executar à mão.

### 3. `limpar_reservas.py`
Apaga do banco as `ReservaTemporaria` com `expira_em <= agora`, via `ReservaTemporariaService.limpar_expiradas`. As reservas do carrinho duram 15 minutos (`RESERVA_TTL_MINUTOS`, `services/reserva_temporaria_service.py:30`). Sem o job, as reservas vencidas se acumulam na tabela, mas não seguram estoque: `calcular_disponivel` já soma só as que têm `expira_em > agora`.

Log: `job_limpar_reservas_concluido`, com `reservas_removidas`.

### 4. `limpar_carrinhos_abandonados.py`
Varre as chaves `carrinho:*` do Redis e apaga as que têm `atualizado_em` com mais de 7 dias, ou que não têm data ou têm data inválida. As chaves de carrinho já são gravadas com TTL de 7 dias, renovado a cada gravação (`CARRINHO_TTL = 604800`, `services/carrinho_service.py:38`). Por isso o Redis já expira os carrinhos sozinho, mesmo sem o job.

Log: `job_limpar_carrinhos_concluido`, com `carrinhos_verificados` e `carrinhos_removidos`.

### 5. `verificar_timeouts_separacao.py`
Para vendas `CONFIRMADA` com `data_confirmacao`:
- **≥ 12h**: log `alerta_separacao_12h`;
- **≥ 24h**: log `alerta_separacao_24h` (a notificação interna é só um `TODO`, na linha 142);
- **≥ 48h**: muda para `CANCELADA`, registra o histórico e envia o WhatsApp de cancelamento se houver `cliente_convidado_telefone`, também sem `empresa_id`. **Não** libera nem devolve estoque e não trata reembolso.

Log: `job_verificar_timeouts_concluido`, com `vendas_verificadas`, `alertas_12h`, `alertas_24h` e `canceladas_48h`.

---

## ▶️ Execução manual

Todos os scripts têm um bloco `__main__` e ajustam o `sys.path` sozinhos. Rode a partir de `services/vendas/` (no container, o `WORKDIR` é `/app`):

```bash
# Dentro do container de dev (serviço "vendas", container erp-vendas-dev)
docker compose -f docker-compose.dev.yml exec vendas python jobs/limpar_reservas.py
docker compose -f docker-compose.dev.yml exec vendas python jobs/limpar_carrinhos_abandonados.py
docker compose -f docker-compose.dev.yml exec vendas python jobs/verificar_timeouts_separacao.py

# Fora do container, a partir de services/vendas/
python jobs/limpar_reservas.py
```

Fora do container, o `Settings` (`config.py`) exige `DATABASE_URL`, `RABBITMQ_URL`, `REDIS_URL` e `SECRET_KEY` no ambiente ou num `.env` no diretório de trabalho.

Os dois jobs agendados também podem ser rodados assim (`python jobs/verificar_pagamentos_pendentes.py`, `python jobs/reconciliar_estoque_vendas.py`), mas não há necessidade: o serviço já os executa.

Atenção: `verificar_timeouts_separacao.py` cancela de verdade vendas confirmadas (pagas) há 48h ou mais. Não rode em produção sem decidir antes o que fazer com estoque e reembolso.

---

## 🔧 Troubleshooting

- **Os loops não estão rodando**: os jobs registram `job_verificar_pagamentos_pendentes_iniciado` e `job_reconciliar_estoque_iniciado` a cada rodada. Se esses eventos não aparecem nos logs do vendas, o `lifespan` não subiu. Procure `vendas.started`.
- **Erro repetido**: procure `loop_periodico_erro` (com `job=<nome>`) e os logs de erro de cada job, `job_*_erro` e `erro_processar_venda_timeout` / `erro_reconciliar_venda`.
- **Venda presa em `PENDENTE_PAGAMENTO`**: o job só considera vendas com `mercadopago_preference_id`. Se o Mercado Pago está fora do ar, o cancelamento é adiado (`timeout_revalidacao_mp_indisponivel_adiando_cancelamento`).

---

## 🚧 Pendências conhecidas

- [ ] Decidir se `limpar_reservas.py`, `limpar_carrinhos_abandonados.py` e `verificar_timeouts_separacao.py` devem ser agendados (por exemplo, como mais um `_loop_periodico` em `main.py`) ou removidos.
- [ ] Notificação interna para os alertas de 12h/24h (o `TODO` em `verificar_timeouts_separacao.py:142`).
- [ ] Passar `empresa_id` para `enviar_pedido_cancelado` nos jobs, para usar a Evolution do tenant.
