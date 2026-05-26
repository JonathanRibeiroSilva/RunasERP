# 🔄 Arquitetura de Comunicação - ERP Runas

Documentação sobre como os microsserviços se comunicam entre si.

---

## 🎯 Padrões de Comunicação

O ERP Runas utiliza **DOIS padrões** de comunicação:

### 1. Cliente → API Gateway → Microsserviço (Síncrono)

Para requisições **externas** (clientes, frontend, apps):

```
Cliente/Frontend
      │
      │ HTTPS
      ▼
API Gateway (8000)
      │
      ├─ Valida JWT
      ├─ Verifica Permissões
      │
      │ HTTP Interno
      ▼
Microsserviço (800X)
```

**Uso**: Todas as requisições vindas de fora do sistema.

---

### 2. Microsserviço ↔ Microsserviço (Síncrono)

Para comunicação **interna** entre serviços:

```
Serviço A (ex: Vendas)
      │
      │ HTTP Direto
      ▼
Serviço B (ex: Clientes)
```

**Uso**: Quando um serviço precisa de dados de outro serviço.

---

### 3. Microsserviço → RabbitMQ → Microsserviço (Assíncrono)

Para eventos e notificações:

```
Serviço A
      │
      │ Publica Evento
      ▼
RabbitMQ
      │
      │ Consome Evento
      ▼
Serviço B
```

**Uso**: Notificações, eventos de domínio, operações não críticas.

---

## ✅ Comunicação Direta Entre Serviços (CORRETO)

### Por Que Comunicação Direta?

1. **Performance**: Sem overhead do gateway
2. **Simplicidade**: Menos saltos na rede
3. **Isolamento**: Gateway não precisa conhecer lógica interna
4. **Escalabilidade**: Cada serviço pode escalar independentemente

### Regras da Especificação

> **"Comunicação entre serviços via HTTP (httpx async) — nunca importar código de outro serviço"**

Isso significa:
- ✅ Serviços podem chamar outros serviços via HTTP
- ❌ Serviços NÃO podem importar código de outros serviços
- ✅ Cada serviço é completamente isolado
- ✅ Comunicação apenas via API REST

---

## 📊 Mapeamento de Comunicações

### Vendas → Outros Serviços

```python
# Vendas precisa comunicar com:

1. Clientes (verificar crédito)
   POST http://clientes:8001/clientes/{id}/credito
   
2. Estoque (verificar disponibilidade)
   GET http://estoque:8003/estoque/{variante_id}
   
3. Estoque (dar baixa)
   POST http://estoque:8003/estoque/{variante_id}/saida
   
4. Financeiro (criar conta a receber)
   POST http://financeiro:8005/contas
```

### Produtos → Estoque

```python
# Produtos precisa consultar estoque para catálogo público

GET http://estoque:8003/estoque/{variante_id}
```

### Financeiro → Clientes

```python
# Financeiro precisa atualizar crédito do cliente

PATCH http://clientes:8001/clientes/{id}/credito
```

### Financeiro → Clientes (Bloqueio)

```python
# Financeiro precisa bloquear cliente inadimplente

PATCH http://clientes:8001/clientes/{id}/bloquear
```

---

## 🔒 Isolamento dos Microsserviços

### ✅ O Que Está Isolado

Cada microsserviço tem:

1. **Banco de Dados Próprio**
   ```
   db-clientes:5432/clientes
   db-produtos:5432/produtos
   db-estoque:5432/estoque
   db-vendas:5432/vendas
   db-financeiro:5432/financeiro
   db-notificacoes:5432/notificacoes
   ```

2. **Código Independente**
   - Sem imports entre serviços
   - Sem dependências compartilhadas (exceto `shared/`)
   - Cada um com seu `requirements.txt`

3. **Deploy Independente**
   - Cada serviço pode ser atualizado separadamente
   - Falha em um não afeta os outros

4. **Escala Independente**
   - Pode escalar apenas o serviço que precisa
   - Recursos dedicados por serviço

---

## 🔄 Fluxos de Comunicação Completos

### Fluxo 1: Checkout Fiado

```
1. Cliente → API Gateway
   POST /carrinho/{token}/checkout
   Body: { modalidade_pagto: "FIADO", cliente_id: "..." }

2. API Gateway → Vendas
   POST http://vendas:8004/carrinho/{token}/checkout

3. Vendas → Clientes (HTTP Direto)
   GET http://clientes:8001/clientes/{id}
   Verifica: bloqueado=False, credito_disponivel >= total

4. Vendas → Clientes (HTTP Direto)
   PATCH http://clientes:8001/clientes/{id}/credito
   Body: { delta: -total }  # Debita crédito

5. Vendas → Estoque (HTTP Direto)
   POST http://estoque:8003/estoque/{variante_id}/saida
   Body: { quantidade: X, referencia_id: pedido_id }

6. Vendas → Financeiro (HTTP Direto)
   POST http://financeiro:8005/contas
   Body: { cliente_id, pedido_id, valor, data_vencimento }

7. Vendas → RabbitMQ (Assíncrono)
   Publica: pedido.confirmado

8. Notificações ← RabbitMQ
   Consome: pedido.confirmado
   Envia WhatsApp para cliente

9. Vendas → API Gateway → Cliente
   Response: { pedido_id, status: "CONFIRMADO" }
```

