# 🔀 Mapeamento de Rotas - API Gateway

Documentação completa de como as rotas são mapeadas do API Gateway para os microsserviços.

---

## 📊 Visão Geral

```
Cliente → API Gateway (8000) → Microsserviço (800X)
```

O API Gateway atua como **proxy reverso**, roteando todas as requisições para os microsserviços apropriados.

---

## 🔐 Rotas de Autenticação

Processadas diretamente no API Gateway:

| Método | Rota | Autenticação | Descrição |
|--------|------|--------------|-----------|
| POST | `/auth/login` | ❌ Pública | Login OAuth2 |
| POST | `/auth/refresh` | ❌ Pública | Renovar token |
| POST | `/auth/logout` | ✅ Requerida | Logout |

**Implementação**: `api-gateway/routers/auth.py`

---

## 🛒 Rotas Públicas (Sem Autenticação)

### Catálogo de Produtos

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| GET | `/catalogo` | `/catalogo` | Produtos (8002) |
| GET | `/catalogo/{id}` | `/catalogo/{id}` | Produtos (8002) |

### Carrinho de Compras

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| POST | `/carrinho` | `/carrinho` | Vendas (8004) |
| GET | `/carrinho/{token}` | `/carrinho/{token}` | Vendas (8004) |
| POST | `/carrinho/{token}/itens` | `/carrinho/{token}/itens` | Vendas (8004) |
| PATCH | `/carrinho/{token}/itens/{id}` | `/carrinho/{token}/itens/{id}` | Vendas (8004) |
| DELETE | `/carrinho/{token}/itens/{id}` | `/carrinho/{token}/itens/{id}` | Vendas (8004) |
| POST | `/carrinho/{token}/checkout` | `/carrinho/{token}/checkout` | Vendas (8004) |

### Webhooks

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| POST | `/pagamentos/webhook/mercadopago` | `/pagamentos/webhook/mercadopago` | Vendas (8004) |

---

## 🔒 Rotas Protegidas (Autenticação Requerida)

### Clientes

**Permissão**: ADMIN ou OPERADOR

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| POST | `/clientes` | `/clientes` | Clientes (8001) |
| GET | `/clientes` | `/clientes` | Clientes (8001) |
| GET | `/clientes/{id}` | `/clientes/{id}` | Clientes (8001) |
| GET | `/clientes/cpf/{cpf}` | `/clientes/cpf/{cpf}` | Clientes (8001) |
| PATCH | `/clientes/{id}` | `/clientes/{id}` | Clientes (8001) |
| DELETE | `/clientes/{id}` | `/clientes/{id}` | Clientes (8001) |
| POST | `/clientes/{id}/enderecos` | `/clientes/{id}/enderecos` | Clientes (8001) |
| GET | `/clientes/{id}/enderecos` | `/clientes/{id}/enderecos` | Clientes (8001) |
| PATCH | `/clientes/{id}/enderecos/{eid}` | `/clientes/{id}/enderecos/{eid}` | Clientes (8001) |
| DELETE | `/clientes/{id}/enderecos/{eid}` | `/clientes/{id}/enderecos/{eid}` | Clientes (8001) |
| PATCH | `/clientes/{id}/credito` | `/clientes/{id}/credito` | Clientes (8001) |
| PATCH | `/clientes/{id}/bloquear` | `/clientes/{id}/bloquear` | Clientes (8001) |
| PATCH | `/clientes/{id}/desbloquear` | `/clientes/{id}/desbloquear` | Clientes (8001) |

### Produtos

**Permissão**: ADMIN ou OPERADOR (leitura) / ADMIN (escrita)

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| POST | `/produtos` | `/produtos` | Produtos (8002) |
| GET | `/produtos` | `/produtos` | Produtos (8002) |
| GET | `/produtos/{id}` | `/produtos/{id}` | Produtos (8002) |
| PATCH | `/produtos/{id}` | `/produtos/{id}` | Produtos (8002) |
| DELETE | `/produtos/{id}` | `/produtos/{id}` | Produtos (8002) |
| POST | `/produtos/{id}/variantes` | `/produtos/{id}/variantes` | Produtos (8002) |
| PATCH | `/produtos/{id}/variantes/{vid}` | `/produtos/{id}/variantes/{vid}` | Produtos (8002) |
| DELETE | `/produtos/{id}/variantes/{vid}` | `/produtos/{id}/variantes/{vid}` | Produtos (8002) |
| POST | `/categorias` | `/categorias` | Produtos (8002) |
| GET | `/categorias` | `/categorias` | Produtos (8002) |
| POST | `/fornecedores` | `/fornecedores` | Produtos (8002) |
| GET | `/fornecedores` | `/fornecedores` | Produtos (8002) |

### Pedidos

**Permissão**: ADMIN ou OPERADOR

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| GET | `/pedidos` | `/pedidos` | Vendas (8004) |
| GET | `/pedidos/{id}` | `/pedidos/{id}` | Vendas (8004) |
| PATCH | `/pedidos/{id}/status` | `/pedidos/{id}/status` | Vendas (8004) |
| DELETE | `/pedidos/{id}/cancelar` | `/pedidos/{id}/cancelar` | Vendas (8004) |
| PATCH | `/pedidos/{id}/frete` | `/pedidos/{id}/frete` | Vendas (8004) |

### Pagamentos

**Permissão**: ADMIN

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| PATCH | `/pagamentos/{pedido_id}/confirmar` | `/pagamentos/{pedido_id}/confirmar` | Vendas (8004) |

---

## 🔐 Rotas Apenas ADMIN

