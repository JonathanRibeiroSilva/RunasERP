# 🔒 Security Hooks - Prevenção de Vazamento de Secrets

## 📋 Visão Geral

Este projeto possui hooks Git nativos que previnem o commit acidental de secrets, tokens e credenciais sensíveis.

## 🪝 Hooks Configurados

### 1. Pre-Commit Hook (`.git/hooks/pre-commit`)

**Localização**: `.git/hooks/pre-commit`  
**Tipo**: Git Hook Nativo (Shell Script)  
**Quando roda**: Antes de cada `git commit`

### O que ele verifica:

#### ❌ Arquivos `.env` Bloqueados

Impede commit de arquivos de ambiente com secrets reais:
- `.env`
- `.env.local`
- `.env.ngrok`
- `.env.cloudflare`
- `.env.production`

#### ✅ Arquivos `.env` Permitidos

Permite templates sem secrets:
- `.env.example`
- `.env.production.example`
- `.env.cloudflare.example`

#### 🔍 Padrões de Secrets Detectados

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| **Mercado Pago Access Token** | `APP_USR-{13 digits}-{6 digits}-{32 hex}-{10 digits}` | `APP_USR-1234567890123-123456-abc...` |
| **Mercado Pago Public Key** | `APP_USR-{UUID format}` | `APP_USR-12345678-1234-...` |
| **Stripe Secret Key** | `sk_test_` ou `sk_live_` + 24+ chars | `sk_live_abc123...` |
| **Stripe Public Key** | `pk_test_` ou `pk_live_` + 24+ chars | `pk_test_abc123...` |
| **Google API Key** | `AIza` + 35 chars | `AIzaSyAbc123...` |
| **AWS Access Key** | `AKIA` + 16 uppercase | `AKIA...16 chars...` |
| **Cloudflare Tunnel Token** | JWT base64 começando com `eyJhIjoiW0-9a-f]{32}` | `eyJhIjoiOWIzYTcwZTk...` |
| **Cloudflare API Token** | 32+ hex chars | `abc123...32 hex chars...` |
| **GitHub Token** | `ghp_`, `gho_`, `ghs_`, `ghr_` + 36 chars | `ghp_abc123...` |
| **PostgreSQL Connection** | Connection string com senha | Não commitado - use var de ambiente |
| **MongoDB Connection** | Connection string com senha | Não commitado - use var de ambiente |
| **MySQL Connection** | Connection string com senha | Não commitado - use var de ambiente |

## 🎯 Como Funciona

### Fluxo Normal

```bash
# Você tenta commitar
git add .
git commit -m "feat: add new feature"

# Hook roda automaticamente
🔍 Verificando arquivos sensíveis...

# Se encontrar algo:
❌ ERRO: Padrão sensível detectado em config.py
Padrão: APP_USR-1234567890123-...

# Se estiver tudo OK:
✅ Verificação de segurança concluída
```

### Exemplo: Tentativa de Commit de .env

```bash
$ git add .env.cloudflare
$ git commit -m "add cloudflare config"

🔍 Verificando arquivos sensíveis...
❌ ERRO: Tentativa de commit de arquivo .env com secrets!
Arquivos .env não devem ser commitados. Use .env.example como modelo.

Arquivos bloqueados:
  - .env
  - .env.local
  - .env.ngrok
  - .env.cloudflare
  - .env.production

Arquivos permitidos (sem secrets reais):
  - .env.example
  - .env.production.example

# Commit foi bloqueado! ✅
```

### Exemplo: Token Detectado no Código

```bash
$ echo 'TOKEN="sk_live_abc123def456ghi789jkl"' > config.py
$ git add config.py
$ git commit -m "add config"

🔍 Verificando arquivos sensíveis...
❌ ERRO: Padrão sensível detectado em config.py
Padrão: sk_live_[0-9a-zA-Z]{24,}

Por favor, remova dados sensíveis antes de commitar.
Dicas:
  - Use variáveis de ambiente
  - Use placeholders em exemplos (ex: sk_live_XXXX...XXXX)
  - Adicione o arquivo ao .gitignore se necessário

# Commit foi bloqueado! ✅
```

## 🚨 Incidente: Token do Cloudflare Commitado

### O que aconteceu

No commit `f8474cf`, o arquivo `.env.cloudflare` foi commitado contendo um **Cloudflare Tunnel Token** real:

```env
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiOWIzYTcwZTkwNGQ0OWUzM2MzYjkwZTE1MWE1MWJmMTQi...
```

### Ações Tomadas

1. ✅ **Removido do repositório** via `git rm --cached .env.cloudflare`
2. ✅ **Adicionado ao .gitignore** para prevenir futuras ocorrências
3. ✅ **Criado .env.cloudflare.example** como template seguro
4. ✅ **Hook atualizado** para detectar tokens do Cloudflare
5. ✅ **Padrões genéricos adicionados** (tokens, API keys, secrets)

### Token ainda é válido?

✅ **SIM** - O repositório é **privado**, então o token continua seguro.

❌ **Não foi necessário** regenerar o token, mas o hook agora previne vazamentos futuros.

## 🛠️ Manutenção do Hook

### Adicionar Novo Padrão de Detecção

Edite `.git/hooks/pre-commit` e adicione o padrão ao array `SENSITIVE_PATTERNS`:

```bash
SENSITIVE_PATTERNS=(
    # ... padrões existentes ...
    
    # Seu novo padrão
    "new_token_[0-9a-zA-Z]{32}"  # Descrição do token
)
```

### Testar o Hook

```bash
# Criar arquivo de teste com token fake
echo 'TOKEN="sk_live_abc123def456ghi789jkl"' > test.txt

# Tentar commitar
git add test.txt
git commit -m "test"

# Deve bloquear!
```

### Desabilitar Temporariamente (NÃO RECOMENDADO)

```bash
# CUIDADO: Desabilita verificação de segurança!
git commit --no-verify -m "bypass hook"
```

## 📚 Boas Práticas

### ✅ Faça

- Use `.env.example` files com placeholders
- Use variáveis de ambiente para secrets
- Mantenha secrets fora do repositório
- Use placeholders óbvios em exemplos: `XXXX`, `your-token-here`, etc.

### ❌ Não Faça

- Commitar arquivos `.env` com secrets reais
- Usar `--no-verify` para bypass do hook
- Hardcodar tokens/passwords no código
- Compartilhar secrets via Git

## 🔄 Sincronização entre Desenvolvedores

**IMPORTANTE**: O hook `.git/hooks/pre-commit` **não é versionado** no Git (por design).

### Como garantir que todos tenham o hook:

1. **Documentar** (este arquivo!)
2. **Script de setup** que copia o hook
3. **Onboarding** de novos devs

### Setup para Novo Desenvolvedor

```bash
# 1. Clone o repositório
git clone https://github.com/seu-user/seu-repo.git

# 2. Copiar hook (se não estiver presente)
cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# 3. Testar
git commit --allow-empty -m "test hook"
```

## 🎓 Referências

- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

---

**Última atualização**: 2026-06-24  
**Versão do Hook**: 2.0 (com detecção de Cloudflare Tunnel Tokens)  
**Mantido por**: Time de Segurança do Projeto
