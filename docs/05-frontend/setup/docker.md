# Docker - Frontend ERP Runas

Referência do frontend dentro do Docker: quais arquivos existem, qual serviço
sobe, em que porta e com quais variáveis.

Para subir a stack pela primeira vez em 5 minutos, use
[docker-quick-start.md](./docker-quick-start.md) — este documento é a referência
detalhada, não o roteiro de primeira execução.

---

## ⚠️ Não existe `docker-compose.yml` na raiz

A raiz do repositório tem **quatro** arquivos Compose, e nenhum deles se chama
`docker-compose.yml`:

| Arquivo | Para que serve |
|---|---|
| `docker-compose.dev.yml` | Ambiente de desenvolvimento completo (infra + 8 serviços + frontend) |
| `docker-compose.cloudflare.yml` | Overlay do Cloudflare Tunnel sobre o dev. Não é standalone |
| `docker-compose.build.yml` | Contextos e build args das imagens publicadas no GHCR |
| `docker-compose.prod.yml` | Produção (lido pelo Coolify na VPS) |

Consequência prática: **todo comando precisa de `-f <arquivo>`**. Um
`docker compose up` sem `-f` não encontra arquivo nenhum e falha.

Também **não existe** `frontend/docker-compose.yml`. Os serviços do frontend são
declarados nos arquivos da raiz, com `context: ./frontend`.

---

## 📦 Arquivos Docker do frontend

Em `frontend/`:

1. **`Dockerfile`** — build de produção, multi-stage (`node:22-alpine` →
   `nginx:alpine`)
2. **`Dockerfile.dev`** — desenvolvimento com hot reload (`node:22-alpine`)
3. **`nginx.conf`** — configuração do Nginx que serve o SPA dentro da imagem de
   produção
4. **`.dockerignore`** — mantém `node_modules`, `dist`, `.env*` e `coverage`
   fora do contexto de build

---

## 🚀 Desenvolvimento (`frontend-dev`)

Serviço: **`frontend-dev`** · container: **`erp-frontend-dev`** ·
porta: **3000:3000**

```bash
# Toda a stack (infra + serviços + frontend)
docker compose -f docker-compose.dev.yml up -d

# Só o frontend (sobe api-gateway junto, por depends_on)
docker compose -f docker-compose.dev.yml up -d frontend-dev
```

**Acesso:** http://localhost:3000

A porta 3000 não é escolha do Compose: `frontend/vite.config.ts` fixa
`server.port: 3000` e `server.host: '0.0.0.0'` (e `preview.port: 3000`). O
`Dockerfile.dev` expõe 3000 e o Compose publica `3000:3000`.

### Como o frontend fala com a API em dev

Não há nginx em desenvolvimento. O próprio Vite faz o proxy:

- `VITE_API_URL` tem default `/api` no Compose (URL relativa)
- `VITE_USE_PROXY: "true"` no Compose
- `vite.config.ts` cria o proxy quando `VITE_USE_PROXY !== 'false'`:
  `/api` → `http://api-gateway:8000` (alvo sobrescrevível por
  `VITE_API_GATEWAY_TARGET`), com `rewrite` removendo o prefixo `/api`
- Se `VITE_API_URL` não estiver definida, `src/config/env.ts` cai no fallback
  `'/api'`

### Volumes montados

```yaml
- ./frontend/src:/app/src
- ./frontend/public:/app/public
- ./frontend/vite.config.ts:/app/vite.config.ts:ro
- /app/node_modules          # volume anônimo: preserva o install da imagem
```

Só `src/`, `public/` e `vite.config.ts` são montados. Mexer em
`package.json`, `tsconfig.json` ou `index.html` **exige rebuild** — o hot reload
não vê esses arquivos.

### Hot reload

Watch por polling, porque inotify não atravessa bind mount no Docker Desktop
(Windows/macOS). Configurado em três lugares que precisam concordar:

- `Dockerfile.dev`: `ENV CHOKIDAR_USEPOLLING=true`, `ENV CHOKIDAR_INTERVAL=1000`
- `docker-compose.dev.yml`: `CHOKIDAR_USEPOLLING: "true"`,
  `CHOKIDAR_INTERVAL: "1000"`
- `vite.config.ts`: `server.watch.usePolling: true`, `interval: 1000`

O intervalo é 1s de propósito: valores menores geram falsos positivos de
mudança no Windows/Docker.

---

## 🌐 Variáveis de ambiente

### Desenvolvimento

Vêm do `.env` da **raiz** do repositório (não de `frontend/.env`), interpoladas
pelo `docker-compose.dev.yml`:

