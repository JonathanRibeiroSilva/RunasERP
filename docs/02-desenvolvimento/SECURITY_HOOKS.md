# 🔒 Security Hooks — Prevenção de Vazamento de Secrets

## 📋 Visão Geral

O repositório tem uma verificação de pre-commit que bloqueia segredos antes de
entrarem no histórico. Ela é feita de três partes:

| Parte | Arquivo | Versionado? |
|-------|---------|-------------|
| Shim de duas linhas que o Git chama | `.git/hooks/pre-commit` | **Não** — `.git/` nunca é versionado |
| A lógica de verdade | `scripts/check-secrets.sh` | Sim |
| O teste da lógica | `scripts/test-check-secrets.sh` | Sim |

O shim é burro de propósito:

```sh
#!/bin/sh
exec "$(git rev-parse --show-toplevel)/scripts/check-secrets.sh"
```

Tudo o que decide o que passa e o que não passa mora em `scripts/check-secrets.sh`,
que é versionado, revisável em PR e testável.

---

## ⚠️ Um clone novo NÃO tem o hook

`.git/hooks/` não vem no clone, e **nenhum script, workflow ou postinstall deste
repositório instala o shim por você**. Quem clona e começa a commitar está sem
proteção nenhuma contra vazar segredo.

Instale na mão, uma vez por clone (Git Bash no Windows):

```bash
cat > .git/hooks/pre-commit <<'SH'
#!/bin/sh
exec "$(git rev-parse --show-toplevel)/scripts/check-secrets.sh"
SH
chmod +x .git/hooks/pre-commit
```

Confira que pegou:

```bash
git commit --allow-empty -m "teste do hook"
# deve imprimir: 🔍 Verificando arquivos sensíveis...
```

O mesmo passo aparece em [`QUICK-START.md`](../../QUICK-START.md) (Passo 0.5) e em
[`.github/CONTRIBUTING.md`](../../.github/CONTRIBUTING.md) (seção 4.2).

---

## 🎯 O que o check verifica

### 1. Arquivos `.env` pelo nome

Bloqueia arquivos **adicionados ou modificados** cujo nome case com
`.env`, `.env.local`, `.env.ngrok`, `.env.cloudflare`, `.env.production` ou
`.env.coolify` (em qualquer diretório).

Passam sempre: qualquer caminho terminado em `.example` (`.env.example`,
`.env.production.example`, `.env.cloudflare.example`) e tudo sob `graphify-out/`.
Deleção de um `.env` também passa — só Added/Modified são olhados.

### 2. Padrões de segredo nas **linhas adicionadas**

> **Importante**: o check varre **apenas as linhas adicionadas** do diff staged
> (`git diff --cached -U0 --diff-filter=ACM`, filtrando `^+[^+]`), e não os
> arquivos inteiros. Um DSN que está num arquivo desde 2024 não bloqueia todo
> commit que encosta naquele arquivo; o que se barra é o que você está
> introduzindo agora.

Padrões atuais de `scripts/check-secrets.sh`:

| Tipo | Padrão |
|------|--------|
| Mercado Pago — access token | `APP_USR-[0-9]{13}-[0-9]{6}-[a-f0-9]{32}-[0-9]{10}` |
| Mercado Pago — public key | `APP_USR-[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}` |
| Stripe (secret e public) | `(sk\|pk)_(test\|live)_[0-9a-zA-Z]{24,}` |
| Google API key | `AIza[0-9A-Za-z_-]{35}` |
| AWS access key id | `AKIA[0-9A-Z]{16}` |
| Cloudflare Tunnel token | `eyJhIjoi[A-Za-z0-9_+/=-]{40,}` |
| GitHub token | `gh[pousr]_[0-9a-zA-Z]{36}` |
| DSN PostgreSQL | `postgres(ql)?(\+[a-z]+)?://usuário:senha@`, senha de 12+ chars |
| DSN MongoDB | `mongodb(\+srv)?://usuário:senha@`, senha de 12+ chars |
| DSN MySQL | `mysql://usuário:senha@`, senha de 12+ chars |
| Header Bearer | `[Bb]earer [a-zA-Z0-9._~+/-]{20,}=*` |
| Atribuição genérica | `token` / `api_key` / `secret` recebendo string de 20+ chars entre aspas |

O mínimo de 12 caracteres na senha dos DSNs é o que mantém os placeholders reais
da árvore quietos: `erp:erp@`, `user:password@` e `postgres:sua-senha@` são todos
mais curtos que isso; uma senha gerada não é.

Dois padrões antigos foram **removidos** por só saberem gritar sem motivo:
`[a-f0-9]{32,}` (casava com todo sha de commit, todo md5 e todo hash de
lockfile) e um `postgres://` que nunca casava, porque este projeto escreve
`postgresql://` e `postgresql+asyncpg://`.

### Exclusões do scan

`graphify-out/` e `scripts/test-check-secrets.sh` ficam de fora. O arquivo de
teste existe justamente para guardar segredos falsos — ele se autobloqueou na
primeira execução. O custo é real: **uma chave de verdade colada nesse arquivo
passa direto**. Ele é fixture de teste; mantenha assim.

