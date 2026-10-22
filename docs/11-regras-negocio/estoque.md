# 📊 Regras de Negócio - Estoque

Regras de negócio do serviço de Estoque, conferidas contra `services/estoque/` (`models/estoque.py`, `schemas/estoque.py`, `services/estoque_service.py`, `repositories/estoque_repository.py`).

> **Legenda de status**: **Implementado** = existe e roda no código; **Parcial** = existe com ressalvas; **Não implementado** = aparecia neste documento mas não há código que o faça.

---

## 1. Entidade: Estoque

### 📊 Estrutura de Dados

Tabela `estoque.estoque`.

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `empresa_id` | Integer | Sim | Não | Tenant (multi-tenancy) |
| `produto_id` | UUID | Sim | Não | Produto (id do serviço de Produtos, sem FK no banco) |
| `variante_id` | UUID | Não | Não | Variante (idem) |
| `quantidade` | Float | Sim | Não | Quantidade física total |
| `quantidade_reservada` | Float | Sim | Não | Quantidade reservada |
| `quantidade_disponivel` | Float | Sim | Não | `quantidade - quantidade_reservada` |
| `estoque_minimo` | Float | Sim | Não | Estoque mínimo (padrão 0) |
| `estoque_maximo` | Float | Não | Não | Estoque máximo |
| `localizacao` | String(100) | Não | Não | Localização física |
| `ativo` | Boolean | Sim | Não | Estoque ativo? |
| `created_at` | DateTime | Sim | Não | Data de criação |
| `updated_at` | DateTime | Sim | Não | Data de atualização |

Restrições no banco: `UNIQUE (empresa_id, produto_id, variante_id)` e `CHECK (quantidade >= 0 AND quantidade_reservada >= 0 AND quantidade_disponivel >= 0)` (`ck_estoque_quantidades_nao_negativas`).

### ✅ Regras de Validação

**RN-EST-001: Produto ou Variante** (Implementado)
- Estoque é sempre de um `produto_id`; `variante_id` é opcional.
- Com `variante_id`, controla a variante específica; sem ele, o estoque geral do produto.
- Um mesmo par `(empresa, produto, variante)` só pode ter um registro. Atenção: como `NULL` não é igual a `NULL` no `UNIQUE` do PostgreSQL, a unicidade para produto **sem variante** é garantida só pela checagem do serviço, não pelo banco (nenhuma migration de estoque cria índice parcial).
- Ao criar (`POST /estoque`) ou na primeira entrada, o serviço consulta o serviço de Produtos: produto inexistente, de outra empresa ou **inativo** não inicia estoque (variante, se informada, precisa existir).

**RN-EST-002: Cálculo de Quantidade Disponível** (Implementado)
- `quantidade_disponivel = quantidade - quantidade_reservada`, recalculado a cada operação.
- Nenhuma rota permite editá-lo diretamente.

**RN-EST-003: Validação de Quantidades** (Parcial)
- Schema: `quantidade >= 0`, `estoque_minimo >= 0`, `estoque_maximo >= 0` (se informado).
- `quantidade_reservada` nunca passa de `quantidade`: garantido pela checagem em `reservar` e pelo CHECK do banco.
- **Não há validação** de `estoque_maximo > estoque_minimo`.
- Ajuste (`quantidade_nova`) menor que a quantidade reservada é recusado com 400: "Libere as reservas antes".

**RN-EST-004: Alertas de Estoque** (Implementado, com ressalva)
- **Estoque baixo**: `quantidade <= estoque_minimo` **e** `quantidade > 0` (compara a quantidade **física**, não a disponível, e usa `<=`).
- **Estoque zerado**: `quantidade == 0`.
- **Estoque negativo**: impossível (validações do serviço + CHECK do banco).
- Os alertas são campos de resposta (`alerta_estoque_baixo`, `alerta_estoque_zerado`); não disparam notificação. O filtro `apenas_baixo` da listagem inclui itens zerados (`quantidade <= estoque_minimo`, sem o `> 0`).

**RN-EST-005: Localização Física** (Implementado)
- Opcional, texto livre até 100 caracteres. **Exemplos**: `Prateleira A1`, `Depósito 2`.