| Variável | Default no Compose |
|---|---|
| `VITE_API_URL` | `/api` |
| `VITE_OAUTH_REDIRECT_URI` | `http://localhost:3000/auth/callback` |
| `VITE_GOOGLE_CLIENT_ID` | (sem default) |
| `VITE_MICROSOFT_CLIENT_ID` | (sem default) |
| `VITE_MICROSOFT_TENANT_ID` | `common` |
| `VITE_USE_PROXY` | `"true"` (fixo) |
| `CHOKIDAR_USEPOLLING` / `CHOKIDAR_INTERVAL` | `"true"` / `"1000"` (fixos) |

**Depois de editar o `.env`, recrie o container:**

```bash
docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev
```

`docker restart erp-frontend-dev` **não** relê o `.env`.

### Produção

As `VITE_*` são embutidas no bundle durante o `npm run build`, então têm de estar
corretas no momento do build (no runner do GitHub Actions), não só no Coolify.
`docker-compose.build.yml` declara os `args` do serviço `frontend-prod`:
`VITE_API_URL=/api`, `VITE_OAUTH_REDIRECT_URI=${FRONTEND_URL}/auth/callback`,
`VITE_GOOGLE_CLIENT_ID`, `VITE_MICROSOFT_CLIENT_ID` e `VITE_MICROSOFT_TENANT_ID`.

**Ressalva verificada:** `frontend/Dockerfile` **não declara nenhum `ARG`**. Sem
`ARG`, um `--build-arg` não vira variável de ambiente dentro do build, logo esses
valores não chegam ao `npm run build`. Para `VITE_API_URL` isso é inofensivo — o
fallback `'/api'` em `src/config/env.ts` coincide com o valor pretendido.

A CONFIRMAR: como `VITE_GOOGLE_CLIENT_ID`, `VITE_MICROSOFT_CLIENT_ID` e
`VITE_OAUTH_REDIRECT_URI` chegam ao bundle de produção hoje, dado que não há
`ARG` no Dockerfile — ou se o OAuth em produção depende de outro caminho.

---

## 🏭 Produção (`frontend-prod`)

Serviço: **`frontend-prod`** · container: **`erp-frontend-prod`**

Diferenças relevantes em relação ao dev:

- **Não faz build na VPS.** Consome a imagem publicada:
  `${REGISTRY:-ghcr.io/jonathanribeirosilva/runaserp}/frontend:${TAG:-latest}`,
  com `pull_policy: always`. A VPS tem 1 vCPU; o build roda no runner do GitHub
  Actions (`.github/workflows/deploy.yml`).
- **Não publica porta no host.** Não existe `ports:` no serviço. O único ingress
  é o Cloudflare Tunnel (`cloudflared`), que roteia
  `app.runaserp.com.br` → `http://frontend-prod:80` pela rede interna.
  Portanto **não há `http://localhost` para acessar em produção**.
- `depends_on: api-gateway-prod (service_healthy)`.
- Healthcheck: `wget -q --spider http://127.0.0.1/health`. É `127.0.0.1` e não
  `localhost` porque o `wget` do busybox tenta `::1` primeiro e desiste ali, e o
  `nginx.conf` só tem `listen 80`.

O build da imagem, quando precisa ser feito à mão:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.build.yml build frontend-prod
```

Deploy completo e rollback: [docs/06-operacao/deploy.md](../../06-operacao/deploy.md).

---

## 🔧 O que o `nginx.conf` faz (só produção)

O arquivo serve o SPA construído dentro da imagem. Pontos que costumam ser
consultados:

- **`location /api/`** — proxy para o gateway. O hostname fica numa variável
  (`set $gateway api-gateway-prod:8000;`) com `resolver 127.0.0.11 valid=10s`,
  porque com hostname literal em `proxy_pass` o nginx resolve uma vez no boot e
  cacheia o IP para sempre — já causou `/` respondendo 200 e `/api/*` 502 por
  20+ minutos depois de um deploy que trocou só o gateway. O
  `rewrite ^/api/(.*)$ /$1 break;` remove o prefixo, espelhando o `rewrite` do
  `vite.config.ts`.
- **`location = /health`** — retorna `200 "ok"`, é o alvo do healthcheck.
- **`location /assets/`** — `expires 1y` + `Cache-Control "public, immutable"`
  (o Vite gera nomes com hash de conteúdo). Repete
  `add_header X-Content-Type-Options nosniff` porque o nginx só herda
  `add_header` do nível acima quando o nível atual não declara nenhum.
- **`location /plataforma`** — devolve 404 quando o host não casa `^admin\.`; no
  host do painel faz o mesmo `try_files` do fallback. Sem isso, `app.*/plataforma`
  devolveria o `index.html` com 200, o que já contaria que o painel existe.
- **`location /`** — `try_files $uri $uri/ /index.html` (fallback do SPA).
- **Headers de segurança** — `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` e
  um `Content-Security-Policy` onde `style-src` permite `'unsafe-inline'` (JSX
  usa `style={{...}}`) mas `script-src` fica só em `'self'`.
- **Gzip** — `gzip on` para `text/plain`, `text/css`,
  `application/javascript`, `application/json` e `image/svg+xml`, a partir de
  1024 bytes.

Leia o arquivo antes de alterar: `frontend/nginx.conf`.

---

## 📊 Comandos úteis

Todos com `-f`. Sem `-f`, nenhum funciona.

```bash
# Logs
docker compose -f docker-compose.dev.yml logs -f frontend-dev
docker logs erp-frontend-dev -f

