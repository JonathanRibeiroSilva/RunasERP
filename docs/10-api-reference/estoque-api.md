# API de Estoque - Runas

> **Referência** da API do serviço de Estoque, conferida contra `services/estoque/routers/estoque.py`, `schemas/estoque.py`, `services/estoque_service.py` e `repositories/estoque_repository.py`.

---

## 📋 Visão Geral

**Porta do serviço**: `8003` (`services/estoque/Dockerfile`; no compose de dev fica em `127.0.0.1:8003`)
**Prefixo**: todas as rotas ficam sob `/estoque` (mais `/health`)
**Formato**: JSON

### Autenticação e tenant

O serviço **não valida JWT**. Quem autentica é o api-gateway, e o serviço confia em headers:

| Header | Obrigatório | Função |
|--------|-------------|--------|
| `X-Empresa-Id` | Sim, em todas as rotas de `/estoque` | ID da empresa (tenant). Ausente: 422 do FastAPI. Menor ou igual a zero: 400. |
| `X-Servico-Interno-Token` | Só quando `SERVICO_INTERNO_TOKEN` estiver configurado | Prova de origem interna (`interno.py`). Sem a variável, o serviço aceita a chamada e apenas loga. `/health` é isento. |

Pelo gateway (`api-gateway/routers/proxy.py`), todo `/estoque` exige usuário **ADMIN ou OPERADOR** (`require_admin_or_operador`), e o gateway injeta `X-Empresa-Id`. Os exemplos abaixo chamam o serviço direto (dev), por isso mostram os headers.

Rotas que recebem `empresa_id` no corpo (`POST /estoque`, `/entrada`, `/saida`, `/baixar-venda`, `/estornar-venda`, `/reservar`, `/liberar-reserva`) respondem **403** se ele diferir do header. `POST /estoque/ajuste` não tem `empresa_id` no corpo.

### Convenções

- Quantidades são `float` (não inteiro).
- Listagens retornam **array simples**, paginado por `skip`/`limit` (padrão `limit=100`, máximo `1000`). Não existe envelope `items/total/page`.
- Datas de criação/atualização se chamam `created_at` / `updated_at`.

---

## 📍 Endpoints

| Verbo | Caminho | Status | Descrição |
|-------|---------|--------|-----------|
| POST | `/estoque` | 201 | Cria registro de estoque |
| GET | `/estoque` | 200 | Lista estoques (com alertas) |
| GET | `/estoque/baixo` | 200 | Atalho: só estoque baixo |
| GET | `/estoque/zerado` | 200 | Atalho: só zerado |
| GET | `/estoque/disponibilidade` | 200 | Disponibilidade de produto/variante |
| GET | `/estoque/{estoque_id}` | 200 | Busca por ID do registro de estoque |
| PUT | `/estoque/{estoque_id}` | 200 | Atualiza mínimo, máximo, localização, ativo |
| POST | `/estoque/entrada` | 201 | Entrada de mercadoria |
| POST | `/estoque/saida` | 200 | Saída de mercadoria |
| POST | `/estoque/baixar-venda` | 200 | Baixa atômica e idempotente dos itens de uma venda |
| POST | `/estoque/estornar-venda` | 200 | Estorno atômico e idempotente de uma venda |
| POST | `/estoque/ajuste` | 200 | Ajuste de inventário (define a quantidade) |
| POST | `/estoque/reservar` | 200 | Reserva quantidade |
| POST | `/estoque/liberar-reserva` | 200 | Libera reserva |
| GET | `/estoque/{estoque_id}/movimentacoes` | 200 | Histórico do registro |
| GET | `/estoque/{estoque_id}/lotes` | 200 | Lotes do registro |
| GET | `/estoque/lotes/vencendo` | 200 | Lotes que vencem em até 30 dias |
| GET | `/estoque/relatorios/geral` | 200 | Relatório geral |
| GET | `/estoque/relatorios/movimentacoes` | 200 | Relatório por período (ver aviso abaixo) |

O identificador do estoque é o `id` do **registro de estoque**, não o `variante_id`. Para achar o estoque de um produto/variante use `GET /estoque/disponibilidade` ou filtre a listagem.

---

### Criar Estoque
```http
POST /estoque
```

```json
{
  "empresa_id": 1,
  "produto_id": "uuid",
  "variante_id": "uuid-ou-null",
  "quantidade": 0,
  "estoque_minimo": 10,
  "estoque_maximo": null,
  "localizacao": "Prateleira A1"
}
```

