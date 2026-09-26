# 📊 Regras de Negócio - Estoque

Regras de negócio do serviço de Estoque.

---

## 1. Entidade: Estoque

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Não | FK para Produto (externo) |
| `variante_id` | UUID | Não | Não | FK para Variante (externo) |
| `quantidade` | Float | Sim | Não | Quantidade total |
| `quantidade_reservada` | Float | Sim | Não | Quantidade reservada |
| `quantidade_disponivel` | Float | Sim | Não | Quantidade disponível |
| `estoque_minimo` | Float | Sim | Não | Estoque mínimo |
| `estoque_maximo` | Float | Não | Não | Estoque máximo |
| `localizacao` | String(100) | Não | Não | Localização física |
| `ativo` | Boolean | Sim | Não | Estoque ativo? |
| `created_at` | DateTime | Sim | Não | Data de criação |
| `updated_at` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-EST-001: Produto ou Variante**
- Estoque deve estar vinculado a um `produto_id`
- `variante_id` é opcional
- Se `variante_id` for fornecido, controla estoque da variante específica
- Se `variante_id` for NULL, controla estoque geral do produto

**RN-EST-002: Cálculo de Quantidade Disponível**
- Fórmula: `quantidade_disponivel = quantidade - quantidade_reservada`
- Calculado automaticamente
- Não pode ser editado diretamente

**RN-EST-003: Validação de Quantidades**
- `quantidade` deve ser maior ou igual a zero
- `quantidade_reservada` deve ser maior ou igual a zero
- `quantidade_reservada` não pode ser maior que `quantidade`
- `estoque_minimo` deve ser maior ou igual a zero
- `estoque_maximo` (se fornecido) deve ser maior que `estoque_minimo`

**RN-EST-004: Alertas de Estoque**
- **Estoque Baixo**: `quantidade_disponivel < estoque_minimo`
- **Estoque Zerado**: `quantidade_disponivel = 0`
- **Estoque Negativo**: Não permitido (validação impede)

**RN-EST-005: Localização Física**
- Localização é opcional
- Usado para organização física do estoque
- **Exemplos**: `Prateleira A1`, `Depósito 2`, `Geladeira 3`

**RN-EST-006: Reserva de Estoque**
- Estoque pode ser reservado para vendas pendentes
- Reserva diminui `quantidade_disponivel` mas não `quantidade`
- Reserva é liberada quando:
  - Venda é finalizada (quantidade é decrementada)
  - Venda é cancelada (reserva é removida)
  - Reserva expira (após X horas)

### 🔄 Fluxo de Reserva

```
Estado Inicial:
  quantidade = 100
  quantidade_reservada = 0
  quantidade_disponivel = 100

1. Reservar (carrinho):
   quantidade_reservada += 5      → 5
   quantidade_disponivel -= 5     → 95
   quantidade permanece           → 100

2. Confirmar Reserva (venda):
   quantidade_reservada -= 5      → 0
   quantidade -= 5                → 95
   quantidade_disponivel permanece → 95

3. Cancelar (liberar reserva):
   quantidade_reservada -= 5      → 0
   quantidade_disponivel += 5     → 100
   quantidade permanece           → 100
```

---

## 2. Entidade: Movimentação

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `estoque_id` | UUID | Sim | Não | FK para Estoque |
| `lote_id` | UUID | Não | Não | FK para Lote |
| `tipo` | Enum | Sim | Não | Tipo de movimentação |
| `quantidade` | Float | Sim | Não | Quantidade movimentada |
| `quantidade_anterior` | Float | Sim | Não | Quantidade antes |
| `quantidade_posterior` | Float | Sim | Não | Quantidade depois |
| `motivo` | String(200) | Não | Não | Motivo da movimentação |
| `observacao` | Text | Não | Não | Observações |
| `documento` | String(100) | Não | Não | Número do documento |
| `usuario_id` | UUID | Não | Não | Usuário responsável |
| `custo_unitario` | Float | Não | Não | Custo unitário |
| `custo_total` | Float | Não | Não | Custo total |
| `created_at` | DateTime | Sim | Não | Data da movimentação |

### ✅ Regras de Validação

**RN-MOV-001: Tipos de Movimentação**
- `ENTRADA`: Entrada de mercadoria (compra, devolução de cliente)
- `SAIDA`: Saída de mercadoria (venda, perda, doação)
- `AJUSTE`: Ajuste de inventário (correção de quantidade)
- `DEVOLUCAO`: Devolução para fornecedor
- `PERDA`: Perda de mercadoria (vencimento, quebra, roubo)
- `TRANSFERENCIA`: Transferência entre locais

**RN-MOV-002: Validação de Quantidade**
- `quantidade` deve ser maior que zero
- Para `ENTRADA`: quantidade é positiva
- Para `SAIDA`: quantidade é positiva (mas decrementa o estoque)
- Sistema registra `quantidade_anterior` e `quantidade_posterior` automaticamente

**RN-MOV-003: Rastreabilidade**
- Toda movimentação é registrada permanentemente
- Movimentações não podem ser editadas ou excluídas
- Correções devem ser feitas com novas movimentações de ajuste

**RN-MOV-004: Custo**
- `custo_unitario` é opcional
- `custo_total` é calculado: `custo_total = quantidade * custo_unitario`
- Usado para cálculo de valor do estoque

