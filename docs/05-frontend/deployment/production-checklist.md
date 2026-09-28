# Checklist de Produção - Frontend

Verificações para o frontend antes e depois de um deploy. Vale para o deploy
real deste projeto: o CI constrói as imagens e publica no ghcr, o Coolify faz
pull na VPS e o Cloudflare Tunnel é a única entrada. Como o fluxo inteiro
funciona está em [deploy.md](../../06-operacao/deploy.md); incidentes, em
[runbook-producao.md](../../06-operacao/runbook-producao.md).

A landing (`runaserp.com.br`) não passa por aqui: é um site estático no
Cloudflare Pages com workflow próprio (`.github/workflows/landing.yml`).

## Como o frontend chega à produção

1. PR para `main` roda o CI (`.github/workflows/ci.yml`). O job `frontend` faz
   `npm ci`, `npm run lint`, `npm run build` (`tsc && vite build`) e
   `npm run test -- --run`; o job `build` constrói as nove imagens de produção.
2. Merge em `main` dispara `.github/workflows/deploy.yml`, que constrói as
   imagens no runner com `docker-compose.prod.yml` + `docker-compose.build.yml`,
   publica `:<sha>` e `:latest` no ghcr e chama o Coolify.
3. O Coolify lê `docker-compose.prod.yml`, que não tem `build:` por desenho:
   a VPS (1 vCPU) só faz pull. O deploy.yml espera o registro de deploy do
   Coolify terminar como `finished`/`success`.

Mudanças só em `docs/**`, `**.md`, `.github/**`, `scripts/**` e
`landing-page/**` não disparam deploy (`paths-ignore` no deploy.yml).

## Antes do merge em main

- [ ] CI verde no PR (lint, build, testes do frontend e build das imagens).
- [ ] O PR tem `Developer` ou `main` como base: o CI só roda em PR para essas
      branches (`ci.yml`, `on.pull_request.branches`).
- [ ] Nenhum `console.log` de debug novo. Hoje restam cinco, todos em
      `frontend/src/pages/LojaOnlinePublico/CheckoutPage.tsx` (linhas 689, 691,
      734, 748 e 749), um deles imprimindo `document.cookie`. O build não os
      remove: `vite.config.ts` não configura `drop_console`.
- [ ] `npm audit` em `frontend/` quando o PR adiciona dependência: o CI não
      roda auditoria (o Dependabot, em `.github/dependabot.yml`, abre PRs
      semanais de atualização de versão).

## Build e imagem

- `frontend/Dockerfile`: stage `node:22-alpine` com `npm ci` e
  `npm run build`; stage `nginx:alpine` servindo `dist/` com
  `frontend/nginx.conf`.
- `vite.config.ts` gera o build em `dist/` com `sourcemap: true`.

## Variáveis de ambiente

O Vite embute `VITE_*` no bundle na hora do build. As que o código lê estão em
`frontend/src/config/env.ts` e `frontend/src/config/host.ts`:

| Variável | Default no código | Uso real |
|---|---|---|
| `VITE_API_URL` | `/api` | Base do axios. Em produção precisa ser `/api` (relativo). |
| `VITE_API_TIMEOUT` | `30000` | Timeout do axios (`services/api/axios.ts`). |
| `VITE_ENABLE_DEVTOOLS` | desligado | React Query Devtools (`main.tsx`). |
| `VITE_HOST_PLATAFORMA` | `admin` | Rótulo do host do painel da plataforma (`host.ts`). |
| `VITE_APP_NAME`, `VITE_APP_VERSION`, `VITE_ENABLE_ANALYTICS`, `VITE_TOKEN_REFRESH_THRESHOLD` | ver `env.ts` | Lidas em `env.ts`, nenhum outro código as usa. |
| `VITE_GOOGLE_CLIENT_ID`, `VITE_MICROSOFT_CLIENT_ID`, `VITE_MICROSOFT_TENANT_ID`, `VITE_OAUTH_REDIRECT_URI` | ver `env.ts` | Lidas em `env.ts` (`env.oauth`), nenhum código as usa: o OAuth é montado pelo gateway e o `redirect_uri` sai de `window.location.origin`. |

Atenção: `docker-compose.build.yml` passa `VITE_API_URL`,
`VITE_OAUTH_REDIRECT_URI` e as `VITE_*` de OAuth como `args:` do build, mas
`frontend/Dockerfile` não declara nenhum `ARG`. Build arg não declarado não
chega ao `RUN npm run build`, então o bundle de produção sai com os defaults de
`env.ts` e `host.ts`. Hoje isso não muda nada (o default de `VITE_API_URL` já é `/api`,
`VITE_HOST_PLATAFORMA` nem é passada e vale `admin`, e as outras não são usadas), mas quem precisar de uma `VITE_*` nova em produção tem
de declarar o `ARG`/`ENV` no Dockerfile.

No backend, a que importa para o frontend é `FRONTEND_URL`
(`.env.production.example`: `https://app.runaserp.com.br`; obrigatória no
compose via `${FRONTEND_URL:?}`):

- CORS do gateway: `allow_origins=[settings.FRONTEND_URL]`
  (`api-gateway/main.py:81`).
- Flag `secure` dos cookies: `FRONTEND_URL.startswith("https://")`
  (`api-gateway/routers/auth.py:39`, `routers/auth_cliente.py:34`,
  `services/vendas/routers/loja.py:35`).
- Link de reset de senha (`api-gateway/services/email_service.py:140`), back_url
  da assinatura e URLs de retorno do Mercado Pago no vendas.

