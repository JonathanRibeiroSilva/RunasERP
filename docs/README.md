# Documentação — Runas ERP

Índice da documentação. 67 arquivos em `docs/` (66 `.md` + `openapi.yaml`),
organizados em nove pastas numeradas — a taxonomia está em
[.docs-policy.md](./.docs-policy.md).

> **Novo nesta árvore:** [06. Operação](#06-operação) (runbook de produção e deploy),
> [07. Legal](#07-legal), [plano de controle da plataforma](./03-arquitetura/plataforma.md)
> e [API da Plataforma](./10-api-reference/plataforma-api.md).

---

## Comece por aqui

| Quero… | Abra |
|--------|------|
| entender o produto | [O SISTEMA.md](../O%20SISTEMA.md) · [Visão Geral](./01-visao-geral/README.md) |
| subir o ambiente local | [QUICK-START.md](../QUICK-START.md) |
| entender a arquitetura | [03-arquitetura/visao-geral.md](./03-arquitetura/visao-geral.md) |
| consumir a API | [10-api-reference/README.md](./10-api-reference/README.md) |
| resolver um problema | [06-operacao/troubleshooting.md](./06-operacao/troubleshooting.md) |
| operar produção | [06-operacao/runbook-producao.md](./06-operacao/runbook-producao.md) |
| contribuir | [.github/CONTRIBUTING.md](../.github/CONTRIBUTING.md) |

---

## 01. Visão Geral

- [Sobre o projeto](./01-visao-geral/README.md)
- [FAQ](./01-visao-geral/faq.md)
- [Glossário](./01-visao-geral/glossario.md)
- [Roadmap](./01-visao-geral/roadmap.md)

## 02. Desenvolvimento

- [Índice de desenvolvimento](./02-desenvolvimento/README.md)
- [Checklist de desenvolvimento](./02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md)
- [Máscaras e validações](./02-desenvolvimento/GUIA_MASCARAS_VALIDACOES.md)
- [OAuth — fluxo completo](./02-desenvolvimento/OAUTH_FLUXO_COMPLETO.md)
- [OAuth — configuração dos provedores](./02-desenvolvimento/OAUTH_PROVIDERS_CONFIG.md)
- [Security hooks (prevenção de vazamento de secrets)](./02-desenvolvimento/SECURITY_HOOKS.md)
- [Graphify — setup](./02-desenvolvimento/GRAPHIFY_SETUP.md) · [Graphify — workflow](./02-desenvolvimento/GRAPHIFY_WORKFLOW.md)

## 03. Arquitetura

- [Índice de arquitetura](./03-arquitetura/README.md)
- [Visão geral da arquitetura](./03-arquitetura/visao-geral.md)
- [Detalhamento dos microsserviços](./03-arquitetura/microsservicos.md)
- [Comunicação entre serviços](./03-arquitetura/comunicacao.md)
- [Plano de controle da plataforma (SaaS)](./03-arquitetura/plataforma.md) — novo
- [Persistência e durabilidade dos dados](./03-arquitetura/persistencia-e-durabilidade.md)
- [Performance e consumo de CPU](./03-arquitetura/performance-cpu.md)

## 04. Backend

- [Índice de backend](./04-backend/README.md)
- [Transações de banco de dados](./04-backend/transacoes-banco-dados.md)
- [Integração: Evolution API (WhatsApp)](./04-backend/integracao/evolution-api.md)

## 05. Frontend

- [Índice de frontend](./05-frontend/README.md)
- [Estado atual (factual)](./05-frontend/frontend-current-state.md)
- [Log de dívida arquitetural](./05-frontend/frontend-architectural-debt-log.md)
- Setup: [pré-requisitos](./05-frontend/setup/prerequisites.md) · [Docker](./05-frontend/setup/docker.md) · [Docker quick start](./05-frontend/setup/docker-quick-start.md)
- Design system: [design](./05-frontend/design/design.md) · [componentes](./05-frontend/design/componentes.md) · [cores e tipografia](./05-frontend/design/cores-tipografia.md) · [layouts](./05-frontend/design/layouts.md)
- [Guia: API pelo cliente Axios](./05-frontend/guias/api-examples.md)
- [Resumo da implementação OAuth](./05-frontend/oauth/oauth-summary.md)
- [Feature: interface de categorias](./05-frontend/features/categorias.md)
- [Checklist de produção](./05-frontend/deployment/production-checklist.md)
- Planos em execução (`status: active` — não editar): [fase 1](./05-frontend/plans/frontend-phase-1-stability.md) · [fase 2](./05-frontend/plans/frontend-phase-2-architecture.md) · [fase 3](./05-frontend/plans/frontend-phase-3-consolidation.md) · [fase 4](./05-frontend/plans/frontend-phase-4-completion.md)
- Auditoria: [AUD-2026-06-29](./05-frontend/audits/AUD-2026-06-29.md)

## 06. Operação

Novo. O que se faz com o sistema já de pé.

- [Runbook de produção](./06-operacao/runbook-producao.md) — novo
- [Deploy — como funciona](./06-operacao/deploy.md) — novo
- [Troubleshooting](./06-operacao/troubleshooting.md)
- [Configuração do Mercado Pago](./06-operacao/CONFIGURACAO_MERCADO_PAGO.md)
- [PIX no Mercado Pago sandbox](./06-operacao/MERCADOPAGO_PIX_SANDBOX.md)
- [Seed de dados completo](./06-operacao/SEED_DATA_COMPLETO.md)

## 07. Legal

Novo. Documentos jurídicos do produto — a licença do código fica em [../LICENSE](../LICENSE).

- [EULA comercial](./07-legal/EULA-comercial.md)

## 10. Referência de APIs

- [Índice das APIs](./10-api-reference/README.md)
- [Mapeamento de rotas](./10-api-reference/mapeamento-rotas.md)
- [Guia de autenticação](./10-api-reference/guia-autenticacao.md)
- [Exemplos práticos](./10-api-reference/exemplos-praticos.md)
- Por domínio: [clientes](./10-api-reference/clientes-api.md) · [produtos](./10-api-reference/produtos-api.md) · [estoque](./10-api-reference/estoque-api.md) · [vendas](./10-api-reference/vendas-api.md) · [financeiro](./10-api-reference/financeiro-api.md)
- [API da Plataforma](./10-api-reference/plataforma-api.md) — novo
- [Especificação OpenAPI](./10-api-reference/openapi.yaml)

## 11. Regras de Negócio

- [Índice das regras](./11-regras-negocio/README.md)
- [Clientes](./11-regras-negocio/clientes.md) · [Produtos](./11-regras-negocio/produtos.md) · [Estoque](./11-regras-negocio/estoque.md) · [Vendas](./11-regras-negocio/vendas.md) · [Financeiro](./11-regras-negocio/financeiro.md)

> `08` e `09` não existem: são números reservados. Motivo do salto de `07` para
> `10` em [.docs-policy.md](./.docs-policy.md).

---

## Estrutura do repositório

```
RunasERP/
├── api-gateway/        # API Gateway (FastAPI)
├── services/           # 7 microsserviços FastAPI
│   ├── clientes/
│   ├── empresas/
│   ├── estoque/
│   ├── financeiro/
│   ├── notificacoes/
│   ├── produtos/
│   └── vendas/
├── frontend/           # React 19 + TypeScript + Vite
├── landing-page/
├── shared/             # código compartilhado
├── postgres/ pgadmin/  # configuração dos containers de banco
├── scripts/
├── tests/
└── docs/               # você está aqui
```

## Histórico de mudanças

Não há changelog escrito à mão — `git log` é a fonte da verdade
([política](./.docs-policy.md)):

```bash
git log --oneline --graph --all
git log --oneline -20   # o repositório não tem tags de versão
```

## Links úteis

- [README do repositório](../README.md)
- [O SISTEMA](../O%20SISTEMA.md)
- [QUICK-START](../QUICK-START.md)
- [FRONTEND_IMPLEMENTACAO](../FRONTEND_IMPLEMENTACAO.md)
- [Como contribuir](../.github/CONTRIBUTING.md)
- [Licença](../LICENSE)
- [Política de documentação](./.docs-policy.md)
