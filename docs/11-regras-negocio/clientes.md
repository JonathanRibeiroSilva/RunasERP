# 👥 Regras de Negócio - Clientes

Regras de negócio do serviço de Clientes (`services/clientes/`).

> **Como ler este documento.** Cada regra traz o status verificado no código e o
> arquivo/linha que sustenta a afirmação:
>
> - **IMPLEMENTADA** — existe código que a aplica, com a evidência citada.
> - **PARCIAL** — parte da regra roda, parte não; o texto diz qual é qual.
> - **NÃO IMPLEMENTADA** — nenhum código a aplica. É especificação a construir,
>   não comportamento vigente. Não escreva código nem teste assumindo que ela já
>   existe.
>
> O serviço monta dois routers (`services/clientes/main.py:57-58`):
> `clientes_router` e `enderecos_router`.

---

## 0. Isolamento por empresa (multi-tenancy)

**IMPLEMENTADA.** Toda rota dos dois routers depende de `get_empresa_id`
(`services/clientes/utils/tenant.py:6`), que exige o header `X-Empresa-Id`:

- Header ausente → `400 Bad Request`, "Header X-Empresa-Id é obrigatório".
- Header `<= 0` → `400 Bad Request`, "X-Empresa-Id deve ser maior que zero".

Em `POST /clientes` e `POST /clientes/oauth`, o `empresa_id` do corpo tem de ser
igual ao do header, senão `400` (`services/clientes/routers/clientes.py:59-63`
e `:92-96`).

Todas as consultas do repositório filtram por `empresa_id`
(`services/clientes/repositories/cliente_repository.py`). `Endereco` **não** tem
coluna `empresa_id`: o isolamento dos endereços vem do cliente dono, verificado
antes de cada operação nos métodos de endereço de
`services/clientes/services/cliente_service.py`.

**Não há verificação de papel (ADMIN, GERENTE, VENDEDOR) em nenhuma rota deste
serviço.** No gateway, `/clientes` e `/clientes/{path}` exigem apenas
`get_current_active_user`, isto é, qualquer usuário autenticado
(`api-gateway/routers/proxy.py:229-268`). Onde este documento falava em
"usuários ADMIN ou GERENTE", a restrição não existe.

---

## 1. Entidade: Cliente

Tabela `clientes.clientes` (`services/clientes/models/cliente.py:13-54`).

### 📊 Estrutura de Dados

| Campo | Tipo | Nulo no banco | Descrição |
|-------|------|---------------|-----------|
| `id` | UUID (PK) | Não | Identificador único, `default=uuid4` |
| `empresa_id` | Integer | Não | ID da empresa (multi-tenancy), indexado |
| `cpf` | String(11) | **Sim** | CPF sem formatação, indexado. Nulo por causa dos clientes OAuth |
| `nome` | String(255) | Não | Nome completo |
| `telefone` | String(20) | **Sim** | Formato E.164. Nulo por causa dos clientes OAuth |
| `email` | String(255) | Sim | Email do cliente |
| `data_nasc` | Date | Sim | Data de nascimento |
| `limite_credito` | Numeric(10,2) | Não | Limite de crédito fiado, `default=0.00` |
| `credito_disponivel` | Numeric(10,2) | Não | Crédito disponível, `default=0.00` |
| `dia_vencimento` | Integer | Sim | Dia do vencimento |
| `bloqueado` | Boolean | Não | Cliente bloqueado? `default=False` |
| `ativo` | Boolean | Não | Cliente ativo? `default=True` |
| `criado_em` | DateTime | Não | `default=datetime.utcnow` |

Constraints e índices (`models/cliente.py:17-22`):

- `uq_clientes_empresa_cpf` — único em **(`empresa_id`, `cpf`)**. O CPF é único
  **por empresa**, não no sistema: o mesmo CPF pode existir em duas empresas.
- `ix_clientes_empresa_id_ativo` e `ix_clientes_empresa_id_nome`.
- Relação `enderecos` com `cascade="all, delete-orphan"` (`:47-51`).

### ✅ Regras de Validação

**RN-CLI-001: Validação de CPF — IMPLEMENTADA (com ressalva de comprimento)**

Evidência: `services/clientes/schemas/cliente.py:15` e `:20-27`;
`services/clientes/utils/validators.py:11-21` e `:24-34`.

- Campo: `cpf: str = Field(..., min_length=11, max_length=14)`. **Os limites de
  comprimento são checados antes do validador**, sobre a string crua: uma string
  com mais de 14 caracteres é rejeitada com `422` ainda que, sem formatação,
  tenha 11 dígitos.
