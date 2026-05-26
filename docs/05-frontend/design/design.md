# Design Document: Frontend ERP Runas

## Overview

O Frontend do ERP Runas é uma aplicação web moderna construída com React, TypeScript e Bootstrap, projetada para fornecer uma interface intuitiva e responsiva para gerenciamento de comércio de alimentos e bebidas.

**Características principais:**
- Design minimalista e UI/UX agradável
- Totalmente responsivo (mobile-first approach)
- Autenticação JWT com refresh token automático
- Suporte a diferentes roles (ADMIN, OPERADOR)
- Módulos separados por funcionalidade
- Integração com backend FastAPI via API Gateway
- Gerenciamento de estado com Context API + React Query
- Validação de formulários com React Hook Form + Zod

## Tech Stack

### Core
- **React** 18.2+ - Library UI
- **TypeScript** 5.0+ - Type safety
- **Vite** 4.0+ - Build tool e dev server
- **React Router** 6.0+ - Roteamento

### UI/Styling
- **Bootstrap** 5.3+ - Framework CSS
- **React Bootstrap** 2.8+ - Componentes React
- **React Icons** 4.10+ - Ícones
- **SASS** - Preprocessador CSS

### State Management
- **React Query** 4.0+ - Server state
- **Context API** - Global state (auth, theme)
- **Zustand** (opcional) - Client state complexo

### Forms & Validation
- **React Hook Form** 7.45+ - Gerenciamento de formulários
- **Zod** 3.21+ - Schema validation
- **@hookform/resolvers** - Integração RHF + Zod

### HTTP & API
- **Axios** 1.4+ - HTTP client
- **Axios Interceptors** - Token refresh automático

### Utils
- **date-fns** 2.30+ - Manipulação de datas
- **react-toastify** 9.1+ - Notificações toast
- **react-loading-skeleton** 3.3+ - Loading states
- **chart.js** + **react-chartjs-2** - Gráficos dashboard

## Architecture

### High-Level Architecture

```
Browser
  ↓
React App (Port 3000)
  ↓
API Client (Axios)
  ↓
API Gateway (Port 8000)
  ↓
Microsserviços (8001-8006)
```

### Component Architecture

```
App
├── AuthProvider (Context)
├── QueryClientProvider (React Query)
├── ToastContainer
└── Router
    ├── PublicRoute (Login)
    └── PrivateRoute (MainLayout)
        ├── Navbar
        ├── Sidebar
        ├── Content
        │   ├── Dashboard
        │   ├── Clientes
        │   ├── Produtos
        │   ├── Vendas
        │   ├── Estoque
        │   └── Financeiro
        └── Footer
```

### Data Flow

```
Component
  ↓ (useQuery/useMutation)
React Query
  ↓ (API call)
API Service
  ↓ (axios)
Axios Interceptor (add token)
  ↓
API Gateway
  ↓
Backend
  ↓ (response)
React Query Cache
  ↓ (auto update)
Component Re-render
```

## Folder Structure

