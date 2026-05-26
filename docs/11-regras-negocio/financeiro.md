# 💰 Regras de Negócio - Financeiro

Regras de negócio do serviço Financeiro (Contas a Receber e Vendas Fiadas).

---

## 1. Entidade: Conta a Receber

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `cliente_id` | UUID | Sim | Não | FK para Cliente (externo) |
| `venda_id` | UUID | Sim | Não | FK para Venda (externo) |
| `valor` | Decimal(10,2) | Sim | Não | Valor da conta |
| `valor_pago` | Decimal(10,2) | Sim | Não | Valor já pago |
| `valor_pendente` | Decimal(10,2) | Sim | Não | Valor pendente |
| `data_vencimento` | Date | Sim | Não | Data de vencimento |
| `data_pagamento` | Date | Não | Não | Data do pagamento |
| `status` | Enum | Sim | Não | Status da conta |
| `observacao` | Text | Não | Não | Observações |
| `criado_em` | DateTime | Sim | Não | Data de criação |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-FIN-001: Criação de Conta**
- Conta é criada automaticamente ao finalizar venda fiada
- Valor inicial = valor da venda
- `valor_pago` inicial = 0
- `valor_pendente` inicial = valor da venda
- Status inicial = `PENDENTE`

**RN-FIN-002: Cálculo de Vencimento**
- Vencimento é calculado baseado no `dia_vencimento` do cliente
- Se `dia_vencimento` não fornecido, padrão é 30 dias
- **Exemplo**: 
  - Venda em 15/05, `dia_vencimento = 10`
  - Vencimento: 10/06

**RN-FIN-003: Validação de Valores**
- `valor` deve ser maior que zero
- `valor_pago` deve ser maior ou igual a zero
- `valor_pago` não pode ser maior que `valor`
- `valor_pendente` é calculado: `valor - valor_pago`

**RN-FIN-004: Status da Conta**
- `PENDENTE`: Conta não paga
- `PAGA`: Conta totalmente paga
- `VENCIDA`: Conta passou do vencimento e não foi paga
- `PARCIAL`: Conta parcialmente paga

**RN-FIN-005: Pagamento**
- Ao registrar pagamento:
  - `valor_pago` é incrementado
  - `valor_pendente` é decrementado
  - `data_pagamento` é registrada
  - Status muda para `PAGA` se `valor_pendente = 0`
  - Crédito do cliente é creditado

**RN-FIN-006: Pagamento Parcial**
- Sistema aceita pagamentos parciais
- Status muda para `PARCIAL`
- Cliente pode fazer múltiplos pagamentos
- Crédito é creditado proporcionalmente

**RN-FIN-007: Conta Vencida**
- Job diário verifica contas vencidas
- Marca status como `VENCIDA`
- Publica evento `conta.vencida`
- Notificação é enviada ao cliente

**RN-FIN-008: Bloqueio por Inadimplência**
- Cliente é bloqueado se tiver conta vencida há mais de 30 dias
- Cliente bloqueado não pode fazer novas compras fiadas
- Publica evento `cliente.bloqueado`

---

## 2. Entidade: Pagamento Fiado

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `conta_id` | UUID | Sim | Não | FK para Conta a Receber |
| `valor` | Decimal(10,2) | Sim | Não | Valor do pagamento |
| `forma_pagamento` | Enum | Sim | Não | Forma de pagamento |
| `data_pagamento` | Date | Sim | Não | Data do pagamento |
| `observacao` | Text | Não | Não | Observações |
| `usuario_id` | UUID | Não | Não | Usuário que registrou |
| `criado_em` | DateTime | Sim | Não | Data de criação |

### ✅ Regras de Validação

**RN-PAG-001: Validação de Valor**
- Valor deve ser maior que zero
- Valor não pode ser maior que `valor_pendente` da conta

**RN-PAG-002: Formas de Pagamento**
- `DINHEIRO`: Pagamento em dinheiro
- `PIX`: Pagamento via PIX
- `CARTAO_DEBITO`: Cartão de débito
- `CARTAO_CREDITO`: Cartão de crédito
- `TRANSFERENCIA`: Transferência bancária

**RN-PAG-003: Registro de Pagamento**
- Ao registrar pagamento:
  - Cria registro em `pagamentos_fiados`
  - Atualiza `valor_pago` da conta
  - Atualiza `valor_pendente` da conta
  - Credita crédito do cliente
  - Publica evento `pagamento.recebido`

**RN-PAG-004: Histórico de Pagamentos**
- Todos os pagamentos são registrados permanentemente
- Pagamentos não podem ser editados ou excluídos
- Correções devem ser feitas com novos registros

---

## 3. Controle de Crédito

### ✅ Regras de Crédito

**RN-CRE-001: Débito de Crédito**
- Ao criar venda fiada:
  - `credito_disponivel` do cliente é decrementado
  - Valor debitado = valor da venda
  - Se `credito_disponivel` ficar negativo, cliente é bloqueado