**RN-EST-006: Reserva de Estoque** (Parcial)
- `POST /estoque/reservar` aumenta `quantidade_reservada` e reduz `quantidade_disponivel`; `quantidade` não muda. Recusa (400) se a reserva total passar da `quantidade`.
- `POST /estoque/liberar-reserva` devolve à disponibilidade; recusa (400) se liberar mais do que reservado.
- A venda confirmada é `POST /estoque/baixar-venda`: baixa a quantidade física **e** desconta a reserva correspondente (sem ficar negativa).
- **Não há expiração de reserva neste serviço.** A expiração de 15 minutos do carrinho é do serviço de Vendas (`reserva_temporaria_service.py`, com Redis).

### 🔄 Fluxo de Reserva

```
Estado inicial:  quantidade=100  reservada=0  disponivel=100

1. Reservar 5 (carrinho):
   reservada=5  disponivel=95  quantidade=100

2. Venda confirmada (baixar-venda de 5):
   quantidade=95  reservada=0  disponivel=95

3. Alternativa: cancelar (liberar-reserva de 5):
   reservada=0  disponivel=100  quantidade=100
```

### 🔒 Concorrência

**RN-EST-007: Lock de linha** (Implementado)
- Entrada, saída, ajuste, reserva, liberação, baixa e estorno leem o registro com `SELECT ... FOR UPDATE` dentro da transação, para que duas requisições simultâneas não partam do mesmo valor (atualização perdida) nem reservem o último item duas vezes.
- Baixa e estorno de venda travam vários registros em ordem determinística por `(produto_id, variante_id)` para evitar deadlock e refazem a operação em até 3 tentativas (backoff exponencial a partir de 50 ms) em `40P01`/`40001`.
- Baixa e estorno são **idempotentes** por `(empresa_id, documento)`, com tabelas de ledger (`baixas_venda_processadas`, `estornos_venda_processados`) e constraint única.

---

## 2. Entidade: Movimentação

### 📊 Estrutura de Dados

Tabela `estoque.movimentacoes` (não tem `empresa_id` próprio; o tenant vem do estoque dono).

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `estoque_id` | UUID | Sim | Não | FK para Estoque |
| `lote_id` | UUID | Não | Não | FK para Lote |
| `tipo` | String(20) | Sim | Não | `TipoMovimentacao` |
| `quantidade` | Float | Sim | Não | Quantidade movimentada (valor absoluto) |
| `quantidade_anterior` | Float | Sim | Não | Quantidade antes |
| `quantidade_posterior` | Float | Sim | Não | Quantidade depois |
| `motivo` | String(200) | Não | Não | Motivo |
| `observacao` | Text | Não | Não | Observações |
| `documento` | String(100) | Não | Não | Número do documento |
| `usuario_id` | UUID | Não | Não | Usuário responsável (as rotas atuais não o preenchem) |
| `custo_unitario` | Float | Não | Não | Custo unitário |
| `custo_total` | Float | Não | Não | Custo total |
| `created_at` | DateTime | Sim | Não | Data da movimentação |

### ✅ Regras de Validação

**RN-MOV-001: Tipos de Movimentação** (Parcial)
Enum: `ENTRADA`, `SAIDA`, `AJUSTE`, `DEVOLUCAO`, `PERDA`, `TRANSFERENCIA`. Uso real:
- `ENTRADA`: `POST /estoque/entrada` e `POST /estoque/entrada-nfe` (motivo `Entrada por XML de NF-e`; a mesma chave de acesso não entra duas vezes por empresa, 409).
- `SAIDA`: `POST /estoque/saida` e `baixar-venda` (motivo `Venda confirmada`).
- `AJUSTE`: `POST /estoque/ajuste`.
- `DEVOLUCAO`: **estorno de venda reembolsada** (`estornar-venda`, motivo `Venda reembolsada`), que **aumenta** o estoque. Não é devolução ao fornecedor.
- `PERDA` e `TRANSFERENCIA`: existem no enum e aceitam filtro, mas nenhuma rota os grava. Perda hoje se registra como saída com motivo.

