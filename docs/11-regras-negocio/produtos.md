# 📦 Regras de Negócio - Produtos

Regras de negócio do serviço de Produtos.

---

## 1. Entidade: Categoria

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `nome` | String(100) | Sim | Sim | Nome da categoria |
| `descricao` | String(500) | Não | Não | Descrição da categoria |

### ✅ Regras de Validação

**RN-CAT-001: Nome Único**
- Nome da categoria deve ser único no sistema
- Não pode haver duas categorias com o mesmo nome
- Comparação é case-insensitive

**RN-CAT-002: Validação de Nome**
- Nome deve ter no mínimo 1 caractere
- Nome deve ter no máximo 100 caracteres
- Nome é obrigatório

**RN-CAT-003: Exclusão de Categoria**
- Categoria não pode ser excluída se tiver produtos vinculados
- Restrição: `RESTRICT` no banco de dados
- Solução: Reatribuir produtos para outra categoria antes de excluir

---

## 2. Entidade: Produto

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `categoria_id` | UUID | Sim | Não | FK para Categoria |
| `nome` | String(255) | Sim | Não | Nome do produto |
| `descricao` | Text | Não | Não | Descrição detalhada |
| `ativo` | Boolean | Sim | Não | Produto ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |

### ✅ Regras de Validação

**RN-PRO-001: Validação de Nome**
- Nome deve ter no mínimo 1 caractere
- Nome deve ter no máximo 255 caracteres
- Nome é obrigatório

**RN-PRO-002: Categoria Obrigatória**
- Todo produto deve estar vinculado a uma categoria
- Categoria deve existir no sistema
- Categoria não pode ser NULL

**RN-PRO-003: Produto Ativo/Inativo**
- Produtos inativos não aparecem no catálogo público
- Produtos inativos não podem ser adicionados a novas vendas
- Produtos inativos mantêm histórico de vendas anteriores

**RN-PRO-004: Exclusão de Produto**
- Produto não pode ser excluído se tiver:
  - Estoque registrado
  - Vendas associadas
  - Variantes ativas
- Solução: Desativar o produto ao invés de excluir

**RN-PRO-005: Relacionamentos em Cascata**
- Ao excluir produto, suas variantes são excluídas automaticamente
- Ao excluir produto, suas fotos de catálogo são excluídas
- Ao excluir produto, sua configuração de catálogo é excluída
- Ao excluir produto, vínculos com fornecedores são excluídos

---

## 3. Entidade: Variante

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Não | FK para Produto |
| `sku` | String(100) | Sim | Sim | Código SKU único |
| `preco_custo` | Decimal(10,2) | Sim | Não | Preço de custo |
| `markup_pct` | Decimal(5,2) | Sim | Não | Percentual de markup |
| `preco_venda` | Decimal(10,2) | Sim | Não | Preço de venda |
| `ativo` | Boolean | Sim | Não | Variante ativa? |

### ✅ Regras de Validação

**RN-VAR-001: SKU Único**
- SKU deve ser único em todo o sistema
- SKU identifica unicamente uma variante
- SKU deve ter entre 1 e 100 caracteres
- **Exemplo**: `CAMISA-P-AZUL`, `TENIS-42-PRETO`

**RN-VAR-002: Validação de Preços**
- `preco_custo` deve ser maior que zero
- `preco_venda` deve ser maior que zero
- `markup_pct` deve ser maior ou igual a zero
- Todos os preços têm 2 casas decimais

**RN-VAR-003: Cálculo de Preço de Venda**
- Fórmula: `preco_venda = preco_custo * (1 + markup_pct / 100)`
- **Exemplo**: 
  - Custo: R$ 100,00
  - Markup: 50%
  - Venda: R$ 150,00
- Sistema pode calcular automaticamente ou aceitar valor manual

**RN-VAR-004: Atributos de Variante**
- Variante pode ter múltiplos atributos (cor, tamanho, etc)
- Cada atributo tem uma chave e um valor
- **Exemplos**:
  - `cor: Azul`
  - `tamanho: P`
  - `voltagem: 110V`
- Atributos são armazenados na tabela `atributos_variante`

**RN-VAR-005: Exclusão de Variante**
- Variante não pode ser excluída se tiver:
  - Estoque registrado
  - Vendas associadas
- Solução: Desativar a variante ao invés de excluir

**RN-VAR-006: Variante Ativa/Inativa**
- Variantes inativas não aparecem no catálogo
- Variantes inativas não podem ser vendidas
- Produto pode ter todas as variantes inativas

---

