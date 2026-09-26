# API de Vendas - Runas

> **Referência completa** da API do serviço de Vendas

---

## 📋 Visão Geral

**Base URL**: `http://localhost:8004`  
**Autenticação**: Bearer Token (JWT) / Público para carrinho  
**Formato**: JSON

---

## � Autenticação

- **Rotas públicas**: Carrinho e webhook de pagamento
- **Rotas protegidas**: Pedidos, gestão de status, pagamentos manuais

```http
Authorization: Bearer <access_token>
```

---

## 📍 Endpoints

### Carrinho (Público)

#### Criar Carrinho
```http
POST /carrinho
```

**Request Body:**
```json
{
  "cliente_id": "uuid-opcional"
}
```

**Response 201:**
```json
{
  "token": "abc123xyz",
  "cliente_id": "uuid",
  "itens": [],
  "subtotal": 0.00,
  "frete": 0.00,
  "total": 0.00,
  "criado_em": "2026-05-26T10:00:00Z",
  "expira_em": "2026-05-26T12:00:00Z"
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8004/carrinho \
  -H "Content-Type: application/json" \
  -d '{"cliente_id":"550e8400-e29b-41d4-a716-446655440000"}'
```

---

#### Consultar Carrinho
```http
GET /carrinho/{token}
```

**Response 200:**
```json
{
  "token": "abc123xyz",
  "cliente_id": "uuid",
  "itens": [
    {
      "id": "uuid",
      "produto_id": "uuid",
      "variante_id": "uuid",
      "nome": "Camiseta Básica",
      "variante": "P - Azul",
      "quantidade": 2,
      "preco_unitario": 49.90,
      "subtotal": 99.80
    }
  ],
  "subtotal": 99.80,
  "frete": 15.00,
  "total": 114.80,
  "criado_em": "2026-05-26T10:00:00Z",
  "expira_em": "2026-05-26T12:00:00Z"
}
```

**Exemplo cURL:**
```bash
curl -X GET http://localhost:8004/carrinho/abc123xyz
```

---

#### Adicionar Item ao Carrinho
```http
POST /carrinho/{token}/itens
```

**Request Body:**
```json
{
  "produto_id": "uuid",
  "variante_id": "uuid-opcional",
  "quantidade": 2
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "produto_id": "uuid",
  "variante_id": "uuid",
  "nome": "Camiseta Básica",
  "variante": "P - Azul",
  "quantidade": 2,
  "preco_unitario": 49.90,
  "subtotal": 99.80
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8004/carrinho/abc123xyz/itens \
  -H "Content-Type: application/json" \
  -d '{
    "produto_id":"550e8400-e29b-41d4-a716-446655440001",
    "variante_id":"550e8400-e29b-41d4-a716-446655440002",
    "quantidade":2
  }'
```

---

#### Alterar Quantidade de Item
```http
PATCH /carrinho/{token}/itens/{item_id}
```

**Request Body:**
```json
{
  "quantidade": 5
}
```

**Response 200:** Item atualizado

**Exemplo cURL:**
```bash
curl -X PATCH http://localhost:8004/carrinho/abc123xyz/itens/550e8400-e29b-41d4-a716-446655440003 \
  -H "Content-Type: application/json" \
  -d '{"quantidade":5}'
```

---

#### Remover Item do Carrinho
```http
DELETE /carrinho/{token}/itens/{item_id}
```

**Response 204:** Item removido

**Exemplo cURL:**
```bash
curl -X DELETE http://localhost:8004/carrinho/abc123xyz/itens/550e8400-e29b-41d4-a716-446655440003
```

---

#### Finalizar Compra (Checkout)
```http
POST /carrinho/{token}/checkout
```

**Request Body:**
```json
{
  "cliente_id": "uuid",
  "endereco_entrega_id": "uuid",
  "forma_pagamento": "PIX",
  "observacoes": "Entregar após 18h"
}
```

**Formas de Pagamento:**
- `PIX` - Pagamento via PIX (gera QR Code)
- `DINHEIRO` - Pagamento em dinheiro na entrega
- `FIADO` - Pagamento a prazo (requer crédito disponível)

