# ⚡ Quick Start - Runas ERP

**Tempo estimado**: 10 minutos
**Pré-requisitos**: Docker e Docker Compose instalados, PowerShell (Windows)

---

## 🔑 Passo 0 — `.env` (obrigatório, antes de qualquer `up`)

Nada sobe sem isso. O `docker-compose.dev.yml` lê variáveis que **não têm valor
padrão** (`DATABASE_URL_GATEWAY`, `SERVICO_INTERNO_TOKEN`,
`PLATAFORMA_INTERNO_TOKEN`, entre outras).

```powershell
Copy-Item .env.example .env
```

Os defaults do `.env.example` já servem para desenvolvimento local. Dois campos
merecem atenção:

- `SERVICO_INTERNO_TOKEN` e `PLATAFORMA_INTERNO_TOKEN` vêm **vazios** do
  `.env.example`. O primeiro vazio é *fail-closed*: todo serviço responde 403,
  menos em `/health`. O segundo vazio é *fail-open* de propósito: loga e deixa
  passar. Gere com `openssl rand -hex 32` e use o **mesmo valor** em todos os
  containers (`.env.example:182,188`); o `SERVICO_INTERNO_TOKEN` é obrigatório.
- `ADMIN_EMAIL` / `ADMIN_PASSWORD` (`.env.example:93-94`) definem o usuário que
  o gateway cria sozinho no boot.

---

## 🔒 Passo 0.5 — Instalar o hook de pre-commit

`.git/hooks/` não é versionado e **nenhum script do repositório instala o hook
por você**. Um clone novo fica sem nenhuma proteção contra vazar segredo até
você rodar isto na mão (Git Bash):

```bash
cat > .git/hooks/pre-commit <<'SH'
#!/bin/sh
exec "$(git rev-parse --show-toplevel)/scripts/check-secrets.sh"
SH
chmod +x .git/hooks/pre-commit
```

O hook é só um shim de duas linhas; a lógica versionada mora em
`scripts/check-secrets.sh`, que bloqueia segredos nas **linhas adicionadas** do
diff staged. Detalhes em `.github/CONTRIBUTING.md`.

---

## 🚀 Subir o ambiente

### 📍 Método 1: `erp.ps1` (recomendado)

O entrypoint do repositório é o `erp.ps1` (ou `Menu.bat`, que é só um wrapper
que chama o `erp.ps1` com `-ExecutionPolicy Bypass`). Sem argumento, abre um
menu interativo.

```powershell
# Menu interativo
.\erp.ps1
# ou, se a ExecutionPolicy estiver travada:
.\Menu.bat

# Tudo (12 containers)
.\erp.ps1 up

# Só um subconjunto: gateway + frontend + vendas + as dependências de vendas
.\erp.ps1 up vendas

# Vários de uma vez
.\erp.ps1 up vendas,estoque

# Backend apenas — pula o Vite, que é o container mais pesado
.\erp.ps1 up clientes -NoFrontend

# Com o overlay do Cloudflare Tunnel
.\erp.ps1 up vendas -Cloudflare
```

Comandos disponíveis (`erp.ps1:18`): `up`, `down`, `restart`, `logs`, `ps`,
`health`, `rebuild`, `prune`, `shell`, `menu`.

```powershell
.\erp.ps1 logs vendas          # segue os logs de um serviço (ou de todos, se omitir)
.\erp.ps1 ps                   # status
.\erp.ps1 health               # status + consumo de CPU/memória
.\erp.ps1 shell erp-vendas-dev # shell dentro de um container
.\erp.ps1 down
```

Postgres, Redis e RabbitMQ nunca aparecem na lista: todo serviço os declara em
`depends_on`, então o compose os sobe sozinho.

Microsserviços válidos: `api-gateway`, `empresas`, `clientes`, `produtos`,
`estoque`, `vendas`, `financeiro`, `notificacoes` (mais `frontend-dev`).

### 📍 Método 2: docker compose direto

