#!/bin/bash
# Blocks staged secrets. Called by .git/hooks/pre-commit, which is a two-line
# shim — the logic lives here so it is version-controlled, reviewable and
# testable (scripts/test-check-secrets.sh). Hooks in .git/hooks are not.
#
# This scans ADDED LINES, not whole files. Two reasons: a DSN that has been in
# a file since 2024 should not block every commit that touches that file, and
# what you are gating is what you are introducing. It also removes the entire
# file loop, the binary check and the -f test, which is where the old version
# kept its bugs.
#
# History worth keeping: this script's predecessor ran
#   git diff --cached --name-only | grep -v "^graphify-out/" --diff-filter=AM
# The --diff-filter belongs to git diff, not to grep. grep died with "unknown
# option", the file list came out empty, every pattern loop ran over nothing and
# it printed its success line anyway. It never blocked anything, on any commit.

set -u

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Verificando arquivos sensíveis..."

# .env files by NAME. Deletions are fine, so only Added/Modified.
if git diff --cached --name-only --diff-filter=AM \
   | grep -Ev '^graphify-out/|\.example$' \
   | grep -E '(^|/)\.env(\.local|\.ngrok|\.cloudflare|\.production|\.coolify)?$'; then
    printf "${RED}❌ ERRO: tentativa de commit de arquivo .env com secrets!${NC}\n"
    echo "Use .env.example / .env.production.example como modelo."
    exit 1
fi

# Every pattern below was checked against the current tree and matches nothing
# there. That is the bar: a pattern that fires on committed content turns the
# hook into something you learn to bypass with --no-verify, which is worse than
# no hook. Verify with scripts/test-check-secrets.sh after adding one.
SENSITIVE_PATTERNS=(
    # Payment gateways
    "APP_USR-[0-9]{13}-[0-9]{6}-[a-f0-9]{32}-[0-9]{10}"        # Mercado Pago access token
    "APP_USR-[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}"        # Mercado Pago public key
    "(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}"                     # Stripe

    # Cloud providers
    "AIza[0-9A-Za-z_-]{35}"                                    # Google API key
    "AKIA[0-9A-Z]{16}"                                         # AWS access key id

    # Cloudflare tunnel token: base64 of {"a":"<account>","t":...}. eyJhIjoi is
    # that prefix encoded. The old entry here was "eyJhIjoiW0-9a-f]{32}..." — a
    # missing [ turned the character class into literal text, so it matched
    # nothing. Its neighbour was "[a-f0-9]{32,}", which is every git sha, every
    # md5, every hex digest in a lockfile: deleted, it can only cry wolf.
    "eyJhIjoi[A-Za-z0-9_+/=-]{40,}"

    # GitHub
    "gh[pousr]_[0-9a-zA-Z]{36}"

    # Database DSNs. The old pattern was "postgres://" — this project writes
    # postgresql:// and postgresql+asyncpg://, so it never once matched the
    # scheme actually in use. The {12,} on the password is what keeps the real
    # placeholders in the tree quiet: erp:erp@, user:password@, postgres:sua-senha@
    # are all shorter, a generated password is not.
    "postgres(ql)?(\+[a-z]+)?://[^:@/[:space:]]+:[^@/[:space:]]{12,}@"
    "mongodb(\+srv)?://[^:@/[:space:]]+:[^@/[:space:]]{12,}@"
    "mysql://[^:@/[:space:]]+:[^@/[:space:]]{12,}@"

    # Generic assignments
    "[Bb]earer [a-zA-Z0-9._~+/-]{20,}=*"                       # was "bearer" only; grep -E is case sensitive
    "(token|api[_-]?key|secret)[\"']?[[:space:]]*[:=][[:space:]]*[\"'][a-zA-Z0-9._~+/-]{20,}[\"']"
)

# -U0 keeps context lines out; ^+[^+] drops the +++ header. No subshell, so the
# exits below actually exit.
# test-check-secrets.sh is excluded because it exists to hold fake secrets — it
# flagged itself on its first run. The cost is real: a genuine key pasted into
# that one file walks straight through. It is a test fixture, keep it that way.
ADDED="$(git diff --cached -U0 --diff-filter=ACM -- .          ':!graphify-out/' ':!scripts/test-check-secrets.sh' | grep '^+[^+]' || true)"

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    hit="$(printf '%s\n' "$ADDED" | grep -m1 -E -- "$pattern" || true)"
    if [ -n "$hit" ]; then
        printf "${RED}❌ ERRO: padrão sensível em linha adicionada${NC}\n"
        printf "${YELLOW}Padrão: %s${NC}\n" "$pattern"
        printf "Linha:  %.160s\n" "$hit"
        echo ""
        echo "Use variáveis de ambiente, ou um placeholder curto em exemplos."
        exit 1
    fi
done

echo "✅ Verificação de segurança concluída"
