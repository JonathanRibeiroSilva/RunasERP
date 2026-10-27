# FAQ - Perguntas Frequentes

> **Respostas para dúvidas comuns** sobre o Runas

---

## 📋 Índice

- [Geral](#geral)
- [Instalação e Setup](#instalação-e-setup)
- [Funcionalidades](#funcionalidades)
- [Técnico](#técnico)
- [Segurança](#segurança)
- [Licenciamento](#licenciamento)

---

## 🎯 Geral

### O que é o Runas?

O Runas é um sistema de gestão empresarial (ERP) moderno e acessível, desenvolvido especificamente para pequenos comércios brasileiros. Ele oferece gestão completa de clientes, produtos, estoque, vendas e financeiro.

### Para quem o Runas é indicado?

O Runas é ideal para:
- Pequenos comércios de alimentos e bebidas
- Mercearias e minimercados
- Distribuidoras de pequeno porte
- Lojas de conveniência
- Negócios que trabalham com vendas fiadas

### Quanto custa o Runas?

O Runas **não é open-source**: o `LICENSE` na raiz é uma licença proprietária da
DenebCorp (ver [Licenciamento](#licenciamento) abaixo e
[`docs/07-legal/EULA-comercial.md`](../07-legal/EULA-comercial.md)).

**A CONFIRMAR**: tabela de preços e modalidades de contratação. Não há nada no
repositório que defina valores — o serviço `empresas` tem assinatura por tenant
(`services/empresas/`) e o gateway corta escrita por inadimplência
(`api-gateway/middleware/inadimplencia_middleware.py`), mas nenhum preço está
versionado.

### Preciso de internet para usar?

A stack sobe inteira em `localhost` via `docker compose -f docker-compose.dev.yml`
(ver [QUICK-START](../../QUICK-START.md)). O que depende de rede externa:

- Pagamentos via PIX (Mercado Pago) — `services/vendas/services/mercadopago_service.py`
- Validação de CEP (ViaCEP) — `services/vendas/services/entrega_service.py:27`
- OAuth2 Google/Microsoft no login — `api-gateway/routers/`
- O túnel Cloudflare, quando usado

A produção não roda offline: o acesso chega pelo Cloudflare Tunnel e o TLS
termina no Cloudflare (`docker-compose.prod.yml:9`).

---

## 🚀 Instalação e Setup

### Quais são os requisitos mínimos?

**Para desenvolvimento:**
- Docker Desktop instalado
- Windows 10+, macOS 10.15+, ou Linux
- **A CONFIRMAR**: RAM e disco mínimos. O `docker-compose.dev.yml` sobe 12
  containers com limites em `deploy` (`dev-limits`), mas nenhum número de
  requisito de máquina está versionado.

**Para produção:** a VPS atual é **1 vCPU / 4 GB**, e é por isso que nada é
compilado nela — `docker-compose.prod.yml` é *pull only*, sem nenhum `build:`
(o racional está em `docker-compose.prod.yml:4-7`). Imagens vêm do ghcr.

### Como instalo o Runas?

```bash
# 1. Clone o repositório
git clone https://github.com/JonathanRibeiroSilva/RunasERP.git
cd RunasERP

# 2. Configure o ambiente — obrigatório antes de qualquer `up`:
#    o compose lê variáveis SEM valor padrão (DATABASE_URL_GATEWAY etc.)
cp .env.example .env

# 3. Suba os containers (não existe docker-compose.yml na raiz: o -f é obrigatório)
docker compose -f docker-compose.dev.yml up -d

# 4. Migrations e admin: nada a rodar na mão.
#    Cada app roda `alembic upgrade head` no próprio startup (init_db() em
#    <app>/database.py) e o gateway cria o admin no boot (api-gateway/main.py:46
#    chama seed_admin()).
#    Seed de dados de exemplo, se quiser:
#    docker compose -f docker-compose.dev.yml exec <serviço> python seed.py

# 5. Acesse o sistema
# Frontend: http://localhost:3000
# API:      http://localhost:8000  (docs em /docs)
```

> **Não existe Makefile neste repositório** — `make migrate` / `make seed` não
> rodam. O entrypoint é o `erp.ps1` (Windows/PowerShell) ou `docker compose -f`
> direto. Consulte o [Guia de Setup](../../QUICK-START.md).

### Posso instalar sem Docker?

Não é um caminho suportado — não há script nem documentação de instalação
manual no repositório. As versões que as imagens usam, se você insistir:

- Python **3.12** (`FROM python:3.12-slim` no `Dockerfile` do gateway e de cada serviço)
- PostgreSQL **15** (`postgres:15-alpine`) — um banco único, um schema por serviço
- Redis **7** (`redis:7-alpine`)
- RabbitMQ **3.12** (`rabbitmq:3.12-management-alpine`) — sobe, mas nenhum código
  publica evento nele hoje
- Node **22** (`frontend/Dockerfile.dev:4` — `FROM node:22-alpine`). O
  `package.json` não declara `engines`, então a imagem é a única referência.

Evolution API **não** é requisito: o serviço de notificações é casca (só
`/health`) e nada no repositório envia mensagem de WhatsApp.

### Como atualizo o Runas?

Em **produção** a atualização é o deploy, não um `git pull` no servidor: o CI
publica as imagens e o Coolify puxa. O procedimento completo (incluindo o
`pg_dump` que roda antes de migrar e o rollback pelo campo `tag` do `workflow_dispatch`, seção 6) está em
[`docs/06-operacao/deploy.md`](../06-operacao/deploy.md).

Em **desenvolvimento**:

```bash
git pull origin Developer
docker compose -f docker-compose.dev.yml up -d --build
```

As migrations sobem sozinhas no startup de cada serviço. Atenção: uma revisão
que falhe nos dados existentes deixa o container em *crashloop* — o
`init_db()` usa `subprocess.run(..., check=True)` de propósito.

---

## 💼 Funcionalidades

### Posso vender online com o Runas?

Sim! O Runas possui um catálogo público onde clientes podem:
- Visualizar produtos disponíveis
- Adicionar ao carrinho
- Finalizar compra
- Pagar via PIX

### Como funciona o sistema de crédito (fiado)?

Hoje existe o **cadastro**, não o ciclo automático. `services/clientes/models/cliente.py`
tem os campos `limite_credito` (`:39`), `dia_vencimento` (`:41`) e `bloqueado`
(`:42`), e a venda pode ser marcada como fiada.

O que **não** existe: a conta a receber, o cálculo de juros/multa, a cobrança
automática e o bloqueio por atraso. Tudo isso dependeria do serviço `financeiro`,
que é casca — `services/financeiro/main.py:56` expõe só `/health` e
`routers/__init__.py` tem 22 bytes. Está aberto no
[Roadmap](./roadmap.md) como Prioridade 1.

> Não confundir com o corte por inadimplência que **já funciona**: esse é do
> *lojista* com a plataforma (assinatura em atraso → 402 nas escritas), em
> `api-gateway/middleware/inadimplencia_middleware.py`, e não tem relação com o
> fiado do cliente final.

### Posso emitir nota fiscal?

Não no MVP. A emissão de NF-e está planejada para versões futuras. Consulte o [Roadmap](./roadmap.md).

### Como funciona a integração com WhatsApp?

**Não funciona hoje.** Existe a *configuração* por tenant
(`services/vendas/config.py:27-30`, `services/vendas/routers/admin_integracao.py`)
e um schema `evolution` no banco, mas **nenhum código envia mensagem**. O serviço
`notificacoes` é casca: `services/notificacoes/main.py:56` expõe apenas
`/health`, e `routers/`, `services/` e `models/` contêm só a docstring do pacote.

O que **já existe** de notificação é e-mail, e vive no gateway:
`api-gateway/services/email_service.py`.

### Posso usar múltiplas lojas?

**Sim — o Runas é multi-tenant desde já.** Uma instalação atende vários
lojistas:

- serviço `empresas` (porta 8007) com tenants, usuários e assinaturas
- `api-gateway/proxy/service_proxy.py` injeta `X-Empresa-Id` em toda requisição
  proxied, e os serviços exigem o header
- um plano de controle para o dono da plataforma:
  `api-gateway/routers/plataforma.py` + `frontend/src/pages/Plataforma/`
- ver [Plataforma](../03-arquitetura/plataforma.md)

### Como faço backup dos dados?

O banco é **um só** PostgreSQL com um schema por serviço — não há `db-clientes`,
`db-produtos` etc. O dump é do banco inteiro:

```bash
# Desenvolvimento
docker exec erp-db-dev pg_dump -U erp erp > backup.sql
```

Em produção o `pg_dump` roda automaticamente **antes de cada deploy**, no
container `erp-db-backup-prod` (serviço `db-backup` em `docker-compose.prod.yml`).
É *fail-closed*: o `db-init` só sobe se o backup sair 0, e todo serviço espera o
`db-init` — deploy que não consegue backup não migra. Detalhes e restauração em
[`docs/06-operacao/deploy.md`](../06-operacao/deploy.md) e
[`docs/06-operacao/runbook-producao.md`](../06-operacao/runbook-producao.md).

---

## 🔧 Técnico

### Qual linguagem é usada no backend?

Python 3.12+ com FastAPI. Escolhemos Python por:
- Produtividade e legibilidade
- Ecossistema rico de bibliotecas
- Excelente para APIs REST
- Comunidade ativa

### Qual framework é usado no frontend?

**React 19** com TypeScript e Vite (`frontend/package.json`: `react: ^19.3.0`).
UI em Bootstrap 5 + react-bootstrap + Sass — **não** há Tailwind. Estado de
servidor em TanStack React Query 5, formulários em React Hook Form + Zod,
gráficos em Chart.js, testes em Vitest.

### Por que microsserviços?

São **7 microsserviços FastAPI mais o api-gateway** (8 aplicações), cada um com
seu schema no mesmo PostgreSQL. As vantagens de organização por domínio valem;
duas ressalvas honestas sobre esta implementação:

- **Não são independentes no banco**: é um Postgres só, um schema por serviço.
- **Não há isolamento de falha via mensageria**: a comunicação é 100% HTTP
  síncrono via `httpx`. O RabbitMQ sobe e cada serviço tem `events/publisher.py`,
  mas nenhum arquivo importa o publisher — zero chamadas a `publish()`.

### Posso usar outro banco de dados?

O Runas foi projetado para PostgreSQL. Usar outro banco requer:
- Adaptar migrations (Alembic)
- Ajustar queries específicas do PostgreSQL
- Testar extensivamente

Não recomendamos para usuários iniciantes.

### Como adiciono um novo microsserviço?

1. Estrutura de pastas no padrão dos existentes (`router → service → repository → model`)
2. `Dockerfile` (`python:3.12-slim`) e `requirements.txt`
3. Entrada em `docker-compose.dev.yml` e em `docker-compose.prod.yml`
4. Schema novo no `db-init` (`docker-compose.prod.yml` e
   `postgres/init-schemas.sql`) e `version_table_schema` no `alembic/env.py`
5. Todo modelo com `__table_args__ = {"schema": "<nome>"}`
6. Registrar a rota no gateway e a URL do serviço em `api-gateway/config.py`
7. Adicionar o serviço à matriz de testes em `.github/workflows/ci.yml`

Consulte a [Arquitetura](../03-arquitetura/) e o
[CLAUDE.md](../../CLAUDE.md) para detalhes.

### Posso contribuir com código?

Sim! Consulte o [Guia de Contribuição](../../.github/CONTRIBUTING.md).

---

## 🔒 Segurança

### O que já existe de segurança?

No gateway, que é o único caminho público:

- Autenticação JWT + OAuth2 (`api-gateway/auth/jwt.py`)
- Senhas com hash — ver a pergunta abaixo
- Rate limiting (`api-gateway/middleware/rate_limit.py`)
- Auditoria de requisição (`api-gateway/middleware/auditoria_middleware.py`)
- Isolamento por tenant antes de chegar ao serviço (`X-Empresa-Id` injetado em
  `api-gateway/proxy/service_proxy.py`)
- TLS terminado no Cloudflare; a VPS não abre porta de entrada nenhuma
  (`docker-compose.prod.yml:9-10`)
- Pre-commit que barra segredo em linha adicionada
  ([SECURITY_HOOKS](../02-desenvolvimento/SECURITY_HOOKS.md)) — mas **não vem
  instalado no clone**, é passo manual

Limites que você deve conhecer:

- **Nenhum serviço valida JWT.** Todos confiam no `X-Empresa-Id` que o gateway
  injeta. Por isso as portas 8001–8007 estão presas em `127.0.0.1` no
  `docker-compose.dev.yml` — publicá-las na LAN é entregar qualquer tenant a
  qualquer um na rede.
- `SERVICO_INTERNO_TOKEN` e `PLATAFORMA_INTERNO_TOKEN` vêm **vazios** do
  `.env.example` (`:136`, `:142`). Vazio no `SERVICO_INTERNO_TOKEN` é
  *fail-closed* (403 em tudo menos `/health`); vazio no `PLATAFORMA_INTERNO_TOKEN`
  é *fail-open*: loga a ausência e deixa passar.
- **A CONFIRMAR**: não há medição de cobertura de teste publicada nem auditoria
  de segurança externa registrada no repositório.

### Como são armazenadas as senhas?

Com **bcrypt** via passlib, nunca em texto plano:
`CryptContext(schemes=["bcrypt"], deprecated="auto")` em
`api-gateway/repositories/usuario_repository.py:12` (usuários do lojista) e em
`api-gateway/repositories/cliente_auth_repository.py:12` (clientes da loja).

> `bcrypt` está pinado em `4.0.1` de propósito: o passlib 1.7.4 lê
> `bcrypt.__about__`, removido no 4.1, e o backend carrega pela metade — o login
> devolve 500. Não despine um sem o outro (`api-gateway/requirements.txt:4-9`).

### Posso usar autenticação de dois fatores (2FA)?

Não existe hoje. **A CONFIRMAR**: previsão de 2FA — não consta no [Roadmap](./roadmap.md).

### Como reporto uma vulnerabilidade?

**NÃO** abra issues públicas. **A CONFIRMAR**: canal de segurança — `security@denebcorp.com`
não aparece em nenhum outro arquivo do repositório; o contato versionado é
`contato@denebcorp.com` (README e Roadmap).

### Os dados são criptografados?

- **Em trânsito**: Sim, via HTTPS
- **Em repouso**: Depende da configuração do PostgreSQL

Para dados sensíveis, recomendamos:
- Criptografia de disco no servidor
- Backups criptografados
- Acesso restrito ao banco

---

## 📄 Licenciamento

### Qual é a licença do Runas?

O Runas é proprietário da DenebCorp. Consulte o arquivo [LICENSE](../../LICENSE) para detalhes.

### Posso usar comercialmente?

Depende de contrato. O `LICENSE` não concede nenhum direito de uso; quem usa
o Runas sob licença comercial segue o [EULA](../07-legal/EULA-comercial.md).
Licenciamento e permissões: `legal@runas.com` (indicado no `LICENSE`).

### Posso revender o Runas?

Não. Qualquer redistribuição exige autorização prévia por escrito (`LICENSE`;
EULA, seção 2).

### Posso modificar o código?

Não sem permissão. O `LICENSE` exige autorização prévia por escrito para copiar,
modificar ou distribuir, e o EULA (seção 2) proíbe modificar e criar trabalhos
derivados.

### Posso ver o código-fonte?

Só onde o acesso de leitura foi concedido: o `LICENSE` admite acesso para leitura e
avaliação técnica (portfólio, seleção, auditoria, due diligence), e isso não
constitui licença de uso.

---

## 🆘 Suporte

### Onde obtenho ajuda?

- **Documentação**: [docs/](../)
- **GitHub Issues**: [github.com/JonathanRibeiroSilva/RunasERP/issues](https://github.com/JonathanRibeiroSilva/RunasERP/issues)
- **Discord**: A CONFIRMAR (nenhum servidor versionado)
- **Email**: A CONFIRMAR (`support@denebcorp.com` só aparece em docs; o contato versionado é `contato@denebcorp.com`)

### Como reporto um bug?

1. Verifique se já não foi reportado
2. Abra uma issue no GitHub
3. Descreva o problema (não há templates em `.github/ISSUE_TEMPLATE/`)
4. Inclua logs e passos para reproduzir

### Como sugiro uma funcionalidade?

1. Verifique se já não foi sugerida
2. Abra uma issue no GitHub
3. Descreva o caso de uso
4. Explique o problema que resolve

### Existe suporte comercial?

**A CONFIRMAR**: oferta de suporte comercial. O EULA (seção 7) diz que suporte só
existe mediante acordo separado. Contato versionado: `contato@denebcorp.com`.

---

## 📚 Recursos Adicionais

- [Documentação Completa](../)
- [Guia de Setup](../../QUICK-START.md)
- [Arquitetura](../03-arquitetura/)
- [Roadmap](./roadmap.md)
- [Guia de Contribuição](../../.github/CONTRIBUTING.md)

---

## ❓ Sua pergunta não está aqui?

Abra uma issue no GitHub com a tag `question` ou entre em contato:
- **Email**: `contato@denebcorp.com`
- **Discord**: A CONFIRMAR

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
