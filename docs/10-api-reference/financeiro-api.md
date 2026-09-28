# API Financeiro - Runas

> **STATUS: NÃO IMPLEMENTADO.** Este documento é especificação planejada, não
> contrato vigente. O serviço financeiro hoje expõe apenas `GET /health`.

**Evidência, lida do código:**

- `services/financeiro/main.py` não tem nenhum `include_router`. A única rota
  declarada é `@app.get("/health")`, na linha 56.
- `services/financeiro/routers/__init__.py` tem 22 bytes: nenhum router existe.
- O baseline `services/financeiro/alembic/versions/20260919_baseline.py` diz, na
  própria docstring: *"The service has no models, so there is nothing to
  create."* Não há tabela de contas nem de pagamentos — `upgrade()` é `pass`.
- O caminho já existe no gateway, mas não no destino: `api-gateway/routers/proxy.py`
  declara `/contas/{path:path}` (métodos GET, POST e PATCH, sob `require_admin`) e
  `api-gateway/proxy/service_proxy.py:35` mapeia `/contas` para `FINANCEIRO_URL`.
  O gateway encaminha e o serviço responde 404.

Tudo abaixo descreve o comportamento **pretendido**. Nenhum exemplo cURL ou
JavaScript deste documento funciona hoje.

---

## 📋 Visão Geral (planejado)

**Porta do serviço**: `8005` — `docker-compose.dev.yml` publica
`127.0.0.1:8005:8005` e sobe `uvicorn main:app --port 8005`. Em dev isso escuta
só em loopback; o serviço não é ponto de entrada.

**Base URL planejada**: o consumo previsto é através do gateway. O nginx do
frontend faz `rewrite ^/api/(.*)$ /$1` para `api-gateway-prod:8000` (nome do container em produção, `frontend/nginx.conf`), então
`/api/contas` chega ao gateway como `/contas` e de lá segue para `financeiro:8005`.
Os exemplos abaixo usam `http://localhost:8005` porque falam direto com o
serviço — não é o caminho de produção.

**Autenticação**: o serviço financeiro **não valida JWT**. O único controle na
porta dele é o header `X-Servico-Interno-Token` (`services/financeiro/interno.py`),
hoje fail-open e com `/health` isento. O JWT de admin é exigido pelo gateway, na
rota de proxy, nunca pelo serviço.

**Formato**: JSON

---

## 🔐 Autenticação (planejado)

Pelo gateway, a rota `/contas/{path:path}` exige JWT de admin (`require_admin`):

```http
Authorization: Bearer <access_token>
```

Os cabeçalhos `Authorization` nos exemplos deste documento refletem essa
intenção. Chamadas diretas à porta 8005 não verificam esse token.

---

## 📍 Endpoints (planejados — nenhum implementado)

### Contas a Receber

#### Listar Contas
```http
GET /contas
```

**Query Parameters:**
- `page` (int, opcional): Número da página (padrão: 1)
- `size` (int, opcional): Itens por página (padrão: 20)
- `cliente_id` (uuid, opcional): Filtrar por cliente
- `status` (string, opcional): Filtrar por status (`ABERTA`, `PAGA`, `VENCIDA`, `CANCELADA`)
- `data_inicio` (date, opcional): Data inicial de vencimento (formato: YYYY-MM-DD)
- `data_fim` (date, opcional): Data final de vencimento (formato: YYYY-MM-DD)

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "pedido_id": "uuid",
      "cliente_id": "uuid",
      "cliente_nome": "João Silva",
      "valor_total": 114.80,
      "valor_pago": 0.00,
      "saldo": 114.80,
      "data_vencimento": "2026-06-10",
      "status": "ABERTA",
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
curl -X GET "http://localhost:8005/contas?status=ABERTA&page=1" \
  -H "Authorization: Bearer {token}"
```

---

#### Criar Conta (Interno)
```http
POST /contas
```

**Request Body:**
```json
{
  "pedido_id": "uuid",
  "cliente_id": "uuid",
  "valor_total": 114.80,
  "data_vencimento": "2026-06-10"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "pedido_id": "uuid",
  "cliente_id": "uuid",
  "valor_total": 114.80,
  "valor_pago": 0.00,
  "saldo": 114.80,
  "data_vencimento": "2026-06-10",
  "status": "ABERTA",
  "criado_em": "2026-05-26T10:00:00Z"
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:8005/contas \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "pedido_id":"550e8400-e29b-41d4-a716-446655440005",
    "cliente_id":"550e8400-e29b-41d4-a716-446655440000",
    "valor_total":114.80,
    "data_vencimento":"2026-06-10"
  }'
