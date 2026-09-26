# API de Estoque - Runas

> **Referência completa** da API do serviço de Estoque

---

## 📋 Visão Geral

**Base URL**: `http://localhost:8003`  
**Autenticação**: Bearer Token (JWT)  
**Formato**: JSON

---

## 📍 Endpoints

### Listar Estoque
```http
GET /estoque
```

**Query Parameters:**
- `page` (int): Número da página (padrão: 1)
- `size` (int): Itens por página (padrão: 20)
- `variante_id` (uuid, opcional): Filtrar por variante
- `abaixo_minimo` (boolean, opcional): Apenas itens abaixo do mínimo

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "variante_id": "uuid",
      "quantidade": 50,
      "quantidade_minima": 10,
      "atualizado_em": "2026-05-26T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

---

### Consultar Estoque de Variante
```http
GET /estoque/{variante_id}
```

**Response 200:**
```json
{
  "id": "uuid",
  "variante_id": "uuid",
  "quantidade": 50,
  "quantidade_minima": 10,
  "atualizado_em": "2026-05-26T10:00:00Z"
}
```

**Exemplo cURL:**
```bash
curl -X GET "http://localhost:8003/estoque/{variante_id}" \
  -H "Authorization: Bearer <token>"
```

---

### Registrar Entrada
```http
POST /estoque/{variante_id}/entrada
```

**Request Body:**
```json
{
  "quantidade": 100,
  "motivo": "Compra do fornecedor ABC",
  "referencia_id": "uuid-nota-fiscal"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "variante_id": "uuid",
  "tipo": "ENTRADA",
  "quantidade": 100,
  "motivo": "Compra do fornecedor ABC",
  "referencia_id": "uuid-nota-fiscal",
  "criado_em": "2026-05-26T10:00:00Z"
}
```

**Exemplo cURL:**
```bash
curl -X POST "http://localhost:8003/estoque/{variante_id}/entrada" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "quantidade": 100,
    "motivo": "Compra do fornecedor ABC"
  }'
```

---

### Registrar Saída
```http
POST /estoque/{variante_id}/saida
```

**Request Body:**
```json
{
  "quantidade": 10,
  "motivo": "Venda balcão",
  "referencia_id": "uuid-pedido"
}
```

**Response 201:** Movimentação criada

**Erro 422:** Estoque insuficiente
```json
{
  "detail": "Estoque insuficiente. Disponível: 5, Solicitado: 10"
}
```

---

### Ajuste de Inventário
```http
POST /estoque/{variante_id}/ajuste
```

**Request Body:**
```json
{
  "quantidade": 45,
  "motivo": "Inventário mensal - contagem física"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "variante_id": "uuid",
  "tipo": "AJUSTE",
  "quantidade": -5,
  "motivo": "Inventário mensal - contagem física",
  "criado_em": "2026-05-26T10:00:00Z"
}
```

**Nota:** O sistema calcula automaticamente a diferença:
- Estoque atual: 50
- Quantidade informada: 45
- Ajuste registrado: -5

---

### Histórico de Movimentações
```http
GET /estoque/{variante_id}/movimentacoes
```

**Query Parameters:**
- `page` (int): Número da página
- `size` (int): Itens por página
- `tipo` (string, opcional): ENTRADA, SAIDA, AJUSTE, DEVOLUCAO

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "variante_id": "uuid",
      "tipo": "ENTRADA",
      "quantidade": 100,
      "motivo": "Compra do fornecedor ABC",
      "referencia_id": "uuid",
      "criado_em": "2026-05-26T10:00:00Z"
    },
    {
      "id": "uuid",
      "variante_id": "uuid",
      "tipo": "SAIDA",
      "quantidade": -10,
      "motivo": "Venda pedido #123",
      "referencia_id": "uuid-pedido",
      "criado_em": "2026-05-26T11:00:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

---

### Alertas de Estoque Mínimo
```http
GET /estoque/alertas/minimo
```

**Response 200:**
```json
[
  {
    "variante_id": "uuid",
    "sku": "COCA-2L",
    "produto_nome": "Coca-Cola",
    "quantidade_atual": 5,
    "quantidade_minima": 10,
    "diferenca": -5
  }
]
```

**Exemplo cURL:**
```bash
curl -X GET "http://localhost:8003/estoque/alertas/minimo" \
  -H "Authorization: Bearer <token>"
```

---

## 💡 Casos de Uso

### Caso 1: Receber Mercadoria do Fornecedor

```bash
# 1. Registrar entrada para cada produto
curl -X POST "http://localhost:8003/estoque/{variante_id}/entrada" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "quantidade": 100,
    "motivo": "NF 12345 - Fornecedor ABC",
    "referencia_id": "uuid-nota-fiscal"
  }'

# 2. Verificar estoque atualizado
curl -X GET "http://localhost:8003/estoque/{variante_id}" \
  -H "Authorization: Bearer $TOKEN"
```

---

### Caso 2: Inventário Mensal

```python
import requests

TOKEN = "seu_token_aqui"
BASE_URL = "http://localhost:8003"

# Lista de contagem física
inventario = [
    {"variante_id": "uuid-1", "quantidade_contada": 45},
    {"variante_id": "uuid-2", "quantidade_contada": 120},
    {"variante_id": "uuid-3", "quantidade_contada": 8}
]

# Ajustar cada item
for item in inventario:
    response = requests.post(
        f"{BASE_URL}/estoque/{item['variante_id']}/ajuste",
        headers={"Authorization": f"Bearer {TOKEN}"},
        json={
            "quantidade": item["quantidade_contada"],
            "motivo": "Inventário mensal - 26/05/2026"
        }
    )
    print(f"Ajustado: {item['variante_id']}")
```

---

### Caso 3: Monitorar Estoque Baixo

```bash
# Verificar alertas
curl -X GET "http://localhost:8003/estoque/alertas/minimo" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Resultado:
# [
#   {
#     "sku": "COCA-2L",
#     "quantidade_atual": 5,
#     "quantidade_minima": 10
#   }
# ]

# Fazer pedido ao fornecedor...
```

---

## 🚨 Regras Importantes

### 1. Movimentações são Imutáveis
- ❌ Não é possível editar ou deletar movimentações
- ✅ Para corrigir, faça um novo ajuste

### 2. Quantidade Nunca Negativa
- Sistema impede saídas maiores que estoque disponível
- Retorna erro 422 se tentar

### 3. Alertas Automáticos
- Quando `quantidade <= quantidade_minima`
- Evento `estoque.minimo` publicado no RabbitMQ
- Notificação WhatsApp enviada automaticamente

### 4. Transações Atômicas
- Movimentação + Atualização de estoque = 1 transação
- Se falhar, nada é salvo

---

## 🚨 Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Requisição inválida |
| 401 | Não autenticado |
| 404 | Variante não encontrada |
| 422 | Estoque insuficiente / Quantidade inválida |
| 500 | Erro interno |

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Estoque](../11-regras-negocio/estoque.md)
- [Mapeamento Completo de Rotas](./mapeamento-rotas.md)
- [OpenAPI Specification](./openapi.yaml)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
