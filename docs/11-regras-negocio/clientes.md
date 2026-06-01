# 👥 Regras de Negócio - Clientes

Regras de negócio do serviço de Clientes.

---

## 1. Entidade: Cliente

### 📊 Estrutura de Dados

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

### ✅ Regras de Validação

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

### 💳 Regras de Crédito

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

### 🗑️ Regras de Exclusão

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

## 2. Entidade: Endereço

### 📊 Estrutura de Dados

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

### ✅ Regras de Validação

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

## 3. Casos de Uso

### 3.1. Cliente com Crédito Insuficiente

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

## 📚 Referências

- [Diagramas de Sequência - Clientes](../03-arquitetura/diagramas/sequencia.md#1-operações-de-cliente)
- [API de Clientes](../10-api-reference/clientes-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