- Passando o comprimento, `normalizar_cpf` remove tudo que não é dígito
  (`re.sub(r'\D', '', cpf)`) e `validar_cpf` delega a
  `validate_docbr.CPF().validate()` — dependência `validate-docbr==2.0.0`
  (`services/clientes/requirements.txt:14`). CPF reprovado → `422`,
  "CPF inválido".
- **Exemplos aceitos**: `12345678909`, `123.456.789-09` (14 caracteres),
  `30180957660` e `43747818030` (os dois usados em
  `services/clientes/seed_clientes.py`).
- **Exemplo rejeitado**: `12345678901` — os dígitos verificadores corretos para
  `123456789` são `09`, não `01`.
- **A CONFIRMAR:** se o `validate-docbr` 2.0.0 rejeita CPFs de dígitos repetidos
  (`11111111111`, `00000000000`). O algoritmo puro dos dígitos verificadores
  aprova os dois; a rejeição, se existe, vem da biblioteca, que não está
  instalada neste ambiente para ser testada.
- No fluxo OAuth o CPF é opcional; se enviado, passa pelo mesmo validador
  (`schemas/cliente.py:49` e `:53-62`).

**RN-CLI-002: Validação de Telefone — IMPLEMENTADA**

Evidência: `schemas/cliente.py:16` e `:29-37`;
`services/clientes/utils/validators.py:37-48` e `:51-82`.

- `normalizar_telefone` **aceita telefone brasileiro sem código de país e
  formatado**: remove tudo que não é dígito, descarta um `0` inicial e, se
  sobrarem 10 ou 11 dígitos, prefixa `+55`.
- **Exemplos aceitos**: `(11) 99999-9999` → `+5511999999999`;
  `11999999999` → `+5511999999999`; `1130001000` → `+551130001000` (formato
  usado no seed); `+5511999999999` → devolvido como está.
- **Exemplo rejeitado**: string que, sem `+`, não tenha 10 nem 11 dígitos — por
  exemplo `999999999` (9 dígitos). Erro: "Não foi possível normalizar o
  telefone: ...".
- Com `+`, a validação é o regex E.164 `^\+[1-9]\d{1,14}$`
  (`utils/validators.py:47-48`).
- Em `POST /clientes` o telefone é obrigatório (`ClienteBase`); em
  `POST /clientes/oauth` é opcional (`schemas/cliente.py:50`).

**RN-CLI-003: Validação de Nome — IMPLEMENTADA**
- `nome: str = Field(..., min_length=3, max_length=255)` na criação
  (`schemas/cliente.py:14`) e no update (`:78`).
- Obrigatório na criação, opcional no `PATCH`.

**RN-CLI-004: Email — NÃO VALIDADO**
- O campo é `email: str | None = None`, `str` puro, **sem `EmailStr` e sem
  validador** (`schemas/cliente.py:17`). Qualquer string passa.
- O limite de 255 caracteres existe só no banco (`String(255)`,
  `models/cliente.py:37`), não no schema: uma string maior estoura no `INSERT`,
  não em `422`.
- Exceção: em `POST /clientes/oauth` o email é **obrigatório**
  (`schemas/cliente.py:48`) e serve de chave de idempotência (RN-CLI-013).

**RN-CLI-005: Data de Nascimento — PARCIAL**
- Opcional, e o Pydantic garante data válida (`date | None`,
  `schemas/cliente.py:18`).
- **Não existe checagem de que a data esteja no passado.** Data futura é aceita.

### 💳 Regras de Crédito

**RN-CLI-006: Limite de Crédito — PARCIAL**

Evidência: `schemas/cliente.py:116`; `services/cliente_service.py:218-260`;
`repositories/cliente_repository.py:166-185`.

- Padrão do banco: `0.00` (`models/cliente.py:39`).
- `limite_credito: Decimal = Field(..., ge=0)` — negativo é `422`.
- `PUT /clientes/{cliente_id}/credito` grava limite e dia de vencimento.
- **A fórmula `credito_disponivel = limite_credito - débitos_pendentes` NÃO
  roda.** O serviço fixa `saldo_devedor = Decimal("0.00")` sob um
  `TODO: Buscar saldo devedor do serviço financeiro`
  (`services/cliente_service.py:235-236`), a variável não é usada, e o
  repositório grava `credito_disponivel = limite_credito` direto
  (`repositories/cliente_repository.py:180-181`). Consequência prática: definir o
  limite **descarta qualquer débito já descontado do disponível**.
- Isso é consistente com o estado do serviço financeiro, que não tem rotas de
  negócio montadas — ver o aviso em [README.md](./README.md).

**RN-CLI-007: Crédito Disponível — PARCIAL**