```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── logo.png
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.module.scss
│   │   │   │   └── index.ts
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   ├── Table/
│   │   │   ├── Pagination/
│   │   │   ├── Loading/
│   │   │   ├── ErrorBoundary/
│   │   │   ├── Card/
│   │   │   ├── Badge/
│   │   │   └── ConfirmDialog/
│   │   ├── layout/
│   │   │   ├── Navbar/
│   │   │   ├── Sidebar/
│   │   │   ├── Footer/
│   │   │   ├── MainLayout/
│   │   │   └── Breadcrumbs/
│   │   ├── clientes/
│   │   │   ├── ClienteForm/
│   │   │   ├── ClienteList/
│   │   │   ├── ClienteCard/
│   │   │   ├── EnderecoForm/
│   │   │   └── CreditoManager/
│   │   ├── produtos/
│   │   │   ├── ProdutoForm/
│   │   │   ├── ProdutoList/
│   │   │   ├── VarianteForm/
│   │   │   ├── CategoriaSelect/
│   │   │   └── FornecedorManager/
│   │   ├── vendas/
│   │   │   ├── PedidoList/
│   │   │   ├── PedidoDetail/
│   │   │   ├── StatusBadge/
│   │   │   └── PagamentoForm/
│   │   ├── estoque/
│   │   │   ├── EstoqueList/
│   │   │   ├── MovimentacaoForm/
│   │   │   ├── InventarioForm/
│   │   │   └── AlertaEstoque/
│   │   └── financeiro/
│   │       ├── ContaList/
│   │       ├── ContaDetail/
│   │       ├── PagamentoForm/
│   │       └── ContasVencidas/
│   ├── pages/
│   │   ├── Login/
│   │   ├── Dashboard/
│   │   ├── Clientes/
│   │   │   ├── ClientesPage.tsx
│   │   │   ├── ClienteDetailPage.tsx
│   │   │   └── ClienteFormPage.tsx
│   │   ├── Produtos/
│   │   ├── Vendas/
│   │   ├── Estoque/
│   │   ├── Financeiro/
│   │   └── NotFound/
│   ├── services/
│   │   ├── api/
│   │   │   ├── axios.ts
│   │   │   ├── clientesApi.ts
│   │   │   ├── produtosApi.ts
│   │   │   ├── vendasApi.ts
│   │   │   ├── estoqueApi.ts
│   │   │   └── financeiroApi.ts
│   │   └── auth/
│   │       ├── authService.ts
│   │       └── tokenService.ts
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useClientes.ts
│   │   ├── useProdutos.ts
│   │   ├── useVendas.ts
│   │   ├── useEstoque.ts
│   │   ├── useFinanceiro.ts
│   │   ├── useDebounce.ts
│   │   └── usePermissions.ts
│   ├── contexts/
│   │   ├── AuthContext.tsx
│   │   └── ThemeContext.tsx
│   ├── types/
│   │   ├── cliente.ts
│   │   ├── produto.ts
│   │   ├── venda.ts
│   │   ├── estoque.ts
│   │   ├── financeiro.ts
│   │   ├── auth.ts
│   │   └── common.ts
│   ├── utils/
│   │   ├── validators.ts
│   │   ├── formatters.ts
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── config/
│   │   └── env.ts
│   ├── styles/
│   │   ├── global.scss
│   │   ├── variables.scss
│   │   └── mixins.scss
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .env.example
├── .env.development
├── .env.production
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Core Patterns

### 1. Authentication Flow

```typescript
// AuthContext.tsx
interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Token refresh automático via Axios Interceptor
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshed = await refreshToken();
      if (refreshed) {
        return axios(error.config);
      }
      logout();
    }
    return Promise.reject(error);
  }
);
```

### 2. API Service Pattern

```typescript
// clientesApi.ts
export const clientesApi = {
  list: (params: ListParams) => 
    axios.get<PaginatedResponse<Cliente>>('/clientes', { params }),
  
  getById: (id: string) => 
    axios.get<Cliente>(`/clientes/${id}`),
  
  create: (data: ClienteCreate) => 
    axios.post<Cliente>('/clientes', data),
  
  update: (id: string, data: ClienteUpdate) => 
    axios.patch<Cliente>(`/clientes/${id}`, data),
  
  delete: (id: string) => 
    axios.delete(`/clientes/${id}`),
};
```

### 3. React Query Hook Pattern

```typescript
// useClientes.ts
export const useClientes = (params: ListParams) => {
  return useQuery({
    queryKey: ['clientes', params],
    queryFn: () => clientesApi.list(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useCreateCliente = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: clientesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['clientes']);
      toast.success('Cliente criado com sucesso!');
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
};
```

### 4. Form Validation Pattern

```typescript
// ClienteForm.tsx
const clienteSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  cpf: z.string().refine(validateCPF, 'CPF inválido'),
  telefone: z.string().refine(validatePhone, 'Telefone inválido'),
  email: z.string().email('Email inválido').optional(),
});

type ClienteFormData = z.infer<typeof clienteSchema>;

const { register, handleSubmit, formState: { errors } } = useForm<ClienteFormData>({
  resolver: zodResolver(clienteSchema),
});
```

## UI/UX Design Principles

> **Importante:** Consulte o **Design System completo** para detalhes sobre cores, tipografia, componentes e filosofia visual:
> - **[Cores e Tipografia](./cores-tipografia.md)** - Paleta, tipografia, espaçamentos, sombras
> - **[Componentes](./componentes.md)** - Botões, cards, inputs, modais, tabelas, badges
> - **[Layouts e Responsividade](./layouts.md)** - Breakpoints, grid, mobile first, filosofia visual

### Runas Brand Identity

**Filosofia:** Clareza, inteligência e controle. Inspirado em Linear, Vercel, Stripe e Notion.

**O que somos:**
- Ferramenta operacional moderna
- Interface inteligente e clara
- Design profissional e confiável

**O que NÃO somos:**
- Software fiscal legado
- Interface cyberpunk/neon
- Design exagerado ou chamativo

### Color Palette (Dark Mode First)

```scss
// Background
$background: #0F1115;           // Fundo principal
$surface: #171A21;              // Cards, modais
$surface-hover: #1F2430;        // Hover states

