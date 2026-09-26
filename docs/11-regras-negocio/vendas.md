# 🛒 Regras de Negócio - Vendas

Regras de negócio do serviço de Vendas (Carrinho, Pedidos e Pagamentos).

---

## 1. Carrinho

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `token` | UUID | Sim | Identificador único do carrinho |
| `cliente_id` | UUID | Não | FK para Cliente (opcional) |
| `itens` | Array | Sim | Lista de itens no carrinho |
| `total` | Decimal(10,2) | Sim | Valor total do carrinho |
| `criado_em` | DateTime | Sim | Data de criação |
| `expira_em` | DateTime | Sim | Data de expiração |

### ✅ Regras de Validação

**RN-CAR-001: Carrinho Anônimo**
- Cliente pode criar carrinho sem estar autenticado
- Carrinho é identificado por token único (UUID)
- Carrinho anônimo pode ser convertido em carrinho de cliente

**RN-CAR-002: Expiração de Carrinho**
- Carrinho tem TTL (Time To Live) de 2 horas
- Após expiração, reservas são liberadas automaticamente
- Job Celery executa a cada 15 minutos para limpar carrinhos expirados

**RN-CAR-003: Reserva de Estoque no Carrinho**
- Ao adicionar item ao carrinho, estoque é reservado
- Reserva diminui `quantidade_disponivel`
- Reserva aumenta `quantidade_reservada`
- Quantidade física não é alterada na reserva

**RN-CAR-004: Validação de Disponibilidade**
- Sistema verifica disponibilidade antes de adicionar ao carrinho
- Se estoque insuficiente, item não é adicionado
- Cliente é notificado da indisponibilidade

**RN-CAR-005: Remoção de Item**
- Ao remover item, reserva é liberada automaticamente
- `quantidade_disponivel` é restaurada
- `quantidade_reservada` é decrementada

**RN-CAR-006: Armazenamento**
- Carrinho é armazenado no Redis (cache)
- TTL de 2 horas
- Formato JSON

---

## 2. Pedido

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `cliente_id` | UUID | Sim | Não | FK para Cliente |
| `endereco_entrega_id` | UUID | Sim | Não | FK para Endereço |
| `status` | Enum | Sim | Não | Status do pedido |
| `forma_pagamento` | Enum | Sim | Não | Forma de pagamento |
| `total` | Decimal(10,2) | Sim | Não | Valor total |
| `itens` | JSON | Sim | Não | Itens do pedido |
| `payment_id` | String | Não | Não | ID do pagamento externo |
| `link_pagamento` | String | Não | Não | Link para pagamento |
| `motivo_cancelamento` | String | Não | Não | Motivo do cancelamento |
| `criado_em` | DateTime | Sim | Não | Data de criação |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-PED-001: Validações no Checkout**
- Cliente deve estar cadastrado e ativo
- Cliente não pode estar bloqueado
- Endereço de entrega deve existir
- Carrinho não pode estar vazio

**RN-PED-002: Conversão Carrinho → Pedido**
- Checkout cria pedido com status `PENDENTE`
- Reservas são mantidas durante processamento
- Carrinho é removido após criação do pedido

**RN-PED-003: Formas de Pagamento**
- **À vista (PIX/Cartão)**: Pedido fica `AGUARDANDO_PAGAMENTO`
- **Fiado**: Valida crédito e cria conta a receber

**RN-PED-004: Pagamento PIX**
- Sistema gera QR Code via Mercado Pago
- Pedido aguarda webhook de confirmação
- Timeout de 30 minutos para pagamento

**RN-PED-005: Pagamento Fiado**
- Valida crédito disponível do cliente
- Cria conta a receber no Financeiro
- Debita crédito do cliente
- Pedido vai direto para `CONFIRMADO`

**RN-PED-006: Confirmação de Pagamento**
- Webhook Mercado Pago confirma pagamento
- Pedido muda para `PAGO`
- Sistema converte pedido em venda
- Reservas são confirmadas (baixa física)

**RN-PED-007: Falha no Pagamento**
- Pagamento recusado: pedido vai para `PAGAMENTO_RECUSADO`
- Todas as reservas são liberadas
- Cliente pode tentar novamente

**RN-PED-008: Cancelamento de Pedido**
- Apenas pedidos não finalizados podem ser cancelados
- Reservas são liberadas automaticamente
- Se fiado: crédito é estornado
- Motivo do cancelamento é obrigatório

### 📊 Status do Pedido

| Status | Descrição | Próximos Estados |
|--------|-----------|------------------|
| `PENDENTE` | Pedido criado, aguardando processamento | `AGUARDANDO_PAGAMENTO`, `CONFIRMADO`, `CANCELADO` |
| `AGUARDANDO_PAGAMENTO` | Aguardando confirmação de pagamento | `PAGO`, `PAGAMENTO_RECUSADO`, `CANCELADO` |
| `PAGO` | Pagamento confirmado | `FINALIZADO` |
| `CONFIRMADO` | Pedido confirmado (fiado) | `FINALIZADO` |
| `PAGAMENTO_RECUSADO` | Pagamento recusado | `CANCELADO` |
| `CANCELADO` | Pedido cancelado | - |
| `FINALIZADO` | Pedido finalizado e convertido em venda | - |

