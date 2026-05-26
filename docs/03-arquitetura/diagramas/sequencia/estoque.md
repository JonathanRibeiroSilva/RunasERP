# 📊 Diagramas de Sequência - Estoque

**Data**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Domínio**: Estoque

---

## 📑 Índice

1. [Criar Registro de Estoque](#31-criar-registro-de-estoque)
2. [Entrada de Estoque](#32-entrada-de-estoque)
3. [Saída de Estoque](#33-saída-de-estoque)
4. [Reservar Estoque](#34-reservar-estoque)
5. [Liberar Reserva](#35-liberar-reserva)
6. [Confirmar Reserva](#36-confirmar-reserva)
7. [Realizar Inventário](#37-realizar-inventário)
8. [Finalizar Inventário e Ajustar](#38-finalizar-inventário-e-ajustar-estoque)

---

## 3.1. Criar Registro de Estoque (POST /api/estoque)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant E as Estoque Service
    participant P as Produtos Service
    participant DB as PostgreSQL (Estoque)
    
    U->>G: POST /api/estoque<br/>{produto_id, variante_id, estoque_minimo}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>E: POST /estoque
    
    Note over E: Validar produto existe
    E->>P: GET /produtos/{produto_id}
    P->>E: Produto encontrado
    
    alt variante_id fornecido
        E->>P: GET /produtos/{produto_id}/variantes/{variante_id}
        P->>E: Variante encontrada
    end
    
    E->>DB: SELECT * FROM estoque<br/>WHERE produto_id = ? AND variante_id = ?
    DB->>E: Verificar duplicidade
    
    alt Estoque já existe
        E->>G: 400 Bad Request<br/>"Estoque já cadastrado"
        G->>U: 400 Bad Request
    else Estoque novo
        E->>DB: INSERT INTO estoque<br/>(id, produto_id, variante_id,<br/>quantidade=0, estoque_minimo, ...)
        DB->>E: Estoque criado (UUID)
        
        E->>G: 201 Created<br/>{id, produto_id, quantidade: 0, ...}
        G->>U: 201 Created
    end
```

### Campos do Estoque

```json
{
  "produto_id": "uuid",
  "variante_id": "uuid",
  "quantidade": 0,
  "quantidade_reservada": 0,
  "quantidade_disponivel": 0,
  "estoque_minimo": 10,
  "estoque_maximo": 100,
  "localizacao": "A1-P2-N3"
}
```

### Regras de Negócio

- Cada produto/variante tem apenas um registro de estoque
- Quantidade inicial é sempre 0
- `quantidade_disponivel = quantidade - quantidade_reservada`
- Estoque mínimo define quando enviar alerta
- Localização ajuda na organização física do depósito

---

## 3.2. Entrada de Estoque (POST /api/estoque/entrada)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Estoque)
    participant R as RabbitMQ
    
    U->>G: POST /api/estoque/entrada<br/>{produto_id, quantidade: 100,<br/>criar_lote: true, codigo_lote, ...}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>E: POST /estoque/entrada
    
    E->>DB: SELECT * FROM estoque<br/>WHERE produto_id = ? AND variante_id = ?
    DB->>E: Estoque encontrado
    
    Note over E: Registrar quantidade anterior
    E->>E: quantidade_anterior = estoque.quantidade
    
    alt criar_lote = true
        E->>DB: INSERT INTO lotes<br/>(id, estoque_id, codigo, quantidade,<br/>data_validade, ...)
        DB->>E: Lote criado (UUID)
    end
    
    E->>DB: UPDATE estoque<br/>SET quantidade = quantidade + 100,<br/>quantidade_disponivel = quantidade_disponivel + 100
    DB->>E: Estoque atualizado
    
    E->>DB: INSERT INTO movimentacoes<br/>(id, estoque_id, tipo='ENTRADA',<br/>quantidade=100, quantidade_anterior, ...)
    DB->>E: Movimentação registrada
    
    Note over E: Publicar evento
    E->>R: Publish: estoque.entrada<br/>{produto_id, quantidade, lote_id}
    
    E->>G: 200 OK<br/>{estoque_id, quantidade_nova: 100,<br/>lote_id, movimentacao_id}
    G->>U: 200 OK
```

### Entrada com Lote

**Quando usar lotes?**
- Produtos perecíveis (alimentos, bebidas)
- Produtos com validade (medicamentos, cosméticos)
- Controle de qualidade por fornecedor
- Rastreabilidade (recall de produtos)

**Exemplo de Lote**:
```json
{
  "codigo_lote": "LOTE-2026-05-001",
  "data_fabricacao": "2026-05-01",
  "data_validade": "2026-11-01",
  "fornecedor_id": "uuid",
  "nota_fiscal": "NF-12345",
  "quantidade": 100
}
```

### Tipos de Entrada

1. **Compra de Fornecedor**: Entrada normal com nota fiscal
2. **Devolução de Cliente**: Entrada por devolução
3. **Transferência entre Depósitos**: Entrada em um, saída em outro
4. **Ajuste de Inventário**: Correção após contagem

---

## 3.3. Saída de Estoque (POST /api/estoque/saida)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Estoque)
    participant R as RabbitMQ
    
    U->>G: POST /api/estoque/saida<br/>{produto_id, quantidade: 50,<br/>motivo: "Venda", documento: "VENDA-123"}
    G->>A: Validar Token JWT
    A->>G: Token válido
    
    G->>E: POST /estoque/saida
    
    E->>DB: SELECT * FROM estoque<br/>WHERE produto_id = ? AND variante_id = ?
    DB->>E: Estoque encontrado
    
    Note over E: Validar disponibilidade
    E->>E: quantidade_disponivel >= 50?
    
    alt Estoque insuficiente
        E->>G: 400 Bad Request<br/>"Estoque insuficiente"
        G->>U: 400 Bad Request
    else Estoque suficiente
        Note over E: Registrar quantidade anterior
        E->>E: quantidade_anterior = estoque.quantidade
        
        alt lote_id fornecido
            E->>DB: UPDATE lotes<br/>SET quantidade = quantidade - 50<br/>WHERE id = {lote_id}
            DB->>E: Lote atualizado
        end
        
        E->>DB: UPDATE estoque<br/>SET quantidade = quantidade - 50,<br/>quantidade_disponivel = quantidade_disponivel - 50
        DB->>E: Estoque atualizado
        
        E->>DB: INSERT INTO movimentacoes<br/>(id, estoque_id, tipo='SAIDA',<br/>quantidade=50, motivo, documento, ...)
        DB->>E: Movimentação registrada
        
        Note over E: Publicar evento
        E->>R: Publish: estoque.saida<br/>{produto_id, quantidade, documento}
        
        Note over E: Verificar estoque baixo
        alt quantidade_disponivel < estoque_minimo
            E->>R: Publish: estoque.alerta_baixo<br/>{produto_id, quantidade_disponivel}
        end
        
        E->>G: 200 OK<br/>{estoque_id, quantidade_nova: 50,<br/>movimentacao_id}
        G->>U: 200 OK
    end
```

### Tipos de Saída

1. **Venda**: Saída por venda ao cliente
2. **Perda**: Produto vencido, danificado ou roubado
3. **Transferência**: Saída para outro depósito
4. **Devolução ao Fornecedor**: Produto com defeito
5. **Consumo Interno**: Uso interno da empresa
6. **Ajuste de Inventário**: Correção após contagem

### Motivos de Saída

```json
{
  "tipo": "SAIDA",
  "motivo": "Venda",
  "documento": "VENDA-123",
  "quantidade": 50,
  "observacao": "Venda realizada no balcão"
}
```

---

## 3.4. Reservar Estoque (POST /api/estoque/reservar)

```mermaid
sequenceDiagram
    participant V as Vendas Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Estoque)
    participant R as RabbitMQ
    
    Note over V: Cliente adiciona produto ao carrinho
    V->>E: POST /estoque/reservar<br/>{produto_id, variante_id,<br/>quantidade: 5, documento: "CARRINHO-789"}
    
    E->>DB: SELECT * FROM estoque<br/>WHERE produto_id = ? AND variante_id = ?<br/>FOR UPDATE
    DB->>E: Estoque encontrado (lock)
    
    Note over E: Validar disponibilidade
    E->>E: quantidade_disponivel >= 5?
    
    alt Estoque insuficiente
        E->>V: 400 Bad Request<br/>"Estoque insuficiente"
    else Estoque suficiente
        Note over E: Reserva diminui disponível<br/>e aumenta reservado
        E->>DB: UPDATE estoque<br/>SET quantidade_reservada = quantidade_reservada + 5,<br/>quantidade_disponivel = quantidade_disponivel - 5<br/>WHERE id = {estoque_id}
        DB->>E: Estoque atualizado
        
        Note over E: Publicar evento
        E->>R: Publish: estoque.reservado<br/>{produto_id, quantidade: 5, documento}
        
        E->>V: 200 OK<br/>{estoque_id, quantidade_reservada: 5}
    end
```

### Como Funciona a Reserva?

**Estado Inicial**:
```
quantidade = 100
quantidade_reservada = 0
quantidade_disponivel = 100
```

**Após Reservar 5 unidades**:
```
quantidade = 100 (não muda)
quantidade_reservada = 5 (aumenta)
quantidade_disponivel = 95 (diminui)
```

**Fórmula**:
```
quantidade_disponivel = quantidade - quantidade_reservada
```

### Quando Usar Reserva?

- ✅ **Carrinho de compras**: Reserva enquanto cliente decide
- ✅ **Orçamento**: Reserva para garantir disponibilidade
- ✅ **Pedido pendente**: Reserva até confirmação de pagamento
- ❌ **Venda finalizada**: Usar confirmar reserva (baixa física)

### Expiração de Reservas

Reservas devem ter TTL (Time To Live):
- Carrinho: 2 horas
- Orçamento: 24 horas
- Pedido: Até confirmação de pagamento

Job agendado libera reservas expiradas automaticamente.

---

## 3.5. Liberar Reserva (POST /api/estoque/liberar-reserva)

```mermaid
sequenceDiagram
    participant V as Vendas Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Estoque)
    participant R as RabbitMQ
    
    Note over V: Cliente cancela carrinho ou reserva expira
    V->>E: POST /estoque/liberar-reserva<br/>{produto_id, variante_id,<br/>quantidade: 5, documento: "CARRINHO-789"}
    
    E->>DB: SELECT * FROM estoque<br/>WHERE produto_id = ? AND variante_id = ?<br/>FOR UPDATE
    DB->>E: Estoque encontrado (lock)
    
    Note over E: Libera reserva e devolve<br/>para disponível
    E->>DB: UPDATE estoque<br/>SET quantidade_reservada = quantidade_reservada - 5,<br/>quantidade_disponivel = quantidade_disponivel + 5<br/>WHERE id = {estoque_id}
    DB->>E: Estoque atualizado
    
    Note over E: Publicar evento
    E->>R: Publish: estoque.reserva_liberada<br/>{produto_id, quantidade: 5, documento}
    
    E->>V: 200 OK<br/>{estoque_id, quantidade_liberada: 5}
```

### Quando Liberar Reserva?

1. **Cliente cancela carrinho**: Libera imediatamente
2. **Reserva expira**: Job agendado libera automaticamente
3. **Pagamento recusado**: Libera após falha no pagamento
4. **Cliente remove item**: Libera item específico

### Fluxo Completo

```
1. Reservar (carrinho):
   quantidade = 100
   quantidade_reservada = 5
   quantidade_disponivel = 95

2. Liberar (cancelamento):
   quantidade = 100 (não muda)
   quantidade_reservada = 0 (volta a 0)
   quantidade_disponivel = 100 (volta ao normal)
```

---

## 3.6. Confirmar Reserva (POST /api/estoque/confirmar-reserva)

```mermaid
sequenceDiagram
    participant V as Vendas Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Estoque)
    participant R as RabbitMQ
    
    Note over V: Venda finalizada, confirmar reserva
    V->>E: POST /estoque/confirmar-reserva<br/>{produto_id, variante_id,<br/>quantidade: 5, documento: "VENDA-123"}
    
    E->>DB: SELECT * FROM estoque<br/>WHERE produto_id = ? AND variante_id = ?<br/>FOR UPDATE
    DB->>E: Estoque encontrado (lock)
    
    Note over E: Registrar quantidade anterior
    E->>E: quantidade_anterior = estoque.quantidade
    
    Note over E: Confirma reserva:<br/>diminui reservado e quantidade física
    E->>DB: UPDATE estoque<br/>SET quantidade_reservada = quantidade_reservada - 5,<br/>quantidade = quantidade - 5<br/>WHERE id = {estoque_id}
    DB->>E: Estoque atualizado
    
    E->>DB: INSERT INTO movimentacoes<br/>(id, estoque_id, tipo='SAIDA',<br/>quantidade=5, quantidade_anterior,<br/>motivo='Venda', documento='VENDA-123')
    DB->>E: Movimentação registrada
    
    Note over E: Publicar evento
    E->>R: Publish: estoque.confirmado<br/>{produto_id, quantidade: 5, documento}
    
    Note over E: Verificar estoque baixo
    alt quantidade_disponivel < estoque_minimo
        E->>R: Publish: estoque.alerta_baixo<br/>{produto_id, quantidade_disponivel}
    end
    
    E->>V: 200 OK<br/>{estoque_id, quantidade_nova,<br/>movimentacao_id}
```

### Diferença: Reservar vs Confirmar

| Operação | quantidade | quantidade_reservada | quantidade_disponivel |
|----------|------------|---------------------|----------------------|
| **Estado Inicial** | 100 | 0 | 100 |
| **Reservar 5** | 100 | 5 | 95 |
| **Confirmar 5** | 95 | 0 | 95 |

**Confirmar Reserva**:
- Diminui `quantidade` física (baixa real)
- Diminui `quantidade_reservada` (libera reserva)
- `quantidade_disponivel` não muda (já estava descontada)
- Cria movimentação de SAÍDA
- **Evita baixa dupla de estoque!**

---

## 3.7. Realizar Inventário (POST /api/estoque/inventario)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Estoque)
    
    U->>G: POST /api/estoque/inventario<br/>{responsavel: "João",<br/>itens: [{estoque_id, quantidade_contada}, ...]}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>E: POST /estoque/inventario
    
    E->>DB: INSERT INTO inventarios<br/>(id, responsavel, data_inventario)
    DB->>E: Inventário criado (UUID)
    
    loop Para cada item
        E->>DB: SELECT * FROM estoque<br/>WHERE id = {estoque_id}
        DB->>E: Estoque encontrado
        
        Note over E: Calcular diferença
        E->>E: diferenca = quantidade_contada - quantidade_sistema
        
        E->>DB: INSERT INTO itens_inventario<br/>(id, inventario_id, estoque_id,<br/>quantidade_sistema, quantidade_contada, diferenca)
        DB->>E: Item registrado
    end
    
    E->>G: 201 Created<br/>{inventario_id, itens: [...]}
    G->>U: 201 Created
```

### Processo de Inventário

**Fase 1: Contagem Física**
1. Responsável conta fisicamente os produtos
2. Registra quantidade contada no sistema
3. Sistema calcula diferença automaticamente

**Fase 2: Análise**
- Revisar itens com diferença
- Investigar causas (perda, roubo, erro de registro)
- Decidir se ajusta ou reconta

**Fase 3: Finalização**
- Finalizar inventário (próximo diagrama)
- Sistema ajusta estoque automaticamente
- Gera relatório de ajustes

### Exemplo de Inventário

```json
{
  "id": "uuid",
  "responsavel": "João Silva",
  "data_inventario": "2026-05-26T10:00:00Z",
  "finalizado": false,
  "itens": [
    {
      "estoque_id": "uuid-coca-2l",
      "produto_nome": "Coca-Cola 2L",
      "quantidade_sistema": 100,
      "quantidade_contada": 98,
      "diferenca": -2,
      "observacao": "2 unidades danificadas"
    },
    {
      "estoque_id": "uuid-guarana-2l",
      "produto_nome": "Guaraná 2L",
      "quantidade_sistema": 50,
      "quantidade_contada": 52,
      "diferenca": +2,
      "observacao": "Entrada não registrada"
    }
  ]
}
```

---

## 3.8. Finalizar Inventário e Ajustar Estoque (POST /api/estoque/inventario/{id}/finalizar)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant E as Estoque Service
    participant DB as PostgreSQL (Estoque)
    participant R as RabbitMQ
    
    U->>G: POST /api/estoque/inventario/{uuid}/finalizar
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN)
    
    G->>E: POST /estoque/inventario/{uuid}/finalizar
    
    E->>DB: SELECT * FROM inventarios<br/>WHERE id = {uuid}
    DB->>E: Inventário encontrado
    
    alt Já finalizado
        E->>G: 400 Bad Request<br/>"Inventário já finalizado"
        G->>U: 400 Bad Request
    else Não finalizado
        E->>DB: SELECT * FROM itens_inventario<br/>WHERE inventario_id = {uuid}
        DB->>E: Lista de itens
        
        loop Para cada item com diferença != 0
            E->>DB: SELECT * FROM estoque<br/>WHERE id = {estoque_id}<br/>FOR UPDATE
            DB->>E: Estoque (lock)
            
            Note over E: Ajustar estoque
            E->>DB: UPDATE estoque<br/>SET quantidade = quantidade_contada
            DB->>E: Estoque ajustado
            
            E->>DB: INSERT INTO movimentacoes<br/>(tipo='AJUSTE', quantidade=diferenca,<br/>motivo='Inventário #{uuid}')
            DB->>E: Movimentação registrada
            
            E->>DB: UPDATE itens_inventario<br/>SET ajustado = true<br/>WHERE id = {item_id}
            DB->>E: Item marcado como ajustado
        end
        
        E->>DB: UPDATE inventarios<br/>SET finalizado = true,<br/>data_finalizacao = NOW()
        DB->>E: Inventário finalizado
        
        Note over E: Publicar evento
        E->>R: Publish: estoque.inventario_finalizado<br/>{inventario_id, total_ajustes}
        
        E->>G: 200 OK<br/>{inventario_id, itens_ajustados: 15}
        G->>U: 200 OK
    end
```

### Ajustes Automáticos

**Para cada item com diferença**:
1. Atualiza `quantidade` para `quantidade_contada`
2. Cria movimentação tipo `AJUSTE`
3. Marca item como `ajustado = true`

**Exemplo**:
```
Sistema: 100 unidades
Contado: 98 unidades
Diferença: -2

Ajuste:
- quantidade: 100 → 98
- Movimentação: AJUSTE, -2, "Inventário #123"
```

### Relatório de Inventário

```json
{
  "inventario_id": "uuid",
  "responsavel": "João Silva",
  "data_inicio": "2026-05-26T10:00:00Z",
  "data_finalizacao": "2026-05-26T14:30:00Z",
  "total_itens": 150,
  "itens_ajustados": 15,
  "ajustes": {
    "positivos": 5,
    "negativos": 10,
    "valor_total_ajustes": -250.00
  }
}
```

---

## 📊 Resumo de Endpoints

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| POST | `/api/estoque` | Criar registro | ADMIN/GERENTE |
| GET | `/api/estoque` | Listar estoque | Todos |
| POST | `/api/estoque/entrada` | Entrada | ADMIN/GERENTE |
| POST | `/api/estoque/saida` | Saída direta | ADMIN/GERENTE |
| POST | `/api/estoque/reservar` | Reservar | Sistema |
| POST | `/api/estoque/liberar-reserva` | Liberar | Sistema |
| POST | `/api/estoque/confirmar-reserva` | Confirmar | Sistema |
| POST | `/api/estoque/inventario` | Criar inventário | ADMIN/GERENTE |
| POST | `/api/estoque/inventario/{id}/finalizar` | Finalizar | ADMIN |

---

## 🔐 Permissões por Role

| Operação | ADMIN | GERENTE | VENDEDOR | OPERADOR |
|----------|-------|---------|----------|----------|
| Criar estoque | ✅ | ✅ | ❌ | ❌ |
| Consultar estoque | ✅ | ✅ | ✅ | ✅ |
| Entrada | ✅ | ✅ | ❌ | ❌ |
| Saída direta | ✅ | ✅ | ❌ | ❌ |
| Inventário | ✅ | ✅ | ❌ | ❌ |
| Finalizar inventário | ✅ | ❌ | ❌ | ❌ |
| Reservas | Sistema | Sistema | Sistema | Sistema |

---

## 📚 Documentação Relacionada

- **[Regras de Negócio - Estoque](../../../11-regras-negocio/estoque.md)** - Regras detalhadas
- **[API Reference - Estoque](../../../10-api-reference/mapeamento-rotas.md#estoque)** - Referência completa
- **[Vendas](./vendas.md)** - Como vendas interagem com estoque
- **[Fluxos Integrados](./fluxos-integrados.md)** - Fluxos completos
- **[Índice Geral](./README.md)** - Voltar ao índice

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Mantido por**: Equipe DenebCorp

---

<div align="center">

**[⬆ Voltar ao topo](#-diagramas-de-sequência---estoque)**

</div>
