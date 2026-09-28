# Componentes - Design System Runas

> **Componentes reutilizáveis que existem em `frontend/src/components/`, suas props reais e os estilos compartilhados de botões, badges, cards, inputs, modais e tabelas.**

Tokens (cores, fontes, espaçamentos, raios, sombras): ver [cores-tipografia.md](cores-tipografia.md).

---

## Como a UI é montada

- **Bootstrap 5 compilado** é importado em `frontend/src/main.tsx` (`bootstrap/dist/css/bootstrap.min.css`), e `@/styles/global.scss` vem **depois** para sobrescrever.
- Como o Bootstrap entra como CSS pronto, **não há variáveis SCSS de componente** (`$btn-*`, `$card-*`, `$input-*`, `$modal-*`, `$table-*`, `$badge-*`) no projeto. Os estilos de componente usam os tokens de `frontend/src/styles/variables.scss` e os mixins de `frontend/src/styles/mixins.scss`.
- `react-bootstrap` é usado só dentro de `ResponsiveCard` (`Card`), `ResponsiveTable` (`Table`) e `ResponsiveContainer` (`Container`).
- Ícones: `react-icons/fi` (Feather). Exceção: `FaGoogle` e `FaMicrosoft` de `react-icons/fa` em `pages/LojaOnlinePublico/ClienteLoginPage.tsx`.

---

## 📦 Inventário de componentes

| Componente | Arquivo | Usado em |
|------------|---------|----------|
| `Modal` | `components/common/Modal/Modal.tsx` | Usuários, Plataforma, Detalhe do tenant, Operação de estoque |
| `MaskedInput` | `components/common/MaskedInput/MaskedInput.tsx` | Empresa, Plataforma, Checkout da loja pública |
| `ErrorBoundary` | `components/common/ErrorBoundary/ErrorBoundary.tsx` | `main.tsx` e `MainLayout` |
| `RoleProtectedRoute` | `components/common/RoleProtectedRoute.tsx` | `App.tsx` |
| `ResponsiveCard` | `components/common/ResponsiveCard/ResponsiveCard.tsx` | nenhum import encontrado em `src/` |
| `ResponsiveTable` | `components/common/ResponsiveTable/ResponsiveTable.tsx` | nenhum import encontrado em `src/` |
| `ResponsiveContainer` | `components/common/ResponsiveContainer/ResponsiveContainer.tsx` | nenhum import encontrado em `src/` |
| `MainLayout` | `components/layout/MainLayout/MainLayout.tsx` | layout das rotas autenticadas |
| `Navbar` | `components/layout/Navbar/Navbar.tsx` | `MainLayout` |
| `Sidebar` | `components/layout/Sidebar/Sidebar.tsx` | `MainLayout` |

`components/common/index.ts` reexporta apenas `ResponsiveContainer`, `ResponsiveTable` e `ResponsiveCard`.

**Não implementados** (não existem em `components/`): `Button`, `Badge`, `Card` próprio, `Input` genérico, `Dropdown`, `Spinner`, `EmptyState`, `Skeleton`. Botões e badges são classes CSS (ver abaixo).

---

## 🔲 Botões

Não há componente `Button`. Os botões usam as classes do Bootstrap (`.btn`, `.btn-primary`, `.btn-secondary`, `.btn-outline-*`...) com sobrescritas no `.scss` de cada página (ex.: `pages/Clientes/ClientesPage.scss`, `pages/LojaOnlinePublico/CheckoutPage.scss`).

Existe o mixin `button-base` em `mixins.scss`, mas nenhum arquivo o inclui hoje. O que ele define:

```scss
@mixin button-base {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: $spacer-2;                      // 8px
  padding: $spacer-2 $spacer-3;        // 8px 12px
  font-size: $font-size-sm;            // 14px
  font-weight: $font-weight-medium;    // 500
  border-radius: $border-radius-md;    // 10px
  border: none;
  cursor: pointer;
  transition: all $transition-fast;

  &:disabled { opacity: 0.5; cursor: not-allowed; }
  &:focus-visible { @include focus-glow; }
}
```

Variantes (ghost, danger, gold etc.) não existem como tokens nem como mixin.

---

## 🏷️ Badges

Não há componente `Badge`. Existe a classe global `.badge` em `global.scss`, com quatro variantes:

```scss
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  font-size: $font-size-xs;              // 12px
  font-weight: $font-weight-semibold;    // 600
  border-radius: $border-radius-full;    // pílula
  letter-spacing: $letter-spacing-wide;  // 0.025em

  &-success { background: $success-light; color: $success; border: 1px solid $success-border; }
  &-warning { background: $warning-light; color: $warning; border: 1px solid $warning-border; }
  &-error   { background: $error-light;   color: $error;   border: 1px solid $error-border; }
  &-info    { background: $info-light;    color: $info;    border: 1px solid rgba(59, 130, 246, 0.3); }
}
```

Como `global.scss` é importado depois do Bootstrap, `.badge` sobrescreve a do Bootstrap. Não existem variantes `primary`, `gold` ou `neutral`. Cores de status de pedido são definidas por página (ex.: `pages/Dashboard/DashboardPage.scss`, `pages/LojaOnlinePublico/RastreamentoPedidoPage.scss`).

---

## 🪟 Modal

`Modal.tsx` é uma casca própria (não usa o `Modal` do react-bootstrap).

### Props

```tsx
interface ModalProps {
  isOpen: boolean;              // false => não renderiza nada
  title: string;                // vira <h2> e o aria-label do diálogo
  onClose: () => void;          // chamado no ESC, no clique no overlay e no botão X
  children: React.ReactNode;    // corpo (.modal-body)
  footer?: React.ReactNode;     // opcional (.modal-footer)
}
```

Comportamento: `role="dialog"`, `aria-modal="true"`, botão de fechar com `aria-label="Fechar"` e ícone `FiX`. Não há foco preso (focus trap) nem devolução de foco ao fechar.

### Estilo (`Modal.scss`)

```scss
.modal-overlay  { z-index: $z-index-modal; background: $overlay-heavy; padding: 1rem; }
.modal-dialog   { max-width: 520px; max-height: 90vh; background: $surface;
                  border: 1px solid $border-default; border-radius: $border-radius-lg; // 16px
                  box-shadow: $box-shadow-xl; }
.modal-header   { padding: 1.25rem 1.5rem; border-bottom: 1px solid $border-default; }
.modal-header h2 { font-size: 1.15rem; font-weight: 600; }
.modal-body     { padding: 1.5rem; }
.modal-footer   { padding: 1rem 1.5rem; border-top: 1px solid $border-default; gap: 0.75rem; }
```

Entrada com a animação `modal-fade` (0.15s).

---

## 📝 MaskedInput

### Props

```tsx
type MaskType = 'cpf' | 'cnpj' | 'phone' | 'cep' | 'date' | 'creditCard' | 'currency';

interface MaskedInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  mask?: MaskType;
  value: string;
  onChange: (value: string) => void;         // recebe o valor já mascarado
  onValidate?: (value: string) => string | null;  // roda no blur (e ao digitar, se showValidation e o campo já perdeu o foco uma vez)
  label?: string;
  error?: string;                            // erro externo tem prioridade sobre o interno
  helperText?: string;
  showValidation?: boolean;                  // default false
}
```

O `<input>` é sempre `type="text"`. A máscara `currency` está no tipo, mas não tem implementação: o valor passa sem formatação.

### Estilo (`MaskedInput.scss`)

- Campo: `padding: $spacer-3` (12px), `border: 1px solid $border-default`, `border-radius: $border-radius` (10px), fundo `$background`, fonte `$font-size-base` (15px).
- Hover: borda `$border-hover`, fundo `$surface`.
- Foco: borda `$primary`, `box-shadow: 0 0 0 3px $primary-light`.
- Erro: borda `$error`; no foco, `box-shadow` com `$error-light`.
- Desabilitado: `opacity: 0.6`, fundo `$surface-hover`.
- Placeholder e helper: `$text-tertiary`. Mensagem de erro: `$font-size-xs`, cor `$error`, prefixo `⚠`.

Outros campos de formulário usam as classes do Bootstrap ou as regras de `.admin-form` em `global.scss` (`padding: 0.7rem 1rem`, `border-radius: 0.5rem`, foco com borda `rgba($primary, 0.5)`).

---

## 📇 ResponsiveCard

Não é usado por nenhuma página hoje.

```tsx
interface ResponsiveCardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;          // default ''
  hoverable?: boolean;         // default false
  clickable?: boolean;         // default false; adiciona tabIndex=0, role="button", Enter/Espaço
  onClick?: () => void;        // só dispara se clickable
  headerActions?: React.ReactNode;
  footer?: React.ReactNode;
}
```

Estilo (`ResponsiveCard.scss`): base no mixin `card` (que inclui `premium-card` → `glass-panel`), `margin-bottom: $spacer-3`. Hover (`.hoverable`): `translateY(-2px)`, `$box-shadow-lg`, borda `$border-strong`. Variantes por classe: `.card-primary`, `.card-success`, `.card-warning`, `.card-error`.