// Primary - Azul (ações principais)
$primary: #3B82F6;              // Azul vibrante
$primary-hover: #2563EB;
$primary-light: rgba(59, 130, 246, 0.1);

// Secondary - Ciano (modernidade)
$secondary: #22D3EE;            // Ciano vibrante
$secondary-light: rgba(34, 211, 238, 0.1);

// Accent - Dourado (RARO - máximo 3x por tela)
$accent-gold: #D4A017;          // Apenas destaques importantes
$accent-gold-light: rgba(212, 160, 23, 0.1);

// Text
$text-primary: #E5E7EB;         // Texto principal
$text-secondary: #94A3B8;       // Texto secundário
$text-tertiary: #64748B;        // Labels, hints

// Semantic
$success: #10B981;              // Verde - confirmações
$warning: #F59E0B;              // Laranja - avisos
$error: #EF4444;                // Vermelho - APENAS erros críticos
$info: #22D3EE;                 // Ciano
```

**Regras importantes:**
- Dourado: máximo 3 usos por tela, apenas para destaques premium
- Vermelho: APENAS para erros críticos, não para decoração
- Use azul/ciano para status neutros e positivos

### Typography

```scss
$font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
$font-size-base: 1rem;      // 16px
$font-size-sm: 0.875rem;    // 14px
$font-size-lg: 1.125rem;    // 18px

$h1-font-size: 2.5rem;      // 40px
$h2-font-size: 2rem;        // 32px
$h3-font-size: 1.75rem;     // 28px
$h4-font-size: 1.5rem;      // 24px
```

### Spacing

```scss
$spacer: 1rem;  // 16px
$spacers: (
  0: 0,
  1: $spacer * 0.25,  // 4px
  2: $spacer * 0.5,   // 8px
  3: $spacer,         // 16px
  4: $spacer * 1.5,   // 24px
  5: $spacer * 3,     // 48px
);
```

### Responsive Breakpoints

```scss
$grid-breakpoints: (
  xs: 0,
  sm: 576px,
  md: 768px,
  lg: 992px,
  xl: 1200px,
  xxl: 1400px
);
```

### Component States

- **Loading**: Skeleton loaders
- **Empty**: Ilustração + mensagem + ação
- **Error**: Mensagem clara + ação de retry
- **Success**: Toast notification (3s)

### Accessibility

- Contraste mínimo 4.5:1 (WCAG AA)
- Foco visível em todos os elementos interativos
- Labels em todos os inputs
- Navegação por teclado
- Mensagens de erro associadas aos campos

## Key Features Design

### 1. Dashboard

**Layout:**
- Grid 3 colunas (desktop) / 1 coluna (mobile)
- Cards com métricas principais
- Gráfico de vendas (últimos 7 dias)
- Lista de alertas (estoque baixo, contas vencidas)

**Métricas:**
- Vendas do dia/mês
- Clientes ativos
- Produtos com estoque baixo
- Contas vencidas

### 2. Clientes

**Lista:**
- Tabela responsiva com paginação
- Filtros: nome, CPF, status
- Busca com debounce (300ms)
- Ações: visualizar, editar, desativar

**Formulário:**
- Validação em tempo real
- Máscara de CPF e telefone
- Busca de endereço por CEP (ViaCEP)
- Gestão de múltiplos endereços

**Detalhes:**
- Tabs: Dados, Endereços, Crédito, Pedidos, Contas
- Histórico de movimentações
- Ações rápidas

### 3. Produtos

**Lista:**
- Cards com imagem (desktop) / Lista (mobile)
- Filtros: categoria, status
- Busca por nome/SKU

**Formulário:**
- Wizard: Dados → Variantes → Catálogo
- Upload de imagens (drag & drop)
- Gestão de variantes dinâmica
- Cálculo automático de preço

### 4. Estoque

**Dashboard:**
- Alertas de estoque baixo
- Movimentações recentes
- Ação rápida: entrada/saída

**Movimentação:**
- Formulário com seleção de produto
- Validação de quantidade disponível
- Confirmação antes de salvar

**Inventário:**
- Wizard: Criar → Adicionar itens → Contar → Finalizar
- Cálculo automático de diferenças
- Ajuste automático ao finalizar

### 5. Vendas

**Lista:**
- Filtros: status, período, cliente
- Badges coloridos por status
- Ações conforme status

**Detalhes:**
- Timeline de status
- Itens do pedido
- Dados de pagamento e entrega
- Ações: avançar status, cancelar, ajustar frete

### 6. Financeiro

**Dashboard:**
- Total a receber
- Contas vencidas (destaque)
- Contas a vencer (próximos 7 dias)

**Conta:**
- Detalhes completos
- Histórico de pagamentos
- Ação: registrar pagamento

**Pagamento:**
- Modal com formulário
- Cálculo automático de saldo
- Confirmação

## Performance Optimization

### Code Splitting

```typescript
// Lazy loading de páginas
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Clientes = lazy(() => import('./pages/Clientes'));
const Produtos = lazy(() => import('./pages/Produtos'));