Não aponte `FRONTEND_URL` para `runaserp.com.br` (a landing): isso quebra o
login. Os valores reais ficam no Coolify (runtime) e no secret `PROD_ENV` do
GitHub (build); o modelo é `.env.production.example`.

## Servir o frontend (nginx dentro da imagem)

Estado atual de `frontend/nginx.conf`:

- [x] gzip para texto, CSS, JS, JSON e SVG (linhas 9-12).
- [x] `/assets/` com `expires 1y` e `Cache-Control: public, immutable`
      (linhas 47-55); seguro porque o Vite gera nomes com hash.
- [x] Fallback de SPA: `try_files $uri $uri/ /index.html` (linha 79).
- [x] `/plataforma` devolve 404 fora do host `admin.*` (linhas 71-76).
- [x] `/api/` repassado ao `api-gateway-prod:8000` com o prefixo removido e
      DNS resolvido por requisição (linhas 25-44), para não ficar preso ao IP
      de um gateway recriado.
- [x] `/health` estático, responde `ok` sem tocar no backend (linhas 57-60).

## Segurança

- [x] Headers `X-Content-Type-Options`, `X-Frame-Options DENY` e
      `Referrer-Policy` (`nginx.conf:14-16`).
- [x] CSP com `script-src 'self'` (`nginx.conf:21`). Script, fonte ou API
      externa nova precisa entrar no CSP, senão o browser bloqueia; o
      `connect-src` hoje só libera `'self'` e `https://viacep.com.br`.
- [x] HTTPS na borda pelo Cloudflare; o nginx repassa
      `X-Forwarded-Proto https` fixo (`nginx.conf:42`).
- [ ] A CONFIRMAR: HSTS. O `nginx.conf` não envia `Strict-Transport-Security`;
      se existe, vem de configuração do Cloudflare, que não está no repositório.
- [x] Rate limiting no gateway com slowapi (`api-gateway/main.py:74-76`).
- [x] Tokens: `ACCESS_TOKEN_EXPIRE_MINUTES=30` e `REFRESH_TOKEN_EXPIRE_DAYS=7`
      como default (`api-gateway/config.py:15-16`).
- [x] Nenhum `CLIENT_SECRET` no frontend (`git grep -i client_secret -- frontend/src`
      não encontra nada).
- [ ] Source maps públicos: `sourcemap: true` (`vite.config.ts:95`) publica os
      `.map` em `/assets/`, com o código-fonte legível por qualquer um. Decidir
      entre `false`, `'hidden'` (gera sem referenciar) ou manter de propósito.

## Performance

- [x] Minificação: padrão do `vite build`.
- [ ] Code splitting: só duas rotas usam `lazy()` (páginas da Plataforma em
      `frontend/src/App.tsx`); o resto é import estático e entra no bundle
      principal.
- [ ] A CONFIRMAR: tamanho do bundle. Não há orçamento nem análise no CI;
      conferir com `npm run build` (o Vite avisa chunks acima de 500 kB).

## Observabilidade

- [ ] Error reporting do frontend: não existe. `ErrorBoundary.tsx` e
      `utils/errorLogger.ts` só logam no console; Sentry aparece apenas em
      comentário como plano futuro.
- [x] Sonda externa: `.github/workflows/uptime.yml` consulta
      `https://app.runaserp.com.br/api/health/ready` (cron de 10 min; na
      prática o GitHub espaça as execuções para até ~30 min) e alerta no
      Telegram.

## Depois do deploy

A borda desafia User-Agent com `curl` ou `wget` (regra de WAF), então passe um
UA de browser, senão a resposta é um 403 do Cloudflare e não do app:

```bash
UA='Mozilla/5.0 (compatible; verificacao-manual)'

# Readiness profunda: gateway + Postgres + Redis + os sete serviços.
# 503 traz {"down": [...]} com quem caiu.
curl -s -A "$UA" https://app.runaserp.com.br/api/health/ready

# Liveness do frontend: é o nginx da imagem respondendo "ok",
# não diz nada sobre o backend.
curl -s -A "$UA" https://app.runaserp.com.br/health
```

- [ ] Job do deploy.yml verde (ele espera o status do deploy no Coolify, não
      testa HTTP).
- [ ] `/api/health/ready` com 200. `/health` sozinho não basta: `/` com 200 e
      `/api/*` com 502 já aconteceu depois de um deploy parcial.
- [ ] Login e uma tela com dados carregando no app.
- [ ] Se mexeu em OAuth de cliente: testar Google e Microsoft pela loja
      online. O frontend envia como `redirect_uri`
      `${window.location.origin}/auth/callback/google` e
      `.../auth/callback/microsoft`, que precisam estar cadastrados nos
      provedores (A CONFIRMAR: o cadastro atual no Google Cloud e no Azure não
      está no repositório). Problema conhecido: o login pela
      `ClienteLoginPage.tsx` não grava `oauth_state` nem `oauth_empresa_slug`
      no `sessionStorage` (o `CheckoutPage.tsx` grava, linhas 385-386 e
      416-417), e o
      `GoogleCallback.tsx`/`MicrosoftCallback.tsx` recusa o retorno com
      "State inválido".

Rollback: rodar o deploy.yml manualmente (`workflow_dispatch`) com `tag` = um
sha que já está no ghcr; ele republica essas imagens como `:latest` sem
rebuild. Detalhes em [deploy.md](../../06-operacao/deploy.md).