**Response 201:**
```json
{
  "pedido_id": "uuid",
  "numero": "PED-2026-001",
  "status": "AGUARDANDO_PAGAMENTO",
  "total": 114.80,
  "forma_pagamento": "PIX",
  "pix": {
    "qr_code": "00020126580014br.gov.bcb.pix...",
    "qr_code_url": "https://api.mercadopago.com/qr/...",
    "expira_em": "2026-05-26T10:30:00Z"
  }
}
```

**Exemplo cURL (PIX):**
```bash
curl -X POST http://localhost:8004/carrinho/abc123xyz/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id":"550e8400-e29b-41d4-a716-446655440000",
    "endereco_entrega_id":"550e8400-e29b-41d4-a716-446655440004",
    "forma_pagamento":"PIX",
    "observacoes":"Entregar após 18h"
  }'
```

**Exemplo cURL (Dinheiro):**
```bash
curl -X POST http://localhost:8004/carrinho/abc123xyz/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id":"550e8400-e29b-41d4-a716-446655440000",
    "endereco_entrega_id":"550e8400-e29b-41d4-a716-446655440004",
    "forma_pagamento":"DINHEIRO"
  }'
```

**Exemplo cURL (Fiado):**
```bash
curl -X POST http://localhost:8004/carrinho/abc123xyz/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_id":"550e8400-e29b-41d4-a716-446655440000",
    "endereco_entrega_id":"550e8400-e29b-41d4-a716-446655440004",
    "forma_pagamento":"FIADO"
  }'
```

---

### Pedidos (Protegido)

#### Listar Pedidos
```http
GET /pedidos
```

**Query Parameters:**
- `page` (int, opcional): Número da página (padrão: 1)
- `size` (int, opcional): Itens por página (padrão: 20)
- `cliente_id` (uuid, opcional): Filtrar por cliente
- `status` (string, opcional): Filtrar por status
- `data_inicio` (date, opcional): Data inicial (formato: YYYY-MM-DD)
- `data_fim` (date, opcional): Data final (formato: YYYY-MM-DD)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "numero": "PED-2026-001",
      "cliente_id": "uuid",
      "cliente_nome": "João Silva",
      "status": "AGUARDANDO_PAGAMENTO",
      "forma_pagamento": "PIX",
      "subtotal": 99.80,
      "frete": 15.00,
      "total": 114.80,
      "criado_em": "2026-05-26T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

**Exemplo cURL:**
```bash
curl -X GET "http://localhost:8004/pedidos?status=AGUARDANDO_PAGAMENTO&page=1" \
  -H "Authorization: Bearer {token}"
```

---

#### Detalhe do Pedido
```http
GET /pedidos/{id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "numero": "PED-2026-001",
  "cliente": {
    "id": "uuid",
    "nome": "João Silva",
    "cpf": "12345678909",
    "telefone": "+5511999999999"
  },
  "endereco_entrega": {
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "complemento": "Apto 101",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP",
    "cep": "01310-100"
  },
  "itens": [
    {
      "id": "uuid",
      "produto_id": "uuid",
      "produto_nome": "Camiseta Básica",
      "variante": "P - Azul",
      "quantidade": 2,
      "preco_unitario": 49.90,
      "subtotal": 99.80
    }
  ],
  "status": "AGUARDANDO_PAGAMENTO",
  "forma_pagamento": "PIX",
  "subtotal": 99.80,
  "frete": 15.00,
  "total": 114.80,
  "observacoes": "Entregar após 18h",
  "criado_em": "2026-05-26T10:00:00Z",
  "atualizado_em": "2026-05-26T10:00:00Z"
}
```

**Exemplo cURL:**
```bash
curl -X GET http://localhost:8004/pedidos/550e8400-e29b-41d4-a716-446655440005 \
  -H "Authorization: Bearer {token}"
```

---

#### Avançar Status do Pedido (ADMIN)
```http
PATCH /pedidos/{id}/status
```

**Request Body:**
```json
{
  "status": "EM_SEPARACAO"
}
```

**Status Válidos (em ordem):**
1. `AGUARDANDO_PAGAMENTO` - Aguardando confirmação de pagamento
2. `PAGO` - Pagamento confirmado
3. `EM_SEPARACAO` - Produtos sendo separados
4. `PRONTO_ENVIO` - Pronto para envio
5. `ENVIADO` - Pedido enviado
6. `ENTREGUE` - Pedido entregue
7. `CANCELADO` - Pedido cancelado