```

---

#### Detalhe da Conta
```http
GET /contas/{id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "pedido_id": "uuid",
  "cliente": {
    "id": "uuid",
    "nome": "João Silva",
    "cpf": "12345678909",
    "telefone": "+5511999999999"
  },
  "valor_total": 114.80,
  "valor_pago": 50.00,
  "saldo": 64.80,
  "data_vencimento": "2026-06-10",
  "status": "ABERTA",
  "pagamentos": [
    {
      "id": "uuid",
      "valor": 50.00,
      "data_pagamento": "2026-05-27T14:30:00Z",
      "forma_pagamento": "DINHEIRO",
      "observacoes": "Pagamento parcial"
    }
  ],
  "criado_em": "2026-05-26T10:00:00Z",
  "atualizado_em": "2026-05-27T14:30:00Z"
}
```

**Exemplo cURL:**
```bash
curl -X GET http://localhost:8005/contas/550e8400-e29b-41d4-a716-446655440010 \
  -H "Authorization: Bearer {token}"
```

---

#### Contas do Cliente
```http
GET /contas/cliente/{cliente_id}
```

**Query Parameters:**
- `status` (string, opcional): Filtrar por status

**Response 200:**
```json
[
  {
    "id": "uuid",
    "pedido_id": "uuid",
    "valor_total": 114.80,
    "valor_pago": 50.00,
    "saldo": 64.80,
    "data_vencimento": "2026-06-10",
    "status": "ABERTA",
    "criado_em": "2026-05-26T10:00:00Z"
  }
]
```

**Exemplo cURL:**
```bash
curl -X GET http://localhost:8005/contas/cliente/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {token}"
```

---

#### Contas a Vencer
```http
GET /contas/vencer
```

**Query Parameters:**
- `dias` (int, opcional): Número de dias à frente (padrão: 7)

**Response 200:**
```json
[
  {
    "id": "uuid",
    "cliente_id": "uuid",
    "cliente_nome": "João Silva",
    "valor_total": 114.80,
    "saldo": 64.80,
    "data_vencimento": "2026-06-02",
    "dias_para_vencer": 7
  }
]
```

**Exemplo cURL:**
```bash
curl -X GET "http://localhost:8005/contas/vencer?dias=7" \
  -H "Authorization: Bearer {token}"
```

---

#### Contas Vencidas
```http
GET /contas/vencidas
```

**Response 200:**
```json
[
  {
    "id": "uuid",
    "cliente_id": "uuid",
    "cliente_nome": "Maria Santos",
    "valor_total": 200.00,
    "saldo": 200.00,
    "data_vencimento": "2026-05-20",
    "dias_vencido": 6
  }
]
```

**Exemplo cURL:**
```bash
curl -X GET http://localhost:8005/contas/vencidas \
  -H "Authorization: Bearer {token}"
```

---

### Pagamentos

#### Registrar Pagamento
```http
POST /contas/{id}/pagamentos
```

**Request Body:**
```json
{
  "valor": 50.00,
  "forma_pagamento": "DINHEIRO",
  "data_pagamento": "2026-05-27T14:30:00Z",
  "observacoes": "Pagamento parcial"
}
```

**Formas de Pagamento:**
- `DINHEIRO` - Pagamento em dinheiro
- `PIX` - Pagamento via PIX
- `CARTAO_CREDITO` - Cartão de crédito
- `CARTAO_DEBITO` - Cartão de débito
- `TRANSFERENCIA` - Transferência bancária

**Response 201:**
```json
{
  "id": "uuid",
  "conta_id": "uuid",
  "valor": 50.00,
  "forma_pagamento": "DINHEIRO",
  "data_pagamento": "2026-05-27T14:30:00Z",
  "observacoes": "Pagamento parcial",
  "saldo_restante": 64.80
}
```

**Exemplo cURL (Pagamento Parcial):**
```bash
curl -X POST http://localhost:8005/contas/550e8400-e29b-41d4-a716-446655440010/pagamentos \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "valor":50.00,
    "forma_pagamento":"DINHEIRO",
    "data_pagamento":"2026-05-27T14:30:00Z",
    "observacoes":"Pagamento parcial"
  }'
```

**Exemplo cURL (Quitação):**
```bash
curl -X POST http://localhost:8005/contas/550e8400-e29b-41d4-a716-446655440010/pagamentos \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "valor":64.80,
    "forma_pagamento":"PIX",
    "data_pagamento":"2026-05-28T10:00:00Z",
    "observacoes":"Quitação total"
  }'
```

---

#### Marcar como Vencida (job interno previsto)
```http
PATCH /contas/{id}/marcar-vencida
```

**Response 200:** Conta marcada como vencida

> O job que chamaria esta rota também não existe: `marcar-vencida` não aparece em
> nenhum código do repositório (só nesta documentação), e `services/financeiro/` não tem pasta de jobs
> nem entrada de cron.

**Exemplo cURL:**
```bash
curl -X PATCH http://localhost:8005/contas/550e8400-e29b-41d4-a716-446655440010/marcar-vencida \
  -H "Authorization: Bearer {token}"