**RN-CRE-002: Crédito de Crédito**
- Ao registrar pagamento:
  - `credito_disponivel` do cliente é incrementado
  - Valor creditado = valor do pagamento
  - Se cliente estava bloqueado e crédito ficar positivo, pode ser desbloqueado

**RN-CRE-003: Ajuste de Limite**
- Apenas ADMIN ou GERENTE podem ajustar limite de crédito
- Ajuste de limite não afeta `credito_disponivel` diretamente
- `credito_disponivel` é recalculado: `limite_credito - débitos_pendentes`

**RN-CRE-004: Validação de Crédito**
- Antes de criar venda fiada:
  - Verifica se cliente tem crédito disponível
  - Verifica se cliente não está bloqueado
  - Se crédito insuficiente, venda é recusada

---

## 4. Jobs Agendados (Celery)

### 4.1. Verificar Contas Vencidas

**Frequência**: Diário às 08:00

**Ações**:
1. Busca contas com `status = PENDENTE` e `data_vencimento < hoje`
2. Marca status como `VENCIDA`
3. Publica evento `conta.vencida`
4. Envia notificação ao cliente via WhatsApp

### 4.2. Lembrete de Vencimento

**Frequência**: Diário às 08:00

**Ações**:
1. Busca contas com vencimento em 3 dias
2. Envia lembrete ao cliente via WhatsApp
3. Registra notificação enviada

### 4.3. Bloqueio por Inadimplência

**Frequência**: Diário às 08:00

**Ações**:
1. Busca contas vencidas há mais de 30 dias
2. Bloqueia cliente automaticamente
3. Publica evento `cliente.bloqueado`
4. Envia notificação ao gerente

---

## 5. Eventos Assíncronos

### Eventos Publicados

| Evento | Quando | Consumidores | Descrição |
|--------|--------|--------------|-----------|
| `conta.criada` | Venda fiada finalizada | Relatórios | Nova conta a receber |
| `conta.vencida` | Conta vence | Notificações | Conta venceu |
| `conta.paga` | Pagamento total | Clientes, Relatórios | Conta foi paga |
| `pagamento.recebido` | Pagamento registrado | Clientes | Pagamento confirmado |
| `cliente.bloqueado` | Inadimplência | Vendas | Cliente bloqueado |

### Eventos Consumidos

| Evento | Origem | Ação |
|--------|--------|------|
| `venda.fiada_criada` | Vendas | Criar conta a receber |
| `venda.cancelada` | Vendas | Cancelar conta (se existir) |

---

## 6. Casos de Uso

### 6.1. Venda Fiada com Crédito Suficiente

**Cenário**: Cliente com limite de R$ 1.000 e crédito disponível de R$ 800 tenta compra de R$ 500

**Fluxo**:
1. Sistema valida crédito disponível (R$ 800 >= R$ 500) ✅
2. Cria venda fiada
3. Cria conta a receber no Financeiro
4. Debita R$ 500 do crédito do cliente
5. Novo crédito disponível: R$ 300
6. Venda é finalizada

### 6.2. Venda Fiada com Crédito Insuficiente

**Cenário**: Cliente com crédito disponível de R$ 300 tenta compra de R$ 500

**Fluxo**:
1. Sistema valida crédito disponível (R$ 300 < R$ 500) ❌
2. Retorna erro: `400 Bad Request - Crédito insuficiente`
3. Venda não é criada
4. Estoque não é reservado

### 6.3. Pagamento Parcial

**Cenário**: Cliente com conta de R$ 500 paga R$ 200

**Fluxo**:
1. Registra pagamento de R$ 200
2. `valor_pago` = R$ 200
3. `valor_pendente` = R$ 300
4. Status muda para `PARCIAL`
5. Credita R$ 200 no crédito do cliente
6. Publica evento `pagamento.recebido`

### 6.4. Conta Vencida e Bloqueio

**Cenário**: Cliente tem conta vencida há 35 dias

**Fluxo**:
1. Job diário detecta conta vencida há > 30 dias
2. Marca cliente como bloqueado
3. Publica evento `cliente.bloqueado`
4. Envia notificação ao gerente
5. Cliente não pode fazer novas compras fiadas
6. Cliente pode ser desbloqueado manualmente após pagamento

---

## 7. Relatórios

### 7.1. Contas a Receber

**Informações**:
- Total a receber
- Total vencido
- Total por cliente
- Previsão de recebimento por período

### 7.2. Inadimplência

**Informações**:
- Clientes inadimplentes
- Valor total em atraso
- Tempo médio de atraso
- Taxa de inadimplência

### 7.3. Fluxo de Caixa

**Informações**:
- Recebimentos do dia/semana/mês
- Previsão de recebimentos futuros
- Comparativo com períodos anteriores

---

## 📚 Referências

- [Diagramas de Sequência - Financeiro](../03-arquitetura/diagramas/sequencia.md#4-fluxos-integrados)
- [API Financeiro](../10-api-reference/financeiro-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