**Response 200:** Pedido atualizado

**Exemplo cURL:**
```bash
curl -X PATCH http://localhost:8004/pedidos/550e8400-e29b-41d4-a716-446655440005/status \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"status":"EM_SEPARACAO"}'
```

---

#### Ajustar Frete (ADMIN)
```http
PATCH /pedidos/{id}/frete
```

**Request Body:**
```json
{
  "frete": 20.00
}
```

**Response 200:** Frete atualizado

**Exemplo cURL:**
```bash
curl -X PATCH http://localhost:8004/pedidos/550e8400-e29b-41d4-a716-446655440005/frete \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"frete":20.00}'
```

---

#### Cancelar Pedido
```http
DELETE /pedidos/{id}/cancelar
```

**Response 200:**
```json
{
  "message": "Pedido cancelado com sucesso",
  "estoque_devolvido": true,
  "credito_liberado": true
}
```

**Exemplo cURL:**
```bash
curl -X DELETE http://localhost:8004/pedidos/550e8400-e29b-41d4-a716-446655440005/cancelar \
  -H "Authorization: Bearer {token}"
```

---

### Pagamentos

#### Webhook PIX (Mercado Pago)
```http
POST /pagamentos/webhook/mercadopago
```

**Request Body:** (enviado pelo Mercado Pago)
```json
{
  "action": "payment.updated",
  "data": {
    "id": "123456789"
  }
}
```

**Response 200:** Webhook processado

---

#### Confirmar Pagamento Manual (ADMIN)
```http
PATCH /pagamentos/{pedido_id}/confirmar
```

**Request Body:**
```json
{
  "forma_pagamento": "DINHEIRO",
  "valor_pago": 114.80,
  "observacoes": "Pago na entrega"
}
```

**Response 200:** Pagamento confirmado

**Exemplo cURL:**
```bash
curl -X PATCH http://localhost:8004/pagamentos/550e8400-e29b-41d4-a716-446655440005/confirmar \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "forma_pagamento":"DINHEIRO",
    "valor_pago":114.80,
    "observacoes":"Pago na entrega"
  }'
```

---

## � Casos de Uso

### Caso 1: Criar Carrinho e Adicionar Produtos

```javascript
// 1. Criar carrinho
const carrinho = await axios.post('http://localhost:8004/carrinho', {
  cliente_id: '550e8400-e29b-41d4-a716-446655440000'
});

const token = carrinho.data.token;

// 2. Adicionar produto
await axios.post(`http://localhost:8004/carrinho/${token}/itens`, {
  produto_id: '550e8400-e29b-41d4-a716-446655440001',
  variante_id: '550e8400-e29b-41d4-a716-446655440002',
  quantidade: 2
});

// 3. Adicionar outro produto
await axios.post(`http://localhost:8004/carrinho/${token}/itens`, {
  produto_id: '550e8400-e29b-41d4-a716-446655440006',
  quantidade: 1
});

// 4. Consultar carrinho
const carrinhoAtual = await axios.get(`http://localhost:8004/carrinho/${token}`);
console.log('Total:', carrinhoAtual.data.total);
```

---

### Caso 2: Checkout com PIX

```javascript
// Finalizar compra com PIX
const pedido = await axios.post(`http://localhost:8004/carrinho/${token}/checkout`, {
  cliente_id: '550e8400-e29b-41d4-a716-446655440000',
  endereco_entrega_id: '550e8400-e29b-41d4-a716-446655440004',
  forma_pagamento: 'PIX',
  observacoes: 'Entregar após 18h'
});

// Exibir QR Code para o cliente
console.log('QR Code:', pedido.data.pix.qr_code);
console.log('URL do QR Code:', pedido.data.pix.qr_code_url);
console.log('Expira em:', pedido.data.pix.expira_em);

