# Tasks: Frontend ERP Runas

## Fase 1: Setup e Configuração Inicial

### TASK-001: Inicializar Projeto
**Status:** pending  
**Prioridade:** crítica  
**Estimativa:** 2h

**Descrição:**
Criar projeto React com Vite, TypeScript e configurações iniciais.

**Subtarefas:**
- [ ] Criar projeto com `npm create vite@latest frontend -- --template react-ts`
- [ ] Instalar dependências principais (React Router, Bootstrap, etc)
- [ ] Configurar ESLint e Prettier
- [ ] Configurar variáveis de ambiente (.env.example, .env.development)
- [ ] Criar estrutura de pastas base
- [ ] Configurar Git (gitignore, etc)
- [ ] Criar README.md com instruções

**Critérios de Aceitação:**
- Projeto inicia sem erros (`npm run dev`)
- ESLint configurado e funcionando
- Estrutura de pastas criada conforme design
- Variáveis de ambiente configuradas

---

### TASK-002: Configurar Axios e API Client
**Status:** pending  
**Prioridade:** crítica  
**Estimativa:** 3h

**Descrição:**
Configurar Axios com interceptors para autenticação e tratamento de erros.

**Subtarefas:**
- [ ] Instalar axios
- [ ] Criar `src/services/api/axios.ts` com configuração base
- [ ] Implementar interceptor de request (adicionar token)
- [ ] Implementar interceptor de response (refresh token automático)
- [ ] Criar `src/services/auth/tokenService.ts`
- [ ] Criar tipos base em `src/types/common.ts`
- [ ] Testar conexão com backend

**Critérios de Aceitação:**
- Axios configurado com base URL
- Interceptors funcionando
- Token adicionado automaticamente nas requisições
- Refresh token automático antes da expiração
- Tratamento de erros 401, 403, 500

---

### TASK-003: Configurar React Query
**Status:** pending  
**Prioridade:** crítica  
**Estimativa:** 2h

**Descrição:**
Configurar React Query para gerenciamento de estado do servidor.

**Subtarefas:**
- [ ] Instalar @tanstack/react-query
- [ ] Criar QueryClient com configurações
- [ ] Adicionar QueryClientProvider no App.tsx
- [ ] Instalar React Query Devtools
- [ ] Criar hooks base de exemplo

**Critérios de Aceitação:**
- React Query configurado
- Devtools funcionando em desenvolvimento
- Cache configurado (5min stale, 10min cache)
- Exemplo de useQuery funcionando

---

## Fase 2: Autenticação e Layout

### TASK-004: Implementar AuthContext
**Status:** pending  
**Prioridade:** crítica  
**Estimativa:** 4h

**Descrição:**
Criar contexto de autenticação com login, logout e verificação de permissões.

**Subtarefas:**
- [ ] Criar `src/contexts/AuthContext.tsx`
- [ ] Criar `src/services/auth/authService.ts`
- [ ] Implementar função de login
- [ ] Implementar função de logout
- [ ] Implementar verificação de autenticação
- [ ] Criar hook `useAuth`
- [ ] Criar tipos em `src/types/auth.ts`
- [ ] Implementar verificação de roles

**Critérios de Aceitação:**
- Login funcional com API
- Logout limpa tokens e redireciona
- Estado de autenticação persistido
- Hook useAuth retorna user, login, logout, isAuthenticated
- Verificação de roles (ADMIN, OPERADOR)

---

### TASK-005: Criar Página de Login
**Status:** pending  
**Prioridade:** crítica  
**Estimativa:** 4h

**Descrição:**
Implementar página de login com validação de formulário.

**Subtarefas:**
- [ ] Instalar react-hook-form e zod
- [ ] Criar `src/pages/Login/LoginPage.tsx`
- [ ] Criar formulário com validação
- [ ] Implementar máscara de email
- [ ] Adicionar loading state
- [ ] Adicionar tratamento de erros
- [ ] Estilizar com Bootstrap
- [ ] Adicionar logo e branding

**Critérios de Aceitação:**
- Formulário com validação em tempo real
- Mensagens de erro claras
- Loading durante autenticação
- Redirecionamento após login bem-sucedido
- Design responsivo

---

### TASK-006: Criar Layout Principal
**Status:** pending  
**Prioridade:** crítica  
**Estimativa:** 6h

**Descrição:**
Implementar layout principal com Navbar, Sidebar e Footer.

