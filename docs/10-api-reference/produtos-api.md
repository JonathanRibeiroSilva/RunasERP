# API de Produtos - Runas

> **Referência completa** da API do serviço de Produtos

---

## 📋 Visão Geral

**Base URL**: `http://localhost:8002`  
**Autenticação**: Bearer Token (JWT)  
**Formato**: JSON

---

## � Autenticação

Todas as rotas (exceto `/catalogo`) requerem autenticação via JWT:

```http
Authorization: Bearer <access_token>
```

---

## 📍 Categorias

### Listar Categorias
```http
GET /categorias
```

**Response 200:**
```json
[
  {
    "id": "uuid",
    "nome": "Bebidas",
    "descricao": "Bebidas em geral"
  }
]
```

**Exemplo cURL:**
```bash
curl -X GET "http://localhost:8002/categorias" \
  -H "Authorization: Bearer <token>"
```

---

### Criar Categoria
```http
POST /categorias
```

**Request Body:**
```json
{
  "nome": "Bebidas",
  "descricao": "Bebidas em geral"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "nome": "Bebidas",
  "descricao": "Bebidas em geral"
}
```

**Exemplo cURL:**
```bash
curl -X POST "http://localhost:8002/categorias" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Bebidas",
    "descricao": "Bebidas em geral"
  }'
```

---

## 📦 Produtos

### Listar Produtos
```http
GET /produtos
```

**Query Parameters:**
- `page` (int, opcional): Número da página (padrão: 1)
- `size` (int, opcional): Itens por página (padrão: 20)
- `categoria_id` (uuid, opcional): Filtrar por categoria
- `ativo` (boolean, opcional): Filtrar por status
- `nome` (string, opcional): Buscar por nome

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "categoria_id": "uuid",
      "nome": "Coca-Cola",
      "descricao": "Refrigerante",
      "ativo": true,
      "criado_em": "2026-05-26T10:00:00Z",
      "variantes": [
        {
          "id": "uuid",
          "sku": "COCA-2L",
          "preco_custo": 5.00,
          "markup_pct": 40.0,
          "preco_venda": 7.00,
          "ativo": true,
          "atributos": [
            {"chave": "tamanho", "valor": "2L"}
          ]
        }
      ]
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
curl -X GET "http://localhost:8002/produtos?categoria_id=uuid&page=1&size=20" \
  -H "Authorization: Bearer <token>"
```

---

### Criar Produto
```http
POST /produtos
```

**Request Body:**
```json
{
  "categoria_id": "uuid",
  "nome": "Coca-Cola",
  "descricao": "Refrigerante"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "categoria_id": "uuid",
  "nome": "Coca-Cola",
  "descricao": "Refrigerante",
  "ativo": true,
  "criado_em": "2026-05-26T10:00:00Z",
  "variantes": []
}
```

**Exemplo cURL:**
```bash
curl -X POST "http://localhost:8002/produtos" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "categoria_id": "uuid",
    "nome": "Coca-Cola",
    "descricao": "Refrigerante"
  }'
```

---

### Buscar Produto
```http
GET /produtos/{id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "categoria_id": "uuid",
  "nome": "Coca-Cola",
  "descricao": "Refrigerante",
  "ativo": true,
  "criado_em": "2026-05-26T10:00:00Z",
  "variantes": [
    {
      "id": "uuid",
      "sku": "COCA-2L",
      "preco_custo": 5.00,
      "markup_pct": 40.0,
      "preco_venda": 7.00,
      "ativo": true,
      "atributos": [
        {"chave": "tamanho", "valor": "2L"}
      ]
    }
  ],
  "catalogo": {
    "visivel": true,
    "destaque": false,
    "ordem_exibicao": 0,
    "descricao_publica": "Refrigerante Coca-Cola 2L",
    "fotos": [
      {
        "url": "https://example.com/coca.jpg",
        "ordem": 0
      }
    ]
  }
}
```

---

## 🏷️ Variantes

### Adicionar Variante
```http
POST /produtos/{id}/variantes
```

**Request Body:**
```json
{
  "sku": "COCA-2L",
  "preco_custo": 5.00,
  "markup_pct": 40.0,
  "atributos": [
    {"chave": "tamanho", "valor": "2L"}
  ]
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "produto_id": "uuid",
  "sku": "COCA-2L",
  "preco_custo": 5.00,
  "markup_pct": 40.0,
  "preco_venda": 7.00,
  "ativo": true,
  "atributos": [
    {"chave": "tamanho", "valor": "2L"}
  ]
}
```

**Cálculo Automático:**
```
preco_venda = preco_custo * (1 + markup_pct / 100)
preco_venda = 5.00 * (1 + 40 / 100)
preco_venda = 5.00 * 1.40
preco_venda = 7.00
```

**Exemplo cURL:**
```bash
curl -X POST "http://localhost:8002/produtos/{id}/variantes" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "COCA-2L",
    "preco_custo": 5.00,
    "markup_pct": 40.0,
    "atributos": [
      {"chave": "tamanho", "valor": "2L"}
    ]
  }'