// Suspense com fallback
<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
    <Route path="/clientes" element={<Clientes />} />
  </Routes>
</Suspense>
```

### React Query Configuration

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      cacheTime: 10 * 60 * 1000,     // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
```

### Image Optimization

- Lazy loading de imagens
- Placeholder durante carregamento
- Compressão automática
- Formato WebP quando suportado

### Bundle Optimization

- Tree shaking automático (Vite)
- Minificação de CSS e JS
- Compressão gzip/brotli
- Análise de bundle (vite-bundle-visualizer)

## Security

### Token Storage

```typescript
// Opção 1: httpOnly Cookie (mais seguro)
// Configurado no backend

// Opção 2: localStorage (MVP)
const tokenService = {
  getAccessToken: () => localStorage.getItem('access_token'),
  setAccessToken: (token: string) => localStorage.setItem('access_token', token),
  getRefreshToken: () => localStorage.getItem('refresh_token'),
  setRefreshToken: (token: string) => localStorage.setItem('refresh_token', token),
  clearTokens: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
};
```

### Input Sanitization

```typescript
import DOMPurify from 'dompurify';

const sanitizeInput = (input: string): string => {
  return DOMPurify.sanitize(input, { ALLOWED_TAGS: [] });
};
```

### HTTPS Only

- Produção: HTTPS obrigatório
- Desenvolvimento: HTTP permitido
- Redirect automático HTTP → HTTPS

## Testing Strategy

### Unit Tests (Vitest)

```typescript
// Button.test.tsx
describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledOnce();
  });
});
```

### Integration Tests (React Testing Library)

```typescript
// ClienteForm.test.tsx
describe('ClienteForm', () => {
  it('submits form with valid data', async () => {
    const onSubmit = vi.fn();
    render(<ClienteForm onSubmit={onSubmit} />);
    
    await userEvent.type(screen.getByLabelText('Nome'), 'João Silva');
    await userEvent.type(screen.getByLabelText('CPF'), '12345678909');
    await userEvent.click(screen.getByText('Salvar'));
    
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        nome: 'João Silva',
        cpf: '12345678909',
      });
    });
  });
});
```

### E2E Tests (Playwright - Opcional)

```typescript
test('login flow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.fill('[name="email"]', 'admin@runas.com');
  await page.fill('[name="password"]', 'Admin@123');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

## Deployment

### Build

```bash
npm run build
# Output: dist/
```

### Environment Variables

```env
# .env.production
VITE_API_URL=https://api.runas.com
VITE_APP_NAME=ERP Runas
VITE_APP_VERSION=1.0.0
```

### Docker

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy Frontend
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm ci
      - run: npm run build
      - run: npm run test
      - name: Deploy to production
        run: |
          # Deploy script
```

## Monitoring

### Error Tracking

- Sentry (opcional)
- Console.error em desenvolvimento
- Log estruturado em produção

### Analytics

- Google Analytics (opcional)
- Eventos customizados para ações principais

### Performance Monitoring

- Web Vitals (LCP, FID, CLS)
- React DevTools Profiler
- Lighthouse CI

## Documentation

### Component Documentation

```typescript
/**
 * Button component
 * 
 * @param variant - Button style variant
 * @param size - Button size
 * @param disabled - Disable button
 * @param loading - Show loading state
 * @param onClick - Click handler
 * 
 * @example
 * <Button variant="primary" size="lg" onClick={handleClick}>
 *   Click me
 * </Button>
 */
```

### API Documentation

- Swagger UI do backend: http://localhost:8000/docs
- Documentação de rotas: `/docs/MAPEAMENTO-ROTAS.md`

## Next Steps

1. Setup inicial do projeto (Vite + React + TypeScript)
2. Configuração de linting e formatting (ESLint + Prettier)
3. Estrutura de pastas e arquivos base
4. Configuração de rotas e layout
5. Implementação de autenticação
6. Desenvolvimento de componentes comuns
7. Implementação de módulos (Clientes, Produtos, etc)
8. Testes
9. Deploy

---

**Versão:** 1.0.0  
**Data:** 2026-05-25  
**Status:** ✅ Design Completo
