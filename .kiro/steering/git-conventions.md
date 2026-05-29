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
