# Exemplos de API - Frontend

> Exemplos de payloads de requisição e resposta para referência rápida durante desenvolvimento

---

## 🔐 Autenticação

### Login

**Request:**
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@runas.com&password=Admin@123
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "nome": "Administrador",
    "email": "admin@runas.com",
    "role": "ADMIN",
    "ativo": true
  }
}
```

### Refresh Token

**Request:**
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 👥 Clientes

### Listar Clientes

**Request:**
```http
GET /clientes?page=1&size=20&nome=João&bloqueado=false
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "cpf": "12345678909",
      "nome": "João Silva",
      "telefone": "+5511999999999",
      "email": "joao@email.com",
      "data_nasc": "1990-01-15",
      "limite_credito": 1000.00,
      "credito_disponivel": 750.00,
      "dia_vencimento": 10,
      "bloqueado": false,
      "ativo": true,
      "criado_em": "2026-01-01T10:00:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

### Criar Cliente

**Request:**
```http
POST /clientes
Authorization: Bearer {token}
Content-Type: application/json

{
  "cpf": "12345678909",
  "nome": "João Silva",
  "telefone": "+5511999999999",
  "email": "joao@email.com",
  "data_nasc": "1990-01-15"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "cpf": "12345678909",
  "nome": "João Silva",
  "telefone": "+5511999999999",
  "email": "joao@email.com",
  "data_nasc": "1990-01-15",
  "limite_credito": 0.00,
  "credito_disponivel": 0.00,
  "dia_vencimento": null,
  "bloqueado": false,
  "ativo": true,
  "criado_em": "2026-05-25T10:00:00Z"
}
```

### Adicionar Endereço

**Request:**
```http
POST /clientes/{id}/enderecos
Authorization: Bearer {token}
Content-Type: application/json

{
  "cep": "01234567",
  "logradouro": "Rua das Flores",
  "numero": "123",
  "complemento": "Apto 45",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "uf": "SP",
  "principal": true
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "cliente_id": "uuid",
  "cep": "01234567",
  "logradouro": "Rua das Flores",
  "numero": "123",
  "complemento": "Apto 45",
  "bairro": "Centro",
  "cidade": "São Paulo",
  "uf": "SP",
  "principal": true
}
```

---

## 📦 Produtos

### Listar Produtos

**Request:**
```http
GET /produtos?page=1&size=20&categoria_id=uuid&ativo=true
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "categoria_id": "uuid",
      "categoria_nome": "Bebidas",
      "nome": "Coca-Cola",
      "descricao": "Refrigerante",
      "ativo": true,
      "variantes_count": 3,
      "criado_em": "2026-01-01T10:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### Criar Produto com Variante

**Request:**
```http
POST /produtos
Authorization: Bearer {token}
Content-Type: application/json

{
  "categoria_id": "uuid",
  "nome": "Coca-Cola",
  "descricao": "Refrigerante"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "categoria_id": "uuid",
  "nome": "Coca-Cola",
  "descricao": "Refrigerante",
  "ativo": true,
  "criado_em": "2026-05-25T10:00:00Z"
}
```

### Adicionar Variante

**Request:**
```http
POST /produtos/{id}/variantes
Authorization: Bearer {token}
Content-Type: application/json

{
  "sku": "COCA-350ML",
  "preco_custo": 2.50,
  "markup_pct": 50.00,
  "atributos": [
    { "chave": "tamanho", "valor": "350ml" },
    { "chave": "tipo", "valor": "Lata" }
  ]
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "produto_id": "uuid",
  "sku": "COCA-350ML",
  "preco_custo": 2.50,
  "markup_pct": 50.00,
  "preco_venda": 3.75,
  "ativo": true,
  "atributos": [
    {
      "id": "uuid",
      "chave": "tamanho",
      "valor": "350ml"
    },
    {
      "id": "uuid",
      "chave": "tipo",
      "valor": "Lata"
    }
  ]
}
```

---

## 📊 Estoque

### Consultar Estoque

**Request:**
```http
GET /estoque/{variante_id}
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": "uuid",
  "variante_id": "uuid",
  "quantidade": 100,
  "quantidade_minima": 20,
  "atualizado_em": "2026-05-25T10:00:00Z"
}
```

### Entrada de Estoque

**Request:**
```http
POST /estoque/{variante_id}/entrada
Authorization: Bearer {token}
Content-Type: application/json

