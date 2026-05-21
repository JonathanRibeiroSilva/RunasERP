# 📋 Regras de Negócio - ERP Runas

**Data**: 2026-05-21  
**Versão**: 1.0.0  
**Status**: ✅ Documentação Completa

---

## 📑 Índice

1. [Serviço de Clientes](#1-serviço-de-clientes)
2. [Serviço de Produtos](#2-serviço-de-produtos)
3. [Serviço de Estoque](#3-serviço-de-estoque)
4. [Integrações entre Serviços](#4-integrações-entre-serviços)
5. [Validações Globais](#5-validações-globais)

---

## 1. Serviço de Clientes

### 1.1. Entidade: Cliente

#### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `cpf` | String(11) | Sim | Sim | CPF sem formatação |
| `nome` | String(255) | Sim | Não | Nome completo |
| `telefone` | String(20) | Sim | Não | Formato E.164 |
| `email` | String(255) | Não | Não | Email do cliente |
| `data_nasc` | Date | Não | Não | Data de nascimento |
| `limite_credito` | Decimal(10,2) | Sim | Não | Limite de crédito fiado |
| `credito_disponivel` | Decimal(10,2) | Sim | Não | Crédito disponível |
| `dia_vencimento` | Integer | Não | Não | Dia do vencimento (1-28) |
| `bloqueado` | Boolean | Sim | Não | Cliente bloqueado? |
| `ativo` | Boolean | Sim | Não | Cliente ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |


#### ✅ Regras de Validação

**RN-CLI-001: Validação de CPF**
- O CPF deve conter exatamente 11 dígitos numéricos
- O CPF deve ser válido segundo o algoritmo de validação brasileiro
- O CPF é normalizado automaticamente (remove pontos e traços)
- CPF deve ser único no sistema
- **Exemplo válido**: `12345678901` ou `123.456.789-01`
- **Exemplo inválido**: `11111111111`, `00000000000`

**RN-CLI-002: Validação de Telefone**
- Telefone deve estar no formato E.164 internacional
- Formato: `+[código país][DDD][número]`
- **Exemplo válido**: `+5511999999999`
- **Exemplo inválido**: `(11) 99999-9999`, `11999999999`
- Sistema normaliza automaticamente para E.164

**RN-CLI-003: Validação de Nome**
- Nome deve ter no mínimo 3 caracteres
- Nome deve ter no máximo 255 caracteres
- Nome é obrigatório

**RN-CLI-004: Validação de Email**
- Email é opcional
- Se fornecido, deve ser um email válido
- Máximo de 255 caracteres

**RN-CLI-005: Validação de Data de Nascimento**
- Data de nascimento é opcional
- Se fornecida, deve ser uma data válida no passado


#### 💳 Regras de Crédito

**RN-CLI-006: Limite de Crédito**
- Limite de crédito padrão é R$ 0,00
- Limite de crédito deve ser maior ou igual a zero
- Limite de crédito pode ser ajustado por usuários ADMIN ou GERENTE
- Crédito disponível é calculado automaticamente: `credito_disponivel = limite_credito - débitos_pendentes`

**RN-CLI-007: Crédito Disponível**
- Crédito disponível é calculado automaticamente
- Não pode ser editado diretamente
- É atualizado quando:
  - Limite de crédito é alterado
  - Uma venda fiada é realizada (diminui)
  - Um pagamento é recebido (aumenta)

**RN-CLI-008: Dia de Vencimento**
- Dia de vencimento é opcional
- Se fornecido, deve estar entre 1 e 28
- Usado para calcular vencimento de vendas fiadas
- **Exemplo**: Se `dia_vencimento = 10`, vendas fiadas vencem todo dia 10

**RN-CLI-009: Bloqueio de Cliente**
- Cliente pode ser bloqueado manualmente
- Cliente bloqueado não pode realizar novas compras fiadas
- Cliente é bloqueado automaticamente se:
  - Crédito disponível for negativo
  - Tiver parcelas vencidas há mais de 30 dias
- Cliente bloqueado pode ser desbloqueado por ADMIN ou GERENTE


#### 🗑️ Regras de Exclusão

**RN-CLI-010: Soft Delete**
- Clientes não são excluídos fisicamente do banco
- Ao "deletar", o campo `ativo` é marcado como `false`
- Clientes inativos não aparecem em listagens padrão
- Clientes inativos podem ser reativados

**RN-CLI-011: Restrições de Exclusão**
- Cliente não pode ser desativado se tiver:
  - Vendas em aberto
  - Débitos pendentes
  - Reservas de estoque ativas

---

### 1.2. Entidade: Endereço

#### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `cliente_id` | UUID | Sim | Não | FK para Cliente |
| `cep` | String(8) | Sim | Não | CEP sem formatação |
| `logradouro` | String(255) | Sim | Não | Rua, avenida, etc |
| `numero` | String(20) | Sim | Não | Número do imóvel |
| `complemento` | String(255) | Não | Não | Apto, bloco, etc |
| `bairro` | String(100) | Sim | Não | Bairro |
| `cidade` | String(100) | Sim | Não | Cidade |
| `uf` | String(2) | Sim | Não | Estado (sigla) |
| `principal` | Boolean | Sim | Não | Endereço principal? |


#### ✅ Regras de Validação

**RN-END-001: Validação de CEP**
- CEP deve conter exatamente 8 dígitos numéricos
- CEP é normalizado automaticamente (remove traços)
- **Exemplo válido**: `01234567` ou `01234-567`

**RN-END-002: Validação de UF**
- UF deve conter exatamente 2 caracteres
- UF deve ser uma sigla válida de estado brasileiro
- **Exemplos válidos**: `SP`, `RJ`, `MG`

**RN-END-003: Validação de Campos Obrigatórios**
- Logradouro: mínimo 3, máximo 255 caracteres
- Número: mínimo 1, máximo 20 caracteres
- Bairro: mínimo 3, máximo 100 caracteres
- Cidade: mínimo 3, máximo 100 caracteres

**RN-END-004: Endereço Principal**
- Cliente pode ter múltiplos endereços
- Apenas um endereço pode ser marcado como principal
- Se um endereço for marcado como principal, os demais são desmarcados automaticamente
- Se cliente não tiver endereço principal, o primeiro cadastrado é marcado automaticamente

**RN-END-005: Exclusão em Cascata**
- Ao desativar um cliente, seus endereços são mantidos
- Endereços são excluídos apenas se o cliente for excluído fisicamente (raro)

---

## 2. Serviço de Produtos

### 2.1. Entidade: Categoria

#### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `nome` | String(100) | Sim | Sim | Nome da categoria |
| `descricao` | String(500) | Não | Não | Descrição da categoria |

#### ✅ Regras de Validação

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

### 2.2. Entidade: Produto

#### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `categoria_id` | UUID | Sim | Não | FK para Categoria |
| `nome` | String(255) | Sim | Não | Nome do produto |
| `descricao` | Text | Não | Não | Descrição detalhada |
| `ativo` | Boolean | Sim | Não | Produto ativo? |
| `criado_em` | DateTime | Sim | Não | Data de criação |


#### ✅ Regras de Validação

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

### 2.3. Entidade: Variante

#### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Não | FK para Produto |
| `sku` | String(100) | Sim | Sim | Código SKU único |
| `preco_custo` | Decimal(10,2) | Sim | Não | Preço de custo |
| `markup_pct` | Decimal(5,2) | Sim | Não | Percentual de markup |
| `preco_venda` | Decimal(10,2) | Sim | Não | Preço de venda |
| `ativo` | Boolean | Sim | Não | Variante ativa? |

#### ✅ Regras de Validação

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

### 2.4. Entidade: Fornecedor

#### 📊 Estrutura de Dados

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


#### ✅ Regras de Validação

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

### 2.5. Entidade: Fornecedor-Produto (Vínculo)

#### 📊 Estrutura de Dados

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


#### ✅ Regras de Validação

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

### 2.6. Entidade: Catálogo (Configuração)

#### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Sim | FK para Produto (1:1) |
| `visivel` | Boolean | Sim | Não | Visível no catálogo público? |
| `destaque` | Boolean | Sim | Não | Produto em destaque? |
| `ordem_exibicao` | Integer | Sim | Não | Ordem de exibição |
| `descricao_publica` | Text | Não | Não | Descrição para o público |
| `atualizado_em` | DateTime | Sim | Não | Data de atualização |


#### ✅ Regras de Validação

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

### 2.7. Entidade: Catálogo (Fotos)

#### 📊 Estrutura de Dados

| Campo | Tipo | Obrigatório | Único | Descrição |
|-------|------|-------------|-------|-----------|
| `id` | UUID | Sim | Sim | Identificador único |
| `produto_id` | UUID | Sim | Não | FK para Produto |
| `url` | String(500) | Sim | Não | URL da foto |
| `ordem` | Integer | Sim | Não | Ordem de exibição |


#### ✅ Regras de Validação

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

## 3. Serviço de Estoque

### 3.1. Entidade: Estoque

#### 📊 Estrutura de Dados

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


#### ✅ Regras de Validação

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

---

### 3.2. Entidade: Movimentação

#### 📊 Estrutura de Dados

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


#### ✅ Regras de Validação

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

### 3.3. Entidade: Lote

#### 📊 Estrutura de Dados

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

#### ✅ Regras de Validação

**RN-LOT-001: Código Único**
- Código do lote deve ser único no sistema
- Usado para rastreabilidade
- **Exemplo**: `LOTE-2026-001`, `FAB-20260521`

