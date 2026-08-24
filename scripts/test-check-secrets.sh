#!/bin/bash
# Runnable check for scripts/check-secrets.sh. Builds a throwaway repo, stages
# things, asserts the exit code. Run it after touching a pattern.
#   bash scripts/test-check-secrets.sh
set -u
CHECK="$(cd "$(dirname "$0")" && pwd)/check-secrets.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP" || exit 1
git init -q . && git config user.email t@t && git config user.name t
fails=0

# want=0 espera passar, want=1 espera bloquear
try() {
    want="$1"; name="$2"; file="$3"; content="$4"
    printf '%s\n' "$content" > "$file"
    git add -A -- "$file" >/dev/null 2>&1
    out="$(bash "$CHECK" 2>&1)"; got=$?
    git reset -q; rm -f "$file"
    if [ "$got" != "$want" ]; then
        echo "FALHOU: $name (esperado $want, saiu $got)"; echo "$out" | sed 's/^/    /'
        fails=$((fails+1))
    else
        echo "ok: $name"
    fi
}

try 1 "aws key"          app.py   'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
try 1 "stripe live"      app.py   'k = "sk_live_4eC39HqLyjWDarjtT1zdp7dcXXXX"'
try 1 "github pat"       app.py   'T="ghp_abcdefghij0123456789ABCDEFGHIJ012345"'
try 1 "dsn real"         app.py   'DATABASE_URL=postgresql+asyncpg://erp:S3nh4-Gerada-Longa-99@db:5432/erp'
try 1 "arquivo .env"     .env     'SECRET=x'
try 0 "dsn placeholder"  docs.md  'DATABASE_URL=postgresql://user:password@localhost:5432/erp_runas'
try 0 "dsn dev erp:erp"  dc.yml   'DATABASE_CONNECTION_URI: postgresql://erp:erp@db:5432/erp'
try 0 "sha de commit"    docs.md  'Commit d3b79dd8f4a1c2e3b5d6a7f8091a2b3c4d5e6f70 fez o deploy'
try 0 ".env.example"     .env.example 'SECRET=coloque-aqui'
try 0 "nome com espaco"  'O TESTE.md' 'texto comum sem segredo'

# O caso que motivou tudo: um segredo dentro de um arquivo com espaco no nome.
# O loop antigo fazia `for file in $FILES`, entao "O SISTEMA.md" virava dois
# tokens, nenhum dos dois existia, e o arquivo era pulado em silencio.
try 1 "segredo em nome com espaco" 'O SISTEMA.md' 'chave: AKIAIOSFODNN7EXAMPLE'

[ "$fails" = 0 ] && echo "todos passaram" || echo "$fails falha(s)"
exit "$fails"
