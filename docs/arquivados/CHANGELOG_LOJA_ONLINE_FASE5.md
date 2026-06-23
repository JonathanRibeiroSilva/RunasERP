# Changelog - Loja Online MVP - FASE 5: Jobs e Automações

## Data: 2026-06-11

## 📋 Resumo
Implementação completa de jobs de automação para gerenciar timeouts, limpeza de dados e notificações automáticas da loja online.

---

## 🆕 Novos Jobs Criados

### 1. `jobs/verificar_timeouts_separacao.py`
**Propósito**: Gerencia timeouts de separação de vendas CONFIRMADAS.

**Frequência**: A cada 1 hora

**Fluxo**:
1. **12h após confirmação**: 
   - Registra alerta no log (aviso)
   - Conta para métricas

2. **24h após confirmação**:
   - Registra alerta crítico no log
   - Conta para métricas
   - TODO: Notificar admin/lojista internamente

3. **48h após confirmação**:
   - **Auto-cancela** a venda
   - Muda status: `CONFIRMADA` → `CANCELADA`
   - Libera reservas de estoque
   - Registra no histórico de status
   - Envia notificação WhatsApp ao cliente
   - Motivo: "Cancelamento automático: timeout de 48h para separação"

**Métricas**:
- `vendas_verificadas`: Total de vendas confirmadas verificadas
- `alertas_12h`: Vendas com 12h+ pendentes
- `alertas_24h`: Vendas com 24h+ pendentes (crítico)
- `canceladas_48h`: Vendas canceladas por timeout

**Logs importantes**:
```json
{
  "event": "venda_cancelada_timeout_48h",
  "venda_id": "uuid",
  "numero_venda": "V-2026-00001",
  "empresa_id": 1,
  "horas_decorridas": 48.5
}
```

---

### 2. `jobs/limpar_carrinhos_abandonados.py`
**Propósito**: Limpa carrinhos abandonados do Redis (>7 dias).

**Frequência**: Diariamente (recomendado: 3h da manhã)

**Fluxo**:
1. Varre todas as chaves de carrinho no Redis (`carrinho:*`)
2. Para cada carrinho, verifica `atualizado_em`
3. Se `atualizado_em` > 7 dias atrás: remove do Redis
4. Se não tem `atualizado_em`: remove (carrinho antigo)

**Critério de remoção**:
- Carrinhos não acessados há mais de 7 dias
- Carrinhos sem data de atualização (formato antigo)

**Métricas**:
- `carrinhos_verificados`: Total de carrinhos verificados
- `carrinhos_removidos`: Total de carrinhos removidos

**Benefícios**:
- Libera memória do Redis
- Remove dados obsoletos
- Melhora performance do Redis

**Logs importantes**:
```json
{
  "event": "carrinho_abandonado_removido",
  "key": "carrinho:abc123:1",
  "atualizado_em": "2026-06-01T10:00:00Z",
  "dias_abandonado": 10
}
```

---

### 3. `jobs/verificar_pagamentos_pendentes.py`
**Propósito**: Cancela vendas com pagamento online pendente que expiraram.

**Frequência**: A cada 5 minutos

**Fluxo**:
1. Busca vendas com status `PENDENTE_PAGAMENTO`
2. Verifica se tem `mercadopago_preference_id` (pagamento online)
3. Calcula tempo desde `data_pedido`
4. Se > 5 minutos:
   - Libera reservas de estoque (serviço de estoque)
   - Atualiza reservas no banco: `RESERVADA` → `LIBERADA`
   - Cancela venda: `PENDENTE_PAGAMENTO` → `CANCELADA`
   - Registra no histórico de status
   - Envia notificação WhatsApp ao cliente
   - Motivo: "Cancelamento automático: timeout de pagamento (5min)"

**Timeout Mercado Pago**: 5 minutos (conforme configurado na criação da preferência)

**Métricas**:
- `vendas_verificadas`: Total de vendas pendentes verificadas
- `vendas_canceladas`: Total de vendas canceladas por timeout

**Logs importantes**:
```json
{
  "event": "venda_cancelada_timeout_pagamento",
  "venda_id": "uuid",
  "numero_venda": "V-2026-00002",
  "empresa_id": 1,
  "minutos_decorridos": 5.2
}
```

---

### 4. `jobs/__init__.py`
**Propósito**: Documentação central dos jobs disponíveis.

Lista todos os jobs com descrição e frequência.

---

### 5. `jobs/README.md`
**Propósito**: Documentação completa de configuração e uso dos jobs.

