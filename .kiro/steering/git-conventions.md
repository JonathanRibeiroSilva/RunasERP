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
