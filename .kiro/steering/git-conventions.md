---
inclusion: always
---

# Language Conventions

## Chat
Always respond to the user in **Brazilian Portuguese (PT-BR)**.

## Code
- Identifiers, variable names, function names, class names: **keep as-is in the existing codebase** (project uses PT-BR identifiers — do not change them)
- Code comments: **PT-BR**
- Commit messages: **English** (see below)
- Documentation files (`.md`): follow the existing file's language

---

# Engineering Standards

All code written must follow software engineering best practices. These are non-negotiable.

## Clean Code

- **Nomes descritivos**: variáveis, funções e classes devem revelar intenção. Sem abreviações obscuras (`cli`, `tmp`, `x`)
- **Funções pequenas**: uma função faz uma coisa só. Se precisar de comentário para explicar o que ela faz, ela deve ser dividida
- **Sem números mágicos**: usar constantes nomeadas
- **Sem código morto**: não deixar código comentado ou funções não utilizadas
- **DRY** (Don't Repeat Yourself): lógica duplicada deve ser extraída
- **Sem side effects ocultos**: funções não devem alterar estado externo sem que o nome deixe claro

## SOLID Principles

- **S** — Single Responsibility: cada classe/módulo tem uma única razão para mudar
- **O** — Open/Closed: aberto para extensão, fechado para modificação
- **L** — Liskov Substitution: subclasses devem ser substituíveis pelas suas bases
- **I** — Interface Segregation: interfaces específicas são melhores que uma genérica
- **D** — Dependency Inversion: depender de abstrações, não de implementações concretas

## KISS & YAGNI

- **KISS** (Keep It Simple, Stupid): simplicidade é melhor que complexidade
  - Evitar abstrações prematuras
  - Preferir soluções diretas a "elegantes"
  - Se precisa de um diagrama para explicar, está complexo demais
- **YAGNI** (You Aren't Gonna Need It): não implementar funcionalidades especulativas
  - Só adicionar features quando houver necessidade real
  - Não criar "ganchos" ou "preparar" para futuras features
  - Refatorar quando precisar, não antes

## Code Calisthenics (9 regras)

1. **Um nível de indentação por método**: se tem `if` dentro de `for` dentro de `if`, extrair métodos
2. **Não usar `else`**: preferir early returns, guard clauses, ou polimorfismo
3. **Encapsular primitivos**: valores de negócio devem ser objetos (ex: `CPF`, `Email`, `Dinheiro`)
4. **Coleções de primeira classe**: classes que wrapeiam listas devem ter métodos de domínio
5. **Um ponto por linha**: evitar `usuario.empresa.endereco.cidade` — usar Lei de Demeter
6. **Não abreviar**: `calcular_total_com_desconto()` > `calc_tot_desc()`
7. **Manter entidades pequenas**: classes com +200 linhas ou +15 métodos devem ser divididas
8. **Máximo 2 variáveis de instância por classe**: forçar coesão alta
9. **Sem getters/setters públicos**: expor comportamento, não dados

## Fail-Safe Design

- **Defensive Programming**: validar inputs em todas as camadas
- **Graceful Degradation**: sistema continua funcionando parcialmente em caso de falha
  - Se serviço externo cair, retornar dados em cache ou modo degradado
  - Se email falhar, logar e continuar processo
- **Circuit Breaker**: após N falhas, parar tentativas por X tempo
- **Idempotência**: operações repetidas devem ter mesmo efeito (importante para retry)
- **Transações atômicas**: operações críticas devem ser "tudo ou nada"
- **Rollback automático**: se falhar no meio, reverter mudanças

## Testability

- **Injeção de dependências**: nunca instanciar dependências dentro de métodos
- **Evitar static/global state**: torna testes imprevisíveis
- **Sem chamadas diretas a I/O**: banco, API, filesystem devem ser mockáveis
- **Métodos puros quando possível**: mesmos inputs → mesmos outputs
- **Testes devem ser FIRST**:
  - **F**ast: rodar em milissegundos
  - **I**ndependent: ordem não importa
  - **R**epeatable: mesmo resultado sempre
  - **S**elf-validating: pass/fail, sem verificação manual
  - **T**imely: escrever junto com o código

## Performance

- **Otimização prematura é raiz do mal**: medir antes de otimizar
- **N+1 queries**: sempre usar `joinedload()` ou `selectinload()` no SQLAlchemy
- **Paginação obrigatória**: endpoints que retornam listas devem paginar
- **Índices estratégicos**: adicionar índices em colunas usadas em WHERE e JOIN
- **Cache inteligente**: Redis para dados frequentemente lidos e raramente alterados
- **Lazy loading**: carregar dados pesados só quando necessário

## Observability

- **Logs estruturados**: usar `structlog` com contexto rico
  - Incluir: `request_id`, `usuario_id`, `empresa_id`, `action`, `duration_ms`
- **Métricas**: instrumentar operações críticas
  - Contadores: requests, erros, eventos de negócio
  - Histogramas: latência, tamanho de resposta
- **Tracing distribuído**: propagate `trace_id` entre microsserviços
- **Health checks**: `/health` deve verificar dependências (DB, Redis, APIs externas)

## Graphify Workflow (Economia de Tokens)

**Graphify é OBRIGATÓRIO antes de qualquer modificação no código.**

### Antes de Modificar Código

1. **Sempre consultar graphify primeiro**: `graphify query "<o que preciso entender>"`
2. **Usar comandos específicos**:
   - `graphify query "pergunta sobre arquitetura"` - entender estrutura, dependências, fluxos
   - `graphify path "ComponenteA" "ComponenteB"` - ver como componentes se conectam
   - `graphify explain "padrão ou conceito"` - entender um conceito/padrão do projeto
3. **Só ler arquivos depois** - use graphify para descobrir QUAIS arquivos ler
4. **Nunca fazer suposições** - se não tem certeza da arquitetura, pergunta ao graphify

### Exemplos de Queries Úteis

```bash
# Antes de adicionar uma feature
graphify query "como funciona o fluxo de autenticação de clientes?"

# Antes de refatorar
graphify query "quais arquivos dependem do ClienteRepository?"

# Entendendo integrações
graphify path "api-gateway" "servico-clientes"

# Compreendendo padrões
graphify explain "Repository Pattern neste projeto"
```

### Após Modificar Código

1. **Atualizar o grafo**: sempre que modificar estrutura do código
   - Rodar `graphify` no terminal para reprocessar o projeto
   - Especialmente após: criar novos arquivos, adicionar imports, mudar interfaces públicas
2. **Validar mudanças**: opcional, mas recomendado
   - `graphify query` sobre a área modificada para confirmar consistência

### Benefícios

- 📉 **-70% consumo de tokens**: subgraph focado vs ler múltiplos arquivos completos
- 🎯 **Contexto preciso**: apenas o necessário para a tarefa
- 🚀 **Respostas mais rápidas**: menos contexto = menos processamento
- 🧠 **Decisões informadas**: entender impacto antes de modificar
- 🔍 **Zero surpresas**: descobrir dependências ocultas antes de quebrar algo

### Quando NÃO usar Graphify

- Alterações triviais em um único arquivo já aberto
- Correções de typo ou formatação
- Mudanças puramente estéticas (CSS, comentários)

## Design Patterns (em uso no projeto)

- **Repository Pattern**: toda query ao banco passa pelo repository — nunca direto no service ou router
- **Service Layer**: regras de negócio ficam no service — nunca no router
- **Dependency Injection**: usar `Depends()` do FastAPI para injetar sessão, usuário, etc.
- **DTO / Schema**: usar Pydantic schemas para entrada e saída — nunca expor o model ORM diretamente

## Error Handling

- **Nunca usar `except Exception` genérico** nos services — capturar exceções específicas
- **Exceções de negócio**: usar as exceções customizadas de `shared/exceptions.py` (`ValidationError`, `NotFoundError`, `ConflictError`, etc.)
- **Handlers globais**: os routers não devem ter try/except — os exception handlers do `main.py` cuidam disso
- **Nunca expor stack trace** ao cliente — retornar `request_id` em erros 500
- **Logs estruturados**: usar `structlog` com contexto (`usuario_id`, `path`, `method`)

## Security

- **Nunca confiar só no frontend**: validar todos os dados no backend
- **Nunca logar dados sensíveis**: senhas, tokens, CPF completo
- **Queries parametrizadas**: nunca concatenar strings SQL — usar SQLAlchemy ORM
- **Princípio do menor privilégio**: cada serviço acessa apenas seu próprio schema

## Code Structure (FastAPI + SQLAlchemy)

```
router      → valida entrada (Pydantic), chama service, retorna resposta
service     → regras de negócio, orquestra repositories, lança exceções de negócio
repository  → queries ao banco, sem lógica de negócio
validator   → validações complexas reutilizáveis (CPF, crédito, etc.)
schema      → Pydantic models de entrada/saída
model       → SQLAlchemy ORM models
```

## Testing

- Todo código novo deve ter testes unitários para o service layer
- Validators devem ter 90%+ de cobertura
- Usar `pytest` com fixtures para sessão de banco
- Nomear testes descritivamente: `test_criar_cliente_com_cpf_duplicado_retorna_409`

## Documentation

- Docstrings em PT-BR em todos os métodos públicos de service e repository
- Endpoints FastAPI devem ter `summary` e `description` no decorator
- Parâmetros e retornos documentados quando não óbvios

---

# Git Commit Conventions

All commits must follow the **Conventional Commits** specification in **English**.

## Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

## Types

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, missing semicolons, etc (no logic change) |
| `refactor` | Code change that is neither a fix nor a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates, tooling |
| `ci` | CI/CD configuration changes |
| `revert` | Reverts a previous commit |

## Rules

- Subject line: max 72 characters, imperative mood, no period at the end
- Use English for type, scope, description, and body
- Scope is optional but recommended (e.g. `feat(auth)`, `fix(estoque)`, `docs(checklist)`)
- Body: explain *what* and *why*, not *how*

## Examples

```
feat(auth): add Google OAuth2 login support

fix(estoque): prevent negative stock on concurrent sales

docs(checklist): add backend quality and security section

refactor(clientes): extract CPF validation to shared validator

chore(docker): consolidate 8 postgres containers into one

perf(produtos): add composite indexes on empresa_id and ativo
```