Evidência: `repositories/cliente_repository.py:187-206`;
`services/cliente_service.py:269-323`.

- Existe `POST /clientes/{cliente_id}/credito/ajustar`, que soma um `delta`
  (positivo = crédito, negativo = débito) e **rejeita resultado negativo** —
  `ValueError("Crédito disponível não pode ser negativo")`
  (`repositories/cliente_repository.py:201`) convertido em `400`.
- Alterar o limite reescreve o disponível (RN-CLI-006).
- **NÃO existe atualização automática.** Nenhum serviço chama
  `/credito/ajustar`: não há chamada em `services/vendas/`, em
  `services/financeiro/` nem no `api-gateway/`. Uma venda fiada **não** diminui o
  crédito disponível e um pagamento recebido **não** o aumenta. Hoje o campo só
  muda por chamada explícita à rota.

**RN-CLI-008: Dia de Vencimento — PARCIAL**
- Opcional: `dia_vencimento: int | None = Field(None, ge=1, le=28)` no schema de
  crédito (`schemas/cliente.py:117`), então fora de 1–28 é `422`.
- **O campo não é lido por nenhum código fora do serviço de clientes**: não
  aparece em `services/vendas/`, `services/financeiro/` nem no gateway. Nada
  calcula vencimento de venda fiada a partir dele.
- Cuidado: `PUT /clientes/{cliente_id}/credito` grava
  `cliente.dia_vencimento = dia_vencimento` sem `exclude_unset`
  (`repositories/cliente_repository.py:179`). Omitir o campo na requisição
  **apaga** o valor anterior (grava `NULL`).

**RN-CLI-009: Bloqueio de Cliente — PARCIAL (só manual)**
- Existem bloqueio e desbloqueio manuais: `POST /clientes/{cliente_id}/bloquear`
  e `POST /clientes/{cliente_id}/desbloquear`
  (`routers/clientes.py:281` e `:299`; `repositories/cliente_repository.py:208`
  e `:219`). Ambos só alteram o booleano `bloqueado`.
- Existe o filtro `?bloqueado=true|false` na listagem
  (`repositories/cliente_repository.py:116-117`).
- **NÃO existe bloqueio automático.** Não há código que bloqueie por crédito
  negativo nem por parcela vencida, e não há nenhuma referência a dias de atraso
  no serviço. As duas únicas escritas em `bloqueado` são as rotas manuais acima.
- **NÃO existe restrição de papel para desbloquear**: qualquer usuário
  autenticado alcança a rota (seção 0).
- **A CONFIRMAR:** onde a flag `bloqueado` é consumida na hora de vender. A
  validação de FIADO em `services/vendas/services/venda_service.py:853-855` e em
  `services/vendas/routers/vendas.py:296-297` exige apenas que a venda tenha
  `cliente_id`; não consulta `bloqueado` nem `credito_disponivel`.

### 🗑️ Regras de Exclusão

**RN-CLI-010: Soft Delete — IMPLEMENTADA**
- `DELETE /clientes/{cliente_id}` marca `ativo = False` e não apaga a linha
  (`repositories/cliente_repository.py:144-153`).
- A listagem filtra `ativo == True` por padrão; `?ativo=false` traz os inativos
  (`repositories/cliente_repository.py:95-100`).
- Reativação existe de duas formas:
  - `POST /clientes/{cliente_id}/ativar`
    (`repositories/cliente_repository.py:155-164`);
  - implicitamente em `POST /clientes` — ver RN-CLI-012.

**RN-CLI-011: Restrições de Exclusão — NÃO IMPLEMENTADA**
- O código pretende barrar a desativação de cliente com pendências, mas as duas
  verificações são comentários `TODO`
  (`services/cliente_service.py:197-198`): "Verificar pedidos em aberto
  (integração com serviço de vendas)" e "Verificar contas pendentes (integração
  com serviço financeiro)".
- **Hoje qualquer cliente é desativado sem checagem** de venda em aberto, débito
  pendente ou reserva de estoque.

**RN-CLI-012: Recriar reativa o cliente inativo — IMPLEMENTADA (não óbvia)**
- `POST /clientes` com CPF que já existe na empresa
  (`services/cliente_service.py:44-65`):
  - cliente **ativo** → `409 Conflict`, "CPF já cadastrado para esta empresa";
  - cliente **inativo** → é **reativado**, e `nome`, `telefone`, `email` e
    `data_nasc` são sobrescritos com os dados enviados; a resposta é o registro
    antigo, com o `id` antigo.
- Ou seja: o mesmo `POST` é criação, conflito ou reativação-com-update,
  dependendo do estado anterior.