### Fluxo 2: Catálogo Público

```
1. Cliente → API Gateway
   GET /catalogo

2. API Gateway → Produtos
   GET http://produtos:8002/catalogo

3. Produtos → Estoque (HTTP Direto)
   Para cada variante:
   GET http://estoque:8003/estoque/{variante_id}
   Filtra apenas com quantidade > 0

4. Produtos → API Gateway → Cliente
   Response: [ produtos com estoque disponível ]
```

### Fluxo 3: Cobrança Vencida

```
1. Celery Beat (00:00)
   Trigger: Job diário

2. Financeiro
   Busca contas vencidas no próprio banco

3. Financeiro → Clientes (HTTP Direto)
   Para cada cliente com conta vencida:
   GET http://clientes:8001/clientes/{id}
   Verifica: credito_disponivel == 0

4. Financeiro → Clientes (HTTP Direto)
   PATCH http://clientes:8001/clientes/{id}/bloquear

5. Financeiro → RabbitMQ (Assíncrono)
   Publica: cobranca.vencida

6. Notificações ← RabbitMQ
   Consome: cobranca.vencida
   Envia WhatsApp para cliente
```

---

## 🛡️ Segurança na Comunicação Interna

### Rede Docker Isolada

```yaml
# docker-compose.yml
networks:
  erp-network:
    driver: bridge
```

Todos os serviços na mesma rede privada:
- ✅ Podem se comunicar entre si
- ❌ Não são acessíveis de fora (exceto via gateway)

### Portas Expostas

```yaml
# Apenas o gateway é exposto externamente
api-gateway:
  ports:
    - "8000:8000"  # ✅ Exposto

# Microsserviços NÃO são expostos
clientes:
  # Sem ports: []  # ❌ Não exposto
```

### Autenticação Interna

**Opção 1**: Sem autenticação (rede privada)
- Serviços confiam uns nos outros
- Rede Docker isolada

**Opção 2**: Service-to-Service Auth (futuro)
- Tokens internos
- mTLS
- Service mesh

**MVP**: Opção 1 (sem auth interna)

---

## 📊 Verificação de Isolamento

### ✅ Checklist

- [x] Cada serviço tem seu próprio banco de dados
- [x] Cada serviço tem seu próprio Dockerfile
- [x] Cada serviço tem seu próprio requirements.txt
- [x] Nenhum serviço importa código de outro
- [x] Comunicação apenas via HTTP ou RabbitMQ
- [x] Shared module apenas para tipos comuns
- [x] Cada serviço pode ser deployado independentemente
- [x] Cada serviço pode escalar independentemente

### ✅ Configuração Atual

```python
# services/vendas/config.py
class Settings(BaseSettings):
    DATABASE_URL: str  # Próprio banco
    RABBITMQ_URL: str  # Mensageria compartilhada
    REDIS_URL: str     # Cache compartilhado
    
    # URLs para comunicação HTTP direta
    CLIENTES_URL: str = "http://clientes:8001"
    ESTOQUE_URL: str = "http://estoque:8003"
    FINANCEIRO_URL: str = "http://financeiro:8005"
```

**Status**: ✅ **CORRETO**

---

## 🎯 Resumo

### Cliente → Sistema

```
Cliente → API Gateway → Microsserviço
```

**Uso**: Requisições externas  
**Autenticação**: JWT no gateway  
**Exemplo**: `POST /clientes`

### Microsserviço ↔ Microsserviço

```
Serviço A → HTTP Direto → Serviço B
```

**Uso**: Comunicação interna  
**Autenticação**: Nenhuma (rede privada)  
**Exemplo**: Vendas consulta Clientes

### Eventos Assíncronos

```
Serviço A → RabbitMQ → Serviço B
```

**Uso**: Notificações, eventos  
**Autenticação**: Nenhuma  
**Exemplo**: `pedido.confirmado`

---

## ✅ Conclusão

A arquitetura atual está **CORRETA**:

✅ Microsserviços são isolados (cada um com seu banco)  
✅ Comunicação direta entre serviços via HTTP  
✅ Gateway apenas para requisições externas  
✅ RabbitMQ para eventos assíncronos  
✅ Rede Docker privada para segurança  

**Não precisa mudar nada!** 🎉

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0  
**Status**: ✅ Arquitetura Validada
