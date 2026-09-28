# 📦 Regras de Negócio - Produtos

Regras de negócio do serviço de Produtos, conferidas contra `services/produtos/` (`models/`, `schemas/produtos.py`, `services/produtos.py`, `repositories/produtos.py`).

> **Legenda de status**: **Implementado** = existe e roda no código; **Parcial** = existe com ressalvas; **Não implementado** = aparecia neste documento mas não há código que o faça.

---

## 1. Entidade: Categoria

### 📊 Estrutura de Dados

Tabela `produtos.categorias`.

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `empresa_id` | Integer | Sim | Não | Tenant (multi-tenancy) |
| `nome` | String(100) | Sim | Por empresa | Nome da categoria |
| `descricao` | String(500) | Não | Não | Descrição da categoria |

### ✅ Regras de Validação

**RN-CAT-001: Nome Único** (Implementado, sem ignorar maiúsculas)
- Único **por empresa**: `UNIQUE (empresa_id, nome)`, mais checagem no serviço (400 `Categoria 'X' já existe`).
- A comparação é **exata**, diferencia maiúsculas de minúsculas: `Bebidas` e `bebidas` coexistem.

**RN-CAT-002: Validação de Nome** (Implementado)
- Obrigatório, de 1 a 100 caracteres (schema).

**RN-CAT-003: Exclusão de Categoria** (Implementado no banco, resposta ruim)
- `produtos.categoria_id` tem `ON DELETE RESTRICT`: categoria com produtos (mesmo soft-deletados) não sai.
- O router não trata essa violação: a resposta é **500** `Erro ao deletar categoria`, não um 409 explicativo.
- Solução: reatribuir os produtos a outra categoria antes de excluir.

---

## 2. Entidade: Produto

### 📊 Estrutura de Dados

Tabela `produtos.produtos`.

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `empresa_id` | Integer | Sim | Não | Tenant |
| `categoria_id` | UUID | Sim | Não | FK para Categoria (`RESTRICT`) |
| `nome` | String(255) | Sim | Não | Nome do produto |
| `descricao` | Text | Não | Não | Descrição detalhada |
| `preco` | Numeric(10,2) | Sim | Não | Preço de venda (padrão 0.00) |
| `custo` | Numeric(10,2) | Sim | Não | Custo de aquisição (padrão 0.00) |
| `preco_promocional` | Numeric(10,2) | Não | Não | Preço promocional |
| `promocao_fim` | Date | Não | Não | Último dia da promoção, inclusive |
| `unidade_medida` | String(10) | Sim | Não | Padrão `UN` |
| `codigo_barras` | String(50) | Não | Por empresa | Código de barras/EAN |
| `sku` | String(100) | Não | Não | SKU interno (não exposto para escrita nos schemas) |
| `ativo` | Boolean | Sim | Não | Produto ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |
| `deletado_em` | DateTime | Não | Não | Preenchido no soft delete |

O modelo tem ainda `estoque_minimo`, `estoque_maximo`, `peso_bruto` e `peso_liquido`, que os schemas de criação/leitura **não expõem**. O controle real de estoque mínimo fica no serviço de Estoque.

### ✅ Regras de Validação

**RN-PRO-001: Validação de Nome** (Implementado)
- Obrigatório, de 1 a 255 caracteres.

**RN-PRO-002: Categoria Obrigatória** (Implementado)
- `categoria_id` é obrigatório e a categoria precisa existir **na mesma empresa** (400 se não).

**RN-PRO-003: Produto Ativo/Inativo** (Parcial)
- Produto inativo **não aparece** na vitrine pública (`/loja-online/publico/produtos` exige `ativo`, não deletado e config `visivel = true`) e o detalhe público responde 404.
- Produto inativo **não inicia estoque** (criar registro ou primeira entrada exigem produto ativo no serviço de Produtos).
- **Não há bloqueio de venda** no serviço de Vendas: `venda_service.py` só confere se o produto existe (`GET /produtos/{id}`), sem olhar `ativo`. A CONFIRMAR se algum outro caminho de venda (carrinho/loja) verifica; em `services/vendas` não achei nenhuma checagem de `ativo` de produto.
- O histórico de vendas não depende do produto, pois nada é apagado.

**RN-PRO-004: Exclusão de Produto** (Implementado como soft delete, sem bloqueios)
- `DELETE /produtos/{id}` preenche `deletado_em`; **não há checagem** de estoque, vendas ou variantes. Recusa (404) apenas produto inexistente ou já deletado.
- Produto deletado some da listagem padrão e volta com `PATCH /produtos/{id}/restaurar`.
- Ele continua sendo retornado por `GET /produtos/{id}` e por `/produtos/categoria/{id}`, e a listagem da vitrine pública o exclui.
- Desativar (`ativo = false`) é a alternativa que mantém o produto listado no admin.

**RN-PRO-005: Relacionamentos em Cascata** (Implementado só na exclusão física)
- As FKs de variantes, fotos, config da loja e vínculos de fornecedor são `ON DELETE CASCADE` e o ORM usa `cascade="all, delete-orphan"`; vale se o registro for removido de fato.
- O soft delete **não** dispara cascata: variantes, fotos, config e vínculos permanecem.