**RN-MOV-005: Documento**
- Campo `documento` armazena referência externa
- **Exemplos**: `NF-12345`, `PEDIDO-789`, `VENDA-456`

---

## 3. Entidade: Lote

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `estoque_id` | UUID | Sim | Não | FK para Estoque |
| `codigo` | String(100) | Sim | Sim | Código do lote |
| `quantidade` | Float | Sim | Não | Quantidade atual |
| `quantidade_inicial` | Float | Sim | Não | Quantidade inicial |
| `data_fabricacao` | Date | Não | Não | Data de fabricação |
| `data_validade` | Date | Não | Não | Data de validade |
| `fornecedor` | String(200) | Não | Não | Nome do fornecedor |
| `nota_fiscal` | String(100) | Não | Não | Número da NF |
| `custo_unitario` | Float | Não | Não | Custo unitário |
| `status` | Enum | Sim | Não | Status do lote |
| `created_at` | DateTime | Sim | Não | Data de criação |
| `updated_at` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-LOT-001: Código Único**
- Código do lote deve ser único no sistema
- Usado para rastreabilidade
- **Exemplo**: `LOTE-2026-001`, `FAB-20260521`

**RN-LOT-002: Validação de Quantidades**
- `quantidade` deve ser maior que zero
- `quantidade_inicial` é registrada na criação e não muda
- `quantidade` diminui conforme o lote é consumido

**RN-LOT-003: Validação de Datas**
- `data_validade` deve ser posterior a `data_fabricacao`
- Se `data_validade` for fornecida, sistema monitora vencimento
- Lotes sem data de validade não geram alertas

**RN-LOT-004: Status do Lote**
- `ATIVO`: Lote disponível para uso
- `VENCIDO`: Lote passou da data de validade
- `BLOQUEADO`: Lote bloqueado manualmente (recall, problema de qualidade)

**RN-LOT-005: Alertas de Vencimento**
- Sistema verifica diariamente lotes próximos do vencimento
- Alerta é gerado quando faltam 7 dias para vencer
- Notificação via WhatsApp para gerentes

**RN-LOT-006: Rastreabilidade**
- Código do lote permite rastreamento completo
- Todas as movimentações registram o lote de origem
- Usado para recalls e controle de qualidade

---

## 4. Entidade: Inventário

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `data_inventario` | DateTime | Sim | Não | Data da contagem |
| `responsavel` | String(200) | Sim | Não | Nome do responsável |
| `observacao` | Text | Não | Não | Observações gerais |
| `finalizado` | Boolean | Sim | Não | Inventário finalizado? |
| `data_finalizacao` | DateTime | Não | Não | Data de finalização |
| `created_at` | DateTime | Sim | Não | Data de criação |
| `updated_at` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-INV-001: Criação de Inventário**
- Inventário é criado com `finalizado = false`
- Deve ter pelo menos um item para ser criado
- Responsável é obrigatório

**RN-INV-002: Itens do Inventário**
- Cada item registra:
  - `quantidade_sistema`: Quantidade no sistema
  - `quantidade_contada`: Quantidade física contada
  - `diferenca`: Calculada automaticamente
- Diferença pode ser positiva (sobra) ou negativa (falta)

**RN-INV-003: Finalização de Inventário**
- Apenas inventários não finalizados podem ser finalizados
- Ao finalizar:
  - Todos os itens com diferença são ajustados
  - Movimentações de ajuste são criadas
  - Campo `finalizado` é marcado como `true`
  - `data_finalizacao` é registrada
- Inventário finalizado não pode ser editado

**RN-INV-004: Ajustes Automáticos**
- Ao finalizar inventário, sistema ajusta automaticamente:
  - Aumenta quantidade se diferença for positiva
  - Diminui quantidade se diferença for negativa
- Cada ajuste gera uma movimentação tipo `AJUSTE`

---

## 5. Casos de Uso

### 5.1. Venda com Estoque Insuficiente

**Cenário**: Cliente tenta comprar 100 unidades, mas há apenas 50 em estoque

**Comportamento**:
1. Sistema tenta reservar 100 unidades
2. Estoque valida disponibilidade
3. Retorna erro: `400 Bad Request - Estoque insuficiente`
4. Venda não é criada
5. Nenhuma reserva é feita

**Alternativa**: Venda parcial (futuro)
- Permitir venda de 50 unidades
- Criar backorder para as 50 restantes

### 5.2. Lote Vencido com Estoque

**Cenário**: Lote vence mas ainda tem 50 unidades

**Comportamento**:
1. Job diário verifica lotes vencidos
2. Marca lote como `VENCIDO`
3. Publica evento `estoque.lote_vencido`
4. Notificação é enviada ao gerente
5. Lote vencido não é usado em novas saídas (FIFO)
6. Gerente deve dar baixa manual (perda) ou remarcar validade

### 5.3. Inventário com Grandes Diferenças

**Cenário**: Inventário encontra diferença de -100 unidades (falta)

**Comportamento**:
1. Diferença é registrada no item do inventário
2. Ao finalizar inventário:
   - Quantidade é ajustada para quantidade contada
   - Movimentação tipo `AJUSTE` é criada
   - Motivo: `Inventário #{uuid}`
3. Alerta é gerado se diferença > 10% do estoque

---

## 📚 Referências

- [API de Estoque](../10-api-reference/estoque-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