---

## 3. Venda

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `pedido_id` | UUID | Sim | Não | FK para Pedido |
| `cliente_id` | UUID | Sim | Não | FK para Cliente |
| `status` | Enum | Sim | Não | Status da venda |
| `total` | Decimal(10,2) | Sim | Não | Valor total |
| `forma_pagamento` | Enum | Sim | Não | Forma de pagamento |
| `itens` | JSON | Sim | Não | Itens da venda |
| `criado_em` | DateTime | Sim | Não | Data de criação |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-VEN-001: Criação de Venda**
- Venda é criada após confirmação de pagamento
- Status inicial: `FINALIZADA`
- Venda referencia o pedido original

**RN-VEN-002: Confirmação de Reservas**
- Sistema chama `POST /estoque/confirmar-reserva` para cada item
- `quantidade_reservada` é decrementada
- `quantidade` física é decrementada
- Movimentação tipo `SAIDA` é registrada

**RN-VEN-003: Eventos Publicados**
- `venda.finalizada` - Venda concluída
- `pedido.pago` - Pedido pago
- `estoque.confirmado` - Estoque baixado

**RN-VEN-004: Cancelamento de Venda**
- Vendas finalizadas podem ser canceladas (devolução)
- Estoque é devolvido (movimentação tipo `ENTRADA`)
- Se fiado: crédito é estornado
- Motivo do cancelamento é obrigatório

### 📊 Status da Venda

| Status | Descrição |
|--------|-----------|
| `FINALIZADA` | Venda concluída com sucesso |
| `CANCELADA` | Venda cancelada (devolução) |

---

## 4. Fluxos Completos

### 4.1. Fluxo: Carrinho → Pedido → Venda (À Vista)

```
1. Cliente adiciona itens ao carrinho
   → Estoque é reservado
   → Carrinho armazenado no Redis (TTL 2h)

2. Cliente faz checkout
   → Valida cliente ativo e não bloqueado
   → Valida endereço de entrega
   → Cria pedido com status PENDENTE
   → Gera QR Code PIX (Mercado Pago)
   → Pedido muda para AGUARDANDO_PAGAMENTO

3. Cliente paga via PIX
   → Mercado Pago envia webhook
   → Pedido muda para PAGO

4. Sistema converte pedido em venda
   → Cria venda com status FINALIZADA
   → Confirma reservas (baixa física de estoque)
   → Publica eventos (venda.finalizada, estoque.confirmado)
   → Remove carrinho do Redis
```

### 4.2. Fluxo: Carrinho → Pedido → Venda (Fiado)

```
1. Cliente adiciona itens ao carrinho
   → Estoque é reservado
   → Carrinho armazenado no Redis (TTL 2h)

2. Cliente faz checkout (fiado)
   → Valida cliente ativo e não bloqueado
   → Valida crédito disponível
   → Cria pedido com status PENDENTE
   → Cria conta a receber no Financeiro
   → Debita crédito do cliente
   → Pedido muda para CONFIRMADO

3. Sistema converte pedido em venda
   → Cria venda com status FINALIZADA
   → Confirma reservas (baixa física de estoque)
   → Publica eventos (venda.fiada_criada, estoque.confirmado)
   → Remove carrinho do Redis
```

### 4.3. Fluxo: Cancelamento de Pedido

```
1. Usuário solicita cancelamento
   → Valida se pedido pode ser cancelado
   → Libera todas as reservas de estoque
   → Se fiado: estorna crédito do cliente
   → Marca pedido como CANCELADO
   → Publica evento (pedido.cancelado)
```

---

## 5. Integrações

### 5.1. Integração com Mercado Pago

**Criação de Pagamento PIX**:
- Endpoint: `POST /v1/payments`
- Retorna: `payment_id` e `qr_code`
- Link de pagamento é armazenado no pedido

**Webhook de Confirmação**:
- Endpoint: `POST /webhooks/mercadopago`
- Valida assinatura do webhook
- Atualiza status do pedido
- Converte pedido em venda

**Timeout**:
- Pagamento expira em 30 minutos
- Pedido é cancelado automaticamente
- Reservas são liberadas

### 5.2. Integração com Estoque

**Reservar Estoque**:
- `POST /estoque/reservar`
- Diminui `quantidade_disponivel`
- Aumenta `quantidade_reservada`

**Liberar Reserva**:
- `POST /estoque/liberar-reserva`
- Aumenta `quantidade_disponivel`
- Diminui `quantidade_reservada`

**Confirmar Reserva**:
- `POST /estoque/confirmar-reserva`
- Diminui `quantidade` física
- Diminui `quantidade_reservada`
- Cria movimentação tipo `SAIDA`

### 5.3. Integração com Financeiro

**Criar Conta a Receber**:
- `POST /contas-receber`
- Cria conta com vencimento baseado em `dia_vencimento`
- Vincula à venda

**Registrar Pagamento**:
- `POST /contas-receber/{id}/pagar`
- Marca conta como paga
- Credita crédito do cliente

---

## 📚 Referências

- [API de Vendas](../10-api-reference/vendas-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
