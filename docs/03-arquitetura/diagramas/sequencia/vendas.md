# 🛒 Diagramas de Sequência - Vendas

**Data**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Domínio**: Vendas (Carrinho e Pedidos)

---

## 📑 Índice

1. [Criar Carrinho](#391-criar-carrinho)
2. [Adicionar Item ao Carrinho](#392-adicionar-item-ao-carrinho)
3. [Remover Item do Carrinho](#393-remover-item-do-carrinho)
4. [Finalizar Carrinho (Checkout)](#394-finalizar-carrinho-criar-pedido)
5. [Confirmar Pagamento (Webhook)](#395-confirmar-pagamento-e-converter-pedido-em-venda)
6. [Cancelar Pedido](#396-cancelar-pedido)

---

## 3.9.1. Criar Carrinho (POST /api/carrinho)

```mermaid
sequenceDiagram
    participant U as Usuário (Cliente)
    participant G as API Gateway
    participant V as Vendas Service
    participant C as Clientes Service
    participant DB as PostgreSQL (Vendas)
    participant R as Redis
    
    U->>G: POST /api/carrinho<br/>{cliente_id (opcional)}
    
    alt Cliente autenticado
        G->>V: POST /carrinho<br/>{cliente_id}
        V->>C: GET /clientes/{cliente_id}
        C->>V: Cliente encontrado
    else Cliente anônimo
        G->>V: POST /carrinho<br/>(sem cliente_id)
    end
    
    V->>V: Gerar token único do carrinho
    V->>V: token = uuid4()
    
    V->>R: SET carrinho:{token}<br/>{cliente_id, itens: [], criado_em,<br/>expira_em: +2h}
    R->>V: Carrinho criado no cache
    
    V->>G: 201 Created<br/>{carrinho_token, expira_em}
    G->>U: 201 Created
```

### Carrinho no Redis

**Por que Redis?**
- ✅ **Performance**: Acesso ultra-rápido (in-memory)
- ✅ **TTL**: Expiração automática após 2 horas
- ✅ **Escalabilidade**: Não sobrecarrega banco principal
- ✅ **Temporário**: Carrinho é transitório, não precisa persistir

**Estrutura do Carrinho**:
```json
{
  "token": "abc123-def456-ghi789",
  "cliente_id": "uuid",
  "itens": [],
  "total": 0.00,
  "criado_em": "2026-05-26T10:00:00Z",
  "expira_em": "2026-05-26T12:00:00Z"
}
```

### Carrinho Anônimo vs Autenticado

**Anônimo**:
- Não requer login
- Identificado apenas por token
- Expira em 2 horas
- Não salva histórico

**Autenticado**:
- Vinculado ao cliente
- Pode ser recuperado em outro dispositivo
- Histórico de carrinhos abandonados
- Pode enviar lembretes

---

## 3.9.2. Adicionar Item ao Carrinho (POST /api/carrinho/{token}/itens)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant V as Vendas Service
    participant P as Produtos Service
    participant E as Estoque Service
    participant R as Redis
    
    U->>G: POST /api/carrinho/{token}/itens<br/>{produto_id, variante_id, quantidade}
    G->>V: POST /carrinho/{token}/itens
    
    V->>R: GET carrinho:{token}
    R->>V: Dados do carrinho
    
    alt Carrinho não encontrado ou expirado
        V->>G: 404 Not Found<br/>"Carrinho não encontrado"
        G->>U: 404 Not Found
    else Carrinho válido
        Note over V: 1. Validar Produto
        V->>P: GET /produtos/{produto_id}
        P->>V: Produto encontrado e ativo
        
        alt variante_id fornecido
            V->>P: GET /produtos/{produto_id}/variantes/{variante_id}
            P->>V: Variante encontrada e ativa
        end
        
        Note over V: 2. Verificar Disponibilidade
        V->>E: GET /estoque?produto_id={produto_id}<br/>&variante_id={variante_id}
        E->>V: {quantidade_disponivel}
        
        alt Estoque insuficiente
            V->>G: 400 Bad Request<br/>"Estoque insuficiente"
            G->>U: 400 Bad Request
        else Estoque suficiente
            Note over V: 3. Reservar Estoque
            V->>E: POST /estoque/reservar<br/>{produto_id, quantidade,<br/>documento: "CARRINHO-{token}"}
            E->>V: Estoque reservado
            
            Note over V: 4. Adicionar ao Carrinho
            V->>V: Adicionar item ao carrinho<br/>Calcular subtotal e total
            
            V->>R: SET carrinho:{token}<br/>{...carrinho, itens: [...]}
            R->>V: Carrinho atualizado
            
            V->>G: 201 Created<br/>{item_id, subtotal, total_carrinho}
            G->>U: 201 Created
        end
    end
```

### Fluxo de Validações

1. **Carrinho existe?** → 404 se não encontrado
2. **Produto ativo?** → 400 se inativo
3. **Variante ativa?** → 400 se inativa
4. **Estoque disponível?** → 400 se insuficiente
5. **Reserva OK?** → Adiciona ao carrinho

### Item do Carrinho

```json
{
  "item_id": "uuid",
  "produto_id": "uuid",
  "produto_nome": "Coca-Cola 2L",
  "variante_id": "uuid",
  "sku": "COCA-2L-PT",
  "quantidade": 2,
  "preco_unitario": 8.00,
  "subtotal": 16.00
}
```

### Carrinho Atualizado

```json
{
  "token": "abc123",
  "cliente_id": "uuid",
  "itens": [
    {
      "item_id": "uuid-1",
      "produto_nome": "Coca-Cola 2L",
      "quantidade": 2,
      "preco_unitario": 8.00,
      "subtotal": 16.00
    },
    {
      "item_id": "uuid-2",
      "produto_nome": "Guaraná 2L",
      "quantidade": 1,
      "preco_unitario": 7.00,
      "subtotal": 7.00
    }
  ],
  "total": 23.00,
  "expira_em": "2026-05-26T12:00:00Z"
}
```

---

## 3.9.3. Remover Item do Carrinho (DELETE /api/carrinho/{token}/itens/{item_id})

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant V as Vendas Service
    participant E as Estoque Service
    participant R as Redis
    
    U->>G: DELETE /api/carrinho/{token}/itens/{item_id}
    G->>V: DELETE /carrinho/{token}/itens/{item_id}
    
    V->>R: GET carrinho:{token}
    R->>V: Dados do carrinho
    
    V->>V: Encontrar item no carrinho
    
    alt Item não encontrado
        V->>G: 404 Not Found
        G->>U: 404 Not Found
    else Item encontrado
        Note over V: 1. Liberar Reserva de Estoque
        V->>E: POST /estoque/liberar-reserva<br/>{produto_id, quantidade,<br/>documento: "CARRINHO-{token}"}
        E->>V: Reserva liberada
        
        Note over V: 2. Remover do Carrinho
        V->>V: Remover item<br/>Recalcular total
        
        V->>R: SET carrinho:{token}<br/>{...carrinho sem item}
        R->>V: Carrinho atualizado
        
        V->>G: 204 No Content
        G->>U: 204 No Content
    end
```

### Importante: Liberar Reserva

Ao remover item do carrinho, **sempre liberar a reserva de estoque**:
- Devolve quantidade para `quantidade_disponivel`
- Diminui `quantidade_reservada`
- Permite que outros clientes comprem

### Atualizar Quantidade

Para atualizar quantidade (não remover):
```http
PUT /api/carrinho/{token}/itens/{item_id}
{
  "quantidade": 3
}
```

**Fluxo**:
1. Se aumentar: Reservar diferença adicional
2. Se diminuir: Liberar diferença
3. Atualizar carrinho

---

## 3.9.4. Finalizar Carrinho (Criar Pedido) (POST /api/carrinho/{token}/checkout)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant V as Vendas Service
    participant C as Clientes Service
    participant E as Estoque Service
    participant F as Financeiro Service
    participant R as Redis
    participant DB as PostgreSQL (Vendas)
    participant MQ as RabbitMQ
    
    U->>G: POST /api/carrinho/{token}/checkout<br/>{cliente_id, endereco_entrega_id,<br/>forma_pagamento, ...}
    G->>V: POST /carrinho/{token}/checkout
    
    V->>R: GET carrinho:{token}
    R->>V: Dados do carrinho
    
    alt Carrinho vazio
        V->>G: 400 Bad Request<br/>"Carrinho vazio"
        G->>U: 400 Bad Request
    else Carrinho com itens
        Note over V: 1. Validar Cliente
        V->>C: GET /clientes/{cliente_id}
        C->>V: Cliente encontrado e ativo
        
        alt Cliente bloqueado
            V->>G: 400 Bad Request<br/>"Cliente bloqueado"
            G->>U: 400 Bad Request
        end
        
        Note over V: 2. Validar Endereço
        V->>C: GET /clientes/{cliente_id}/enderecos/{endereco_id}
        C->>V: Endereço encontrado
        
        Note over V: 3. Criar Pedido
        V->>DB: INSERT INTO pedidos<br/>(id, cliente_id, status='PENDENTE',<br/>total, itens, ...)
        DB->>V: Pedido criado (UUID)
        
        loop Para cada item
            V->>DB: INSERT INTO itens_pedido<br/>(pedido_id, produto_id, quantidade, ...)
            DB->>V: Item registrado
        end
        
        Note over V: 4. Processar Pagamento
        alt Pagamento à vista (PIX/Cartão)
            V->>V: Gerar cobrança PIX/Cartão
            V->>DB: UPDATE pedidos<br/>SET status='AGUARDANDO_PAGAMENTO'
            DB->>V: Status atualizado
            
        else Pagamento fiado
            V->>C: GET /clientes/{cliente_id}/credito
            C->>V: Crédito disponível
            
            alt Crédito insuficiente
                V->>DB: UPDATE pedidos<br/>SET status='CANCELADO'
                DB->>V: Pedido cancelado
                
                loop Liberar todas as reservas
                    V->>E: POST /estoque/liberar-reserva
                    E->>V: Reserva liberada
                end
                
                V->>G: 400 Bad Request<br/>"Crédito insuficiente"
                G->>U: 400 Bad Request
            else Crédito suficiente
                V->>F: POST /contas-receber<br/>{cliente_id, valor, vencimento}
                F->>V: Conta criada
                
                V->>C: PUT /clientes/{cliente_id}/credito<br/>{debitar: valor}
                C->>V: Crédito debitado
                
                V->>DB: UPDATE pedidos<br/>SET status='CONFIRMADO'
                DB->>V: Pedido confirmado
            end
        end
        
        Note over V: 5. Limpar Carrinho
        V->>R: DEL carrinho:{token}
        R->>V: Carrinho removido
        
        Note over V: 6. Publicar Evento
        V->>MQ: Publish: pedido.criado<br/>{pedido_id, cliente_id, total}
        
        V->>G: 201 Created<br/>{pedido_id, status, total,<br/>link_pagamento (se PIX)}
        G->>U: 201 Created
    end
```

### Formas de Pagamento

**1. PIX (Mercado Pago)**:
- Gera QR Code
- Status: `AGUARDANDO_PAGAMENTO`
- Aguarda webhook de confirmação
- Reserva mantida até pagamento ou expiração

**2. Cartão de Crédito/Débito**:
- Integração com gateway de pagamento
- Status: `AGUARDANDO_PAGAMENTO`
- Confirmação via webhook

**3. Fiado (Crédito)**:
- Verifica crédito disponível do cliente
- Debita crédito imediatamente
- Cria conta a receber
- Status: `CONFIRMADO` (já pago via crédito)

**4. Dinheiro (Balcão)**:
- Pagamento presencial
- Status: `CONFIRMADO` imediatamente
- Confirma reservas e baixa estoque

### Estados do Pedido

```
PENDENTE → Pedido criado, aguardando processamento
AGUARDANDO_PAGAMENTO → Aguardando confirmação de pagamento
PAGO → Pagamento confirmado
CONFIRMADO → Pedido confirmado (fiado ou dinheiro)
CANCELADO → Pedido cancelado
PAGAMENTO_RECUSADO → Pagamento recusado
```

### Resposta do Checkout

```json
{
  "pedido_id": "uuid",
  "status": "AGUARDANDO_PAGAMENTO",
  "total": 23.00,
  "forma_pagamento": "PIX",
  "link_pagamento": "https://mercadopago.com/pix/abc123",
  "qr_code": "00020126....",
  "expira_em": "2026-05-26T10:30:00Z"
}
```

---

## 3.9.5. Confirmar Pagamento e Converter Pedido em Venda (Webhook)

```mermaid
sequenceDiagram
    participant MP as Mercado Pago
    participant G as API Gateway
    participant V as Vendas Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Vendas)
    participant MQ as RabbitMQ
    
    Note over MP: Cliente pagou via PIX
    MP->>G: POST /webhooks/mercadopago<br/>{payment_id, status: 'approved'}
    G->>V: POST /webhooks/mercadopago
    
    V->>V: Validar assinatura do webhook
    
    V->>DB: SELECT * FROM pedidos<br/>WHERE payment_id = ?
    DB->>V: Pedido encontrado
    
    alt Pagamento aprovado
        V->>DB: UPDATE pedidos<br/>SET status='PAGO'
        DB->>V: Pedido atualizado
        
        Note over V: Converter Pedido em Venda
        V->>DB: INSERT INTO vendas<br/>(id, pedido_id, cliente_id,<br/>status='FINALIZADA', ...)
        DB->>V: Venda criada
        
        loop Para cada item
            Note over V: Confirmar reservas
            V->>E: POST /estoque/confirmar-reserva<br/>{produto_id, quantidade,<br/>documento: "VENDA-{venda_id}"}
            E->>V: Reserva confirmada, estoque baixado
        end
        
        Note over V: Publicar Eventos
        V->>MQ: Publish: venda.finalizada<br/>{venda_id, pedido_id, cliente_id}
        V->>MQ: Publish: pedido.pago<br/>{pedido_id}
        
        V->>G: 200 OK
        G->>MP: 200 OK
        
    else Pagamento recusado
        V->>DB: UPDATE pedidos<br/>SET status='PAGAMENTO_RECUSADO'
        DB->>V: Pedido atualizado
        
        loop Liberar todas as reservas
            V->>E: POST /estoque/liberar-reserva
            E->>V: Reserva liberada
        end
        
        V->>MQ: Publish: pedido.pagamento_recusado
        
        V->>G: 200 OK
        G->>MP: 200 OK
    end
```

### Webhook do Mercado Pago

**Segurança**:
- Validar assinatura HMAC-SHA256
- Verificar IP de origem
- Idempotência (processar apenas uma vez)

**Payload do Webhook**:
```json
{
  "id": "payment-id",
  "type": "payment",
  "data": {
    "id": "payment-id"
  },
  "date_created": "2026-05-26T10:15:00Z",
  "action": "payment.updated"
}
```

**Buscar Detalhes do Pagamento**:
```http
GET https://api.mercadopago.com/v1/payments/{payment_id}
Authorization: Bearer ACCESS_TOKEN
```

### Pedido → Venda

**Diferença**:
- **Pedido**: Intenção de compra (pode ser cancelado)
- **Venda**: Transação finalizada (estoque baixado)

**Conversão**:
1. Pedido com status `PAGO`
2. Criar registro de Venda
3. Confirmar todas as reservas (baixa física)
4. Publicar eventos
5. Enviar notificação ao cliente

---

## 3.9.6. Cancelar Pedido (POST /api/pedidos/{id}/cancelar)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant V as Vendas Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Vendas)
    participant MQ as RabbitMQ
    
    U->>G: POST /api/pedidos/{uuid}/cancelar<br/>{motivo}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>V: POST /pedidos/{uuid}/cancelar
    
    V->>DB: SELECT * FROM pedidos<br/>WHERE id = {uuid}
    DB->>V: Pedido encontrado
    
    alt Pedido já finalizado
        V->>G: 400 Bad Request<br/>"Pedido já finalizado"
        G->>U: 400 Bad Request
    else Pedido pode ser cancelado
        V->>DB: UPDATE pedidos<br/>SET status='CANCELADO',<br/>motivo_cancelamento=?
        DB->>V: Pedido cancelado
        
        loop Para cada item
            Note over V: Liberar reservas
            V->>E: POST /estoque/liberar-reserva<br/>{produto_id, quantidade}
            E->>V: Reserva liberada
        end
        
        alt Pedido fiado (já debitou crédito)
            V->>V: Estornar crédito do cliente
        end
        
        Note over V: Publicar Evento
        V->>MQ: Publish: pedido.cancelado<br/>{pedido_id, motivo}
        
        V->>G: 200 OK<br/>{pedido_id, status: 'CANCELADO'}
        G->>U: 200 OK
    end
```

### Regras de Cancelamento

**Pode cancelar**:
- ✅ Pedido `PENDENTE`
- ✅ Pedido `AGUARDANDO_PAGAMENTO`
- ✅ Pedido `PAGAMENTO_RECUSADO`

**NÃO pode cancelar**:
- ❌ Pedido `PAGO` (já virou venda)
- ❌ Pedido `CONFIRMADO` e já entregue
- ❌ Pedido `CANCELADO` (já está cancelado)

### Estorno de Crédito

Se pedido fiado foi confirmado:
1. Estornar valor no crédito do cliente
2. Cancelar conta a receber
3. Liberar reservas de estoque

### Motivos de Cancelamento

```json
{
  "motivo": "Cliente desistiu",
  "observacao": "Cliente solicitou cancelamento por telefone",
  "cancelado_por": "admin@runas.com",
  "cancelado_em": "2026-05-26T11:00:00Z"
}
```

---

## 📊 Resumo de Endpoints

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| POST | `/api/carrinho` | Criar carrinho | Público |
| GET | `/api/carrinho/{token}` | Consultar carrinho | Público |
| POST | `/api/carrinho/{token}/itens` | Adicionar item | Público |
| PUT | `/api/carrinho/{token}/itens/{item_id}` | Atualizar quantidade | Público |
| DELETE | `/api/carrinho/{token}/itens/{item_id}` | Remover item | Público |
| POST | `/api/carrinho/{token}/checkout` | Finalizar (criar pedido) | Público |
| GET | `/api/pedidos` | Listar pedidos | ADMIN/GERENTE |
| GET | `/api/pedidos/{id}` | Consultar pedido | Todos |
| POST | `/api/pedidos/{id}/cancelar` | Cancelar pedido | ADMIN/GERENTE |
| POST | `/webhooks/mercadopago` | Webhook pagamento | Sistema |

---

## 🔐 Permissões por Role

| Operação | ADMIN | GERENTE | VENDEDOR | OPERADOR | PÚBLICO |
|----------|-------|---------|----------|----------|---------|
| Criar carrinho | ✅ | ✅ | ✅ | ✅ | ✅ |
| Adicionar item | ✅ | ✅ | ✅ | ✅ | ✅ |
| Checkout | ✅ | ✅ | ✅ | ✅ | ✅ |
| Listar pedidos | ✅ | ✅ | ❌ | ❌ | ❌ |
| Cancelar pedido | ✅ | ✅ | ❌ | ❌ | ❌ |
| Ver próprios pedidos | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 📚 Documentação Relacionada

- **[Regras de Negócio - Vendas](../../../11-regras-negocio/vendas.md)** - Regras detalhadas
- **[API Reference - Vendas](../../../10-api-reference/mapeamento-rotas.md#vendas)** - Referência completa
- **[Estoque](./estoque.md)** - Como vendas interagem com estoque
- **[Fluxos Integrados](./fluxos-integrados.md)** - Fluxos completos de venda
- **[Índice Geral](./README.md)** - Voltar ao índice

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Mantido por**: Equipe DenebCorp

---

<div align="center">

**[⬆ Voltar ao topo](#-diagramas-de-sequência---vendas)**

</div>