**RN-PRO-006: Regras de Preço e Promoção** (Implementado; ausente do documento anterior)
- `preco >= custo` (senão 400 `Preço de venda não pode ser menor que o custo`), na criação e no resultado de cada atualização.
- `preco_promocional` (`> 0`) não pode ser maior que `preco` (igual é aceito).
- `preco_promocional` exige `promocao_fim`. Data no passado é aceita (encerra a promoção).
- `preco_efetivo` = `preco_promocional` enquanto `promocao_fim >= hoje` (fuso -03:00, sem horário de verão), senão `preco`. Promoção sem data de fim (dado antigo) cobra o preço normal.
- Baixar o `preco` abaixo do `preco_fornecedor` de qualquer vínculo é recusado (400).
- `unidade_medida` aceita apenas `UN, KG, G, LT, ML, CX, PCT, FD, SC, PAR, M, CM`.

---

## 3. Entidade: Variante

### 📊 Estrutura de Dados

Tabela `produtos.variantes`.

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `empresa_id` | Integer | Sim | Não | Tenant |
| `produto_id` | UUID | Sim | Não | FK para Produto (`CASCADE`) |
| `sku` | String(100) | Sim | Por empresa | Código SKU |
| `preco_custo` | Numeric(10,2) | Sim | Não | Preço de custo |
| `markup_pct` | Numeric(5,2) | Sim | Não | Percentual de markup |
| `preco_venda` | Numeric(10,2) | Sim | Não | Preço de venda (derivado) |
| `ativo` | Boolean | Sim | Não | Variante ativa? |

### ✅ Regras de Validação

**RN-VAR-001: SKU Único** (Implementado)
- Único **por empresa** (`UNIQUE (empresa_id, sku)` + checagem no serviço, 400 `SKU 'X' já existe`), de 1 a 100 caracteres.
- **Exemplo**: `CAMISA-P-AZUL`, `TENIS-42-PRETO`.

**RN-VAR-002: Validação de Preços** (Implementado)
- `preco_custo > 0` e `markup_pct >= 0` (schema; 422 se violar).
- `preco_venda` é derivado, então fica sempre `> 0`. Duas casas decimais.

**RN-VAR-003: Cálculo de Preço de Venda** (Implementado)
- `preco_venda = preco_custo * (1 + markup_pct / 100)`, arredondado a 2 casas com `ROUND_HALF_UP`. **Exemplo**: custo 100,00 e markup 50% dão 150,00.
- É **sempre calculado pelo servidor**: um `preco_venda` enviado no corpo é ignorado. Não é possível informar valor manual.
- Recalculado quando `preco_custo` ou `markup_pct` mudam; desativar não altera o preço.

**RN-VAR-004: Atributos de Variante** (Implementado)
- Vários atributos `chave` (1 a 50) + `valor` (1 a 100), na tabela `atributos_variante`. **Exemplos**: `cor: Azul`, `tamanho: P`, `voltagem: 110V`.
- Atributos só são gravados na **criação** da variante; `PUT /variantes/{id}` não os altera.

**RN-VAR-005: Exclusão de Variante** (Implementado como exclusão física, sem bloqueios)
- `DELETE /variantes/{id}` apaga o registro (e seus atributos). **Não há checagem** de estoque ou vendas. Para preservar histórico, desative (`ativo = false`).

**RN-VAR-006: Variante Ativa/Inativa** (Parcial)
- `ativo` é gravado e devolvido. **Não há filtro** de variantes inativas na vitrine pública (o detalhe público as retorna com `ativo: false`) nem bloqueio de venda no serviço de Vendas. A CONFIRMAR se o frontend as oculta.
- Produto com todas as variantes inativas é permitido.

---

## 4. Entidade: Fornecedor

### 📊 Estrutura de Dados

Tabela `produtos.fornecedores`.

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `empresa_id` | Integer | Sim | Não | Tenant |
| `nome` | String(255) | Sim | Não | Nome do fornecedor |
| `cnpj` | String(18) | Não | Por empresa | CNPJ do fornecedor |
| `email` | String(255) | Não | Não | Email de contato |
| `telefone` | String(20) | Não | Não | Telefone de contato |
| `endereco` | Text | Não | Não | Endereço completo |
| `cidade` | String(100) | Não | Não | Cidade |
| `uf` | String(2) | Não | Não | Estado (sigla) |
| `ativo` | Boolean | Sim | Não | Fornecedor ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-FOR-001: Validação de Nome** (Implementado)
- Obrigatório, de 1 a 255 caracteres.

**RN-FOR-002: CNPJ** (Parcial)
- Opcional, até 18 caracteres (cabe a máscara `00.000.000/0000-00`); **não há validação de formato nem de dígitos**.
- Se informado, é **único por empresa** (`UNIQUE (empresa_id, cnpj)` + checagem, 400 `CNPJ 'X' já cadastrado`). O valor é comparado como digitado, então o mesmo CNPJ com e sem máscara não é detectado como duplicado.

