# 📡 Referência de APIs - Runas

Documentação completa de todas as APIs do sistema Runas.

---

## 📑 Índice

### APIs por Serviço

1. **[API Gateway](./api-gateway.md)** - Autenticação e roteamento
2. **[API de Clientes](./clientes-api.md)** (~200 linhas) - Gestão de clientes e endereços
3. **[API de Produtos](./produtos-api.md)** (~600 linhas) - Catálogo, variantes e fornecedores
4. **[API de Estoque](./estoque-api.md)** (~400 linhas) - Controle de estoque e movimentações
5. **[API de Vendas](./vendas-api.md)** (~650 linhas) - Carrinho, pedidos e pagamentos
6. **[API Financeiro](./financeiro-api.md)** (~550 linhas) - Contas a receber e crédito
7. **[API de Notificações](./notificacoes-api.md)** - WhatsApp e alertas

### Documentos Gerais

- **[Mapeamento de Rotas](./mapeamento-rotas.md)** - Como as rotas são mapeadas do Gateway para os serviços
- **[Autenticação](./autenticacao.md)** - Como funciona a autenticação JWT e OAuth2
- **[Códigos de Erro](./codigos-erro.md)** - Lista completa de códigos de erro

### Guias e Exemplos

- **[Guia de Autenticação](./guia-autenticacao.md)** (~500 linhas) - Guia completo de autenticação OAuth2 e JWT com exemplos em JavaScript/TypeScript e Python
- **[Exemplos Práticos](./exemplos-praticos.md)** (~400 linhas) - 7 cenários completos com código (cadastro, vendas, estoque, relatórios, integrações)

---

## 🎯 Visão Geral

### Arquitetura de APIs

```
Cliente/Frontend
      │
      │ HTTPS
      ▼
API Gateway (:8000)
      │
      ├─ /auth/*          → API Gateway (autenticação)
      ├─ /clientes/*      → Clientes Service (:8001)
      ├─ /produtos/*      → Produtos Service (:8002)
      ├─ /catalogo/*      → Produtos Service (:8002)
      ├─ /estoque/*       → Estoque Service (:8003)
      ├─ /vendas/*        → Vendas Service (:8004)
      ├─ /carrinho/*      → Vendas Service (:8004)
      ├─ /pedidos/*       → Vendas Service (:8004)
      ├─ /financeiro/*    → Financeiro Service (:8005)
      └─ /notificacoes/*  → Notificações Service (:8006)
```

### Base URL

**Desenvolvimento**: `http://localhost:8000`  
**Produção**: `https://api.runas.com.br`

---

## 🔐 Autenticação

### Obter Token

```http
POST /auth/login
Content-Type: application/json

{
  "email": "usuario@exemplo.com",
  "password": "senha123"
}
```

**Resposta**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Usar Token

Incluir o token no header de todas as requisições protegidas:

```http
GET /clientes
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## 📊 Formato de Resposta

### Sucesso

```json
{
  "data": { ... },
  "message": "Operação realizada com sucesso"
}
```

### Lista Paginada

```json
{
  "items": [ ... ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

### Erro

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos",
    "details": {
      "cpf": ["CPF inválido"]
    }
  }
}
```

---

## 🔢 Códigos HTTP

| Código | Significado | Quando Usar |
|--------|-------------|-------------|
| **200** | OK | Operação bem-sucedida (GET, PUT, PATCH) |
| **201** | Created | Recurso criado (POST) |
| **204** | No Content | Operação bem-sucedida sem retorno (DELETE) |
| **400** | Bad Request | Dados inválidos ou regra de negócio violada |
| **401** | Unauthorized | Token ausente ou inválido |
| **403** | Forbidden | Sem permissão para a operação |
| **404** | Not Found | Recurso não encontrado |
| **409** | Conflict | Conflito (ex: CPF duplicado) |
| **422** | Unprocessable Entity | Validação de dados falhou |
| **500** | Internal Server Error | Erro interno do servidor |

---

## 🔒 Níveis de Permissão

| Role | Descrição | Acesso |
|------|-----------|--------|
| **ADMIN** | Administrador | Acesso total ao sistema |
| **GERENTE** | Gerente | Gestão de produtos, estoque, vendas |
| **VENDEDOR** | Vendedor | Criar vendas, consultar clientes |
| **OPERADOR** | Operador | Operações básicas de caixa |

---

## 📝 Convenções

### Nomenclatura de Endpoints

- **Plural**: `/clientes`, `/produtos`, `/vendas`
- **Kebab-case**: `/contas-receber`, `/fornecedores-produtos`
- **Recursos aninhados**: `/clientes/{id}/enderecos`

### Parâmetros de Query

- **Paginação**: `?page=1&per_page=20`
- **Filtros**: `?nome=João&ativo=true`
- **Ordenação**: `?sort=nome&order=asc`
- **Busca**: `?search=termo`

### Formato de Datas

- **ISO 8601**: `2026-05-26T10:30:00Z`
- **Apenas data**: `2026-05-26`

### Formato de Valores Monetários

- **Decimal**: `123.45` (sempre 2 casas decimais)
- **Moeda**: BRL (Real Brasileiro)

---

## 🚀 Rate Limiting

- **Limite**: 100 requisições por minuto por IP
- **Headers de resposta**:
  - `X-RateLimit-Limit`: Limite total
  - `X-RateLimit-Remaining`: Requisições restantes
  - `X-RateLimit-Reset`: Timestamp de reset

**Quando excedido**: HTTP 429 Too Many Requests

---

## 📚 Documentação Interativa

### Swagger UI

Acesse a documentação interativa em:

**Desenvolvimento**: http://localhost:8000/docs  
**Produção**: https://api.runas.com.br/docs

### ReDoc

Documentação alternativa em:

**Desenvolvimento**: http://localhost:8000/redoc  
**Produção**: https://api.runas.com.br/redoc

---

## 🔍 Exemplos de Uso

### cURL

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@runas.com","password":"admin123"}'

# Listar clientes
curl -X GET http://localhost:8000/clientes \
  -H "Authorization: Bearer {token}"
```

### JavaScript (Axios)

```javascript
// Login
const response = await axios.post('http://localhost:8000/auth/login', {
  email: 'admin@runas.com',
  password: 'admin123'
});

const token = response.data.access_token;

// Listar clientes
const clientes = await axios.get('http://localhost:8000/clientes', {
  headers: { Authorization: `Bearer ${token}` }
});
```

### Python (Requests)

```python
import requests

# Login
response = requests.post('http://localhost:8000/auth/login', json={
    'email': 'admin@runas.com',
    'password': 'admin123'
})

token = response.json()['access_token']

# Listar clientes
clientes = requests.get('http://localhost:8000/clientes', headers={
    'Authorization': f'Bearer {token}'
})
```

---

## 📄 Especificação OpenAPI

A API do Runas está completamente documentada no formato OpenAPI 3.0:

- **[openapi.yaml](./openapi.yaml)** - Especificação completa OpenAPI 3.0

### Visualizar a Documentação

#### Opção 1: Swagger UI (Recomendado)

Acesse a documentação interativa em:
```
http://localhost:8000/docs
```

#### Opção 2: Swagger Editor Online

1. Acesse https://editor.swagger.io/
2. Copie o conteúdo de `openapi.yaml`
3. Cole no editor

#### Opção 3: Redoc

Acesse a documentação alternativa em:
```
http://localhost:8000/redoc
```

### Gerar Cliente de API

Você pode gerar clientes de API automaticamente usando o OpenAPI Generator:

```bash
# Instalar OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Gerar cliente TypeScript
openapi-generator-cli generate \
  -i docs/10-api-reference/openapi.yaml \
  -g typescript-axios \
  -o frontend/src/api/generated

# Gerar cliente Python
openapi-generator-cli generate \
  -i docs/10-api-reference/openapi.yaml \
  -g python \
  -o clients/python
```

---

## 📚 Documentos Relacionados

- **[OpenAPI Specification](./openapi.yaml)** - Especificação completa da API
- [Diagramas de Sequência](../03-arquitetura/diagramas/sequencia.md)
- [Regras de Negócio](../11-regras-negocio/)
- [Guia de Desenvolvimento](../07-desenvolvimento/)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
