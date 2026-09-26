# Roadmap - Runas

> **Esta é a única fonte de "o que falta" no projeto.** Qualquer outro documento que
> liste pendências está desatualizado. Todo item aberto abaixo cita a evidência
> (`arquivo:linha`) que prova que ele continua aberto; item sem evidência não entra.

**Última verificação contra o código**: 2026-09-25

---

## 🚨 Aberto — Prioridade 1 (bloqueia o MVP)

### Vendas / PDV — frontend não existe
- **Evidência**: `frontend/src/pages/Vendas/VendasPage.tsx` tem 47 linhas de placeholder ("em breve").
- **Contexto**: o backend está pronto — `services/vendas/routers/` tem `vendas.py`, `loja.py`,
  `admin_pagamento.py`, `admin_entrega.py`, `admin_integracao.py` e `webhook.py`. Falta só a tela.
- Pendências: PDV, lista de vendas, detalhe da venda.

### Financeiro — casca de serviço, sem backend e sem frontend
- **Evidência (backend)**: `services/financeiro/main.py:56` expõe um único endpoint, `@app.get("/health")`.
  `services/financeiro/routers/__init__.py` tem 22 bytes — só a docstring do pacote — e nenhum
  `include_router` é chamado. As pastas `models/` (26 bytes), `repositories/` (19 bytes),
  `services/` (37 bytes) e `schemas/` (23 bytes) estão no mesmo estado: docstring e mais nada.
  O que existe de código real no serviço é infraestrutura compartilhada, não domínio —
  `database.py`, `config.py` e `interno.py` (middleware de origem interna, igual nos 7 serviços).
- **Evidência (frontend)**: `frontend/src/pages/Financeiro/FinanceiroPage.tsx` tem 47 linhas de placeholder.
- Pendências: contas a receber, contas a pagar, pagamentos, cálculo de juros/multa,
  jobs de cobrança, dashboard financeiro, fluxo de caixa.
- **Dependência bloqueada por este item**: a integração Vendas → Financeiro
  (gerar `ContaReceber` para venda FIADO) não tem onde escrever enquanto o serviço for casca.

### Notificações — casca de serviço
- **Evidência**: `services/notificacoes/main.py:56` expõe só `@app.get("/health")`;
  `routers/__init__.py` (22 bytes), `services/__init__.py` (37 bytes) e `models/__init__.py` (26 bytes)
  contêm apenas a docstring do pacote — nenhuma classe, nenhuma função.
- Já existe e **não** é pendência: envio de e-mail, que vive no gateway
  (`api-gateway/services/email_service.py`).
- Pendências: integração WhatsApp via Evolution API, consumidor de eventos,
  deduplicação, retry com backoff, templates de mensagem.
- **Nota**: a configuração de Evolution API já existe do lado de Vendas
  (`services/vendas/config.py:27-30`, `services/vendas/routers/admin_integracao.py:33-36`),
  mas nenhum código envia mensagem — são apenas campos de configuração por tenant.

### Dashboard com dados reais
- **Evidência**: `frontend/src/pages/Dashboard/DashboardPage.tsx:30` abre a seção `// ── MOCK DATA ──`.
  `mockStats` (`:32`, consumido em `:201`), `lineChartData` (`:122`) e `doughnutData` (`:162`) são
  constantes de módulo com números escritos à mão. A página não tem **nenhuma** chamada de API:
  zero ocorrências de `fetch`, `axios`, `useQuery` ou service no arquivo inteiro.
- **Escopo**: os componentes Chart.js estão montados e funcionando — falta ligar a fonte de dados,
  tanto dos cards quanto dos dois gráficos.

---

## ⚠️ Aberto — Prioridade 2 (qualidade e dívida)

### Dívida arquitetural do frontend
Rastreada em `docs/05-frontend/frontend-architectural-debt-log.md`. **Não duplicar aqui** —
o log é a fonte. Itens que valem como marco de roadmap:

| ID | Item | Evidência re-medida hoje |
|----|------|--------------------------|
| C4 | Quebrar o god component `CheckoutPage` | `frontend/src/pages/LojaOnlinePublico/CheckoutPage.tsx` = **1507 linhas** (o log registrou 1.381 — piorou) |
| H5 | Code splitting por rota | `lazy(` em `frontend/src/App.tsx` = 0 ocorrências |
| C6 | Placeholders de módulo | cobre Dashboard, Vendas e Financeiro, já detalhados na Prioridade 1 |

Os demais IDs (C1, C2, C3, C5, H1–H4, H6, H7) seguem no log e valem a revisita —
vários foram parcial ou totalmente resolvidos desde a auditoria; conferir lá antes de agir.

### Página 404 de verdade
- **Evidência**: `frontend/src/App.tsx:244` — `<Route path="*" element={<Navigate to="/dashboard" replace />} />`.
  Qualquer URL errada vira redirecionamento silencioso para o dashboard.

### Cobertura de testes
- **Situação real**: 62 arquivos `test_*.py` versionados, rodando no CI
  (`.github/workflows/ci.yml`, leg `tests/unit` + matriz por serviço) mais a suíte vitest do frontend.
- **Aberto**: não existe medição de cobertura publicada, e não há teste E2E de verdade.
- Meta mantida: 80% de cobertura medida, não estimada.

---

## 📌 Aberto — Prioridade 3 (melhorias de domínio já especificadas)

- **Produtos**: histórico de preços e produtos compostos (kits).
  *Evidência*: nenhum arquivo em `services/produtos/` menciona `HistoricoPreco`, `kit` ou `composto`.