```powershell
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps
docker logs erp-api-gateway-dev -f
```

### ✅ Verificar se subiu de verdade

Não use `/health`: ele é raso de propósito (liveness do healthcheck do Docker) e
responde `200` com o backend inteiro morto atrás dele
(`api-gateway/main.py:104`).

O que realmente diz se a stack está de pé é o **readiness**, que sonda Postgres,
Redis e os sete serviços em paralelo e devolve `503` **nomeando quem caiu**
(`api-gateway/main.py:154`):

```powershell
# Direto no gateway
Invoke-RestMethod -Uri "http://localhost:8000/health/ready" | ConvertTo-Json -Depth 5

# Pela borda (frontend), que reescreve /api -> /
Invoke-RestMethod -Uri "http://localhost:3000/api/health/ready" | ConvertTo-Json -Depth 5
```

### ✅ Acesso local

- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🌐 Cloudflare Tunnel (acesso externo)

**Use quando**: precisa de webhooks, OAuth, testes em celular ou demonstração
remota.

### Desenvolvimento — túnel por arquivo de credencial

O túnel de dev roda `tunnel --config /etc/cloudflared/config.yml run` e monta
`~/.cloudflared` como volume: a autenticação vem do **arquivo de credencial**
referenciado em `cloudflared-config.yml`, não de um token de ambiente. Esse
arquivo `.json` **não está no repositório** — você precisa tê-lo em
`~/.cloudflared/` na sua máquina.

O ingress de dev serve **apenas `app.runaserp.com.br`**, apontando para
`frontend-dev:3000`. O apex e o `www` são a landing page (Cloudflare Pages),
fora do túnel.

```powershell
# Com o erp.ps1 (anexa docker-compose.cloudflare.yml e --profile proxy)
.\erp.ps1 up -Cloudflare

# Ou o compose na mão
docker compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# Verificar a conexão do túnel — o container se chama erp-cloudflared (sem -dev)
docker logs erp-cloudflared -f | Select-String "Registered tunnel connection"
```

> O container `cloudflared` de dev não tem healthcheck: a imagem é distroless,
> sem shell, `wget` ou `curl`. O log acima é a forma de monitorar.

**Acesso via túnel**:
- Frontend: https://app.runaserp.com.br
- API Gateway: https://app.runaserp.com.br/api
- API Docs: https://app.runaserp.com.br/api/docs

### Produção — túnel por token, gerenciado pelo Coolify

Produção **não** usa arquivo de credencial. O container `erp-cloudflared-prod`
roda `tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}`
(`docker-compose.prod.yml:551`), porque um deploy gerenciado pelo Coolify não
monta arquivo de credencial de forma limpa. O ingress é configurado no painel do
Cloudflare Zero Trust, não em arquivo no repositório.

---

## 🧪 Teste manual rápido

> ⚠️ **O gateway não tem prefixo `/api`.** Os routers são montados na raiz
> (`api-gateway/routers/auth.py:26` é `APIRouter(prefix="/auth")`). Batendo
> direto na porta 8000 o caminho é `/auth/login`; o `/api` só existe na borda,
> porque `frontend/vite.config.ts:84` reescreve `^/api` para nada antes de
> repassar ao gateway.

### 1. Login e obter token

```powershell
# Direto no gateway
Invoke-WebRequest -Uri "http://localhost:8000/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=admin@runas.com&password=Admin@123"

# Pela borda (frontend), com /api
Invoke-WebRequest -Uri "http://localhost:3000/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=admin@runas.com&password=Admin@123"

# Via Cloudflare Tunnel
Invoke-WebRequest -Uri "https://app.runaserp.com.br/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=admin@runas.com&password=Admin@123"
```

**Copie o `access_token` da resposta.**

### 2. Criar um cliente