**RN-MOV-002: Validação de Quantidade** (Implementado)
- Na entrada, saída, baixa, estorno e reserva, `quantidade > 0`.
- `quantidade` da movimentação é sempre positiva; o sentido vem do `tipo`. No `AJUSTE`, é `abs(nova - atual)`.
- `quantidade_anterior` e `quantidade_posterior` são gravados automaticamente.

**RN-MOV-003: Rastreabilidade** (Implementado no nível da API)
- Não há rota para editar ou excluir movimentação; correções são novos ajustes. O banco não impede um `UPDATE` manual.

**RN-MOV-004: Custo** (Parcial)
- `custo_unitario` é opcional e só é recebido na **entrada**.
- `custo_total = quantidade * custo_unitario` é calculado apenas quando `custo_unitario` é informado e diferente de zero.
- Não há cálculo de valor total do estoque (`valor_total_estoque` no relatório é sempre `null`).

**RN-MOV-005: Documento** (Implementado)
- `documento` guarda a referência externa. Na baixa/estorno de venda é o número da venda e serve de chave de idempotência. **Exemplos**: `NF-12345`, `PEDIDO-789`.

---

## 3. Entidade: Lote

### 📊 Estrutura de Dados

Tabela `estoque.lotes`.

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `empresa_id` | Integer | Sim | Não | Tenant |
| `estoque_id` | UUID | Sim | Não | FK para Estoque |
| `codigo` | String(100) | Sim | Por empresa | Código do lote |
| `quantidade` | Float | Sim | Não | Quantidade atual |
| `quantidade_inicial` | Float | Sim | Não | Quantidade inicial |
| `data_fabricacao` | Date | Não | Não | Data de fabricação |
| `data_validade` | Date | Não | Não | Data de validade |
| `fornecedor` | String(200) | Não | Não | Nome do fornecedor |
| `nota_fiscal` | String(100) | Não | Não | Número da NF |
| `custo_unitario` | Float | Não | Não | Custo unitário |
| `status` | String(20) | Sim | Não | `ATIVO`, `VENCIDO`, `BLOQUEADO` |
| `created_at` | DateTime | Sim | Não | Data de criação |
| `updated_at` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-LOT-001: Código Único** (Implementado no banco)
- `UNIQUE (empresa_id, codigo)`: único **por empresa**, não no sistema inteiro. Lote repetido numa entrada falha na transação (a resposta sai como erro interno, sem tratamento dedicado). **Exemplo**: `LOTE-2026-001`.

**RN-LOT-002: Quantidades** (Parcial)
- O lote nasce **somente** numa entrada (`criar_lote = true` **e** `codigo_lote` preenchido) com a quantidade da entrada (`> 0`), que vira `quantidade_inicial`.
- `quantidade` diminui só em saída com `lote_id`. Quando chega a 0, o lote passa a `BLOQUEADO`.
- Não existe rota para criar lote avulso nem para editar quantidade ou status (`LoteCreate`/`LoteUpdate` existem nos schemas, mas nenhuma rota os usa).

**RN-LOT-003: Validação de Datas** (Não aplicada)
- O validador "validade não anterior à fabricação" existe em `LoteBase`, que nenhuma rota usa. O caminho real (`EntradaEstoqueRequest`) **não valida** a ordem das datas.

**RN-LOT-004: Status do Lote** (Parcial)
- `ATIVO`: padrão na criação.
- `VENCIDO`: `LoteRepository.marcar_vencidos` existe, mas **nenhum código o chama** (sem job, sem rota). Na prática o status não muda sozinho; o campo `vencido` das respostas de lotes é calculado pela data (`data_validade < hoje`).
- `BLOQUEADO`: saída com esse lote é recusada. O status é definido pelo sistema (quantidade zerada); não há rota para bloquear manualmente (recall).
- Saída de lote `VENCIDO` é permitida de propósito: é a forma de dar baixa em vencido.

**RN-LOT-005: Alertas de Vencimento** (Parcial)
- Calculados **na consulta**: `alerta_vencimento` quando faltam de 1 a **30** dias (não 7); `GET /estoque/lotes/vencendo` lista lotes `ATIVO` com validade em até 30 dias.
- Lotes sem `data_validade` não geram alerta.
- **Não há verificação diária, notificação WhatsApp nem evento**: o `EventPublisher` existe mas nenhum código de estoque o chama.

