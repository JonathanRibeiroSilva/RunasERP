# Pré-requisitos do ambiente de desenvolvimento

**Atualizado:** 2026-09-26
**Escopo:** o que precisa existir na máquina antes de subir o frontend. O roteiro
de primeira execução está em [docker-quick-start.md](./docker-quick-start.md).

---

## Caminho recomendado: Docker

É o único caminho documentado. Com Docker você não instala Node, Python nem
PostgreSQL na máquina — as versões vêm das imagens.

```bash
docker --version
docker compose version
```

Os comandos do projeto usam `docker compose` (plugin v2), não o binário antigo
`docker-compose`.

Sem Docker: https://www.docker.com/products/docker-desktop

**Requer acesso de administrador para instalar** (Docker Desktop no Windows).

### Recursos mínimos

O `frontend-dev` é o container mais pesado da stack: limite de 1.5 CPU e 1536M
(`docker-compose.dev.yml:561-563`). Dimensione a memória do Docker Desktop
acima disso, porque o `db` (1 CPU / 1G) e os 8 containers Python sobem junto.

---

## Caminho alternativo: rodar o frontend fora do Docker

Não é o caminho suportado pelo projeto — nenhum script ou arquivo do repositório
automatiza isso, e o backend continua precisando de Docker (banco, Redis,
RabbitMQ). Se ainda assim for rodar só o Vite na máquina:

```bash
node --version
npm --version
```

A imagem de dev usa **Node 22** (`frontend/Dockerfile.dev:4` — `node:22-alpine`).
`frontend/package.json` não declara campo `engines`, então não há mínimo
publicado no repositório; use 22 para bater com a imagem.

Com o Vite rodando fora do Docker, `http://api-gateway:8000` não resolve. Aponte
o proxy para o gateway publicado no host:

```bash
VITE_API_GATEWAY_TARGET=http://localhost:8000 npm run dev
```

(`frontend/vite.config.ts:82` lê `VITE_API_GATEWAY_TARGET`, com default
`http://api-gateway:8000`.)

### Python

Só é necessário para rodar o backend ou os testes fora do Docker. As imagens do
gateway e dos 7 serviços usam **Python 3.12** (`api-gateway/Dockerfile:2` e
`services/*/Dockerfile` — `python:3.12-slim`).

A CONFIRMAR: versão mínima de Python suportada fora do Docker. Nenhum
`pyproject.toml`/`setup.cfg` do repositório declara `python_requires`.

---

## Configuração de variáveis de ambiente

**Existe um único `.env`, na raiz do repositório.** Não há
`frontend/.env.development` nem `api-gateway/.env` neste projeto — o
`docker-compose.dev.yml` interpola tudo a partir do `.env` da raiz.

```bash
cp .env.example .env
```

O `.env` não é opcional: o compose de dev lê variáveis **sem default**, como
`DATABASE_URL_GATEWAY` (`docker-compose.dev.yml:190`) e `SERVICO_INTERNO_TOKEN`
(`:193`). Sem elas o gateway não sobe.

Variáveis do frontend, com os defaults que o compose já aplica
(`docker-compose.dev.yml:544-555`):

| Variável | Default no Compose |
|---|---|
| `VITE_API_URL` | `/api` |
| `VITE_OAUTH_REDIRECT_URI` | `http://localhost:3000/auth/callback` |
| `VITE_GOOGLE_CLIENT_ID` | (sem default) |
| `VITE_MICROSOFT_CLIENT_ID` | (sem default) |
| `VITE_MICROSOFT_TENANT_ID` | `common` |
| `VITE_USE_PROXY` | `"true"` (fixo) |

`VITE_API_URL` é um caminho relativo (`/api`), não `http://localhost:8000`: o
proxy do Vite é que encaminha para o gateway. A lista completa de variáveis está
em `.env.example`; as obrigatórias estão em
[QUICK-START.md](../../../QUICK-START.md).

Depois de editar o `.env`, **recrie** o container — `docker restart` não relê o
arquivo:

```bash
docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev
```

---

## Banco de dados

Sobe junto com a stack: serviço `db`, imagem `postgres:15-alpine`, publicado em
`5432:5432`, usuário/base `erp` por default
(`docker-compose.dev.yml:69-90`). Não há passo manual de `CREATE DATABASE` —
`postgres/init-schemas.sql` é montado em `docker-entrypoint-initdb.d/`.

```bash
docker compose -f docker-compose.dev.yml exec db psql -U erp -d erp
```

---

## Credenciais de teste

O admin é semeado no boot do gateway (`api-gateway/main.py:46` chama
`seed_admin()`), com os defaults de `api-gateway/seed.py:27-28`:

```
Email: admin@runas.com
Senha: Admin@123
```

Defina `ADMIN_EMAIL` / `ADMIN_PASSWORD` no `.env` para usar outros valores. Não
use esses defaults em nada exposto à internet.

### OAuth (opcional)

Só é necessário para testar login Google/Microsoft. O passo a passo de registro
do app e as variáveis correspondentes estão em
[docs/02-desenvolvimento/OAUTH_PROVIDERS_CONFIG.md](../../02-desenvolvimento/OAUTH_PROVIDERS_CONFIG.md).

---

## Verificação final

```bash
docker --version
docker compose version
test -f .env && echo ".env ok" || echo "falta copiar .env.example"
docker compose -f docker-compose.dev.yml config >/dev/null && echo "compose ok"
```

`docker compose config` valida a sintaxe e imprime o compose resolvido. O
`docker-compose.dev.yml` não usa `${VAR:?}` (nenhuma variável é marcada como
obrigatória), então uma variável ausente **não** faz o comando falhar: ela
aparece como aviso `variable is not set` e vira string vazia. Leia os avisos.

Depois de subir (`docker compose -f docker-compose.dev.yml up frontend-dev`):

- Frontend: http://localhost:3000
- Gateway: http://localhost:8000/health
- Stack completa (banco, Redis e os 7 serviços): http://localhost:8000/health/ready

---

## Problemas comuns

| Sintoma | Causa |
|---|---|
| `no configuration file provided` | Faltou o `-f`. Não existe `docker-compose.yml` na raiz — são quatro arquivos, todos com sufixo |
| `Cannot connect to Docker daemon` | Docker Desktop não terminou de inicializar |
| `Port 3000/8000 already in use` | Outra instância da stack de pé: `docker compose -f docker-compose.dev.yml down` |
| Mudei o `.env` e nada mudou | `docker restart` não relê o `.env`; use `--force-recreate` |

Mais casos, incluindo hot reload e build: [docker.md](./docker.md) e
[docker-quick-start.md](./docker-quick-start.md).

---

## Relacionados

- [docker-quick-start.md](./docker-quick-start.md) — subir a stack
- [docker.md](./docker.md) — referência Docker do frontend
- [../../../QUICK-START.md](../../../QUICK-START.md) — variáveis obrigatórias do `.env`