**Subtarefas:**
- [ ] Criar `src/components/layout/MainLayout/MainLayout.tsx`
- [ ] Criar `src/components/layout/Navbar/Navbar.tsx`
- [ ] Criar `src/components/layout/Sidebar/Sidebar.tsx`
- [ ] Criar `src/components/layout/Footer/Footer.tsx`
- [ ] Criar `src/components/layout/Breadcrumbs/Breadcrumbs.tsx`
- [ ] Implementar menu responsivo (collapse em mobile)
- [ ] Adicionar dropdown de usuário (logout)
- [ ] Estilizar com Bootstrap e SCSS

**Critérios de Aceitação:**
- Layout responsivo (desktop, tablet, mobile)
- Sidebar colapsável
- Navbar com logo, breadcrumbs e user menu
- Footer com informações básicas
- Navegação funcionando

---

### TASK-007: Configurar Rotas
**Status:** pending  
**Prioridade:** crítica  
**Estimativa:** 3h

**Descrição:**
Configurar React Router com rotas públicas e privadas.

**Subtarefas:**
- [ ] Instalar react-router-dom
- [ ] Criar `src/App.tsx` com rotas
- [ ] Criar componente PrivateRoute
- [ ] Criar componente PublicRoute
- [ ] Configurar lazy loading de páginas
- [ ] Criar página 404
- [ ] Configurar redirecionamentos

**Critérios de Aceitação:**
- Rotas públicas acessíveis sem autenticação
- Rotas privadas redirecionam para login
- Lazy loading funcionando
- 404 para rotas inexistentes
- Navegação entre páginas funcionando

---

## Fase 3: Componentes Comuns

### TASK-008: Criar Componentes Base
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 8h

**Descrição:**
Implementar componentes reutilizáveis (Button, Input, Modal, Table, etc).

**Subtarefas:**
- [ ] Criar `src/components/common/Button/Button.tsx`
- [ ] Criar `src/components/common/Input/Input.tsx`
- [ ] Criar `src/components/common/Modal/Modal.tsx`
- [ ] Criar `src/components/common/Table/Table.tsx`
- [ ] Criar `src/components/common/Pagination/Pagination.tsx`
- [ ] Criar `src/components/common/Loading/Loading.tsx`
- [ ] Criar `src/components/common/Card/Card.tsx`
- [ ] Criar `src/components/common/Badge/Badge.tsx`
- [ ] Criar `src/components/common/ConfirmDialog/ConfirmDialog.tsx`
- [ ] Criar `src/components/common/ErrorBoundary/ErrorBoundary.tsx`
- [ ] Estilizar todos os componentes
- [ ] Adicionar TypeScript types

**Critérios de Aceitação:**
- Todos os componentes funcionando
- Props tipadas com TypeScript
- Componentes responsivos
- Acessibilidade básica (labels, aria-*)
- Documentação JSDoc

---

### TASK-009: Configurar Toast Notifications
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 2h

**Descrição:**
Configurar sistema de notificações toast.

**Subtarefas:**
- [ ] Instalar react-toastify
- [ ] Configurar ToastContainer no App.tsx
- [ ] Criar helper `src/utils/toast.ts`
- [ ] Estilizar toasts
- [ ] Testar success, error, warning, info

**Critérios de Aceitação:**
- Toasts funcionando
- Posicionamento correto (top-right)
- Auto-dismiss em 3 segundos
- Diferentes tipos (success, error, warning, info)
- Estilo consistente com o design

---

## Fase 4: Módulo de Clientes

### TASK-010: Criar API Service de Clientes
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 3h

**Descrição:**
Implementar serviço de API para clientes.

**Subtarefas:**
- [ ] Criar `src/services/api/clientesApi.ts`
- [ ] Implementar métodos: list, getById, create, update, delete
- [ ] Implementar métodos de endereços
- [ ] Implementar métodos de crédito
- [ ] Criar tipos em `src/types/cliente.ts`
- [ ] Criar hooks em `src/hooks/useClientes.ts`

**Critérios de Aceitação:**
- Todos os métodos implementados
- Tipos TypeScript completos
- Hooks React Query funcionando
- Tratamento de erros

---

### TASK-011: Criar Página de Lista de Clientes
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 6h

**Descrição:**
Implementar página de listagem de clientes com filtros e busca.

**Subtarefas:**
- [ ] Criar `src/pages/Clientes/ClientesPage.tsx`
- [ ] Criar `src/components/clientes/ClienteList/ClienteList.tsx`
- [ ] Implementar tabela com paginação
- [ ] Implementar filtros (nome, CPF, status)
- [ ] Implementar busca com debounce
- [ ] Adicionar botão "Novo Cliente"
- [ ] Adicionar ações (visualizar, editar, desativar)
- [ ] Adicionar indicadores visuais (bloqueado, inativo)