Apenas `empresa_id` e `produto_id` são obrigatórios; `quantidade` e `estoque_minimo` têm padrão `0`. Antes de criar, o serviço consulta o serviço de Produtos (`GET /produtos/{id}` e, se houver, `/variantes/{id}`) com o tenant correto: produto inexistente, de outra empresa ou **inativo** resulta em **400** `Produto ou variante não encontrado`. Já existir estoque para o par produto/variante: **400**.

**Response 201** (`EstoqueResponse`):
```json
{
  "id": "uuid",
  "empresa_id": 1,
  "produto_id": "uuid",
  "variante_id": null,
  "quantidade": 0.0,
  "estoque_minimo": 10.0,
  "estoque_maximo": null,
  "localizacao": "Prateleira A1",
  "quantidade_reservada": 0.0,
  "quantidade_disponivel": 0.0,
  "ativo": true,
  "created_at": "2026-05-26T10:00:00",
  "updated_at": "2026-05-26T10:00:00"
}
```

---

### Listar Estoque
```http
GET /estoque?skip=0&limit=100&apenas_baixo=false&apenas_zerado=false
```

Retorna só registros com `ativo = true`, ordenados por `produto_id`. Cada item é um `EstoqueResponse` acrescido de:

- `alerta_estoque_baixo`: `quantidade <= estoque_minimo` **e** `quantidade > 0`
- `alerta_estoque_zerado`: `quantidade == 0`

Os alertas usam a quantidade **física** (`quantidade`), não a `quantidade_disponivel`. O filtro `apenas_baixo` (e `GET /estoque/baixo`) usa `quantidade <= estoque_minimo` sem excluir zero, então itens zerados com mínimo maior ou igual a zero também entram.

`GET /estoque/{estoque_id}` devolve o mesmo formato de um item (404 `Estoque não encontrado` se não existir na empresa).

---

### Disponibilidade
```http
GET /estoque/disponibilidade?produto_id=<uuid>&variante_id=<uuid opcional>
```

`produto_id` é obrigatório. Nunca dá 404:

```json
{
  "produto_id": "uuid",
  "variante_id": null,
  "quantidade": 50.0,
  "quantidade_reservada": 5.0,
  "quantidade_disponivel": 45.0,
  "existe": true
}
```

Sem registro de estoque, retorna tudo zerado e `existe: false`.

---

### Atualizar Configuração
```http
PUT /estoque/{estoque_id}
```

Corpo parcial (`EstoqueUpdate`): `estoque_minimo`, `estoque_maximo`, `localizacao`, `ativo`. Não altera quantidade (use entrada/saída/ajuste). 404 se não existir.

---

### Registrar Entrada
```http
POST /estoque/entrada
```

```json
{
  "empresa_id": 1,
  "produto_id": "uuid",
  "variante_id": null,
  "quantidade": 100,
  "motivo": "Compra do fornecedor ABC",
  "documento": "NF-12345",
  "custo_unitario": 4.5,
  "criar_lote": true,
  "codigo_lote": "LOTE-2026-001",
  "data_fabricacao": "2026-05-01",
  "data_validade": "2027-05-01",
  "fornecedor": "ABC",
  "nota_fiscal": "12345"
}
```

Obrigatórios: `empresa_id`, `produto_id`, `quantidade` (> 0). Se ainda não existe estoque do produto/variante, ele é **criado na primeira entrada**, depois de validar produto ativo no serviço de Produtos. O lote só é criado se `criar_lote` for `true` **e** `codigo_lote` vier preenchido.

**Response 201:** o `EstoqueResponse` atualizado (não a movimentação). A movimentação (`tipo: ENTRADA`) é gravada com `quantidade_anterior`/`quantidade_posterior`.

```bash
curl -X POST "http://localhost:8003/estoque/entrada" \
  -H "X-Empresa-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"empresa_id": 1, "produto_id": "<uuid>", "quantidade": 100, "motivo": "Compra do fornecedor ABC"}'
```

---

### Registrar Saída
```http
POST /estoque/saida
```

```json
{
  "empresa_id": 1,
  "produto_id": "uuid",
  "variante_id": null,
  "quantidade": 10,
  "motivo": "Venda balcão",
  "documento": "PEDIDO-789",
  "lote_id": "uuid-opcional"
}
```