```powershell
$token = "SEU_TOKEN_AQUI"

# empresa_id do body tem de ser igual ao da empresa do token; o admin do seed
# usa ADMIN_EMPRESA_ID (padrão 1, api-gateway/seed.py:30). O CPF precisa ter
# dígitos verificadores válidos (schema: services/clientes/schemas/cliente.py).
Invoke-WebRequest -Uri "http://localhost:8000/clientes" `
  -Method POST `
  -Headers @{
    "Authorization"="Bearer $token"
    "Content-Type"="application/json"
  } `
  -Body '{
    "empresa_id": 1,
    "nome": "João Silva",
    "cpf": "52998224725",
    "email": "joao@example.com",
    "telefone": "+5511999999999"
  }'
```

### 3. Listar produtos

```powershell
# Direto no gateway
Invoke-WebRequest -Uri "http://localhost:8000/produtos" `
  -Headers @{"Authorization"="Bearer $token"}

# Via Cloudflare Tunnel
Invoke-WebRequest -Uri "https://app.runaserp.com.br/api/produtos" `
  -Headers @{"Authorization"="Bearer $token"}
```

---

## 🔧 Troubleshooting

### ❌ "Port already in use"

```powershell
netstat -ano | findstr :8000

.\erp.ps1 down
.\erp.ps1 up
```

### ❌ "Container exited with code 1"

```powershell
docker logs erp-api-gateway-dev
docker logs erp-db-dev

# O .env existe? (Passo 0)
Get-Content .env
```

### ❌ "Cannot connect to database"

```powershell
docker ps | Select-String "postgres"
docker logs erp-db-dev

# Aguardar o healthcheck do banco
Start-Sleep -Seconds 30
```

### ❌ Frontend não carrega

```powershell
docker ps | Select-String "frontend"
docker logs erp-frontend-dev -f

# Depois de mexer no .env, use --force-recreate.
# "docker restart" NÃO relê o .env.
docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev
```

### ❌ Login dá 404

Você provavelmente bateu em `http://localhost:8000/api/auth/login`. O gateway
não tem prefixo `/api`. Veja o aviso na seção de teste manual.

---

## 📚 Próximos passos

1. **Frontend**: acesse http://localhost:3000 e entre com `admin@runas.com` /
   `Admin@123` (os defaults de `ADMIN_EMAIL`/`ADMIN_PASSWORD`). O usuário admin
   é criado **automaticamente no boot** do gateway (`api-gateway/main.py:46`
   chama `seed_admin()`) — não há passo manual de seed.
2. **Explorar a API**: http://localhost:8000/docs
3. **Documentação completa**: `docs/README.md`
4. **Contribuir**: `.github/CONTRIBUTING.md`
5. **Operação e deploy**: `docs/06-operacao/runbook-producao.md` e
   `docs/06-operacao/deploy.md`

---

## 🎯 Estrutura do projeto

```
RunasERP/
├── erp.ps1                        # Entrypoint: up/down/logs/health/shell...
├── Menu.bat                       # Wrapper do erp.ps1 (ExecutionPolicy Bypass)
├── api-gateway/                   # Autenticação, proxy e readiness
├── services/                      # Microsserviços
│   ├── empresas/                  # Multi-tenancy
│   ├── clientes/
│   ├── produtos/
│   ├── estoque/
│   ├── vendas/
│   ├── financeiro/
│   └── notificacoes/
├── frontend/                      # React + TypeScript (Vite)
├── shared/                        # Código morto: zero imports, os Dockerfiles não copiam
├── scripts/                       # check-secrets.sh e utilitários
├── tests/                         # Testes pytest
├── .env.example                   # Copiar para .env (Passo 0)
├── cloudflared-config.yml         # Ingress do túnel de DEV
├── docker-compose.dev.yml         # Desenvolvimento
├── docker-compose.prod.yml        # Produção (Coolify)
└── docker-compose.cloudflare.yml  # Overlay do Cloudflare Tunnel (dev)
```

---

<div align="center">

**Quick Start** | Setembro 2026
**Documentação**: `docs/README.md` | **Suporte**: Issues no GitHub

</div>