**RN-CLI-013: Cliente OAuth — IMPLEMENTADA**
- `POST /clientes/oauth` responde `200`, não `201`, porque é idempotente por
  email (`routers/clientes.py:68-72`).
- `email` é obrigatório; `cpf` e `telefone` são opcionais — daí as colunas nulas
  citadas em RN-CLI-001 e RN-CLI-002 (`schemas/cliente.py:44-51`).
- Email já cadastrado e ativo na empresa → devolve o cliente existente, sem erro.
  Inativo → reativa, atualiza `nome` e `data_nasc`, e preenche `cpf`/`telefone`
  só se vierem na requisição (`services/cliente_service.py:78-120`).
- Quem chama é o gateway, no fluxo OAuth de cliente comprador
  (`api-gateway/routers/auth_cliente.py:78-96`).

---

## 2. Entidade: Endereço

Tabela `clientes.enderecos` (`services/clientes/models/cliente.py:57-80`).
Rotas com prefixo `/clientes/{cliente_id}/enderecos`
(`services/clientes/routers/enderecos.py:20`).

### 📊 Estrutura de Dados

| Campo | Tipo | Nulo no banco | Descrição |
|-------|------|---------------|-----------|
| `id` | UUID (PK) | Não | `default=uuid4` |
| `cliente_id` | UUID | Não | FK `clientes.clientes.id`, `ondelete="CASCADE"` |
| `cep` | String(8) | Não | CEP sem formatação |
| `logradouro` | String(255) | Não | Rua, avenida, etc |
| `numero` | String(20) | Não | Número do imóvel |
| `complemento` | String(255) | Sim | Apto, bloco, etc |
| `bairro` | String(100) | Não | Bairro |
| `cidade` | String(100) | Não | Cidade |
| `uf` | String(2) | Não | Estado (sigla) |
| `principal` | Boolean | Não | Endereço principal? `default=False` |

Não há coluna `empresa_id`: o tenant vem do cliente dono.

### ✅ Regras de Validação

**RN-END-001: Validação de CEP — SÓ COMPRIMENTO, e SEM normalização**
- `cep: str = Field(..., min_length=8, max_length=8)`
  (`schemas/cliente.py:127`).
- **Não existe normalização de CEP.** Nenhum validador remove traço, e
  `services/clientes/utils/validators.py` só trata CPF e telefone.
- **Aceito**: `01234567`. **Rejeitado com `422`**: `01234-567`, que tem 9
  caracteres. Quem consome a rota tem de enviar o CEP já limpo.
- Só o comprimento é verificado: `abcdefgh` passa.

**RN-END-002: Validação de UF — SÓ COMPRIMENTO**
- `uf: str = Field(..., min_length=2, max_length=2)` (`schemas/cliente.py:133`).
- **Não existe lista de siglas válidas de estado.** `SP` e `RJ` passam, mas `XX`
  e `zz` também. Nada confere contra as 27 unidades federativas e nada normaliza
  para maiúsculas.

**RN-END-003: Campos Obrigatórios — IMPLEMENTADA**
Exatamente como no schema (`schemas/cliente.py:128-133`):
- Logradouro: mínimo 3, máximo 255.
- Número: mínimo 1, máximo 20.
- Bairro: mínimo 3, máximo 100.
- Cidade: mínimo 3, máximo 100.
- Complemento: opcional, sem limite no schema (255 no banco).

**RN-END-004: Endereço Principal — PARCIAL**
- Cliente pode ter múltiplos endereços (relação um-para-muitos).
- **Implementado**: marcar um endereço como principal desmarca os demais do mesmo
  cliente — na criação (`repositories/cliente_repository.py:239-245`) e no update
  (`:281-288`).
- **NÃO implementado**: marcar automaticamente o primeiro endereço cadastrado. O
  padrão é `principal: bool = False` (`schemas/cliente.py:134`), então um cliente
  pode perfeitamente ficar **sem nenhum endereço principal**.
- Não há constraint no banco limitando a um principal por cliente: a unicidade
  depende só do código acima.

**RN-END-005: Exclusão — IMPLEMENTADA**
- Desativar o cliente é soft delete (RN-CLI-010), então os endereços permanecem
  intactos.
- Os endereços só desaparecem em bloco se a linha do cliente for apagada de fato:
  a FK é `ondelete="CASCADE"` (`models/cliente.py:64`) e a relação é
  `cascade="all, delete-orphan"` (`:50`). **Nenhuma rota do serviço apaga cliente
  fisicamente.** O único hard delete exposto é o de um endereço individual
  (`repositories/cliente_repository.py:296`).

---