{
  "quantidade": 50,
  "motivo": "Compra de fornecedor",
  "documento": "NF-12345",
  "observacao": "Lote 2026-05"
}
```

**Response (200):**
```json
{
  "movimentacao": {
    "id": "uuid",
    "variante_id": "uuid",
    "tipo": "ENTRADA",
    "quantidade": 50,
    "motivo": "Compra de fornecedor",
    "documento": "NF-12345",
    "observacao": "Lote 2026-05",
    "criado_em": "2026-05-25T10:00:00Z"
  },
  "estoque_atual": {
    "quantidade": 150,
    "quantidade_minima": 20
  }
}
```

### Listar Alertas de Estoque Baixo

**Request:**
```http
GET /estoque/alertas/minimo
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "items": [
    {
      "variante_id": "uuid",
      "sku": "COCA-350ML",
      "produto_nome": "Coca-Cola",
      "quantidade": 15,
      "quantidade_minima": 20,
      "diferenca": -5
    }
  ],
  "total": 5
}
```

---

## 🛒 Vendas/Pedidos

### Listar Pedidos

**Request:**
```http
GET /pedidos?page=1&size=20&status=PENDENTE
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "cliente_id": "uuid",
      "cliente_nome": "João Silva",
      "origem": "BALCAO",
      "modalidade_pagto": "A_VISTA",
      "modalidade_entrega": "RETIRADA",
      "status": "PENDENTE",
      "subtotal": 100.00,
      "desconto": 0.00,
      "frete": 0.00,
      "total": 100.00,
      "criado_em": "2026-05-25T10:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "size": 20,
  "pages": 2
}
```

### Detalhes do Pedido

**Request:**
```http
GET /pedidos/{id}
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": "uuid",
  "cliente": {
    "id": "uuid",
    "nome": "João Silva",
    "telefone": "+5511999999999"
  },
  "origem": "BALCAO",
  "modalidade_pagto": "A_VISTA",
  "modalidade_entrega": "RETIRADA",
  "status": "PENDENTE",
  "itens": [
    {
      "id": "uuid",
      "variante_id": "uuid",
      "sku": "COCA-350ML",
      "produto_nome": "Coca-Cola",
      "quantidade": 10,
      "preco_unitario": 3.75,
      "subtotal": 37.50
    }
  ],
  "subtotal": 100.00,
  "desconto": 0.00,
  "frete": 0.00,
  "total": 100.00,
  "pagamento": {
    "metodo": "DINHEIRO",
    "status_confirmacao": "PENDENTE"
  },
  "criado_em": "2026-05-25T10:00:00Z",
  "atualizado_em": "2026-05-25T10:00:00Z"
}
```

### Atualizar Status do Pedido

**Request:**
```http
PATCH /pedidos/{id}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "CONFIRMADO"
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "status": "CONFIRMADO",
  "atualizado_em": "2026-05-25T10:05:00Z"
}
```

---

## 💰 Financeiro

### Listar Contas a Receber

**Request:**
```http
GET /contas?page=1&size=20&status=VENCIDO
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "cliente_id": "uuid",
      "cliente_nome": "João Silva",
      "pedido_id": "uuid",
      "valor_original": 100.00,
      "valor_pago": 0.00,
      "saldo_devedor": 100.00,
      "data_vencimento": "2026-05-20",
      "status": "VENCIDO",
      "criado_em": "2026-05-10T10:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

### Registrar Pagamento

**Request:**
```http
POST /contas/{id}/pagamentos
Authorization: Bearer {token}
Content-Type: application/json

{
  "valor": 50.00,
  "forma": "DINHEIRO",
  "observacao": "Pagamento parcial"
}
```

**Response (201):**
```json
{
  "pagamento": {
    "id": "uuid",
    "conta_id": "uuid",
    "valor": 50.00,
    "forma": "DINHEIRO",
    "observacao": "Pagamento parcial",
    "pago_em": "2026-05-25T10:00:00Z"
  },
  "conta_atualizada": {
    "id": "uuid",
    "valor_original": 100.00,
    "valor_pago": 50.00,
    "saldo_devedor": 50.00,
    "status": "PARCIAL"
  }
}
```

---

## ❌ Erros Comuns

### 400 - Bad Request

```json
{
  "detail": "CPF inválido"
}
```

### 401 - Unauthorized

```json
{
  "detail": "Token inválido ou expirado"
}
```

### 403 - Forbidden

```json
{
  "detail": "Permissão negada. Apenas ADMIN pode acessar este recurso"
}
```

### 404 - Not Found

```json
{
  "detail": "Cliente não encontrado"
}
```

### 409 - Conflict

```json
{
  "detail": "CPF já cadastrado no sistema"
}
```

### 422 - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "cpf"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "telefone"],
      "msg": "Telefone deve estar no formato E.164",
      "type": "value_error"
    }
  ]
}
```

### 500 - Internal Server Error

```json
{
  "detail": "Erro interno do servidor. Tente novamente mais tarde."
}
```

---

## 🔍 Paginação Padrão

Todos os endpoints de listagem seguem o mesmo padrão:

**Query Parameters:**
- `page`: Número da página (default: 1)
- `size`: Itens por página (default: 20, max: 100)

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8
}
```

---

**Versão:** 1.0.0  
**Data:** 2026-05-25  
**Status:** ✅ Exemplos Completos