### Estoque

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| POST | `/estoque` | `/estoque` | Estoque (8003) |
| GET | `/estoque` | `/estoque` | Estoque (8003) |
| GET | `/estoque/{variante_id}` | `/estoque/{variante_id}` | Estoque (8003) |
| POST | `/estoque/{variante_id}/entrada` | `/estoque/{variante_id}/entrada` | Estoque (8003) |
| POST | `/estoque/{variante_id}/saida` | `/estoque/{variante_id}/saida` | Estoque (8003) |
| POST | `/estoque/{variante_id}/ajuste` | `/estoque/{variante_id}/ajuste` | Estoque (8003) |
| GET | `/estoque/{variante_id}/movimentacoes` | `/estoque/{variante_id}/movimentacoes` | Estoque (8003) |
| GET | `/estoque/alertas/minimo` | `/estoque/alertas/minimo` | Estoque (8003) |

### Financeiro

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| POST | `/contas` | `/contas` | Financeiro (8005) |
| GET | `/contas` | `/contas` | Financeiro (8005) |
| GET | `/contas/{id}` | `/contas/{id}` | Financeiro (8005) |
| GET | `/contas/cliente/{cliente_id}` | `/contas/cliente/{cliente_id}` | Financeiro (8005) |
| POST | `/contas/{id}/pagamentos` | `/contas/{id}/pagamentos` | Financeiro (8005) |
| GET | `/contas/vencer` | `/contas/vencer` | Financeiro (8005) |
| GET | `/contas/vencidas` | `/contas/vencidas` | Financeiro (8005) |

### Notificações

| Método | Rota Gateway | Rota Microsserviço | Serviço |
|--------|--------------|-------------------|---------|
| GET | `/notificacoes` | `/notificacoes` | Notificações (8006) |
| POST | `/notificacoes/{id}/reenviar` | `/notificacoes/{id}/reenviar` | Notificações (8006) |

---

## 🔄 Fluxo de Requisição

### Exemplo: Criar Cliente

```
1. Cliente faz requisição:
   POST http://localhost:8000/clientes
   Authorization: Bearer {token}
   Body: { "nome": "João", "cpf": "12345678909", ... }

2. API Gateway:
   a. Valida token JWT
   b. Verifica role (ADMIN ou OPERADOR)
   c. Identifica serviço: /clientes → Clientes (8001)
   d. Faz proxy da requisição

3. Proxy HTTP:
   POST http://clientes:8001/clientes
   Headers: copiados da requisição original
   Body: copiado da requisição original

4. Serviço de Clientes:
   a. Processa requisição
   b. Valida CPF
   c. Salva no banco
   d. Retorna resposta

5. API Gateway:
   a. Recebe resposta do microsserviço
   b. Retorna para o cliente
```

---

## 🛡️ Segurança

### Validação de Token

Todas as rotas protegidas passam por:

1. **Extração do token**: Header `Authorization: Bearer {token}`
2. **Validação JWT**: Verifica assinatura e expiração
3. **Verificação de blacklist**: Consulta Redis
4. **Busca do usuário**: Consulta banco de dados
5. **Verificação de role**: Confere permissões

### Roles e Permissões

| Role | Permissões |
|------|-----------|
| **ADMIN** | Acesso total a todos os endpoints |
| **OPERADOR** | Leitura de produtos, criação de pedidos, consulta de clientes |

---

## 🔧 Configuração

### Variáveis de Ambiente

```env
# URLs dos microsserviços
CLIENTES_URL=http://clientes:8001
PRODUTOS_URL=http://produtos:8002
ESTOQUE_URL=http://estoque:8003
VENDAS_URL=http://vendas:8004
FINANCEIRO_URL=http://financeiro:8005
NOTIFICACOES_URL=http://notificacoes:8006
```

### Timeout

- **Padrão**: 30 segundos
- **Configurável** em: `api-gateway/proxy/service_proxy.py`

---

## 🧪 Testando o Roteamento

### 1. Testar Autenticação

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123"

# Salvar o access_token retornado
TOKEN="eyJ..."
```

### 2. Testar Rota Pública

```bash
# Catálogo (sem autenticação)
curl http://localhost:8000/catalogo
```

### 3. Testar Rota Protegida

```bash
# Listar clientes (com autenticação)
curl http://localhost:8000/clientes \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Testar Rota Admin

```bash
# Listar estoque (apenas admin)
curl http://localhost:8000/estoque \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 Monitoramento

### Logs

Todas as requisições são logadas:

```json
{
  "event": "proxy.request",
  "method": "GET",
  "path": "/clientes",
  "target": "http://clientes:8001/clientes",
  "timestamp": "2026-05-14T10:30:00Z"
}
```

### Health Check

```bash
# API Gateway
curl http://localhost:8000/health

# Microsserviços (através do gateway)
curl http://localhost:8001/health  # Clientes
curl http://localhost:8002/health  # Produtos
curl http://localhost:8003/health  # Estoque
curl http://localhost:8004/health  # Vendas
curl http://localhost:8005/health  # Financeiro
curl http://localhost:8006/health  # Notificações
```

---

## ⚠️ Tratamento de Erros

| Erro | Status | Descrição |
|------|--------|-----------|
| Serviço não encontrado | 404 | Rota não mapeada |
| Timeout | 504 | Serviço não respondeu |
| Conexão recusada | 503 | Serviço indisponível |
| Erro interno | 500 | Erro no proxy |

---

## ✅ Checklist de Verificação

- [x] API Gateway tem proxy configurado
- [x] Rotas públicas mapeadas
- [x] Rotas protegidas com autenticação
- [x] Rotas admin com verificação de role
- [x] URLs dos serviços no .env
- [x] Timeout configurado
- [x] Logs estruturados
- [x] Tratamento de erros

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0  
**Status**: ✅ Roteamento Completo
