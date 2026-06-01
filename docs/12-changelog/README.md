# Changelog - Runas

> **Histórico de versões** e mudanças do projeto

---

## 📚 Documentação de Versões

Este diretório contém o histórico completo de todas as versões do Runas, seguindo o padrão [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e [Semantic Versioning](https://semver.org/lang/pt-BR/).

### Arquivo Principal

- **[CHANGELOG.md](./CHANGELOG.md)** - Histórico completo de versões

---

## 📋 Formato do Changelog

Cada versão documenta:

- **✨ Adicionado** - Novas funcionalidades
- **🔧 Modificado** - Mudanças em funcionalidades existentes
- **🗑️ Removido** - Funcionalidades removidas
- **🐛 Corrigido** - Correções de bugs
- **🔒 Segurança** - Correções de vulnerabilidades
- **📚 Documentação** - Mudanças na documentação
- **⚡ Performance** - Melhorias de performance
- **♻️ Refatoração** - Mudanças de código sem alterar funcionalidade

---

## 🔢 Versionamento Semântico

O Runas segue o [Semantic Versioning](https://semver.org/lang/pt-BR/):

```
MAJOR.MINOR.PATCH

Exemplo: 1.2.3
```

- **MAJOR** (1.x.x): Mudanças incompatíveis na API
- **MINOR** (x.2.x): Novas funcionalidades compatíveis
- **PATCH** (x.x.3): Correções de bugs compatíveis

---

## 📅 Versões

### Versão Atual
- **[1.0.0](./CHANGELOG.md#100---2026-05-26)** - MVP Completo (26 de Maio de 2026)

### Versões Anteriores
- **[0.2.0](./CHANGELOG.md#020---2026-05-15)** - Fase de Planejamento
- **[0.1.0](./CHANGELOG.md#010---2026-05-01)** - Concepção do Projeto

---

## 🔄 Como Atualizar

Para atualizar o Runas para a versão mais recente:

```bash
# 1. Backup do banco de dados
docker exec db-clientes pg_dump -U erp clientes > backup.sql

# 2. Atualizar código
git pull origin main

# 3. Atualizar containers
docker-compose pull
docker-compose up -d

# 4. Executar migrations
make migrate
```

---

## 📝 Contribuir com o Changelog

Ao fazer mudanças no projeto:

1. Adicione suas mudanças na seção `[Unreleased]`
2. Use o formato apropriado (✨ Adicionado, 🐛 Corrigido, etc)
3. Seja claro e conciso na descrição
4. Inclua referências a issues/PRs quando relevante

Exemplo:

```markdown
## [Unreleased]

### ✨ Adicionado
- Validação de CNPJ no cadastro de fornecedores (#123)

### 🐛 Corrigido
- Cálculo incorreto de troco em pagamentos (#124)
```

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