---

## 🖥️ Como fica na prática

```bash
$ git add .env.cloudflare
$ git commit -m "add cloudflare config"
🔍 Verificando arquivos sensíveis...
.env.cloudflare
❌ ERRO: tentativa de commit de arquivo .env com secrets!
Use .env.example / .env.production.example como modelo.
```

```bash
$ echo 'TOKEN="sk_live_EXEMPLO"' >> config.py
$ git add config.py && git commit -m "add config"
🔍 Verificando arquivos sensíveis...
❌ ERRO: padrão sensível em linha adicionada
Padrão: (sk|pk)_(test|live)_[0-9a-zA-Z]{24,}
Linha:  +TOKEN="sk_live_EXEMPLO"

Use variáveis de ambiente, ou um placeholder curto em exemplos.
```

> O `sk_live_EXEMPLO` acima está encurtado de propósito, para este documento não
> disparar o próprio hook. Com esse valor curto o check **não** bloquearia: o
> padrão Stripe exige 24+ caracteres depois de `sk_live_`. A saída mostrada é a
> de uma chave de verdade.

Tudo limpo:

```
🔍 Verificando arquivos sensíveis...
✅ Verificação de segurança concluída
```

---

## 🛠️ Manutenção

### Adicionar um padrão novo

A lógica **não** está mais em `.git/hooks/pre-commit`. Edite o array
`SENSITIVE_PATTERNS` em `scripts/check-secrets.sh`:

```bash
SENSITIVE_PATTERNS=(
    # ... padrões existentes ...
    "new_token_[0-9a-zA-Z]{32}"   # descrição do token
)
```

A regra para aceitar um padrão novo: ele não pode casar com nada que já está na
árvore. Padrão que dispara em conteúdo legítimo vira hook que todo mundo aprende
a pular com `--no-verify` — pior que não ter hook.

### Validar o padrão — `scripts/test-check-secrets.sh`

Essa é a forma correta de testar. O script monta um repositório descartável,
stageia cada caso e confere o exit code (0 = passou, 1 = bloqueou):

```bash
bash scripts/test-check-secrets.sh
```

```
ok: aws key
ok: stripe live
ok: dsn placeholder
...
todos passaram
```

Ao adicionar um padrão, acrescente ao menos dois casos lá: um `try 1` com um
segredo que ele deve barrar e um `try 0` com um placeholder parecido que ele
**não** pode barrar.

### Desabilitar temporariamente (NÃO RECOMENDADO)

```bash
git commit --no-verify -m "bypass hook"
```

### Cuidado: sucesso silencioso já aconteceu

Uma versão anterior do check rodava
`git diff --cached --name-only | grep -v "^graphify-out/" --diff-filter=AM`.
O `--diff-filter` é do `git diff`, não do `grep`: o grep morria com "unknown
option", a lista de arquivos saía vazia, os loops de padrão rodavam sobre nada e
mesmo assim imprimia `✅ Verificação de segurança concluída`. Nunca bloqueou nada,
em commit nenhum. Por isso: **leia a saída do hook**, e rode
`scripts/test-check-secrets.sh` depois de qualquer mexida no script.

---

## 🚨 Incidente: token do Cloudflare commitado

No commit `f8474cf` (24/06/2026), o arquivo `.env.cloudflare` entrou no
repositório contendo um **Cloudflare Tunnel Token** real.

Corrigido em `34c137f`:

1. `.env.cloudflare` removido do repositório
2. `.gitignore` ganhou `.env.cloudflare`, `.env.production` e `!.env.production.example`
   (hoje ele usa o glob `.env.*` com `!.env.*.example`)
3. `.env.cloudflare.example` criado como template seguro
4. O check ganhou a detecção de token de túnel do Cloudflare
5. Este documento foi criado

**O blob continua no histórico**: `git show f8474cf:.env.cloudflare` ainda
devolve o arquivo. Repositório privado reduz a exposição, não remove o segredo —
a única remoção efetiva de um token vazado é **rotacionar** o token.

> **A CONFIRMAR**: se esse token do Cloudflare foi rotacionado depois do
> incidente. A mensagem de `34c137f` afirma "token remains valid"; não há
> registro posterior de rotação no repositório.

---

## 📚 Boas Práticas

### ✅ Faça

- Use arquivos `.env.example` com placeholders
- Use variáveis de ambiente para secrets
- Mantenha secrets fora do repositório
- Use placeholders óbvios: `XXXX`, `your-token-here`, `sua-senha`

### ❌ Não faça

- Commitar arquivos `.env` com secrets reais
- Usar `--no-verify` para pular o hook
- Hardcodar tokens/senhas no código
- Compartilhar secrets via Git

---

## 🎓 Referências

- [Git Hooks Documentation](https://git-scm.com/docs/githooks)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [`.github/CONTRIBUTING.md`](../../.github/CONTRIBUTING.md) — seção 4.2, instalação do hook
- [`QUICK-START.md`](../../QUICK-START.md) — Passo 0.5

---

**Última atualização**: 2026-09-25