**Response 200:** `EstoqueResponse` atualizado. Erros são **400** (não 422):

- `Estoque não encontrado para este produto/variante`
- `Quantidade disponível insuficiente. Disponível: 5.0, Solicitado: 10.0` (compara com `quantidade_disponivel`, ou seja, descontando reservas)
- com `lote_id`: lote de outro estoque, lote `BLOQUEADO`, ou quantidade maior que a do lote. Lote `VENCIDO` **pode** sair (é a forma de dar baixa em vencido).

---

### Baixar Venda
```http
POST /estoque/baixar-venda
```

```json
{
  "empresa_id": 1,
  "documento": "VND-2026-0001",
  "itens": [
    {"produto_id": "uuid", "variante_id": null, "quantidade": 2}
  ]
}
```

`documento` (número da venda) é **obrigatório na prática**: sem ele o serviço recusa. `itens` exige pelo menos 1.

- Atômico: se qualquer item faltar, nada é baixado. Valida a quantidade **física** (`quantidade`), não a disponível, porque converte a reserva do checkout em saída (`quantidade_reservada` diminui, sem ficar negativa).
- Idempotente por `(empresa_id, documento)` (tabela `baixas_venda_processadas`): repetir a chamada não baixa de novo e devolve o estado atual dos itens.
- Trava as linhas com `SELECT ... FOR UPDATE` em ordem determinística por `(produto_id, variante_id)` e refaz até 3 tentativas em deadlock (`40P01`) ou falha de serialização (`40001`).
- Não toca em lotes.
- Qualquer `ValueError` (sem estoque, item inexistente, sem `documento`) vira **409**.

**Response 200:** array de `EstoqueResponse`, um por item.

### Estornar Venda
```http
POST /estoque/estornar-venda
```

Mesmo corpo de `baixar-venda`. Devolve a quantidade física de cada item (movimentação `DEVOLUCAO`, motivo `Venda reembolsada`), de forma atômica e idempotente por `(empresa_id, documento)` (tabela `estornos_venda_processados`). Não exige que a baixa tenha existido. Erros de validação: **400**.

---

### Ajuste de Inventário
```http
POST /estoque/ajuste
```

```json
{
  "estoque_id": "uuid",
  "quantidade_nova": 45,
  "motivo": "Inventário mensal - contagem física",
  "observacao": null
}
```

O corpo usa `estoque_id` e `quantidade_nova` (a **nova quantidade total**, `>= 0`), não a diferença. O serviço grava uma movimentação `AJUSTE` com `quantidade = abs(nova - atual)` (sempre positiva; o sinal se deduz de `quantidade_anterior` e `quantidade_posterior`). `motivo` é obrigatório (máx. 200).

**Response 200:** `EstoqueResponse` atualizado. **400** se o estoque não existir ou se `quantidade_nova` for menor que a `quantidade_reservada` (`Libere as reservas antes.`).

---

### Reservar / Liberar
```http
POST /estoque/reservar
POST /estoque/liberar-reserva
```

Corpo: `empresa_id`, `produto_id`, `variante_id` (opcional), `quantidade` (> 0), `documento` (opcional, só logado). Resposta 200: `EstoqueResponse`.

- Reservar não altera `quantidade`; aumenta `quantidade_reservada` e reduz `quantidade_disponivel`. **400** `Quantidade disponível insuficiente para reserva` se passar do estoque.
- Liberar: **400** `Quantidade reservada insuficiente` se liberar mais do que está reservado.
- Este serviço **não expira** reservas. A expiração de 15 minutos do carrinho é do serviço de Vendas (`reserva_temporaria_service.py`, Redis).

---

### Histórico de Movimentações
```http
GET /estoque/{estoque_id}/movimentacoes?tipo=ENTRADA&skip=0&limit=100
```

`tipo` (opcional) aceita `ENTRADA`, `SAIDA`, `AJUSTE`, `DEVOLUCAO`, `PERDA`, `TRANSFERENCIA`. Ordenado do mais recente ao mais antigo. Array de:

```json
{
  "id": "uuid",
  "estoque_id": "uuid",
  "lote_id": null,
  "tipo": "SAIDA",
  "quantidade": 10.0,
  "quantidade_anterior": 60.0,
  "quantidade_posterior": 50.0,
  "motivo": "Venda confirmada",
  "observacao": null,
  "documento": "VND-2026-0001",
  "custo_unitario": null,
  "custo_total": null,
  "usuario_id": null,
  "created_at": "2026-05-26T11:00:00"
}
```