---

## 📊 ResponsiveTable

Não é usado por nenhuma página hoje.

```tsx
interface ResponsiveTableProps {
  children: React.ReactNode;
  striped?: boolean;       // default true
  hover?: boolean;         // default true
  bordered?: boolean;      // default false
  borderless?: boolean;    // default false
  size?: 'sm' | 'lg';
  variant?: 'dark' | 'light';   // default 'dark'
  responsive?: boolean | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';  // default true
  className?: string;
}
```

Estilo (`ResponsiveTable.scss`): wrapper com scroll horizontal e sombra lateral; abaixo de 768px a tabela ganha `min-width: 600px`; abaixo de 576px a primeira coluna fica `sticky`. Na variante dark, `th` usa `$surface-hover` e `td` usa `$surface`.

As listas administrativas (Usuários, Plataforma) não usam este componente: usam `.admin-list table` de `global.scss` (`th, td { padding: 0.75rem 1rem }`, cabeçalho em `$font-size-xs`, `uppercase`, peso 600).

---

## 📐 ResponsiveContainer

Não é usado por nenhuma página hoje.

```tsx
interface ResponsiveContainerProps {
  children: React.ReactNode;
  fluid?: boolean;        // default false
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'xxl' | 'full';  // default 'xl'; gera a classe max-width-<valor>
}
```

---

## 🛡️ ErrorBoundary e RoleProtectedRoute

```tsx
interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;    // substitui o fallback padrão
}

interface RoleProtectedRouteProps {
  children: React.ReactNode;
  requiredRole: UserRole[];  // sem a role: toast de erro + <Navigate to="/dashboard" replace />
}
```

---

## 🧭 Layout

```tsx
// Navbar
interface NavbarProps {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

// Sidebar
interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
  isMobile?: boolean;      // default false
}
```

`MainLayout` não recebe props: renderiza `Navbar`, `Sidebar` e o `<Outlet />`, e considera mobile abaixo de 768px. Detalhes em [layouts.md](layouts.md).

---

## 🪟 Glassmorphism

Não existem classes `.glass-effect` / `.glass-effect-strong`. Existem **mixins** em `mixins.scss`:

```scss
@mixin glass-panel {
  background: $glass-bg;                 // rgba(16, 20, 29, 0.65)
  backdrop-filter: $glass-blur;          // blur(16px)
  border: 1px solid $glass-border;       // rgba(255, 255, 255, 0.08)
  box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.05), $shadow-md;
  border-radius: $border-radius-lg;      // 16px
}

@mixin glass-effect { @include glass-panel; }   // alias legado

@mixin glass-effect-strong {
  background: rgba(16, 20, 29, 0.85);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
```

`glass-effect` é incluído em `pages/Auth/ForgotPasswordPage.scss` e `pages/Auth/ResetPasswordPage.scss`; `glass-panel` também entra via `premium-card` / `card`.

---

## 🎯 Estados de componentes

- **Loading:** `react-loading-skeleton` está no `package.json`, mas nenhum arquivo de `src/` o importa. Não há componente de spinner compartilhado; cada página resolve o próprio indicador.
- **Empty:** não há componente; existem as classes `.admin-list .empty-state` (`global.scss`) e `.table-empty-state` (`ResponsiveTable.scss`).
- **Error:** `ErrorBoundary` para erros de renderização; erros de backend em formulários usam `.admin-form .form-error`.
- **Toasts:** `react-toastify`, configurado em `main.tsx` com `position="top-right"`, `autoClose={3000}` e `theme="dark"`.

---

## ♿ Acessibilidade (o que existe no código)

- Foco visível: links globais usam o mixin `focus-ring` (`outline: 2px solid $primary; outline-offset: 2px`); a Sidebar usa `focus-glow` (`box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.3)` + glow). Não há regra `*:focus-visible` global.
- `Modal`: `role="dialog"`, `aria-modal`, fecha no ESC. `ResponsiveCard` clicável aceita Enter/Espaço.
- `prefers-reduced-motion`: **não implementado** (nenhuma ocorrência em `src/`).
- Touch target de 44px: só aparece em `components/layout/Sidebar/Sidebar.scss`; não há token global.
- Contraste: A CONFIRMAR, nenhuma razão de contraste foi medida para os tokens atuais.

---

## Referências

- [cores-tipografia.md](cores-tipografia.md): tokens de cor, tipografia, espaçamento e sombra
- [layouts.md](layouts.md): layout de página
- [design.md](design.md): visão geral do design system