**RN-FOR-003: Fornecedor Ativo/Inativo** (Implementado)
- `GET /fornecedores` lista só ativos por padrão (`apenas_ativos=true`).
- Não há módulo de compras neste sistema; qualquer histórico de compras é externo a este serviço.
- `DELETE /fornecedores/{id}` é exclusão física e apaga também os vínculos com produtos.

---

## 5. Entidade: Fornecedor-Produto (Vínculo)

### 📊 Estrutura de Dados

Tabela `produtos.fornecedor_produtos` (não tem `empresa_id`; o tenant é validado pelo fornecedor e pelo produto).

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `fornecedor_id` | UUID | Sim | Não | FK para Fornecedor (`CASCADE`) |
| `produto_id` | UUID | Sim | Não | FK para Produto (`CASCADE`) |
| `codigo_fornecedor` | String(100) | Não | Não | Código do produto no fornecedor |
| `preco_fornecedor` | Numeric(10,2) | Sim | Não | Preço cobrado pelo fornecedor |
| `prazo_entrega_dias` | Integer | Sim | Não | Prazo de entrega em dias (padrão 0) |
| `quantidade_minima` | Integer | Sim | Não | Quantidade mínima de compra (padrão 1) |
| `ativo` | Boolean | Sim | Não | Vínculo ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |

### ✅ Regras de Validação

**RN-FP-001: Validação de Preço** (Implementado)
- `preco_fornecedor > 0`, 2 casas decimais.
- Além disso, `preco_fornecedor` **não pode ser maior que o `preco` de venda do produto** (400); vale ao criar e ao atualizar o vínculo.

**RN-FP-002: Validação de Prazo** (Implementado)
- `prazo_entrega_dias >= 0`; padrão 0.

**RN-FP-003: Validação de Quantidade Mínima** (Implementado)
- `quantidade_minima >= 1`; padrão 1.

**RN-FP-004: Múltiplos Fornecedores** (Implementado)
- Relação N:N pela tabela `fornecedor_produtos`. Não há restrição de unicidade em `(fornecedor_id, produto_id)`: o mesmo par pode ser vinculado mais de uma vez.
- O vínculo nasce `ativo` (o campo no corpo do POST é ignorado).

---

## 6. Entidade: Loja Online (Configuração de exibição)

Tabela `produtos.loja_online_config` (o código não usa o nome "catálogo" para a entidade).

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Sim | FK para Produto (1:1, `CASCADE`) |
| `visivel` | Boolean | Sim | Não | Visível na vitrine pública? |
| `destaque` | Boolean | Sim | Não | Produto em destaque? |
| `ordem_exibicao` | Integer | Sim | Não | Ordem de exibição |
| `descricao_publica` | Text | Não | Não | Descrição para o público |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-CAL-001: Visibilidade** (Implementado)
- A vitrine pública lista só produtos com config `visivel = true` (e produto ativo, não deletado). Sem config = não publicado. Padrão: `visivel = false`.
- Produto invisível continua acessível nas rotas administrativas.

**RN-CAL-002: Destaque** (Parcial)
- `destaque` é gravado e devolvido, padrão `false`. **Nenhuma consulta do serviço o usa para separar ou priorizar produtos**; qualquer tratamento especial é do frontend.

**RN-CAL-003: Ordem de Exibição** (Parcial)
- `ordem_exibicao >= 0`, padrão 0, é gravada e devolvida no admin. A vitrine pública **não ordena por ela**: ordena por `ordenar` = `nome` (padrão), `preco_asc`, `preco_desc` ou `recentes`.

**RN-CAL-004: Descrição Pública** (Implementado)
- Opcional, pode diferir da descrição interna. Está na config, mas as respostas públicas de produto não a incluem hoje (`ProdutoLojaOnlineRead` não tem `descricao_publica`).

**RN-CAL-005: Publicação** (Implementado)
- `PUT /loja-online/produtos/{produto_id}/publicar` cria a config se não existir (upsert) e define `visivel`/`destaque`.

---

## 7. Entidade: Loja Online (Fotos)

Tabela `produtos.loja_online_fotos`.

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Não | FK para Produto (`CASCADE`) |
| `url` | String(500) | Sim | Não | URL da foto |
| `ordem` | Integer | Sim | Não | Ordem de exibição |

### ✅ Regras de Validação

**RN-FOT-001: Múltiplas Fotos** (Implementado)
- Um produto pode ter várias fotos, retornadas ordenadas por `ordem` (a listagem do produto e `GET /loja-online/fotos/{produto_id}`). Por convenção, `ordem = 0` é a principal; o serviço não impõe isso.

**RN-FOT-002: URL da Foto** (Parcial)
- Apenas de 1 a 500 caracteres. **Não há validação de que seja uma URL válida**: aceita URL externa, caminho interno ou qualquer texto.

**RN-FOT-003: Ordem de Exibição** (Parcial)
- `ordem >= 0`, padrão 0. Não há critério de desempate para ordens iguais (a ordem entre elas não é garantida).

---

## 📚 Referências

- [API de Produtos](../10-api-reference/produtos-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última revisão de conteúdo**: 2026-09-26, contra o código  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