**Critérios de Aceitação:**
- Lista paginada funcionando
- Filtros aplicando corretamente
- Busca com debounce de 300ms
- Ações funcionando
- Loading states
- Empty state
- Responsivo

---

### TASK-012: Criar Formulário de Cliente
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 8h

**Descrição:**
Implementar formulário de criação/edição de cliente.

**Subtarefas:**
- [ ] Criar `src/pages/Clientes/ClienteFormPage.tsx`
- [ ] Criar `src/components/clientes/ClienteForm/ClienteForm.tsx`
- [ ] Implementar validação com Zod
- [ ] Adicionar máscaras (CPF, telefone)
- [ ] Implementar validação de CPF
- [ ] Implementar normalização de telefone
- [ ] Adicionar feedback de erros
- [ ] Implementar modo criação e edição
- [ ] Adicionar confirmação antes de salvar

**Critérios de Aceitação:**
- Validação em tempo real
- Máscaras funcionando
- CPF validado corretamente
- Telefone normalizado para E.164
- Mensagens de erro claras
- Loading durante submit
- Redirecionamento após sucesso
- Responsivo

---

### TASK-013: Criar Página de Detalhes do Cliente
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 8h

**Descrição:**
Implementar página de visualização completa do cliente.

**Subtarefas:**
- [ ] Criar `src/pages/Clientes/ClienteDetailPage.tsx`
- [ ] Criar `src/components/clientes/ClienteCard/ClienteCard.tsx`
- [ ] Implementar tabs (Dados, Endereços, Crédito, Pedidos, Contas)
- [ ] Implementar gestão de endereços
- [ ] Implementar gestão de crédito (ADMIN)
- [ ] Mostrar histórico de pedidos
- [ ] Mostrar contas a receber
- [ ] Adicionar ações (editar, bloquear, desbloquear)

**Critérios de Aceitação:**
- Todas as tabs funcionando
- Dados carregando corretamente
- Gestão de endereços completa
- Gestão de crédito (apenas ADMIN)
- Histórico de pedidos
- Contas a receber
- Ações funcionando
- Responsivo

---

## Fase 5: Módulo de Produtos

### TASK-014: Criar API Service de Produtos
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 4h

**Descrição:**
Implementar serviço de API para produtos, variantes, categorias e fornecedores.

**Subtarefas:**
- [ ] Criar `src/services/api/produtosApi.ts`
- [ ] Implementar métodos de produtos
- [ ] Implementar métodos de variantes
- [ ] Implementar métodos de categorias
- [ ] Implementar métodos de fornecedores
- [ ] Criar tipos em `src/types/produto.ts`
- [ ] Criar hooks em `src/hooks/useProdutos.ts`

**Critérios de Aceitação:**
- Todos os métodos implementados
- Tipos completos
- Hooks funcionando
- Tratamento de erros

---

### TASK-015: Criar Página de Lista de Produtos
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 6h

**Descrição:**
Implementar página de listagem de produtos.

**Subtarefas:**
- [ ] Criar `src/pages/Produtos/ProdutosPage.tsx`
- [ ] Criar `src/components/produtos/ProdutoList/ProdutoList.tsx`
- [ ] Implementar grid/lista de produtos
- [ ] Implementar filtros (categoria, status)
- [ ] Implementar busca
- [ ] Adicionar botão "Novo Produto"
- [ ] Adicionar ações

**Critérios de Aceitação:**
- Lista/grid funcionando
- Filtros aplicando
- Busca funcionando
- Ações funcionando
- Responsivo

---

### TASK-016: Criar Formulário de Produto
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 10h

**Descrição:**
Implementar formulário de produto com wizard (Dados → Variantes → Catálogo).

**Subtarefas:**
- [ ] Criar `src/pages/Produtos/ProdutoFormPage.tsx`
- [ ] Criar `src/components/produtos/ProdutoForm/ProdutoForm.tsx`
- [ ] Implementar wizard multi-step
- [ ] Implementar formulário de dados básicos
- [ ] Criar `src/components/produtos/VarianteForm/VarianteForm.tsx`
- [ ] Implementar gestão de variantes
- [ ] Implementar cálculo de preço de venda
- [ ] Implementar upload de imagens
- [ ] Implementar configuração de catálogo

