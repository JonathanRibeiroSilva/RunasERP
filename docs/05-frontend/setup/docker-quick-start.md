# Docker Quick Start - Frontend

**Atualizado:** 2026-09-26
**Escopo:** subir o frontend (Vite) e o api-gateway em desenvolvimento, via `docker-compose.dev.yml`

---

## Início rápido

### Pré-requisitos

```bash
docker --version
docker compose version
```

Todos os comandos abaixo usam `docker compose` (plugin v2). Se a sua máquina só
tem o binário antigo `docker-compose`, troque o comando — o resto é igual.

Sem Docker: https://www.docker.com/products/docker-desktop

### Passo 1: Repositório e `.env`

```bash
cd <caminho-do-seu-clone>/RunasERP
git pull
cp .env.example .env
```

O `.env` não é opcional: `docker-compose.dev.yml` lê variáveis **sem default**,
como `DATABASE_URL_GATEWAY` e `SERVICO_INTERNO_TOKEN`. Sem ele o gateway não
sobe (`docker-compose.dev.yml:190` e `:193`, `.env.example:35`).

### Passo 2: Subir o frontend

```bash
docker compose -f docker-compose.dev.yml up frontend-dev
```

Um comando basta: `frontend-dev` tem `depends_on: api-gateway`, e o gateway
depende de `db` e `redis` com `condition: service_healthy`. Subir o frontend
sobe a cadeia inteira.

**Esperado:**
```
erp-frontend-dev  | VITE v8.x.x  ready in xxx ms
erp-frontend-dev  | ➜  Local:   http://localhost:3000/
```

(Vite `^8.3.0` — `frontend/package.json:53`.)

**Verificar:**
- Frontend: http://localhost:3000
- Gateway: http://localhost:8000/health → `{"status":"healthy","service":"api-gateway"}`
- Stack completa (banco, Redis e os 7 serviços): http://localhost:8000/health/ready

O Swagger em `/docs` **não** está ligado por padrão: `DOCS_ENABLED` é `False`
em `api-gateway/config.py:84` e o compose de dev não define essa variável.
Para habilitar, ponha `DOCS_ENABLED=true` no `.env` e recrie o gateway.

### Passo 3: Entrar

Abra http://localhost:3000 e faça login com o admin semeado no boot do gateway
(`api-gateway/main.py:46` chama `seed_admin()`):

```
Email: admin@runas.com
Senha: Admin@123
```

São os defaults de `ADMIN_EMAIL` / `ADMIN_PASSWORD` (`api-gateway/seed.py:27-28`).
Se você mudou essas variáveis no `.env`, use os seus valores.

---

## Comandos úteis

### Subir / parar

```bash
# Stack inteira
docker compose -f docker-compose.dev.yml up

# Em background
docker compose -f docker-compose.dev.yml up -d

# Parar
docker compose -f docker-compose.dev.yml down

# Parar e apagar volumes (perde o banco de dev)
docker compose -f docker-compose.dev.yml down -v
```

### Logs

```bash
docker compose -f docker-compose.dev.yml logs -f frontend-dev
docker compose -f docker-compose.dev.yml logs -f api-gateway
docker compose -f docker-compose.dev.yml logs -f
```

### Executar comandos dentro dos containers

```bash
# Build de produção do frontend (script "build" de frontend/package.json)
docker compose -f docker-compose.dev.yml exec frontend-dev npm run build

# psql no banco de dev (usuário e base default: erp)
docker compose -f docker-compose.dev.yml exec db psql -U erp -d erp
```

Não rode `pytest` dentro do container do gateway: `api-gateway/requirements.txt`
não instala pytest — a imagem só tem as dependências de runtime. Os testes
rodam no CI / no ambiente local de Python, não no container.

### Rebuild

```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up --build
```

### Depois de mexer no `.env`

```bash
docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev
```

`docker restart` **não** relê o `.env` (comentário em `docker-compose.dev.yml:542`).

---

## Troubleshooting

### "Cannot connect to Docker daemon"

Abra o Docker Desktop, espere terminar de inicializar e repita o comando.

### "Port 3000 already in use" / "Port 8000 already in use"

```bash
docker compose -f docker-compose.dev.yml down
```

As portas são fixas no compose (`"3000:3000"` no `frontend-dev`, `"8000:8000"`
no `api-gateway`) e não há variável de ambiente para trocá-las — não existe
`VITE_PORT` nem `API_PORT` no projeto. Para usar outra porta no host, edite o
lado esquerdo do mapeamento em `docker-compose.dev.yml` (ex.: `"3001:3000"`).

### "Out of memory"

Docker Desktop > Settings > Resources > aumentar memória. O `frontend-dev` é o
container mais pesado da stack: 1.5 CPU e 1536M de limite
(`docker-compose.dev.yml:561-563`).

### "Build failed"

```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.dev.yml up
```

### Hot reload não dispara

O watch usa polling (`CHOKIDAR_USEPOLLING=true`, intervalo de 1000ms) porque
inotify não atravessa bind mounts no Docker/Windows. Só `frontend/src`,
`frontend/public` e `vite.config.ts` estão montados — mudança em qualquer outro
arquivo do frontend exige rebuild da imagem.

---

## O que o compose de dev define (trechos reais)

`docker-compose.dev.yml` não tem chave `version:` (formato Compose Spec).

```yaml
services:
  frontend-dev:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: erp-frontend-dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
      - ./frontend/vite.config.ts:/app/vite.config.ts:ro
      - /app/node_modules
    environment:
      VITE_API_URL: ${VITE_API_URL:-/api}
      VITE_USE_PROXY: "true"
    depends_on:
      - api-gateway

  api-gateway:
    build:
      context: ./api-gateway
      dockerfile: Dockerfile
    container_name: erp-api-gateway-dev
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    container_name: erp-db-dev
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-erp}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-erp}
      POSTGRES_DB: ${POSTGRES_DB:-erp}
    ports:
      - "5432:5432"
```

Detalhe importante: `VITE_API_URL` é `/api` (caminho relativo), não uma URL
absoluta. O Vite faz proxy de `/api/*` para `http://api-gateway:8000`, tirando
o prefixo `/api` no caminho (`frontend/vite.config.ts`, bloco `server.proxy`).
Isso vale enquanto `VITE_USE_PROXY` não for `false`.

O serviço do banco chama-se `db` (não `postgres`), e o nome da base é `erp`.

---

## Por que Docker aqui

- Não precisa instalar Node, Python ou PostgreSQL na máquina.
- Mesmas versões para todo mundo: Python 3.12-slim, postgres:15-alpine, redis:7-alpine.
- Hot reload funciona (com polling, ver Troubleshooting).
- `down -v` limpa tudo sem deixar resto no sistema.

A imagem de dev **não** é a de produção: o frontend usa `Dockerfile.dev` em dev
e o deploy de produção tem compose próprio (`docker-compose.prod.yml`).

---

## Documentação relacionada

- [prerequisites.md](./prerequisites.md) - pré-requisitos do ambiente
- [docker.md](./docker.md) - documentação Docker mais longa (este arquivo é o caminho curto)