```

---

### Atualizar Variante
```http
PATCH /produtos/{id}/variantes/{variante_id}
```

**Request Body:** (todos os campos opcionais)
```json
{
  "preco_custo": 5.50,
  "markup_pct": 45.0
}
```

**Response 200:**
```json
{
  "id": "uuid",
  "produto_id": "uuid",
  "sku": "COCA-2L",
  "preco_custo": 5.50,
  "markup_pct": 45.0,
  "preco_venda": 7.98,
  "ativo": true
}
```

---

## 🛒 Catálogo Público

### Listar Produtos do Catálogo (SEM AUTENTICAÇÃO)
```http
GET /catalogo
```

**Query Parameters:**
- `page` (int, opcional): Número da página
- `size` (int, opcional): Itens por página
- `categoria_id` (uuid, opcional): Filtrar por categoria

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "nome": "Coca-Cola",
      "descricao_publica": "Refrigerante Coca-Cola 2L",
      "destaque": false,
      "fotos": [
        {
          "url": "https://example.com/coca.jpg",
          "ordem": 0
        }
      ],
      "variantes": [
        {
          "id": "uuid",
          "sku": "COCA-2L",
          "preco_venda": 7.00,
          "atributos": [
            {"chave": "tamanho", "valor": "2L"}
          ],
          "estoque_disponivel": 50
        }
      ]
    }
  ],
  "total": 20,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

**Exemplo cURL:**
```bash
# Não precisa de token!
curl -X GET "http://localhost:8002/catalogo?page=1&size=20"
```

---

### Configurar Catálogo (ADMIN)
```http
PATCH /produtos/{id}/catalogo
```

**Request Body:**
```json
{
  "visivel": true,
  "destaque": true,
  "ordem_exibicao": 1,
  "descricao_publica": "Refrigerante Coca-Cola 2L - Gelada!"
}
```

**Response 200:**
```json
{
  "produto_id": "uuid",
  "visivel": true,
  "destaque": true,
  "ordem_exibicao": 1,
  "descricao_publica": "Refrigerante Coca-Cola 2L - Gelada!",
  "atualizado_em": "2026-05-26T10:00:00Z"
}
```

---

### Adicionar Foto ao Catálogo (ADMIN)
```http
POST /produtos/{id}/catalogo/fotos
```

**Request Body:**
```json
{
  "url": "https://example.com/coca.jpg",
  "ordem": 0
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "produto_id": "uuid",
  "url": "https://example.com/coca.jpg",
  "ordem": 0
}
```

---

## 🏭 Fornecedores

### Listar Fornecedores
```http
GET /fornecedores
```

**Response 200:**
```json
[
  {
    "id": "uuid",
    "cnpj": "12345678000190",
    "razao_social": "Distribuidora ABC Ltda",
    "nome_fantasia": "ABC Distribuidora",
    "telefone": "+5511999999999",
    "email": "contato@abc.com",
    "prazo_entrega_dias": 3,
    "ativo": true
  }
]
```

---

### Criar Fornecedor
```http
POST /fornecedores
```

**Request Body:**
```json
{
  "cnpj": "12345678000190",
  "razao_social": "Distribuidora ABC Ltda",
  "nome_fantasia": "ABC Distribuidora",
  "telefone": "+5511999999999",
  "email": "contato@abc.com",
  "prazo_entrega_dias": 3
}
```

**Response 201:** Fornecedor criado

---

### Vincular Produto a Fornecedor
```http
POST /fornecedores/{id}/produtos
```

**Request Body:**
```json
{
  "produto_id": "uuid",
  "preco_custo": 5.00,
  "cod_fornecedor": "ABC-COCA-2L",
  "principal": true
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "fornecedor_id": "uuid",
  "produto_id": "uuid",
  "preco_custo": 5.00,
  "cod_fornecedor": "ABC-COCA-2L",
  "principal": true
}
```

---

## 🚨 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 403 | Sem permissão (role insuficiente) |
| 404 | Produto/Categoria não encontrado |
| 409 | SKU duplicado / Categoria com produtos vinculados |
| 422 | Validação falhou (CNPJ inválido, etc) |
| 500 | Erro interno do servidor |

---

## 💡 Casos de Uso

### Caso 1: Cadastrar Produto Completo

```bash
# 1. Criar categoria
CATEGORIA_ID=$(curl -X POST "http://localhost:8002/categorias" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Bebidas"}' | jq -r '.id')

# 2. Criar produto
PRODUTO_ID=$(curl -X POST "http://localhost:8002/produtos" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"categoria_id\": \"$CATEGORIA_ID\",
    \"nome\": \"Coca-Cola\",
    \"descricao\": \"Refrigerante\"
  }" | jq -r '.id')

# 3. Adicionar variantes
curl -X POST "http://localhost:8002/produtos/$PRODUTO_ID/variantes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "COCA-2L",
    "preco_custo": 5.00,
    "markup_pct": 40.0,
    "atributos": [{"chave": "tamanho", "valor": "2L"}]
  }'

# 4. Publicar no catálogo
curl -X PATCH "http://localhost:8002/produtos/$PRODUTO_ID/catalogo" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "visivel": true,
    "destaque": false,
    "descricao_publica": "Refrigerante Coca-Cola 2L"
  }'
```

---

### Caso 2: Atualizar Preços em Lote

```python
import requests

TOKEN = "seu_token_aqui"
BASE_URL = "http://localhost:8002"

# Buscar todos os produtos
response = requests.get(
    f"{BASE_URL}/produtos",
    headers={"Authorization": f"Bearer {TOKEN}"}
)
produtos = response.json()["items"]

# Aumentar markup em 10% para todos
for produto in produtos:
    for variante in produto["variantes"]:
        novo_markup = variante["markup_pct"] + 10
        
        requests.patch(
            f"{BASE_URL}/produtos/{produto['id']}/variantes/{variante['id']}",
            headers={"Authorization": f"Bearer {TOKEN}"},
            json={"markup_pct": novo_markup}
        )
        
print("Preços atualizados!")
```

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Produtos](../11-regras-negocio/produtos.md)
- [Diagramas de Sequência - Produtos](../03-arquitetura/diagramas/sequencia/produtos.md)
- [Mapeamento Completo de Rotas](./mapeamento-rotas.md)
- [OpenAPI Specification](./openapi.yaml)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