**Critérios de Aceitação:**
- Wizard funcionando
- Validação em cada step
- Gestão de variantes completa
- Cálculo de preço automático
- Upload de imagens funcionando
- Responsivo

---

## Fase 6: Módulo de Estoque

### TASK-017: Criar API Service de Estoque
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 3h

**Descrição:**
Implementar serviço de API para estoque.

**Subtarefas:**
- [ ] Criar `src/services/api/estoqueApi.ts`
- [ ] Implementar métodos de estoque
- [ ] Implementar métodos de movimentações
- [ ] Criar tipos em `src/types/estoque.ts`
- [ ] Criar hooks em `src/hooks/useEstoque.ts`

**Critérios de Aceitação:**
- Métodos implementados
- Tipos completos
- Hooks funcionando

---

### TASK-018: Criar Página de Estoque
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 8h

**Descrição:**
Implementar página de visualização e gestão de estoque.

**Subtarefas:**
- [ ] Criar `src/pages/Estoque/EstoquePage.tsx`
- [ ] Criar `src/components/estoque/EstoqueList/EstoqueList.tsx`
- [ ] Implementar dashboard de alertas
- [ ] Criar `src/components/estoque/MovimentacaoForm/MovimentacaoForm.tsx`
- [ ] Implementar entrada de estoque
- [ ] Implementar saída de estoque
- [ ] Implementar ajuste de estoque
- [ ] Implementar histórico de movimentações

**Critérios de Aceitação:**
- Lista de estoque funcionando
- Alertas visíveis
- Formulários de movimentação funcionando
- Validações corretas
- Histórico completo
- Responsivo

---

## Fase 7: Módulo de Vendas

### TASK-019: Criar API Service de Vendas
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 3h

**Descrição:**
Implementar serviço de API para vendas/pedidos.

**Subtarefas:**
- [ ] Criar `src/services/api/vendasApi.ts`
- [ ] Implementar métodos de pedidos
- [ ] Implementar métodos de pagamentos
- [ ] Criar tipos em `src/types/venda.ts`
- [ ] Criar hooks em `src/hooks/useVendas.ts`

**Critérios de Aceitação:**
- Métodos implementados
- Tipos completos
- Hooks funcionando

---

### TASK-020: Criar Página de Lista de Pedidos
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 6h

**Descrição:**
Implementar página de listagem de pedidos.

**Subtarefas:**
- [ ] Criar `src/pages/Vendas/VendasPage.tsx`
- [ ] Criar `src/components/vendas/PedidoList/PedidoList.tsx`
- [ ] Implementar filtros (status, período, cliente)
- [ ] Criar `src/components/vendas/StatusBadge/StatusBadge.tsx`
- [ ] Implementar busca
- [ ] Adicionar ações

**Critérios de Aceitação:**
- Lista funcionando
- Filtros aplicando
- Badges coloridos por status
- Ações funcionando
- Responsivo

---

### TASK-021: Criar Página de Detalhes do Pedido
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 8h

**Descrição:**
Implementar página de visualização e gestão de pedido.

**Subtarefas:**
- [ ] Criar `src/pages/Vendas/PedidoDetailPage.tsx`
- [ ] Criar `src/components/vendas/PedidoDetail/PedidoDetail.tsx`
- [ ] Implementar timeline de status
- [ ] Implementar ações (avançar status, cancelar, ajustar frete)
- [ ] Criar `src/components/vendas/PagamentoForm/PagamentoForm.tsx`
- [ ] Implementar confirmação de pagamento manual

**Critérios de Aceitação:**
- Detalhes completos
- Timeline funcionando
- Ações conforme status
- Confirmação de pagamento
- Responsivo

---

## Fase 8: Módulo Financeiro

### TASK-022: Criar API Service Financeiro
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 3h

**Descrição:**
Implementar serviço de API para financeiro.

**Subtarefas:**
- [ ] Criar `src/services/api/financeiroApi.ts`
- [ ] Implementar métodos de contas a receber
- [ ] Implementar métodos de pagamentos
- [ ] Criar tipos em `src/types/financeiro.ts`
- [ ] Criar hooks em `src/hooks/useFinanceiro.ts`

**Critérios de Aceitação:**
- Métodos implementados
- Tipos completos
- Hooks funcionando

---

### TASK-023: Criar Página de Contas a Receber
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 8h

**Descrição:**
Implementar página de gestão de contas a receber.

