# API de Clientes - Runas

> **Referência completa** da API do serviço de Clientes

---

## 📋 Visão Geral

**Base URL**: `http://localhost:8001`  
**Autenticação**: Bearer Token (JWT)  
**Formato**: JSON

---

## 🔐 Autenticação

Todas as rotas (exceto as públicas) requerem autenticação via JWT:

```http
Authorization: Bearer <access_token>
```

---

## 📍 Endpoints

### Clientes

#### Listar Clientes
```http
GET /clientes
```

**Query Parameters:**
- `page` (int, opcional): Número da página (padrão: 1)
- `size` (int, opcional): Itens por página (padrão: 20)
- `nome` (string, opcional): Filtrar por nome
- `cpf` (string, opcional): Filtrar por CPF
- `bloqueado` (boolean, opcional): Filtrar por status de bloqueio

**Response 200:**
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
      "credito_disponivel": 800.00,
      "bloqueado": false,
      "ativo": true,
      "criado_em": "2026-05-26T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

---

#### Buscar Cliente por ID
```http
GET /clientes/{id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "cpf": "12345678909",
  "nome": "João Silva",
  "telefone": "+5511999999999",
  "email": "joao@email.com",
  "data_nasc": "1990-01-15",
  "limite_credito": 1000.00,
  "credito_disponivel": 800.00,
  "dia_vencimento": 10,
  "bloqueado": false,
  "ativo": true,
  "criado_em": "2026-05-26T10:00:00Z"
}
```

---

#### Buscar Cliente por CPF
```http
GET /clientes/cpf/{cpf}
```

**Response 200:** Mesmo formato do endpoint anterior

---

#### Criar Cliente
```http
POST /clientes
```

**Request Body:**
```json
{
  "cpf": "12345678909",
  "nome": "João Silva",
  "telefone": "+5511999999999",
  "email": "joao@email.com",
  "data_nasc": "1990-01-15",
  "limite_credito": 1000.00,
  "dia_vencimento": 10
}
```

**Response 201:** Cliente criado

---

#### Atualizar Cliente
```http
PATCH /clientes/{id}
```

**Request Body:** (todos os campos opcionais)
```json
{
  "nome": "João Silva Santos",
  "telefone": "+5511988888888",
  "email": "joao.novo@email.com"
}
```

**Response 200:** Cliente atualizado

---

#### Desativar Cliente (Soft Delete)
```http
DELETE /clientes/{id}
```

**Response 204:** Cliente desativado

---

### Endereços

#### Listar Endereços do Cliente
```http
GET /clientes/{id}/enderecos
```

**Response 200:**
```json
[
  {
    "id": "uuid",
    "cliente_id": "uuid",
    "cep": "01310-100",
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "complemento": "Apto 101",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP",
    "principal": true
  }
]
```

---

#### Adicionar Endereço
```http
POST /clientes/{id}/enderecos
```

**Request Body:**
```json
{
  "cep": "01310-100",
  "logradouro": "Av. Paulista",
  "numero": "1000",
  "complemento": "Apto 101",
  "bairro": "Bela Vista",
  "cidade": "São Paulo",
  "uf": "SP",
  "principal": false
}
```

**Response 201:** Endereço criado

---

#### Atualizar Endereço
```http
PATCH /clientes/{id}/enderecos/{endereco_id}
```

**Request Body:** (campos opcionais)

**Response 200:** Endereço atualizado

---

#### Remover Endereço
```http
DELETE /clientes/{id}/enderecos/{endereco_id}
```

**Response 204:** Endereço removido

---

### Gestão de Crédito (ADMIN)

#### Ajustar Limite de Crédito
```http
PATCH /clientes/{id}/credito
```

**Request Body:**
```json
{
  "limite_credito": 2000.00,
  "dia_vencimento": 15
}
```

**Response 200:** Crédito atualizado

---

#### Bloquear Cliente
```http
PATCH /clientes/{id}/bloquear
```

**Response 200:** Cliente bloqueado

---

#### Desbloquear Cliente
```http
PATCH /clientes/{id}/desbloquear
```

**Response 200:** Cliente desbloqueado

---

#### Histórico de Crédito
```http
GET /clientes/{id}/historico-credito
```

**Response 200:**
```json
[
  {
    "data": "2026-05-26T10:00:00Z",
    "tipo": "COMPRA",
    "valor": -200.00,
    "saldo_anterior": 1000.00,
    "saldo_novo": 800.00,
    "referencia": "Pedido #123"
  }
]
```

---

## 🚨 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Sem permissão (role insuficiente) |
| 404 | Cliente não encontrado |
| 409 | CPF já cadastrado / Cliente com pendências |
| 422 | Validação falhou |
| 500 | Erro interno do servidor |

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Clientes](../11-regras-negocio/clientes.md)
- [Diagramas de Sequência - Clientes](../03-arquitetura/diagramas/sequencia/clientes.md)
- [Mapeamento Completo de Rotas](./mapeamento-rotas.md)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