**Conteúdo**:
- Lista detalhada de todos os jobs
- Instruções de configuração para:
  - Cron (Linux/MacOS)
  - Task Scheduler (Windows)
  - Docker + Supervisor
  - Celery (futuro)
- Exemplos de comandos
- Monitoramento e logs
- Troubleshooting
- Notas sobre idempotência e segurança

---

## ♻️ Job Existente (FASE 2)

### `jobs/limpar_reservas.py`
**Status**: Já implementado na FASE 2

**Propósito**: Limpa reservas temporárias de estoque expiradas.

**Frequência**: A cada 1 minuto

**Descrição**: Remove reservas temporárias (carrinho 15min e checkout 5min) que expiraram do banco de dados.

---

## 📊 Resumo de Jobs

| Job | Frequência | Timeout | Ação |
|-----|-----------|---------|------|
| `limpar_reservas.py` | 1 minuto | - | Remove reservas temporárias expiradas |
| `verificar_pagamentos_pendentes.py` | 5 minutos | 5 min | Cancela vendas com pagamento pendente |
| `verificar_timeouts_separacao.py` | 1 hora | 12h/24h/48h | Alerta e cancela vendas não separadas |
| `limpar_carrinhos_abandonados.py` | Diário | 7 dias | Remove carrinhos abandonados do Redis |

---

## 🔄 Fluxo Completo de Timeouts

### Carrinho → Checkout → Venda

1. **Adiciona ao carrinho**: Reserva 15min criada
   - Job `limpar_reservas.py` remove se expirar

2. **Faz checkout**: Reserva 5min criada (checkout)
   - Cria venda com status `PENDENTE_PAGAMENTO` (online) ou `PEDIDO` (offline)
   - Job `limpar_reservas.py` remove reserva antiga de 15min

3. **Pagamento online pendente**: 5 minutos
   - Se não pagar: Job `verificar_pagamentos_pendentes.py` cancela venda
   - Se pagar: Webhook Mercado Pago → status `CONFIRMADA`

4. **Venda confirmada**: 12h/24h/48h
   - **12h**: Job `verificar_timeouts_separacao.py` registra alerta
   - **24h**: Job registra alerta crítico
   - **48h**: Job cancela venda automaticamente

5. **Carrinho abandonado**: 7 dias
   - Job `limpar_carrinhos_abandonados.py` remove do Redis

---

## 🔒 Integração com Serviços

### HistoricoStatusService
Todos os cancelamentos automáticos registram mudança de status:
```python
await HistoricoStatusService.registrar_mudanca(
    db,
    venda.id,
    status_anterior="PENDENTE_PAGAMENTO",
    status_novo="CANCELADA",
    alterado_por=None,  # Sistema
    observacao="Cancelamento automático por timeout de pagamento (5min)"
)
```

### NotificacaoService
Envia WhatsApp ao cliente quando venda é cancelada:
- Timeout de pagamento (5min)
- Timeout de separação (48h)

### VendaService
Usa métodos existentes para:
- Liberar reservas de estoque
- Atualizar status de reservas no banco

### ReservaTemporariaService
Job `limpar_reservas.py` usa método:
```python
await ReservaTemporariaService.limpar_expiradas(db)
```

---

## ⚙️ Configuração Necessária

### Variáveis de Ambiente
Nenhuma nova variável necessária. Jobs usam configurações existentes:
- `DATABASE_URL`: Conexão com PostgreSQL
- `REDIS_URL`: Conexão com Redis
- `EVOLUTION_API_*`: Notificações WhatsApp (opcional)

### Cron / Task Scheduler
Ver instruções detalhadas em `jobs/README.md`

**Linux (crontab)**:
```bash
# Limpar reservas (1 min)
* * * * * cd /path/to/vendas && python jobs/limpar_reservas.py

# Pagamentos pendentes (5 min)
*/5 * * * * cd /path/to/vendas && python jobs/verificar_pagamentos_pendentes.py

# Timeouts separação (1 hora)
0 * * * * cd /path/to/vendas && python jobs/verificar_timeouts_separacao.py

# Carrinhos abandonados (diário)
0 3 * * * cd /path/to/vendas && python jobs/limpar_carrinhos_abandonados.py
```

**Windows (Task Scheduler)**:
- Ver instruções passo-a-passo em `jobs/README.md`

---

## 📈 Métricas e Monitoramento

### Logs Estruturados
Todos os jobs usam `structlog` com eventos nomeados:

**Eventos de sucesso**:
- `job_limpar_reservas_concluido`
- `job_verificar_timeouts_concluido`
- `job_limpar_carrinhos_concluido`
- `job_verificar_pagamentos_pendentes_concluido`

**Eventos de ação**:
- `venda_cancelada_timeout_48h`
- `venda_cancelada_timeout_pagamento`
- `carrinho_abandonado_removido`
- `alerta_separacao_12h`
- `alerta_separacao_24h`

**Eventos de erro**:
- `job_*_erro`
- `erro_cancelar_venda_timeout`
- `erro_processar_carrinho`

### Métricas Disponíveis

**limpar_reservas.py**:
- `reservas_removidas`: Total de reservas limpas

**verificar_timeouts_separacao.py**:
- `vendas_verificadas`: Total verificado
- `alertas_12h`: Avisos 12h
- `alertas_24h`: Avisos críticos 24h
- `canceladas_48h`: Cancelamentos automáticos

**limpar_carrinhos_abandonados.py**:
- `carrinhos_verificados`: Total verificado
- `carrinhos_removidos`: Total removido

**verificar_pagamentos_pendentes.py**:
- `vendas_verificadas`: Total verificado
- `vendas_canceladas`: Total cancelado

---

## 🔐 Segurança e Confiabilidade

### Idempotência
✅ Todos os jobs são **idempotentes**: podem ser executados múltiplas vezes sem causar duplicação ou inconsistência.

### Transações
✅ Todos os jobs usam transações do SQLAlchemy:
```python
async with db.begin_nested():
    # operações
await db.commit()  # ou rollback em caso de erro
```

### Tratamento de Erros
✅ Erros são logados mas não param a execução:
```python
try:
    # processar item
except Exception as e:
    log.error("erro", error=str(e))
    # continua para próximo item
```

### Isolamento
✅ Jobs são **stateless**: não dependem de estado anterior ou arquivos temporários.

---

## 🧪 Testes

### Testes Manuais

**Teste 1: Timeout de Pagamento (5min)**
1. Criar venda com pagamento online
2. NÃO pagar no Mercado Pago
3. Aguardar 5 minutos
4. Executar job: `python jobs/verificar_pagamentos_pendentes.py`
5. Verificar: venda cancelada, estoque liberado, notificação enviada

**Teste 2: Timeout de Separação (48h)**
1. Criar venda e confirmar pagamento
2. Alterar `data_confirmacao` para 48h atrás (manualmente no banco)
3. Executar job: `python jobs/verificar_timeouts_separacao.py`
4. Verificar: venda cancelada, histórico registrado, notificação enviada

**Teste 3: Carrinho Abandonado (7 dias)**
1. Criar carrinho no Redis
2. Alterar `atualizado_em` para 8 dias atrás
3. Executar job: `python jobs/limpar_carrinhos_abandonados.py`
4. Verificar: carrinho removido do Redis

**Teste 4: Reservas Expiradas**
1. Criar reserva temporária expirada no banco
2. Executar job: `python jobs/limpar_reservas.py`
3. Verificar: reserva removida

---

## 📝 TODOs Futuros

### Notificações Internas
- [ ] Implementar sistema de notificações para admin/lojista
- [ ] Alertas de 12h/24h devem notificar equipe interna
- [ ] Dashboard para monitorar alertas

### Métricas Avançadas
- [ ] Integração com Prometheus
- [ ] Dashboards no Grafana
- [ ] Alertas automáticos (Slack, Email)

### Retry e Resiliência
- [ ] Implementar retry automático em caso de falha transitória
- [ ] Circuit breaker para integrações externas
- [ ] Dead letter queue para jobs falhados

### Health Check
- [ ] Endpoint para verificar se jobs estão rodando
- [ ] Verificar última execução de cada job
- [ ] Alertar se job não rodou no período esperado

### Celery Migration
- [ ] Migrar jobs para Celery Beat
- [ ] Melhor gestão de concorrência
- [ ] Retry automático e dead letter queue

---

## ✅ Status

**FASE 5: COMPLETA** ✅

Todos os jobs de automação foram implementados e documentados. Sistema está pronto para:
1. Configurar cron/Task Scheduler
2. Executar jobs manualmente para teste
3. Monitorar logs e métricas
4. Prosseguir para FASE 6 (Endpoints Administrativos)

**Próximo**: FASE 6 - Endpoints Administrativos
- Configuração de entrega (taxa padrão + exceções)
- Configuração de pagamento (Mercado Pago)
- Gestão de clientes (permite_fiado_online)
