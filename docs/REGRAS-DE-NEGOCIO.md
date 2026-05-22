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

### 3.4. Entidade: Inventário

#### 📊 Estrutura de Dados

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

#### ✅ Regras de Validação

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

## 4. Integrações entre Serviços

### 4.1. Cliente ↔ Vendas

**Validações ao criar venda:**
- Cliente deve existir e estar ativo
- Cliente não pode estar bloqueado
- Se venda fiada: verificar crédito disponível

**Atualizações automáticas:**
- Venda fiada: debita crédito do cliente
- Pagamento recebido: credita crédito do cliente

---

### 4.2. Produto ↔ Estoque

**Validações ao movimentar estoque:**
- Produto deve existir no serviço de Produtos
- Se variante fornecida, deve existir e estar ativa
- Produto deve estar ativo para entrada/saída

**Sincronização:**
- Estoque mantém `produto_id` e `variante_id` como referências
- Não há FK física (serviços separados)
- Validação é feita via API

---

### 4.3. Estoque ↔ Vendas

**Fluxo de reserva:**
1. Cliente adiciona produto ao carrinho
2. Sistema reserva estoque (diminui disponível)
3. Reserva expira em X horas se não finalizada
4. Ao finalizar venda: estoque é baixado e reserva removida
5. Ao cancelar: reserva é liberada

**Validações:**
- Não pode vender mais que o disponível
- Reserva não pode exceder disponível
- Saída de estoque requer documento (número da venda)

---

### 4.4. Cliente ↔ Financeiro

**Integração de crédito:**
- Venda fiada cria conta a receber no Financeiro
- Conta a receber debita crédito do cliente
- Pagamento recebido credita crédito do cliente
- Cliente é bloqueado se crédito ficar negativo

---

### 4.5. Eventos Assíncronos (RabbitMQ)

**Eventos publicados:**

| Evento | Publicador | Consumidores | Descrição |
|--------|-----------|--------------|-----------|
| `estoque.entrada` | Estoque | Relatórios | Entrada de mercadoria |
| `estoque.saida` | Estoque | Relatórios | Saída de mercadoria |
| `estoque.alerta_baixo` | Estoque | Notificações | Estoque abaixo do mínimo |
| `estoque.lote_vencido` | Estoque | Notificações | Lote venceu |
| `venda.finalizada` | Vendas | Financeiro, Estoque | Venda concluída |
| `venda.cancelada` | Vendas | Estoque, Financeiro | Venda cancelada |
| `pagamento.recebido` | Financeiro | Clientes | Pagamento confirmado |
| `cliente.bloqueado` | Clientes | Vendas | Cliente foi bloqueado |

---

## 5. Validações Globais

### 5.1. Validações de Formato

**CPF:**
- 11 dígitos numéricos
- Validação de dígitos verificadores
- Não aceita CPFs conhecidos como inválidos (111.111.111-11)

**Telefone:**
- Formato E.164: `+[código país][DDD][número]`
- Exemplo: `+5511999999999`

**CEP:**
- 8 dígitos numéricos
- Exemplo: `01234567`

**UF:**
- 2 caracteres maiúsculos
- Deve ser sigla válida de estado brasileiro

**Email:**
- Formato válido de email
- Máximo 255 caracteres

---

### 5.2. Validações de Negócio

**Unicidade:**
- CPF único por cliente
- SKU único por variante
- Código de lote único
- Email único por usuário (gateway)

**Valores Monetários:**
- Sempre maior ou igual a zero
- 2 casas decimais
- Tipo: Decimal(10,2)

**Quantidades:**
- Sempre maior ou igual a zero
- Tipo: Float (permite fracionados)

**Datas:**
- Data de nascimento: no passado
- Data de validade: no futuro
- Data de fabricação: anterior à validade

---

### 5.3. Regras de Autorização (RBAC)

| Operação | ADMIN | GERENTE | VENDEDOR | OPERADOR |
|----------|-------|---------|----------|----------|
| Criar Cliente | ✅ | ✅ | ✅ | ❌ |
| Editar Cliente | ✅ | ✅ | ❌ | ❌ |
| Desativar Cliente | ✅ | ❌ | ❌ | ❌ |
| Criar Produto | ✅ | ✅ | ❌ | ❌ |
| Editar Produto | ✅ | ✅ | ❌ | ❌ |
| Entrada Estoque | ✅ | ✅ | ❌ | ❌ |
| Saída Estoque | ✅ | ✅ | ✅ | ✅ |
| Criar Venda | ✅ | ✅ | ✅ | ✅ |
| Cancelar Venda | ✅ | ✅ | ❌ | ❌ |
| Inventário | ✅ | ✅ | ❌ | ❌ |
| Ajustar Crédito | ✅ | ✅ | ❌ | ❌ |

---

## 6. Casos de Uso Especiais

### 6.1. Carrinho e Pedido

#### 6.1.1. Criação e Gestão de Carrinho

**RN-CAR-001: Carrinho Anônimo**
- Cliente pode criar carrinho sem estar autenticado
- Carrinho é identificado por token único (UUID)
- Carrinho anônimo pode ser convertido em carrinho de cliente

**RN-CAR-002: Expiração de Carrinho**
- Carrinho tem TTL (Time To Live) de 2 horas
- Após expiração, reservas são liberadas automaticamente
- Job Celery executa a cada 15 minutos para limpar carrinhos expirados

**RN-CAR-003: Reserva de Estoque no Carrinho**
- Ao adicionar item ao carrinho, estoque é reservado
- Reserva diminui `quantidade_disponivel`
- Reserva aumenta `quantidade_reservada`
- Quantidade física não é alterada na reserva