```

---

## 💡 Casos de Uso

### Caso 1: Consultar Contas em Aberto de um Cliente

```javascript
// Buscar todas as contas em aberto do cliente
const contasAbertas = await axios.get(
  `http://localhost:8005/contas/cliente/${clienteId}?status=ABERTA`,
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

// Calcular total devido
const totalDevido = contasAbertas.data.reduce((sum, conta) => sum + conta.saldo, 0);
console.log('Total devido:', totalDevido);
```

---

### Caso 2: Registrar Pagamento Parcial

```javascript
// Cliente paga parte da conta
const contaId = '550e8400-e29b-41d4-a716-446655440010';

const pagamento = await axios.post(
  `http://localhost:8005/contas/${contaId}/pagamentos`,
  {
    valor: 50.00,
    forma_pagamento: 'DINHEIRO',
    data_pagamento: new Date().toISOString(),
    observacoes: 'Pagamento parcial - primeira parcela'
  },
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

console.log('Saldo restante:', pagamento.data.saldo_restante);
```

---

### Caso 3: Quitar Conta Completamente

```javascript
// Buscar detalhe da conta
const conta = await axios.get(
  `http://localhost:8005/contas/${contaId}`,
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

// Quitar o saldo restante
const quitacao = await axios.post(
  `http://localhost:8005/contas/${contaId}/pagamentos`,
  {
    valor: conta.data.saldo,
    forma_pagamento: 'PIX',
    data_pagamento: new Date().toISOString(),
    observacoes: 'Quitação total'
  },
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

console.log('Conta quitada! Status:', quitacao.data.status); // PAGA
```

---

### Caso 4: Monitorar Contas a Vencer

```javascript
// Buscar contas que vencem nos próximos 7 dias
const contasVencer = await axios.get(
  'http://localhost:8005/contas/vencer?dias=7',
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

// Enviar notificações para clientes
for (const conta of contasVencer.data) {
  console.log(`Cliente ${conta.cliente_nome} tem conta vencendo em ${conta.dias_para_vencer} dias`);
  // Enviar WhatsApp via API de Notificações
}
```

---

### Caso 5: Listar Contas Vencidas

```javascript
// Buscar todas as contas vencidas
const contasVencidas = await axios.get(
  'http://localhost:8005/contas/vencidas',
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

// Gerar relatório
console.log('Total de contas vencidas:', contasVencidas.data.length);

const totalVencido = contasVencidas.data.reduce((sum, conta) => sum + conta.saldo, 0);
console.log('Valor total vencido:', totalVencido);

// Listar clientes inadimplentes
contasVencidas.data.forEach(conta => {
  console.log(`${conta.cliente_nome}: R$ ${conta.saldo} (${conta.dias_vencido} dias)`);
});
```

---

### Caso 6: Histórico de Pagamentos de uma Conta

```javascript
// Buscar detalhe da conta com histórico de pagamentos
const conta = await axios.get(
  `http://localhost:8005/contas/${contaId}`,
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

console.log('Valor total:', conta.data.valor_total);
console.log('Valor pago:', conta.data.valor_pago);
console.log('Saldo:', conta.data.saldo);

// Listar todos os pagamentos
conta.data.pagamentos.forEach(pag => {
  console.log(`${pag.data_pagamento}: R$ ${pag.valor} (${pag.forma_pagamento})`);
});
```

---

### Caso 7: Relatório de Contas por Período

```javascript
// Buscar contas de um período específico
const relatorio = await axios.get(
  'http://localhost:8005/contas?data_inicio=2026-05-01&data_fim=2026-05-31',
  {
    headers: { Authorization: `Bearer ${token}` }
  }
);

// Agrupar por status
const porStatus = relatorio.data.items.reduce((acc, conta) => {
  acc[conta.status] = (acc[conta.status] || 0) + 1;
  return acc;
}, {});

console.log('Contas por status:', porStatus);

// Calcular valores
const totalFaturado = relatorio.data.items.reduce((sum, c) => sum + c.valor_total, 0);
const totalRecebido = relatorio.data.items.reduce((sum, c) => sum + c.valor_pago, 0);
const totalPendente = relatorio.data.items.reduce((sum, c) => sum + c.saldo, 0);

console.log('Total faturado:', totalFaturado);
console.log('Total recebido:', totalRecebido);
console.log('Total pendente:', totalPendente);
```

---

## 🚨 Códigos de Erro (planejados)

Hoje qualquer caminho listado acima responde `404`, e o `@app.exception_handler`
de `main.py` converte exceção não tratada em `500 {"detail": "Erro interno do
servidor"}`. O resto da tabela é intenção.

| Código | Descrição |
|--------|-----------|
| 400 | Requisição inválida / Valor de pagamento inválido |
| 401 | Não autenticado |
| 403 | Sem permissão (role insuficiente) |
| 404 | Conta não encontrada |
| 409 | Conflito (ex: conta já paga) |
| 422 | Validação falhou |
| 500 | Erro interno do servidor |

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Financeiro](../11-regras-negocio/financeiro.md)
- [API de Vendas](./vendas-api.md) - Integração com pedidos
- [API de Clientes](./clientes-api.md) - Gestão de crédito
- [Guia de Autenticação](./guia-autenticacao.md)
- [Exemplos Práticos](./exemplos-praticos.md)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Status:** especificação planejada — nenhum endpoint deste documento existe no código  
**Versão:** 0.1.0 (rascunho de especificação)