**RN-LOT-006: Rastreabilidade** (Parcial)
- Vale para entrada com lote e saída com `lote_id`, que gravam `lote_id` na movimentação.
- **Não é verdade** que todas as movimentações registram lote: baixa de venda, estorno, ajuste e reserva não tocam lotes. Não há saída automática por FIFO.

---

## 4. Entidade: Inventário

> **Não exposto pela API.** Existem tabelas (`inventarios`, `itens_inventario`), schemas e `InventarioRepository`, mas **não há rota nem serviço** que crie ou finalize inventário (o repositório só é importado no service, sem uso). O fluxo de contagem hoje é o `POST /estoque/ajuste` por item. As regras abaixo descrevem o **modelo de dados**, não um comportamento disponível.

### 📊 Estrutura de Dados

Tabela `estoque.inventarios`:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Identificador único |
| `empresa_id` | Integer | Sim | Tenant |
| `data_inventario` | DateTime | Sim | Data da contagem |
| `responsavel` | String(200) | Sim | Nome do responsável |
| `observacao` | Text | Não | Observações gerais |
| `finalizado` | Boolean | Sim | Padrão `false` |
| `data_finalizacao` | DateTime | Não | Data de finalização |
| `created_at` / `updated_at` | DateTime | Sim | Auditoria |

Tabela `estoque.itens_inventario`: `id`, `inventario_id`, `estoque_id`, `quantidade_sistema`, `quantidade_contada`, `diferenca`, `observacao`, `ajustado`, `created_at`.

### Regras (somente modelo/schema)

- **RN-INV-001**: o schema `InventarioCreate` exige `responsavel` e a lista `itens`; `finalizado` nasce `false`.
- **RN-INV-002**: cada item guarda `quantidade_sistema`, `quantidade_contada` e `diferenca`.
- **RN-INV-003 / RN-INV-004** (finalização que ajusta o estoque e gera movimentações `AJUSTE`): **Não implementado.** `InventarioRepository.finalizar` só marca `finalizado = true` e `data_finalizacao`; não ajusta quantidades nem cria movimentações, e nada o chama.

---

## 5. Casos de Uso

### 5.1. Venda com Estoque Insuficiente

**Cenário**: cliente quer 100 unidades, há 50.

**Comportamento real**:
1. Se o chamador reservar (o serviço de Vendas chama `POST /estoque/reservar` em `venda_service.py`): estoque insuficiente responde **400** `Quantidade disponível insuficiente para reserva`, nada é reservado.
2. Na confirmação, `POST /estoque/baixar-venda` valida a quantidade **física** de todos os itens sob lock; qualquer item sem saldo devolve **409** e **nenhum** item é baixado.
3. Venda parcial/backorder: **não existe**.

### 5.2. Lote Vencido com Estoque

**Cenário**: lote vence e ainda tem 50 unidades.

**Comportamento real**:
1. Nenhum job marca o lote como `VENCIDO` nem publica evento ou notificação (ver RN-LOT-004/005).
2. Enquanto vencido, ele aparece com `vencido = true` em `GET /estoque/{id}/lotes` e em `/lotes/vencendo` (se ainda `ATIVO`).
3. O gerente dá baixa com `POST /estoque/saida` informando o `lote_id` (permitido para lote vencido). Não há remarcação de validade por rota.

### 5.3. Contagem com Grandes Diferenças

**Cenário**: a contagem física de um item é 100 unidades menor que o sistema.

**Comportamento real**:
1. O operador chama `POST /estoque/ajuste` com `estoque_id` e `quantidade_nova` (a contagem) e um `motivo`.
2. Grava-se uma movimentação `AJUSTE` com `quantidade = 100`, `quantidade_anterior` e `quantidade_posterior`.
3. O motivo é o texto informado; não há `Inventário #uuid` automático nem alerta por diferença acima de 10%.
4. Se a contagem ficar abaixo da quantidade reservada, o ajuste é recusado (400).

---

## 📚 Referências

- [API de Estoque](../10-api-reference/estoque-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última revisão de conteúdo**: 2026-09-26, contra o código  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