**RN-CAR-004: Validação de Disponibilidade**
- Sistema verifica disponibilidade antes de adicionar ao carrinho
- Se estoque insuficiente, item não é adicionado
- Cliente é notificado da indisponibilidade

**RN-CAR-005: Remoção de Item**
- Ao remover item, reserva é liberada automaticamente
- `quantidade_disponivel` é restaurada
- `quantidade_reservada` é decrementada

#### 6.1.2. Checkout e Criação de Pedido

**RN-PED-001: Validações no Checkout**
- Cliente deve estar cadastrado e ativo
- Cliente não pode estar bloqueado
- Endereço de entrega deve existir
- Carrinho não pode estar vazio

**RN-PED-002: Conversão Carrinho → Pedido**
- Checkout cria pedido com status `PENDENTE`
- Reservas são mantidas durante processamento
- Carrinho é removido após criação do pedido

**RN-PED-003: Formas de Pagamento**
- **À vista (PIX/Cartão)**: Pedido fica `AGUARDANDO_PAGAMENTO`
- **Fiado**: Valida crédito e cria conta a receber

**RN-PED-004: Pagamento PIX**
- Sistema gera QR Code via Mercado Pago
- Pedido aguarda webhook de confirmação
- Timeout de 30 minutos para pagamento

**RN-PED-005: Pagamento Fiado**
- Valida crédito disponível do cliente
- Cria conta a receber no Financeiro
- Debita crédito do cliente
- Pedido vai direto para `CONFIRMADO`

**RN-PED-006: Confirmação de Pagamento**
- Webhook Mercado Pago confirma pagamento
- Pedido muda para `PAGO`
- Sistema converte pedido em venda
- Reservas são confirmadas (baixa física)

**RN-PED-007: Falha no Pagamento**
- Pagamento recusado: pedido vai para `PAGAMENTO_RECUSADO`
- Todas as reservas são liberadas
- Cliente pode tentar novamente

**RN-PED-008: Cancelamento de Pedido**
- Apenas pedidos não finalizados podem ser cancelados
- Reservas são liberadas automaticamente
- Se fiado: crédito é estornado
- Motivo do cancelamento é obrigatório

#### 6.1.3. Conversão Pedido → Venda

**RN-VEN-001: Criação de Venda**
- Venda é criada após confirmação de pagamento
- Status inicial: `FINALIZADA`
- Venda referencia o pedido original

**RN-VEN-002: Confirmação de Reservas**
- Sistema chama `POST /estoque/confirmar-reserva` para cada item
- `quantidade_reservada` é decrementada
- `quantidade` física é decrementada
- Movimentação tipo `SAIDA` é registrada

**RN-VEN-003: Eventos Publicados**
- `venda.finalizada` - Venda concluída
- `pedido.pago` - Pedido pago
- `estoque.confirmado` - Estoque baixado

---

### 6.2. Venda com Estoque Insuficiente

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

---

### 6.3. Cliente com Crédito Insuficiente

**Cenário**: Cliente tenta compra fiada de R$ 500, mas tem apenas R$ 300 de crédito

**Comportamento**:
1. Sistema valida crédito disponível
2. Retorna erro: `400 Bad Request - Crédito insuficiente`
3. Venda não é criada
4. Estoque não é reservado

**Alternativa**: Pagamento misto (futuro)
- R$ 300 no fiado
- R$ 200 à vista

---

### 6.4. Lote Vencido com Estoque

**Cenário**: Lote vence mas ainda tem 50 unidades

**Comportamento**:
1. Job diário verifica lotes vencidos
2. Marca lote como `VENCIDO`
3. Publica evento `estoque.lote_vencido`
4. Notificação é enviada ao gerente
5. Lote vencido não é usado em novas saídas (FIFO)
6. Gerente deve dar baixa manual (perda) ou remarcar validade

---

### 6.5. Inventário com Grandes Diferenças

**Cenário**: Inventário encontra diferença de -100 unidades (falta)

**Comportamento**:
1. Diferença é registrada no item do inventário
2. Ao finalizar inventário:
   - Quantidade é ajustada para quantidade contada
   - Movimentação tipo `AJUSTE` é criada
   - Motivo: `Inventário #{uuid}`
3. Alerta é gerado se diferença > 10% do estoque

---

## 7. Glossário

| Termo | Definição |
|-------|-----------|
| **Soft Delete** | Desativação lógica (ativo=false) ao invés de exclusão física |
| **FIFO** | First In, First Out - Primeiro que entra, primeiro que sai |
| **SKU** | Stock Keeping Unit - Código único de produto/variante |
| **Markup** | Percentual de lucro sobre o custo |
| **E.164** | Formato internacional de telefone |
| **RBAC** | Role-Based Access Control - Controle de acesso baseado em papéis |
| **Saga Pattern** | Padrão para transações distribuídas em microsserviços |
| **Idempotência** | Operação que pode ser executada múltiplas vezes com mesmo resultado |

---

## 📚 Referências

- **Diagramas de Sequência**: [docs/DIAGRAMAS-SEQUENCIA.md](./DIAGRAMAS-SEQUENCIA.md)
- **Arquitetura**: [docs/ARQUITETURA-COMUNICACAO.md](./ARQUITETURA-COMUNICACAO.md)
- **Especificação Técnica**: [docs/ESPECIFICACAO-TECNICA.md](./ESPECIFICACAO-TECNICA.md)
- **Mapeamento de Rotas**: [docs/MAPEAMENTO-ROTAS.md](./MAPEAMENTO-ROTAS.md)

---

**Última atualização**: 2026-05-21  
**Versão**: 1.0.0  
**Autor**: Equipe Runas  
**Status**: ✅ Completo