// Aguardar webhook do Mercado Pago confirmar pagamento
```

---

### Caso 3: Checkout com Dinheiro

```javascript
// Finalizar compra com dinheiro
const pedido = await axios.post(`http://localhost:8004/carrinho/${token}/checkout`, {
  cliente_id: '550e8400-e29b-41d4-a716-446655440000',
  endereco_entrega_id: '550e8400-e29b-41d4-a716-446655440004',
  forma_pagamento: 'DINHEIRO'
});

console.log('Pedido criado:', pedido.data.numero);
console.log('Status:', pedido.data.status); // AGUARDANDO_PAGAMENTO

// Quando o entregador receber o dinheiro, confirmar pagamento
await axios.patch(
  `http://localhost:8004/pagamentos/${pedido.data.pedido_id}/confirmar`,
  {
    forma_pagamento: 'DINHEIRO',
    valor_pago: pedido.data.total,
    observacoes: 'Pago na entrega'
  },
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);
```

---

### Caso 4: Checkout Fiado (Crédito)

```javascript
// Finalizar compra fiado
try {
  const pedido = await axios.post(`http://localhost:8004/carrinho/${token}/checkout`, {
    cliente_id: '550e8400-e29b-41d4-a716-446655440000',
    endereco_entrega_id: '550e8400-e29b-41d4-a716-446655440004',
    forma_pagamento: 'FIADO'
  });

  console.log('Pedido criado:', pedido.data.numero);
  console.log('Status:', pedido.data.status); // PAGO (crédito já descontado)
  
} catch (error) {
  if (error.response.status === 400) {
    console.error('Crédito insuficiente ou cliente bloqueado');
  }
}
```

---

### Caso 5: Listar Pedidos Pendentes

```javascript
// Listar pedidos aguardando pagamento
const pedidosPendentes = await axios.get(
  'http://localhost:8004/pedidos?status=AGUARDANDO_PAGAMENTO',
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

console.log('Pedidos pendentes:', pedidosPendentes.data.items.length);
```

---

### Caso 6: Avançar Status do Pedido

```javascript
// Fluxo completo de status
const pedidoId = '550e8400-e29b-41d4-a716-446655440005';

// 1. Pagamento confirmado
await axios.patch(
  `http://localhost:8004/pedidos/${pedidoId}/status`,
  { status: 'PAGO' },
  { headers: { Authorization: `Bearer ${token}` } }
);

// 2. Iniciar separação
await axios.patch(
  `http://localhost:8004/pedidos/${pedidoId}/status`,
  { status: 'EM_SEPARACAO' },
  { headers: { Authorization: `Bearer ${token}` } }
);

// 3. Pronto para envio
await axios.patch(
  `http://localhost:8004/pedidos/${pedidoId}/status`,
  { status: 'PRONTO_ENVIO' },
  { headers: { Authorization: `Bearer ${token}` } }
);

// 4. Enviado
await axios.patch(
  `http://localhost:8004/pedidos/${pedidoId}/status`,
  { status: 'ENVIADO' },
  { headers: { Authorization: `Bearer ${token}` } }
);

// 5. Entregue
await axios.patch(
  `http://localhost:8004/pedidos/${pedidoId}/status`,
  { status: 'ENTREGUE' },
  { headers: { Authorization: `Bearer ${token}` } }
);
```

---

### Caso 7: Cancelar Pedido

```javascript
// Cancelar pedido (devolve estoque e libera crédito)
const resultado = await axios.delete(
  `http://localhost:8004/pedidos/${pedidoId}/cancelar`,
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

console.log('Estoque devolvido:', resultado.data.estoque_devolvido);
console.log('Crédito liberado:', resultado.data.credito_liberado);
```

---

## 🚨 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Requisição inválida / Crédito insuficiente / Cliente bloqueado |
| 401 | Não autenticado |
| 403 | Sem permissão (role insuficiente) |
| 404 | Carrinho/Pedido não encontrado |
| 409 | Conflito (ex: produto sem estoque) |
| 410 | Carrinho expirado |
| 422 | Validação falhou |
| 500 | Erro interno do servidor |

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Vendas](../11-regras-negocio/vendas.md)
- [API de Estoque](./estoque-api.md) - Integração com estoque
- [API Financeiro](./financeiro-api.md) - Integração com contas a receber
- [Guia de Autenticação](./guia-autenticacao.md)
- [Exemplos Práticos](./exemplos-praticos.md)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
