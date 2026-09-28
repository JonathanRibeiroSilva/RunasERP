# Frontend Runas ERP - Estado Atual

> Retrato do que está implementado em `frontend/` e do que ainda falta.
> Todo dado abaixo foi lido do código; nada aqui é estimativa de progresso.

**Última verificação**: 25/09/2026 (contra a branch `feat/g1b-plataforma-com-prova`); módulo Plataforma, testes e `config/` re-verificados em 28/09/2026 contra o `Developer` (PR #113)

---

## Visão geral por módulo

| Módulo | Estado | Onde está |
|--------|--------|-----------|
| Autenticação | Entregue | `pages/Login/`, `pages/Auth/` (forgot/reset, callbacks Google e Microsoft), `hooks/useAuth.ts` |
| Clientes | Entregue | `pages/Clientes/` (lista, formulário, endereços, crédito), `hooks/useClientes.ts`, `services/api/clientesApi.ts` |
| Produtos | Entregue | `pages/Produtos/` (lista, formulário, detalhes, variantes, categorias), `hooks/useProdutos.ts`, `services/api/produtosApi.ts` |
| Estoque | Entregue | `pages/Estoque/` (`EstoquePage.tsx` 336 linhas, `EstoqueDetalhePage.tsx` 239 linhas, 4 componentes), `hooks/useEstoque.ts`, `services/api/estoqueApi.ts` |
| Loja Online (vitrine pública) | Entregue | `pages/LojaOnlinePublico/` (8 páginas), `hooks/useCarrinho.ts`, `services/api/apiPublica.ts` |
| Loja Online (administração) | Parcial | `pages/LojaOnline/ConfiguracoesLojaPage.tsx` entregue; `PedidosOnlinePage.tsx` é placeholder "em breve" |
| Plataforma (SUPER_ADMIN) | Entregue | `pages/Plataforma/` (`PlataformaDashboard.tsx` 105 linhas, `PlataformaPage.tsx` 396 linhas, `TenantDetalhe.tsx` 327 linhas), `config/host.ts`, `hooks/usePlataforma.ts`, `services/api/plataformaApi.ts` |
| Configurações | Entregue | `pages/Configuracoes/` (`EmpresaPage.tsx` 305, `IntegracoesPage.tsx` 322, `UsuariosPage.tsx` 273 linhas) |
| Perfil | Entregue | `pages/Perfil/PerfilPage.tsx` |
| Dashboard | Só interface | `pages/Dashboard/DashboardPage.tsx` (326 linhas) - gráficos Chart.js reais alimentados por dados fixos no próprio arquivo |
| Vendas / PDV | Não iniciado | `pages/Vendas/VendasPage.tsx` = 47 linhas de tela "em breve" |
| Financeiro | Não iniciado | `pages/Financeiro/FinanceiroPage.tsx` = 47 linhas de tela "em breve" |

---

## O que ainda falta

### 1. Vendas / PDV (não iniciado no frontend)

`pages/Vendas/VendasPage.tsx` tem 47 linhas: cabeçalho, ícone e três cards de "em desenvolvimento".
A rota `vendas` existe em `App.tsx` protegida por `RoleProtectedRoute requiredRole={['ADMIN', 'OPERADOR']}`.
`components/vendas/` existe mas está vazio.

O backend de vendas já responde; o frontend não consome nada dele.

**A CONFIRMAR**: quais rotas de `services/vendas` estão publicadas pelo api-gateway para uso administrativo (fora do prefixo `/loja`). Este documento não as lista porque não foram verificadas nesta revisão.

### 2. Financeiro (não iniciado no frontend)

`pages/Financeiro/FinanceiroPage.tsx` tem 47 linhas, mesmo padrão de tela "em breve".
Rota `financeiro` em `App.tsx`, restrita a `ADMIN`. `components/financeiro/` está vazio.

**A CONFIRMAR**: quais endpoints o `services/financeiro` expõe hoje. O documento anterior afirmava `GET /api/financeiro/contas-receber`, `/contas-pagar` e `POST /api/financeiro/baixa` sem evidência; as rotas foram removidas daqui até serem lidas do router.

### 3. Dashboard com dados fixos

`DashboardPage.tsx` não importa nenhum cliente HTTP. Os quatro indicadores (`mockStats`), a lista `vendasRecentes` e `topProdutos` são arrays literais declarados no arquivo, sob o comentário `// ── MOCK DATA ──`. Os gráficos (`react-chartjs-2`, `Line` e `Doughnut`) são reais, mas leem esses mesmos arrays.

Substituir por chamadas reais é trabalho pendente.

### 4. Pedidos Online (administração)

`pages/LojaOnline/PedidosOnlinePage.tsx` é um empty state de 24 linhas. O fluxo de compra do cliente final funciona ponta a ponta; falta a tela do lojista para acompanhar esses pedidos.

---

## Módulo Plataforma (SUPER_ADMIN)

Painel multi-tenant, ausente das versões anteriores deste documento.

- `pages/Plataforma/PlataformaDashboard.tsx` (105 linhas) - rota `/plataforma`, visão geral: cartões de lojistas, receita mensal (só assinaturas `ATIVA`), a cobrar e sem assinatura, calculados por `resumirTenants` sobre a mesma lista de `GET /plataforma/tenants` (sem endpoint próprio).
- `pages/Plataforma/PlataformaPage.tsx` (396 linhas) - rota `/plataforma/tenants`, lista de lojistas: criação (provisionar), suspensão/reativação, troca de plano, auditoria, dumps e assinatura (cobrança).
- `pages/Plataforma/TenantDetalhe.tsx` (327 linhas) - painel de detalhe de um tenant, renderizado dentro da `PlataformaPage` (não é rota própria).
- `hooks/usePlataforma.ts` e `services/api/plataformaApi.ts`.
- Rotas `plataforma` e `plataforma/tenants` em `App.tsx`, ambas protegidas por `RoleProtectedRoute requiredRole={['SUPER_ADMIN']}` e **registradas só no host do painel** (`ehPainelPlataforma || !separarPorHost`): no host do lojista elas não existem e caem no catch-all, e o `frontend/nginx.conf` devolve 404 em `/plataforma` para host que não comece com `admin.` (commit `045c0c0`). As duas páginas são carregadas com `lazy()` (chunks próprios), dentro de um `Suspense` que envolve as rotas.
- No `Sidebar`, "Plataforma" é um submenu com "Visão Geral" (`/plataforma`, com `end`, para não ficar ativo junto com `/plataforma/tenants`) e "Lojistas" (`/plataforma/tenants`); os subitens repetem `requiredRole: ['SUPER_ADMIN']` porque `podeVer()` trata item sem lista como item de tenant.

**Separação por host** (`config/host.ts`, só no frontend): o mesmo bundle serve o ERP dos lojistas e o painel da plataforma. `ehPainelPlataforma` é verdadeiro quando o primeiro label de `window.location.hostname` é `VITE_HOST_PLATAFORMA` (padrão `admin`). Em dev (`import.meta.env.DEV`) a separação só vale se o host já for o do painel, então as duas aplicações convivem em `localhost` e `admin.localhost:3000` exercita o caminho de produção.

**Guard global** em `App.tsx` (dentro de `ProtectedRoute`), decidido pela função pura `escolherPorta()` (testada em `config/__tests__/host.test.ts`):

- com separação ativa, SUPER_ADMIN fora do host do painel, ou qualquer outro papel no host do painel, recebe a tela `PortaErrada` ("Endereço errado", com botão Sair; no host do lojista o texto não nomeia o painel nem o endereço dele) - uma tela e não um redirect, porque o cookie de sessão é host-only e não iria junto para o outro host;
- SUPER_ADMIN em caminho que não comece por `/plataforma` nem `/perfil` é redirecionado para `/plataforma` (SUPER_ADMIN não tem `empresa_id`, então qualquer tela de tenant consultaria uma empresa inexistente);
- os demais papéis em `/plataforma*` são redirecionados para `/dashboard` (na prática só em dev, em `localhost`: em produção essas rotas não existem no host do lojista);
- `/perfil` vale nos dois lados.

Uma porta só, em vez de um guard por rota - tela nova nasce fechada para quem não é daquele host.

O backend não muda com isso: `/api` é relativo (same-origin nos dois hosts) e `/api/plataforma/*` responde em qualquer host, protegido só por `require_super_admin`. A separação é da interface, não do servidor. Está em produção desde 2026-09-28: o PR #113 chegou à `main` pelo PR #114 (merge `1df3a0f`) e o deploy desse push terminou com sucesso. O hostname `admin.runaserp.com.br` e o Cloudflare Access na frente dele estão configurados fora do repositório (túnel e painel da Cloudflare), segundo verificação de 2026-09-28.

Rotas consumidas por `plataformaApi` (base `VITE_API_URL`, por padrão `/api`):

| Método | Rota |
|--------|------|
| GET | `/plataforma/tenants` |
| POST | `/plataforma/tenants` |
| PATCH | `/plataforma/tenants/{id}/suspender` e `/reativar` |
| PATCH | `/plataforma/tenants/{id}/plano` |
| GET | `/plataforma/tenants/{id}/auditoria` |
| POST | `/plataforma/auditoria/{registro_id}/reverter` |
| GET | `/plataforma/tenants/{id}/dumps` |
| POST | `/plataforma/tenants/{id}/assinatura` |
| DELETE | `/plataforma/tenants/{id}/assinatura` |
| GET | `/plataforma/tenants/{id}/exportar` (download direto, fora do axios) |

Detalhes de arquitetura: [docs/03-arquitetura/plataforma.md](./docs/03-arquitetura/plataforma.md) e [docs/10-api-reference/plataforma-api.md](./docs/10-api-reference/plataforma-api.md).

---

## Loja Online - fluxo completo

Todo o fluxo público está implementado, do catálogo ao rastreamento.

**Páginas** (`pages/LojaOnlinePublico/`): `LojaOnlinePublicoPage`, `ProdutoDetalhePage`, `CarrinhoPage`, `CheckoutPage`, `ClienteLoginPage`, `ClientePerfilPage`, `MeusPedidosPage`, `RastreamentoPedidoPage`.

**Rotas do React Router** (`App.tsx`, públicas): `/c/:empresaSlug`, `/c/:empresaSlug/login`, `/c/:empresaSlug/produto/:produtoId`, `/c/:empresaSlug/carrinho`, `/c/:empresaSlug/checkout`, `/c/:empresaSlug/pedido/:numeroPedido`, `/c/:empresaSlug/minha-conta/pedidos`, `/c/:empresaSlug/minha-conta/perfil`.

**Backend**: `services/vendas/routers/loja.py` (752 linhas, prefixo `/loja`) e `services/vendas/services/carrinho_service.py` (437 linhas). Endpoints existentes:

| Método | Rota | Consumido por |
|--------|------|---------------|
| GET | `/loja/carrinho` | `hooks/useCarrinho.ts` |
| POST | `/loja/carrinho/itens` | `hooks/useCarrinho.ts` |
| PUT | `/loja/carrinho/itens/{produto_id}` | `hooks/useCarrinho.ts` |
| DELETE | `/loja/carrinho/itens/{produto_id}` | `hooks/useCarrinho.ts` |
| DELETE | `/loja/carrinho` | `hooks/useCarrinho.ts` |
| POST | `/loja/checkout` | `CheckoutPage.tsx` |
| GET | `/loja/meus-pedidos` | `MeusPedidosPage.tsx` |
| GET | `/loja/rastrear/{numero_venda}` | `RastreamentoPedidoPage.tsx` |
| POST | `/loja/pedidos/{numero_venda}/retry-payment` | `MeusPedidosPage.tsx` |
| POST | `/loja/pedidos/{numero_venda}/recuperar-carrinho` | `MeusPedidosPage.tsx` |

O carrinho é mantido por cookie de sessão no backend (`CART_COOKIE_MAX_AGE = 604800`, 7 dias), não por `localStorage`.

A administração da loja (`services/api/lojaOnlineApi.ts`) usa outro prefixo: `GET /loja-online/produtos` e `PUT /loja-online/produtos/{id}/publicar`.

---

## Estoque - entregue

- `pages/Estoque/EstoquePage.tsx` (336 linhas) e `EstoqueDetalhePage.tsx` (239 linhas).
- Componentes: `EstoqueOperacaoModal`, `EstoqueStatusBadge`, `MovimentacaoBadge`, `MovimentacaoTimeline`.
- `hooks/useEstoque.ts` expõe `useEstoques`, `useEstoque`, `useRelatorioEstoque`, `useMovimentacoes`, `useLotes` e as mutations `useEntradaEstoque`, `useSaidaEstoque`, `useAjusteEstoque`, `useReservarEstoque`, `useLiberarReserva`.
- `services/api/estoqueApi.ts` consome `/estoque` (GET e POST), `/estoque/{id}` (GET e PUT), `/estoque/relatorios/geral`, `/estoque/{id}/movimentacoes`, `/estoque/{id}/lotes`, `/estoque/disponibilidade`, `/estoque/entrada`, `/estoque/saida`, `/estoque/ajuste`, `/estoque/reservar`, `/estoque/liberar-reserva`.
- Rotas `estoque` e `estoque/:id` em `App.tsx`, restritas a `ADMIN` e `OPERADOR`.

Não existe tela de inventário físico (contagem) no frontend.

---

## Testes

Existe suíte Vitest configurada: `frontend/vitest.config.ts` e 10 arquivos de teste.

```
src/components/layout/Sidebar/__tests__/podeVer.test.ts
src/config/__tests__/host.test.ts
src/pages/Configuracoes/__tests__/empresaSchema.test.ts
src/pages/Configuracoes/__tests__/integracoesSchema.test.ts
src/pages/Configuracoes/__tests__/usuarioSchema.test.ts
src/pages/Plataforma/__tests__/assinaturaSchema.test.ts
src/pages/Plataforma/__tests__/resumirTenants.test.ts
src/pages/Plataforma/__tests__/tenantSchema.test.ts
src/services/api/__tests__/axios.test.ts
src/utils/__tests__/errorLogger.test.ts
```

A cobertura concentra-se em schemas Zod, no interceptador axios e em funções puras. Páginas e hooks ainda não têm testes de renderização.

---

## Stack (lida de `frontend/package.json`)

**Runtime**

- React `^19.3.0` e React DOM `^19.3.0` - https://react.dev
- React Router DOM `^7.18.4` - https://reactrouter.com
- TanStack Query `^5.103.2` - https://tanstack.com/query
- React Bootstrap `^2.9.1` + Bootstrap `^5.3.2`
- React Hook Form `^7.88.0` + `@hookform/resolvers` `^5.9.1`
- Zod `^4.6.5`
- Axios `^1.20.0`
- Chart.js `^4.4.1` + react-chartjs-2 `^5.2.0`
- date-fns `^4.4.0`, react-icons `^5.7.0`, react-toastify `^11.1.0`, react-loading-skeleton `^3.3.1`, sass `^1.105.0`

**Desenvolvimento**

- Vite `^8.3.1` - https://vite.dev
- TypeScript `^5.2.2`
- Vitest `^5.0.1` + jsdom `^30.1.1` + Testing Library (`react` `^16.3.3`, `jest-dom` `^7.0.1`, `user-event` `^14.6.7`, `dom` `^10.4.2`)
- ESLint `^10.11.0` + typescript-eslint `~8.70.1`, Prettier `^3.9.9`

---

## Estrutura de pastas real

```
frontend/src/
├── pages/            Auth, Clientes, Configuracoes, Dashboard, Estoque, Financeiro,
│                     Login, LojaOnline, LojaOnlinePublico, Perfil, Plataforma,
│                     Produtos, Vendas
├── components/
│   ├── common/       ErrorBoundary, MaskedInput, Modal, ResponsiveCard,
│   │                 ResponsiveContainer, ResponsiveTable, RoleProtectedRoute.tsx
│   ├── layout/       MainLayout, Navbar, Sidebar
│   └── clientes/ estoque/ financeiro/ produtos/ vendas/   (diretórios vazios)
├── hooks/            useAuth, useCarrinho, useClientes, useEmpresa, useEstoque,
│                     useIntegracoes, useLojaOnline, usePlataforma, useProdutos,
│                     useUsuarios
├── services/api/     axios, apiPublica, clientesApi, empresaApi, estoqueApi,
│                     integracoesApi, lojaOnlineApi, plataformaApi, produtosApi,
│                     usuariosApi
├── utils/            masks, validators, toast, errorLogger
├── types/
└── config/           env.ts, host.ts (separação painel/lojista por hostname)
```

Componentes de módulo ficam ao lado da página que os usa (ex.: `pages/Estoque/components/`); os diretórios em `components/<modulo>/` estão vazios e não representam nada implementado.

Schemas de validação ficam junto da página (`pages/Configuracoes/empresaSchema.ts`, `pages/Plataforma/tenantSchema.ts`), com teste próprio em `__tests__/`.

---

## Utilitários existentes

- `utils/masks.ts` - `maskCPF`, `maskCNPJ`, `maskPhone`, `maskCEP`, `maskCurrency`, `maskDate`, `maskCreditCard`, `unmask`, `unmaskCurrency`.
- `utils/validators.ts` - `validateCPF`, `validateCNPJ`, `validateEmail`, `validatePhone`, `validateCEP`, `validatePassword`, `validateDate`, `validateRequired`, `validateMinLength`, `validateMaxLength`.
- `utils/toast.ts` - wrapper `Toast` sobre react-toastify.
- `utils/errorLogger.ts` - coberto por `utils/__tests__/errorLogger.test.ts`.
- `services/api/axios.ts` - instância configurada, `getErrorMessage`, `getErrorStatus`; coberto por `services/api/__tests__/axios.test.ts`.

Não existem `components/common/DataTable.tsx`, `components/forms/FormField.tsx`, `components/common/StatusBadge.tsx` nem `utils/date.ts` / `utils/errors.ts`. Versões anteriores deste documento os descreviam como se existissem.

---

## Como rodar

```powershell
git clone https://github.com/JonathanRibeiroSilva/RunasERP.git
cd RunasERP/frontend

npm install
cp .env.example .env
npm run dev
```

`VITE_API_URL` tem `/api` como padrão (Cloudflare faz proxy). Para backend local direto, use `http://localhost:8000`.

### Scripts disponíveis (`frontend/package.json`)

| Script | O que faz |
|--------|-----------|
| `npm run dev` | `vite` |
| `npm run build` | `tsc && vite build` (a checagem de tipos acontece aqui) |
| `npm run preview` | `vite preview` |
| `npm run lint` | `eslint . --report-unused-disable-directives --max-warnings 115` |
| `npm run format` | `prettier --write "src/**/*.{ts,tsx,css,scss}"` |
| `npm test` | `vitest` |
| `npm run test:coverage` | `vitest --coverage` |
| `npm run test:watch` | `vitest --watch` |

Não existe `npm run type-check` nem `npm run test:e2e`. Para verificar tipos, rode `npm run build`.

---

## Referências

- [docs/05-frontend/README.md](./docs/05-frontend/README.md) - arquitetura do frontend
- [docs/05-frontend/frontend-current-state.md](./docs/05-frontend/frontend-current-state.md) - estado detalhado
- [docs/05-frontend/frontend-architectural-debt-log.md](./docs/05-frontend/frontend-architectural-debt-log.md) - dívida arquitetural registrada
- [docs/05-frontend/design/design.md](./docs/05-frontend/design/design.md) - padrões visuais
- [docs/05-frontend/design/componentes.md](./docs/05-frontend/design/componentes.md) - biblioteca de componentes
- [docs/10-api-reference/README.md](./docs/10-api-reference/README.md) - endpoints
- [docs/01-visao-geral/roadmap.md](./docs/01-visao-geral/roadmap.md) - planejamento geral
- [docs/02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md](./docs/02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md) - checklist de desenvolvimento
- [.github/CONTRIBUTING.md](./.github/CONTRIBUTING.md) - convenções de commit e PR

## Problemas comuns

- **API não responde**: verificar se o backend está de pé (`docker compose -f docker-compose.dev.yml ps` - não existe `docker-compose.yml` sem sufixo na raiz).
- **CORS**: configuração fica no api-gateway.
- **401 Unauthorized**: token JWT expirado, fazer login novamente.
- **Build error**: rodar `npm install` novamente.