## 4. Entidade: Fornecedor

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `nome` | String(255) | Sim | Não | Nome do fornecedor |
| `cnpj` | String(18) | Não | Não | CNPJ do fornecedor |
| `email` | String(255) | Não | Não | Email de contato |
| `telefone` | String(20) | Não | Não | Telefone de contato |
| `endereco` | Text | Não | Não | Endereço completo |
| `cidade` | String(100) | Não | Não | Cidade |
| `uf` | String(2) | Não | Não | Estado (sigla) |
| `ativo` | Boolean | Sim | Não | Fornecedor ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-FOR-001: Validação de Nome**
- Nome deve ter no mínimo 1 caractere
- Nome deve ter no máximo 255 caracteres
- Nome é obrigatório

**RN-FOR-002: Validação de CNPJ**
- CNPJ é opcional
- Se fornecido, deve ter formato válido
- CNPJ pode conter formatação (pontos, traços, barra)

**RN-FOR-003: Fornecedor Ativo/Inativo**
- Fornecedores inativos não aparecem em listagens padrão
- Fornecedores inativos mantêm histórico de compras

---

## 5. Entidade: Fornecedor-Produto (Vínculo)

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `fornecedor_id` | UUID | Sim | Não | FK para Fornecedor |
| `produto_id` | UUID | Sim | Não | FK para Produto |
| `codigo_fornecedor` | String(100) | Não | Não | Código do produto no fornecedor |
| `preco_fornecedor` | Decimal(10,2) | Sim | Não | Preço cobrado pelo fornecedor |
| `prazo_entrega_dias` | Integer | Sim | Não | Prazo de entrega em dias |
| `quantidade_minima` | Integer | Sim | Não | Quantidade mínima de compra |
| `ativo` | Boolean | Sim | Não | Vínculo ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |

### ✅ Regras de Validação

**RN-FP-001: Validação de Preço**
- `preco_fornecedor` deve ser maior que zero
- Preço tem 2 casas decimais

**RN-FP-002: Validação de Prazo**
- `prazo_entrega_dias` deve ser maior ou igual a zero
- Padrão: 0 dias (entrega imediata)

**RN-FP-003: Validação de Quantidade Mínima**
- `quantidade_minima` deve ser maior ou igual a 1
- Padrão: 1 unidade

**RN-FP-004: Múltiplos Fornecedores**
- Um produto pode ter múltiplos fornecedores
- Um fornecedor pode fornecer múltiplos produtos
- Relacionamento N:N através da tabela `fornecedor_produtos`

---

## 6. Entidade: Catálogo (Configuração)

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Sim | FK para Produto (1:1) |
| `visivel` | Boolean | Sim | Não | Visível no catálogo público? |
| `destaque` | Boolean | Sim | Não | Produto em destaque? |
| `ordem_exibicao` | Integer | Sim | Não | Ordem de exibição |
| `descricao_publica` | Text | Não | Não | Descrição para o público |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |

### ✅ Regras de Validação

**RN-CAL-001: Visibilidade no Catálogo**
- Apenas produtos com `visivel = true` aparecem no catálogo público
- Produtos invisíveis ainda podem ser vendidos internamente
- Padrão: `visivel = false`

**RN-CAL-002: Produtos em Destaque**
- Produtos com `destaque = true` aparecem em seção especial
- Produtos em destaque têm prioridade na exibição
- Padrão: `destaque = false`

**RN-CAL-003: Ordem de Exibição**
- `ordem_exibicao` define a ordem no catálogo
- Menor número = maior prioridade
- Padrão: 0
- Produtos com mesma ordem são ordenados por nome

**RN-CAL-004: Descrição Pública**
- Descrição pública pode ser diferente da descrição interna
- Usada para marketing e SEO
- Opcional

---

## 7. Entidade: Catálogo (Fotos)

### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Não | FK para Produto |
| `url` | String(500) | Sim | Não | URL da foto |
| `ordem` | Integer | Sim | Não | Ordem de exibição |

### ✅ Regras de Validação

**RN-FOT-001: Múltiplas Fotos**
- Produto pode ter múltiplas fotos
- Fotos são ordenadas pelo campo `ordem`
- Primeira foto (ordem = 0) é a foto principal

**RN-FOT-002: URL da Foto**
- URL deve ter entre 1 e 500 caracteres
- URL deve ser válida
- Pode ser URL externa ou caminho interno

**RN-FOT-003: Ordem de Exibição**
- `ordem` deve ser maior ou igual a zero
- Fotos com mesma ordem são ordenadas por ID

---

## 📚 Referências

- [Diagramas de Sequência - Produtos](../03-arquitetura/diagramas/sequencia.md#2-operações-de-produto)
- [API de Produtos](../10-api-reference/produtos-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