- **Estoque**: FIFO/FEFO.
  *Evidência*: nenhuma ocorrência de `fifo`/`fefo` em `services/estoque/`. (Lote `VENCIDO` sair do
  estoque é intencional — é o descarte, `services/estoque/services/estoque_service.py:324-327` —
  então "bloqueio de lote vencido" não é pendência.)
- **Estoque**: inventário. *Evidência*: o modelo `Inventario` existe (`services/estoque/models/estoque.py:222`)
  e o `InventarioRepository` (`repositories/estoque_repository.py:523`), mas nenhuma rota de
  `services/estoque/routers/` o referencia, `estoque_service.py:34` só o importa e não há tela no frontend.
- **Estoque**: alertas *automáticos* (push) de estoque mínimo e de lote vencendo. Hoje só há alerta sob
  consulta (`GET /baixo` e `GET /lotes/vencendo`, `services/estoque/routers/estoque.py:78` e `:314`); o campo
  `estoque_minimo` está em `models/estoque.py:70`. O disparo depende do serviço de Notificações acima.
- **Vendas**: devolução como entidade própria.
  *Evidência*: nenhuma ocorrência de `devolucao` em `services/vendas/models/`.
  (O *tipo* de movimentação "devolução" já existe no Estoque; falta o fluxo de venda.)
- **Clientes**: histórico de compras na tela do cliente.
  *Evidência*: o único histórico em `frontend/src/pages/Clientes/` é o de crédito
  (`ClienteCreditoPage.tsx:37`); nenhuma ocorrência de histórico de compras em `services/clientes/routers/`.

---

## ✅ Entregue (não é mais roadmap)

Registrado aqui só para impedir que volte à lista de pendências:

- **Estoque, ponta a ponta** — `frontend/src/pages/Estoque/EstoquePage.tsx` (336 linhas),
  `EstoqueDetalhePage.tsx`, `hooks/useEstoque.ts`, backend com movimentações, lotes,
  reserva (`POST /reservar`) e integração com Vendas.
- **Loja Online completa** — `frontend/src/pages/LojaOnlinePublico/` com vitrine, detalhe,
  `CarrinhoPage`, `CheckoutPage`, `ClienteLoginPage`, `ClientePerfilPage`, `MeusPedidosPage`
  e `RastreamentoPedidoPage`; backend em `services/vendas/routers/loja.py` (25 KB).
- **Plataforma (plano de controle SaaS)** — `frontend/src/pages/Plataforma/{PlataformaPage.tsx, TenantDetalhe.tsx}`,
  `api-gateway/routers/plataforma.py`, `services/empresas/`.
- **Configurações** — `frontend/src/pages/Configuracoes/{EmpresaPage, IntegracoesPage, UsuariosPage}.tsx`.
- **Mercado Pago (PIX)** — `services/vendas/routers/admin_pagamento.py` e `webhook.py`.
- **ViaCEP no backend** — `services/vendas/services/entrega_service.py:27` e `:49` validam CEP
  pela API. *(Constava como "backend pendente"; não procede mais.)*
- **Multi-tenancy** por `empresa_id` nos serviços e soft delete em Clientes
  (`services/clientes/repositories/cliente_repository.py:150`, `ativo = False`) e Produtos
  (`services/produtos/models/produto.py:83`, `deletado_em`). **A CONFIRMAR**: soft delete em Estoque e Vendas.
- **CI/CD e operação** — 5 workflows em `.github/workflows/` (ci, deploy, uptime, landing,
  graphify-update), deploy via Coolify, Cloudflare Tunnel, backup `pg_dump` antes de cada deploy
  e readiness profundo em `/health/ready` (`api-gateway/main.py`).
- **Autenticação** — JWT, OAuth2 (Google, Microsoft), recuperação de senha, rate limiting,
  idempotência centralizada no gateway (`api-gateway/proxy/idempotency.py`).

---

## 🔮 Pós-MVP (sem data, sem compromisso)

Nada abaixo tem escopo fechado nem foi iniciado. É intenção de produto, não backlog.

**UX**: onboarding interativo, tutoriais in-app, atalhos de teclado, PWA offline.
**Funcionalidades**: relatórios avançados, exportação PDF/Excel, importação em lote,
tags personalizadas, anexos, auditoria de ações.
**Integrações**: NF-e, marketplaces, API pública para terceiros, Correios (frete).
**Novos módulos**: Compras, Produção, RH, CRM avançado, Marketing.
**Internacionalização**: múltiplos idiomas, moedas e fusos.
**Mobile**: apps nativos com sincronização offline.
**Escala**: Kubernetes, event sourcing, CQRS — hoje a comunicação entre serviços é
100% HTTP síncrono via `httpx`. A mensageria está **escrita mas desligada**: os 7 serviços têm
`events/publisher.py` com a classe `EventPublisher` (conecta no RabbitMQ, declara o exchange
tópico `erp.events`) e `aio-pika==10.0.1` + `celery==5.6.3` nos `requirements.txt`, mas nenhum
arquivo importa o publisher — zero chamadas a `publish()` em todo o repositório. Ligar isso é
trabalho de integração, não de implementação do zero.

---

## 🔄 Como manter este arquivo honesto

1. Item só entra em "Aberto" com `arquivo:linha` que prove que está aberto.
2. Item concluído **sai** da lista de aberto e ganha uma linha em "Entregue" com o arquivo que o prova.
3. Sem percentuais de progresso. Percentual não é verificável; arquivo é.
4. Dívida de frontend mora em `docs/05-frontend/frontend-architectural-debt-log.md` —
   aqui só se referencia por ID.

---

**Projeto**: Runas · **Equipe**: DenebCorp · **Contato**: contato@denebcorp.com