# Parar
docker compose -f docker-compose.dev.yml stop frontend-dev
docker compose -f docker-compose.dev.yml down

# Rebuild
docker compose -f docker-compose.dev.yml build frontend-dev
docker compose -f docker-compose.dev.yml build --no-cache frontend-dev
docker compose -f docker-compose.dev.yml up -d --build frontend-dev

# Recriar lendo o .env de novo
docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev

# Rodar comando dentro do container
docker compose -f docker-compose.dev.yml exec frontend-dev npm run build
docker compose -f docker-compose.dev.yml exec frontend-dev npm run lint

# Shell
docker exec -it erp-frontend-dev sh

# Status
docker compose -f docker-compose.dev.yml ps
```

Com o Cloudflare Tunnel em dev (overlay, exige os dois `-f` e o profile):

```bash
docker compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
```

O overlay sobrescreve `VITE_OAUTH_REDIRECT_URI` e `FRONTEND_URL` do
`frontend-dev` para `https://app.runaserp.com.br`.

---

## 🐛 Troubleshooting

### `no configuration file provided` / `no such file`

Faltou o `-f`. Não existe `docker-compose.yml` na raiz.

### "Cannot find module" após mudar dependências

`node_modules` vive num volume anônimo e `package.json` não é montado. Rebuild:

```bash
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml build --no-cache frontend-dev
docker compose -f docker-compose.dev.yml up -d frontend-dev
```

### "Port 3000 is already in use"

```powershell
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

Ou troque só o lado do host em `docker-compose.dev.yml` (`"3001:3000"`) — o lado
do container precisa continuar 3000, que é o que o Vite escuta.

### Hot reload não funciona

1. Confirme que a mudança foi em `src/` ou `public/` — só esses dois diretórios
   (mais `vite.config.ts`) estão montados.
2. Confirme o polling: `docker exec erp-frontend-dev env | grep CHOKIDAR`.
3. Recrie: `docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev`.

### Mudei o `.env` e nada mudou

`docker restart` não relê o `.env`. Use
`docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev`.

### Frontend abre mas a API não responde

1. O gateway está de pé?
   `docker compose -f docker-compose.dev.yml ps api-gateway`
2. O proxy do Vite está ativo? `VITE_USE_PROXY` tem de ser diferente de
   `"false"` e o alvo padrão é `http://api-gateway:8000` (nome de serviço, só
   resolve dentro da rede `erp-network`).
3. Teste o gateway direto: `curl http://localhost:8000/health`.

Sintomas de produção (502 em `/api`, 530 do Cloudflare, crashloop) estão em
[docs/06-operacao/troubleshooting.md](../../06-operacao/troubleshooting.md) e
[docs/06-operacao/runbook-producao.md](../../06-operacao/runbook-producao.md).

### 404 ao recarregar uma rota interna

Fallback do SPA. Em produção é o `try_files` do `nginx.conf`; em dev o Vite já
resolve. Se falhar em produção, confira `location /` no `frontend/nginx.conf` e
rebuild a imagem.

---

## 🔗 Relacionados

- [docker-quick-start.md](./docker-quick-start.md) — subir a stack em 5 minutos
- [prerequisites.md](./prerequisites.md) — o que instalar antes
- [../../../QUICK-START.md](../../../QUICK-START.md) — variáveis obrigatórias do
  `.env` da raiz
- [docs/06-operacao/deploy.md](../../06-operacao/deploy.md) — pipeline de deploy
- [docs/05-frontend/frontend-current-state.md](../frontend-current-state.md) —
  estado atual do frontend
