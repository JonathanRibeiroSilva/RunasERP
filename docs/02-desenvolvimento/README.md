# 📚 Documentação de Desenvolvimento

> Guias e referências para desenvolvimento do ERP Runas

---

## 📋 Índice de Documentos

### 🎨 Frontend

- **[FRONTEND_IMPLEMENTACAO.md](../../FRONTEND_IMPLEMENTACAO.md)** ⭐
  Documento oficial de implementação do frontend (fica na raiz do repositório, por decisão do projeto).
- **[GUIA_MASCARAS_VALIDACOES.md](./GUIA_MASCARAS_VALIDACOES.md)**
  Referência de máscaras (CPF, telefone, CEP) e validações.
- **[frontend-current-state.md](../05-frontend/frontend-current-state.md)**
  Retrato factual do frontend medido em `frontend/src` — use este para saber o que existe hoje.

### ✅ Processo

- **[CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md)**
  Checklist geral de qualidade e padrões para novas features.
- **[../../.github/CONTRIBUTING.md](../../.github/CONTRIBUTING.md)**
  Fluxo de contribuição, branches e pull requests.

### 🔐 Autenticação e Segurança

- **[OAUTH_FLUXO_COMPLETO.md](./OAUTH_FLUXO_COMPLETO.md)**
  Fluxo OAuth2 ponta a ponta no e-commerce.
- **[OAUTH_PROVIDERS_CONFIG.md](./OAUTH_PROVIDERS_CONFIG.md)**
  Configuração de redirect URIs no Google Cloud e no Azure.
- **[SECURITY_HOOKS.md](./SECURITY_HOOKS.md)**
  Hooks Git nativos que barram commit de secrets, tokens e credenciais.

### 🕸️ Grafo de conhecimento

- **[GRAPHIFY_WORKFLOW.md](./GRAPHIFY_WORKFLOW.md)**
  Como usar o grafo em `graphify-out/` no dia a dia.
- **[GRAPHIFY_SETUP.md](./GRAPHIFY_SETUP.md)**
  Instalação e automação do Graphify neste repositório.

---

## 📊 Estado dos módulos

Estado verificado diretamente no código (`frontend/src/pages/`, `frontend/src/hooks/`,
`frontend/src/services/api/` e `services/*/main.py`). Sem percentuais: cada linha diz
o que foi encontrado no repositório.

### Backend — routers registrados em `main.py`

| Serviço | `include_router` em `main.py` | Situação |
|---------|-------------------------------|----------|
| produtos | 8 | Implementado |
| vendas | 6 | Implementado (inclui loja online, webhooks Mercado Pago e admin) |
| clientes | 2 | Implementado |
| empresas | 1 | Implementado |
| estoque | 1 | Implementado (`routers/estoque.py`) |
| notificacoes | 0 | Só `/health` (`services/notificacoes/main.py:56`). `routers/__init__.py` tem 22 bytes — a docstring do pacote e nada mais |
| financeiro | 0 | Só `/health` (`services/financeiro/main.py:56`). `routers/__init__.py` tem 22 bytes |

### Frontend — páginas e camada de dados

| Módulo | Página | Hook React Query | Serviço de API |
|--------|--------|------------------|----------------|
| Autenticação | `pages/Auth/`, `pages/Login/` | `useAuth.ts` (contexto, não React Query) | — |
| Clientes | `pages/Clientes/` | `useClientes.ts` | `clientesApi.ts` |
| Produtos | `pages/Produtos/` | `useProdutos.ts` | `produtosApi.ts` |
| Loja Online | `pages/LojaOnline/`, `pages/LojaOnlinePublico/` | `useLojaOnline.ts`, `useCarrinho.ts` | `lojaOnlineApi.ts`, `apiPublica.ts` |
| Estoque | `EstoquePage.tsx` (336 linhas) + `EstoqueDetalhePage.tsx` (239) | `useEstoque.ts` | `estoqueApi.ts` |
| Configurações | `pages/Configuracoes/` | `useEmpresa.ts`, `useUsuarios.ts`, `useIntegracoes.ts` | `empresaApi.ts`, `usuariosApi.ts`, `integracoesApi.ts` |
| Plataforma | `pages/Plataforma/` | `usePlataforma.ts` | `plataformaApi.ts` |
| Dashboard | `DashboardPage.tsx` — **dados mockados** (`mockStats`, linha 32) | — | — |
| Vendas | `VendasPage.tsx` — **stub "em breve"**, sem chamada de API | — | — |
| Financeiro | `FinanceiroPage.tsx` — **stub "em breve"**, sem chamada de API | — | — |

As rotas `estoque`, `estoque/:id`, `vendas` e `financeiro` existem em `frontend/src/App.tsx`
(linhas 171, 179, 189 e 199) — inclusive as dos stubs.

> Correção de uma versão anterior deste README: ele afirmava "Estoque | Frontend 0%".
> Estoque tem página, página de detalhe, hook e serviço de API. Já "Financeiro | Backend 0%"
> continua válido — `services/financeiro/main.py` não registra nenhum router.

---

## 🚀 Quick Start — Frontend

```bash
cd frontend
npm install
npm run dev        # Vite
npm run build      # tsc && vite build
npm test           # Vitest
npm run lint       # ESLint
```

Documento principal do frontend:

```bash
code FRONTEND_IMPLEMENTACAO.md   # na raiz do repositório
```

### Próximas entregas

Em ordem de dependência:

1. **Vendas/PDV** — backend pronto (6 routers em `services/vendas/main.py`); falta o frontend:
   a página é um stub e não existe `vendasApi.ts` nem hook de vendas.
2. **Financeiro** — falta backend e frontend: `services/financeiro/` só expõe `/health`,
   e a página é um stub.
3. **Dashboard** — trocar `mockStats` por dados reais de API.

---

## 🎯 Guias Rápidos

### Para implementar uma nova rota

1. Criar o componente de página em `frontend/src/pages/`.
2. Criar o arquivo SCSS ao lado (`sass` é dependência do projeto).
3. Layout responsivo (mobile-first).
4. Criar o serviço de domínio em `frontend/src/services/api/` sobre o cliente `axios.ts`.
5. Criar o hook React Query em `frontend/src/hooks/` (`@tanstack/react-query`).
6. Estados de UI: loading, error, empty.
7. Validação com `zod` + `react-hook-form` (`@hookform/resolvers`).
8. Registrar a rota em `frontend/src/App.tsx`.

### Para criar um componente

1. Interface TypeScript para as props.
2. Documentação JSDoc.
3. Responsivo.
4. Acessibilidade (ARIA).
5. Estados de UI.

---

## 💡 Convenções

### Commits (inglês)

```
feat(vendas): add PDV page
fix(estoque): correct stock calculation
docs(frontend): update implementation guide
```

### Código (PT-BR)

- Variáveis/funções: português
- Comentários: PT-BR
- Commits: inglês
- Docs: PT-BR

Detalhes em [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md) e
[.github/CONTRIBUTING.md](../../.github/CONTRIBUTING.md).

---

## Notas de revisão

- Percentuais de conclusão por módulo: a versão anterior deste README publicava
  números ("98%", "90%", "0%") sem origem rastreável. Foram removidos em vez de
  reestimados. O que está acima é o que existe em disco.
