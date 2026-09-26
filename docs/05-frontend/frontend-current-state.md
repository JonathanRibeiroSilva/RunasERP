---
id: ARCH-frontend-current-state
type: architecture
domain: frontend
status: active
source: AUD-2026-06-29-frontend
---

# Frontend — Estado Atual (factual)

Características factuais do frontend, medidas diretamente em `frontend/src` em 2026-09-24. Sem redesenho, sem recomendações.

> Este documento substitui a versão anterior, que descrevia o estado do AUD-2026-06-29 e ficou desatualizada: a camada de serviços, os hooks React Query e o ErrorBoundary foram implementados depois da auditoria. Os 4 planos em `plans/` e o audit em `audits/` continuam apontando para o estado original — leia-os como histórico, não como retrato de hoje.

**Formato atual:** `App.tsx` (tabela de rotas estática, sem `React.lazy`/`Suspense`) → componentes de página → hooks React Query (`hooks/use*.ts`) → serviços de domínio (`services/api/*Api.ts`) → Axios. `AuthContext` guarda o estado global de autenticação. O fluxo Componente → hook React Query → serviço de API → Axios **existe** para clientes, empresa, estoque, integrações, loja online, plataforma, produtos e usuários; as páginas da loja pública ainda não seguem esse caminho.

Total medido: 15.340 LOC em `.ts`/`.tsx` fora de `__tests__/`.

## Clientes HTTP

- `axios.create` aparece em **3 lugares**:
  - `services/api/axios.ts:17` — cliente canônico `api`, `baseURL: env.apiUrl`, com interceptors de request/response, retry de janela de deploy (502/503/504) e chave de idempotência nas escritas.
  - `services/api/apiPublica.ts:10` — cliente público do storefront, `baseURL: '/api'`, `withCredentials: true`, sem interceptors. O comentário em `apiPublica.ts:7` registra que essa é a fonte única que substituiu as 11 cópias espalhadas pelas páginas da loja.
  - `pages/LojaOnlinePublico/CheckoutPage.tsx:14` — **cópia remanescente**, idêntica em configuração à `apiPublica`, mas com um interceptor de response próprio (`CheckoutPage.tsx:22`) para `ECONNABORTED` e falha de conexão. É a única duplicação que sobrou.

## Uso de React Query

- `useQuery`/`useMutation`/`useQueryClient` aparecem em **12 arquivos**:
  - 8 hooks de domínio: `hooks/useClientes.ts`, `useEmpresa.ts`, `useEstoque.ts`, `useIntegracoes.ts`, `useLojaOnline.ts`, `usePlataforma.ts`, `useProdutos.ts`, `useUsuarios.ts`.
  - 4 páginas que consomem esses hooks e também mutam cache direto: `pages/Clientes/ClienteFormPage.tsx`, `pages/Produtos/CategoriasPage.tsx`, `pages/Produtos/ProdutoDetalhesPage.tsx`, `pages/Produtos/ProdutoFormPage.tsx`.
- O `QueryClient` é configurado em `main.tsx:16-25` (`staleTime` 5 min, `gcTime` 10 min, `refetchOnWindowFocus: false`, `retry: 1`) e o `QueryClientProvider` envolve a aplicação em `main.tsx:28`. O `ReactQueryDevtools` é montado condicionalmente em `main.tsx:46`, atrás de `env.enableDevtools`.
- Fora desses 12 arquivos, a busca de dados continua feita à mão com `useState`/`useEffect` — é o caso de todo o `pages/LojaOnlinePublico/` e dos callbacks de OAuth.

## Error boundaries

- `ErrorBoundary` existe: `components/common/ErrorBoundary/ErrorBoundary.tsx:16` (componente de classe), com `getDerivedStateFromError` em `:19` e `componentDidCatch` em `:23`.
- Está montado em dois níveis: raiz da aplicação (`main.tsx:30`, envolvendo `<App />`) e área autenticada (`MainLayout.tsx:82`, com `key={location.pathname}` — o boundary reseta a cada troca de rota).
- O storefront público (`/c/:empresaSlug/...`) não passa pelo `MainLayout`, então só é coberto pelo boundary raiz.

## Chamadas diretas de API em componentes

- 47 chamadas `api.*`/`apiPublica.*` sobraram em **15 arquivos `.tsx`**, concentradas na loja pública e em produtos:
  - `LojaOnlinePublico/CheckoutPage.tsx` (10), `LojaOnlinePublico/ClienteLoginPage.tsx` (7), `Produtos/ProdutoVariantesPage.tsx` (5), `Produtos/ProdutoFormPage.tsx` (4), `Produtos/CategoriasPage.tsx` (4), `LojaOnlinePublico/LojaOnlinePublicoPage.tsx` (4), `LojaOnlinePublico/MeusPedidosPage.tsx` (3), `Produtos/ProdutoDetalhesPage.tsx` (2), `LojaOnlinePublico/components/ClienteLayout.tsx` (2), e 1 chamada cada em `Perfil/PerfilPage.tsx`, `LojaOnlinePublico/RastreamentoPedidoPage.tsx`, `LojaOnlinePublico/ProdutoDetalhePage.tsx`, `LojaOnlinePublico/ClientePerfilPage.tsx`, `Auth/MicrosoftCallback.tsx`, `Auth/GoogleCallback.tsx`.