## 3. Rotas do serviço

Routers montados em `services/clientes/main.py:57-58`.

| Método | Rota | Observação |
|--------|------|------------|
| POST | `/clientes` | `201`; pode dar `409` ou reativar — RN-CLI-012 |
| POST | `/clientes/oauth` | `200`, idempotente por email — RN-CLI-013 |
| GET | `/clientes` | `skip`/`limit` (limit ≤ 100); filtros `nome`, `cpf`, `bloqueado`, `ativo` |
| GET | `/clientes/{cliente_id}` | |
| GET | `/clientes/{cliente_id}/completo` | Cliente com a lista de endereços |
| GET | `/clientes/cpf/{cpf}` | |
| PATCH | `/clientes/{cliente_id}` | Só `nome`, `telefone`, `email`, `data_nasc` |
| DELETE | `/clientes/{cliente_id}` | Soft delete, sem checagem de pendência |
| POST | `/clientes/{cliente_id}/ativar` | |
| PUT | `/clientes/{cliente_id}/credito` | Limite + dia de vencimento |
| POST | `/clientes/{cliente_id}/credito/ajustar` | Delta; nenhum serviço a chama |
| POST | `/clientes/{cliente_id}/bloquear` | |
| POST | `/clientes/{cliente_id}/desbloquear` | |
| POST | `/clientes/{cliente_id}/enderecos` | |
| GET | `/clientes/{cliente_id}/enderecos` | |
| PATCH | `/clientes/{cliente_id}/enderecos/{endereco_id}` | |
| DELETE | `/clientes/{cliente_id}/enderecos/{endereco_id}` | Hard delete do endereço |

O `PATCH /clientes/{cliente_id}` **não** altera `cpf`, `limite_credito`,
`credito_disponivel`, `dia_vencimento`, `bloqueado` nem `ativo`
(`schemas/cliente.py:76-92`) — cada um tem rota própria, ou nenhuma.

Detalhe de desempenho a conhecer: a contagem total da listagem materializa todas
as linhas antes de paginar — `total = len(count_result.all())`
(`repositories/cliente_repository.py:119-121`), em vez de um `SELECT COUNT(*)`.

---

## 4. Casos de Uso

### 4.1. Cliente com Crédito Insuficiente — NÃO IMPLEMENTADO

**Cenário pretendido**: cliente tenta compra fiada de R$ 500 tendo R$ 300 de
crédito disponível.

**Comportamento pretendido**: `400 Bad Request` de crédito insuficiente, venda
não criada, estoque não reservado.

**Comportamento real hoje**: a venda fiada é aceita. A única validação de FIADO
em vendas é exigir cliente identificado
(`services/vendas/services/venda_service.py:853-855` e
`services/vendas/routers/vendas.py:296-297`); não há consulta a
`credito_disponivel` nem a `bloqueado`. Uma busca por `credito_disponivel` em
`services/vendas/` e em `api-gateway/` não retorna nenhuma ocorrência.

O que existe é `POST /clientes/{id}/credito/ajustar`, que recusa deixar o crédito
negativo (RN-CLI-007) — mas ninguém a chama no fluxo de venda.

**Sobre pagamento misto**: `services/vendas` já aceita uma lista de pagamentos
por venda, e um deles pode ser FIADO
(`services/vendas/services/venda_service.py:853-854`), mas sem qualquer
verificação de limite. Trate "parte fiado, parte à vista" como fluxo sem controle
de crédito.

---

## 5. Lacunas declaradas

- **A CONFIRMAR:** se `validate-docbr` 2.0.0 rejeita CPFs de dígitos repetidos
  (RN-CLI-001).
- **A CONFIRMAR:** quem consome a flag `bloqueado` na hora de vender
  (RN-CLI-009).
- **A CONFIRMAR:** de onde vem `permite_fiado_online`, lido em
  `services/vendas/services/loja_service.py:299-306`. A chave não existe no
  modelo `Cliente` deste serviço, então um `cliente_info.get(...)` alimentado
  pelos dados de cliente sempre cairia no padrão `False`.
- **A CONFIRMAR:** quais testes cobrem estas regras.
  `services/clientes/tests/` contém apenas `conftest.py`, `test_base.py` e
  `__init__.py` — nenhum teste específico de crédito, bloqueio ou endereço.

---

## 📚 Referências

- [API de Clientes](../10-api-reference/clientes-api.md)
- [Regras de Negócio - Índice](./README.md)

---

**Última revisão contra o código**: 26 de Setembro de 2026  
**Escopo da revisão**: `services/clientes/` inteiro, mais os pontos de
`services/vendas/` e `api-gateway/` citados acima.