`quantidade` é sempre positiva; o sentido vem do `tipo`. Hoje só `ENTRADA`, `SAIDA`, `AJUSTE` e `DEVOLUCAO` (estorno de venda) são gravados por rotas; `PERDA` e `TRANSFERENCIA` existem no enum mas nenhuma rota os produz.

---

### Lotes
```http
GET /estoque/{estoque_id}/lotes?skip=0&limit=100
GET /estoque/lotes/vencendo?skip=0&limit=100
```

Não existe rota para criar ou editar lote: ele nasce numa entrada com `criar_lote`. Cada item traz os campos do lote (`codigo`, `quantidade`, `quantidade_inicial`, `data_fabricacao`, `data_validade`, `fornecedor`, `nota_fiscal`, `custo_unitario`, `status`: `ATIVO`/`VENCIDO`/`BLOQUEADO`) e os alertas `dias_para_vencer`, `alerta_vencimento` (vence em 1 a 30 dias) e `vencido` (`dias < 0`).

`/lotes/vencendo` lista lotes `ATIVO` com `data_validade` até hoje + 30 dias (inclui os já vencidos ainda marcados `ATIVO`), ordenados por validade.

---

### Relatórios
```http
GET /estoque/relatorios/geral
GET /estoque/relatorios/movimentacoes?data_inicio=...&data_fim=...
```

`/relatorios/geral` retorna `total_produtos`, `total_em_estoque`, `produtos_estoque_baixo`, `produtos_sem_estoque` e `valor_total_estoque` (sempre `null` hoje). `total_em_estoque` soma no máximo os 10.000 primeiros registros.

`/relatorios/movimentacoes` (`data_inicio` e `data_fim` obrigatórios) devolve `total_entradas`, `total_saidas`, `quantidade_entrada`, `quantidade_saida`.

> **Aviso (defeito no código):** `EstoqueService.gerar_relatorio_movimentacoes` chama `MovimentacaoRepository.contar_por_tipo(db, empresa_id, tipo, ...)`, mas o repositório só aceita `(db, tipo, data_inicio, data_fim)` e não filtra por empresa. Pela leitura do código a rota falha com erro 500. A CONFIRMAR em execução; não use como fonte até corrigir.

---

## 🚨 Regras Importantes

1. **Movimentações são imutáveis pela API**: não há rota para editar ou apagar. Corrige-se com um novo ajuste.
2. **Quantidade nunca negativa**: além das validações do serviço, o banco tem o CHECK `ck_estoque_quantidades_nao_negativas` (`quantidade`, `quantidade_reservada` e `quantidade_disponivel` `>= 0`).
3. **Concorrência**: entrada, saída, ajuste, reserva, liberação, baixa e estorno leem a linha com `FOR UPDATE` dentro da transação, evitando atualização perdida.
4. **Transação atômica**: movimentação + atualização de quantidade (+ lote) na mesma transação; falhou, nada é salvo.
5. **Não há eventos nem alertas automáticos**: o `EventPublisher` (RabbitMQ) existe em `events/publisher.py`, mas nenhum código de estoque o chama; não há evento `estoque.minimo` nem notificação WhatsApp. Os alertas só aparecem nos campos das listagens.

---

## 🚨 Códigos de Erro

| Código | Quando |
|--------|--------|
| 400 | `ValueError` do serviço (estoque não encontrado na operação, quantidade insuficiente, produto inválido, `X-Empresa-Id` <= 0). Vale para criar, entrada, saída, estorno, ajuste, reservar e liberar |
| 403 | `empresa_id` do corpo diferente de `X-Empresa-Id` |
| 404 | `GET`/`PUT /estoque/{estoque_id}` com ID inexistente na empresa |
| 409 | `POST /estoque/baixar-venda` com falha de validação (sem estoque suficiente, item inexistente, sem `documento`) |
| 422 | Validação do Pydantic (campo faltando, quantidade `<= 0`, `X-Empresa-Id` ausente) |
| 500 | Erro interno (`{"detail": "Erro interno do servidor"}`) |

O 401 é do gateway, não deste serviço.

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Estoque](../11-regras-negocio/estoque.md)
- [Mapeamento Completo de Rotas](./mapeamento-rotas.md)
- [OpenAPI Specification](./openapi.yaml)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Última revisão de conteúdo:** contra o código em 2026-09-26