- Nesses arquivos, endpoints, parâmetros e formatos de DTO continuam inline no componente.

## Camada de serviços

- `services/api/` contém **10 arquivos** (mais `__tests__/`): os 2 clientes HTTP (`axios.ts`, `apiPublica.ts`) e **8 serviços de domínio**: `clientesApi.ts`, `empresaApi.ts`, `estoqueApi.ts`, `integracoesApi.ts`, `lojaOnlineApi.ts`, `plataformaApi.ts`, `produtosApi.ts`, `usuariosApi.ts`.
- Não existem `vendasApi.ts` nem `financeiroApi.ts` — coerente com as páginas de Vendas e Financeiro ainda serem stubs.

## Hooks

- `hooks/` tem 10 arquivos: os 8 hooks React Query acima, mais `useAuth.ts` (acesso ao `AuthContext`) e `useCarrinho.ts` (carrinho do storefront, `useState`/`useEffect` sobre `apiPublica`, 5 chamadas HTTP).

## God component

- `pages/LojaOnlinePublico/CheckoutPage.tsx` — **1.507 LOC** (era 1.381 no AUD-2026-06-29: **piorou**). É o maior arquivo do frontend por 3,3× sobre o segundo (`Plataforma/PlataformaPage.tsx`, 460 LOC) e concentra ~10% de todo o código do frontend.
  - 27 declarações `useState` no mesmo componente.
  - Cliente `apiPublica` e interceptor próprios, inline (ver "Clientes HTTP").
  - 7 tipos declarados inline: `ClienteNovo` (`:35`), `Endereco` (`:42`), `Pagamento` (`:52`), `TipoEntrega` (`:58`), `Step` (`:59`), `ModoCheckout` (`:60`), `Cliente` (`:63`).
  - Responsabilidades acumuladas: carrinho, login, cadastro, retorno de OAuth, checkout como convidado, busca de CEP, frete, pagamento e um wizard de 3 etapas.
- Arquivos acima de 300 LOC: **17**. Depois do Checkout: `Plataforma/PlataformaPage.tsx` 460, `Produtos/ProdutoFormPage.tsx` 440, `Clientes/ClienteEnderecosPage.tsx` 382, `LojaOnlinePublico/ClienteLoginPage.tsx` 374, `Clientes/ClienteCreditoPage.tsx` 369, `Clientes/ClientesPage.tsx` 365.

## Módulos incompletos

- **Stubs de "em breve" (47 LOC cada, sem nenhuma chamada de API):** `pages/Vendas/VendasPage.tsx` e `pages/Financeiro/FinanceiroPage.tsx`. Ambos renderizam só cabeçalho e cards de preview de funcionalidades. As rotas existem e estão protegidas por papel (`App.tsx`: `vendas` exige ADMIN/OPERADOR, `financeiro` exige ADMIN).
- **Dados mockados:** `pages/Dashboard/DashboardPage.tsx` (326 LOC) não faz nenhuma chamada de API — tudo vem de constantes no próprio arquivo: `mockStats` (`:32`, renderizado em `:201`), `vendasRecentes` (`:39`), `topProdutos` (`:50`), `categoriasVendas` (`:58`), `lineChartData` (`:122`) e `doughnutData` (`:162`). Os gráficos em si estão implementados (`chart.js` + `react-chartjs-2`, `<Line>` em `:226` e `<Doughnut>` em `:237`); o que falta é a origem real dos dados.
- **Deixaram de ser stubs** (contrariando o AUD-2026-06-29): `pages/Estoque/EstoquePage.tsx` tem 336 LOC e consome `useEstoques`/`useRelatorioEstoque` (mais `EstoqueDetalhePage.tsx`, 239 LOC); em `pages/Configuracoes/`, `IntegracoesPage.tsx` tem 322 LOC, `EmpresaPage.tsx` 305 e `UsuariosPage.tsx` 273, todas com schema de validação próprio e hooks React Query.

## A CONFIRMAR

- Quantos dos módulos do escopo da auditoria original contam como "funcionais" hoje: o recorte de 11 módulos do AUD-2026-06-29 não está documentado item a item, então a proporção antiga ("5 de 11 não funcionais") não foi recalculada. O que está medido acima é a lista nominal: 2 stubs (Vendas, Financeiro) e 1 mock (Dashboard).
- Os agrupamentos de comunidade do Graphify citados na versão anterior (ex.: "Comm. 42") não foram reconfirmados — o grafo em `graphify-out/` está marcado como possivelmente desatualizado. Foram removidos em vez de reescritos.