**Subtarefas:**
- [ ] Criar `src/pages/Financeiro/FinanceiroPage.tsx`
- [ ] Criar `src/components/financeiro/ContaList/ContaList.tsx`
- [ ] Implementar dashboard de contas vencidas
- [ ] Criar `src/components/financeiro/ContaDetail/ContaDetail.tsx`
- [ ] Criar `src/components/financeiro/PagamentoForm/PagamentoForm.tsx`
- [ ] Implementar registro de pagamento
- [ ] Implementar filtros

**Critérios de Aceitação:**
- Lista de contas funcionando
- Dashboard de vencidas
- Detalhes completos
- Registro de pagamento funcionando
- Filtros aplicando
- Responsivo

---

## Fase 9: Dashboard

### TASK-024: Criar Dashboard
**Status:** pending  
**Prioridade:** alta  
**Estimativa:** 10h

**Descrição:**
Implementar dashboard com métricas e gráficos.

**Subtarefas:**
- [ ] Criar `src/pages/Dashboard/DashboardPage.tsx`
- [ ] Instalar chart.js e react-chartjs-2
- [ ] Criar cards de métricas
- [ ] Implementar gráfico de vendas
- [ ] Implementar lista de alertas
- [ ] Implementar atualização automática (5min)
- [ ] Adicionar ações rápidas

**Critérios de Aceitação:**
- Métricas carregando corretamente
- Gráficos funcionando
- Alertas visíveis
- Atualização automática
- Ações rápidas funcionando
- Responsivo

---

## Fase 10: Testes e Refinamentos

### TASK-025: Implementar Testes Unitários
**Status:** pending  
**Prioridade:** média  
**Estimativa:** 16h

**Descrição:**
Criar testes unitários para componentes e hooks principais.

**Subtarefas:**
- [ ] Configurar Vitest e React Testing Library
- [ ] Testar componentes comuns
- [ ] Testar hooks customizados
- [ ] Testar utils e validators
- [ ] Configurar coverage

**Critérios de Aceitação:**
- Testes passando
- Coverage > 70%
- CI configurado

---

### TASK-026: Otimizações de Performance
**Status:** pending  
**Prioridade:** média  
**Estimativa:** 8h

**Descrição:**
Otimizar performance da aplicação.

**Subtarefas:**
- [ ] Implementar lazy loading de imagens
- [ ] Otimizar bundle (code splitting)
- [ ] Implementar virtualização de listas longas
- [ ] Otimizar re-renders
- [ ] Analisar bundle size

**Critérios de Aceitação:**
- Lighthouse score > 90
- Bundle size < 500KB (gzipped)
- Tempo de carregamento < 3s

---

### TASK-027: Acessibilidade
**Status:** pending  
**Prioridade:** média  
**Estimativa:** 6h

**Descrição:**
Melhorar acessibilidade da aplicação.

**Subtarefas:**
- [ ] Adicionar labels em todos os inputs
- [ ] Implementar navegação por teclado
- [ ] Adicionar aria-labels
- [ ] Testar com leitor de tela
- [ ] Verificar contraste de cores

**Critérios de Aceitação:**
- WCAG AA compliance
- Navegação por teclado funcionando
- Sem erros no axe DevTools

---

### TASK-028: Documentação
**Status:** pending  
**Prioridade:** baixa  
**Estimativa:** 4h

**Descrição:**
Criar documentação do projeto.

**Subtarefas:**
- [ ] Atualizar README.md
- [ ] Documentar componentes principais
- [ ] Criar guia de contribuição
- [ ] Documentar variáveis de ambiente
- [ ] Criar guia de deploy

**Critérios de Aceitação:**
- README completo
- Componentes documentados
- Guias criados

---

## Resumo de Estimativas

| Fase | Tarefas | Estimativa Total |
|------|---------|------------------|
| 1. Setup | 3 | 7h |
| 2. Auth e Layout | 4 | 17h |
| 3. Componentes Comuns | 2 | 10h |
| 4. Clientes | 4 | 25h |
| 5. Produtos | 3 | 20h |
| 6. Estoque | 2 | 11h |
| 7. Vendas | 3 | 17h |
| 8. Financeiro | 2 | 11h |
| 9. Dashboard | 1 | 10h |
| 10. Testes e Refinamentos | 4 | 34h |
| **TOTAL** | **28 tarefas** | **162h** |

**Estimativa com buffer (20%):** ~195h  
**Estimativa em dias úteis (8h/dia):** ~24 dias  
**Estimativa em semanas:** ~5 semanas

---

**Versão:** 1.0.0  
**Data:** 2026-05-25  
**Status:** ✅ Tasks Definidas
