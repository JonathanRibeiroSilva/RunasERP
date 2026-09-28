# Cores e Tipografia - Design System Runas

> **Paleta de cores, tipografia, espaçamentos, raios, sombras e transições.**

Fonte única de verdade: `frontend/src/styles/variables.scss`. Os valores abaixo foram copiados de lá; se divergirem, vale o arquivo. Componentes que usam estes tokens: ver [componentes.md](componentes.md).

---

## 🎨 Paleta de cores

O tema é **dark-first** e só existe o modo escuro (não há tema claro nem alternância).

### Fundo e superfícies

```scss
$background: #080A0F;         // fundo principal
$surface: #10141D;            // cards, modais, painéis
$surface-hover: #171C28;      // hover
$surface-elevated: #1A202C;
```

O `body` (`global.scss`) usa `$background` com dois `radial-gradient` muito sutis (primary e secondary a 2%) sobre `linear-gradient(135deg, #080A0F 0%, #040508 100%)`, com `background-attachment: fixed`.

### Primary: ciano/azul elétrico

```scss
$primary: #0EA5E9;
$primary-hover: #38BDF8;      // hover é MAIS CLARO que a base
$primary-active: #0284C7;
$primary-light: rgba(14, 165, 233, 0.15);
$primary-glow: rgba(14, 165, 233, 0.3);
```

### Secondary: índigo

```scss
$secondary: #6366F1;
$secondary-hover: #818CF8;
$secondary-light: rgba(99, 102, 241, 0.15);
$secondary-glow: rgba(99, 102, 241, 0.25);
```

### Texto

```scss
$text-primary: #FFFFFF;
$text-secondary: #94A3B8;     // também é a cor padrão de <p> em global.scss
$text-tertiary: #64748B;      // labels, hints, placeholders
$text-disabled: #475569;
```

### Semânticas

```scss
$success: #10B981;
$success-light: rgba(16, 185, 129, 0.15);
$success-border: rgba(16, 185, 129, 0.3);

$warning: #F59E0B;
$warning-light: rgba(245, 158, 11, 0.15);
$warning-border: rgba(245, 158, 11, 0.3);

$error: #EF4444;
$error-light: rgba(239, 68, 68, 0.15);
$error-border: rgba(239, 68, 68, 0.3);

$info: #3B82F6;
$info-light: rgba(59, 130, 246, 0.15);

// Aliases de erro
$danger: $error;
$danger-light: $error-light;
$danger-dark: #dc2626;
```

### Bordas, overlays e glass

```scss
$border-subtle: rgba(255, 255, 255, 0.04);
$border-default: rgba(255, 255, 255, 0.08);
$border-hover: rgba(255, 255, 255, 0.15);
$border-strong: rgba(255, 255, 255, 0.25);

$overlay-heavy: rgba(8, 10, 15, 0.9);   // fundo do Modal
$overlay-light: rgba(8, 10, 15, 0.5);

$glass-bg: rgba(16, 20, 29, 0.65);
$glass-bg-hover: rgba(23, 28, 40, 0.75);
$glass-border: rgba(255, 255, 255, 0.08);
$glass-border-highlight: rgba(255, 255, 255, 0.15);
$glass-blur: blur(16px);
```

### Aliases legados

```scss
$primary-dark: #0284c7;
$glow-primary: $shadow-glow-primary;
```

### O que NÃO existe

- Não há cor de destaque dourada (`$accent-gold`) nem tokens de status por domínio (`$status-*`, `$estoque-*`, `$conta-*`, `$cliente-*`, `$prioridade-*`). Cores de status são definidas no `.scss` de cada página (ex.: `pages/Dashboard/DashboardPage.scss`, `pages/LojaOnlinePublico/RastreamentoPedidoPage.scss`).
- Não há componente `Badge` com `variant`. Para badges, use as classes `.badge-success`, `.badge-warning`, `.badge-error` e `.badge-info` de `global.scss` (detalhes em [componentes.md](componentes.md), seção Badges).
- Contraste: A CONFIRMAR. Nenhuma razão de contraste WCAG foi medida para estes tokens.

---

## 📝 Tipografia

### Famílias

```scss
$font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
$font-family-monospace: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
```

**Carregamento:** a primeira linha de `frontend/src/styles/global.scss` importa do Google Fonts:

```scss
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```

- Inter: pesos 400, 500, 600 e 700.
- JetBrains Mono: pesos 400 e 500. Use a classe `.font-mono` para aplicar a monoespaçada a dados.
- `index.html` e `main.tsx` não carregam fontes; `main.tsx` só importa o CSS do Bootstrap, `global.scss` e o CSS do react-toastify.
- `Fira Code` não é carregada: só entra se estiver instalada na máquina.

### Tamanhos

```scss
$font-size-xs: 0.75rem;       // 12px
$font-size-sm: 0.875rem;      // 14px
$font-size-base: 0.9375rem;   // 15px (tamanho do body)
$font-size-lg: 1.0625rem;     // 17px
$font-size-xl: 1.25rem;       // 20px
$font-size-2xl: 1.5rem;       // 24px
$font-size-3xl: 2rem;         // 32px
```

Base de cálculo: `html { font-size: 16px; }` em `global.scss`.

### Títulos

Os títulos em `global.scss` usam a escala acima, não os tokens `$hN-font-size`:

| Elemento | Token | Tamanho |
|----------|-------|---------|
| `h1` | `$font-size-3xl` | 32px |
| `h2` | `$font-size-2xl` | 24px |
| `h3` | `$font-size-xl` | 20px |
| `h4` | `$font-size-lg` | 17px |

Todos os `h1`–`h6`: peso `$font-weight-semibold` (600), `letter-spacing: $letter-spacing-tight`, `line-height: 1.2`, cor `$text-primary`.

Tokens legados que continuam definidos (usados, por exemplo, em `ResponsiveCard.scss`):

```scss
$h1-font-size: 2.5rem;    // 40px
$h2-font-size: 2rem;      // 32px
$h3-font-size: 1.75rem;   // 28px
$h4-font-size: 1.5rem;    // 24px
$h5-font-size: 1.25rem;   // 20px
$h6-font-size: 1rem;      // 16px
```

Não há tokens de display (`$display-1` etc.).

### Pesos

```scss
$font-weight-light: 300;      // legado; Inter 300 NÃO é carregada do Google Fonts
$font-weight-regular: 400;
$font-weight-normal: 400;     // legado, igual a regular
$font-weight-medium: 500;
$font-weight-semibold: 600;
$font-weight-bold: 700;
```

### Letter spacing

```scss
$letter-spacing-tight: -0.02em;   // títulos
$letter-spacing-normal: 0;
$letter-spacing-wide: 0.025em;    // badges, cabeçalhos de tabela admin
$letter-spacing-caps: 0.05em;     // mixin text-overline
```

### Line height

```scss
$line-height-base: 1.5;
$line-height-sm: 1.25;
$line-height-lg: 2;
```

O `body` usa `line-height: 1.6` fixo, não `$line-height-base`.

---

## 📏 Espaçamento

Tokens individuais (não há mapa `$spacers` nem `$spacer` único):

```scss
$spacer-0: 0;
$spacer-1: 0.25rem;   // 4px
$spacer-2: 0.5rem;    // 8px
$spacer-3: 0.75rem;   // 12px
$spacer-4: 1rem;      // 16px
$spacer-5: 1.5rem;    // 24px
$spacer-6: 2rem;      // 32px
$spacer-7: 5rem;      // 80px (legado; fora da sequência)
$spacer-8: 3rem;      // 48px
$spacer-10: 4rem;     // 64px
```

`global.scss` redefine só três utilitários com estes tokens: `.mb-3` (12px), `.mb-4` (16px) e `.mt-3` (12px), todos com `!important`. Os demais utilitários de margem/padding (`.px-2`, `.gap-3` etc.) vêm do Bootstrap e seguem a escala dele.

---

## 🔘 Raios de borda

```scss
$border-radius-sm: 6px;
$border-radius-md: 10px;
$border-radius-lg: 16px;
$border-radius-xl: 24px;
$border-radius-full: 9999px;
$border-radius: $border-radius-md;   // alias legado (10px)
```

---

## 🎭 Sombras

```scss
$shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
$shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.6), 0 4px 6px -2px rgba(0, 0, 0, 0.4);
$shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.7), 0 10px 10px -5px rgba(0, 0, 0, 0.5);
$shadow-glow-primary: 0 0 15px rgba(14, 165, 233, 0.4);
$shadow-glow-success: 0 0 15px rgba(16, 185, 129, 0.4);

// Aliases legados
$box-shadow-xs: $shadow-sm;
$box-shadow-sm: $shadow-sm;
$box-shadow: $shadow-md;
$box-shadow-lg: $shadow-lg;
$box-shadow-xl: $shadow-lg;
```

Não existem `$glow-secondary`, `$glow-gold` nem `$inner-shadow`.

---

## 🔄 Transições

```scss
$transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
$transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
$transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
$transition-bounce: 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
```

Atenção: mais abaixo no mesmo arquivo há `$transition-bounce: $transition-slow;`. Como é SCSS sem `!default`, a segunda atribuição vence, e na prática `$transition-bounce` vale o mesmo que `$transition-slow`.

As transições guardam só duração e curva; o uso é `transition: all $transition-base` ou `transition: color $transition-fast`.

### Animações (`mixins.scss`)

```scss
@keyframes fadeSlideUp {
  0%   { opacity: 0; transform: translateY(15px); }
  100% { opacity: 1; transform: translateY(0); }
}
@mixin animate-entrance($delay: 0s) { animation: fadeSlideUp $transition-slow forwards; ... }

// Legados
@mixin fade-in  { animation: legacyFadeIn 0.2s ease-in-out forwards; }
@mixin slide-in { animation: legacySlideIn 0.2s ease-in-out forwards; }  // translateY(10px) -> 0
```

`prefers-reduced-motion` não é tratado em nenhum arquivo de `src/`.

---

## 🧱 Z-index

```scss
$z-index-dropdown: 100;
$z-index-sticky: 200;
$z-index-fixed: 300;
$z-index-modal-backdrop: 400;
$z-index-modal: 500;
$z-index-tooltip: 600;
```

---

## 📱 Breakpoints

```scss
$breakpoint-xs: 0;
$breakpoint-sm: 576px;
$breakpoint-md: 768px;
$breakpoint-lg: 992px;
$breakpoint-xl: 1200px;
```

Mixins em `mixins.scss`: `media-xs` (`max-width: 575px`), `media-sm` (`min-width: 576px`), `media-md` (768px), `media-lg` (992px), `media-xl` (1200px).

---

## 🌈 Gradientes

Não há tokens de gradiente. O que existe:

- Mixin `text-gradient($color1: $primary, $color2: $secondary)`: `linear-gradient(135deg, ...)` aplicado ao texto; exposto na classe `.text-gradient` de `global.scss`.
- O fundo do `body` descrito em "Fundo e superfícies", acima.
- Gradientes escritos direto em páginas, como `linear-gradient(135deg, $primary 0%, #8B5CF6 100%)` em `pages/Auth/ForgotPasswordPage.scss` e `pages/Auth/ResetPasswordPage.scss`.

---

## 🎨 Ícones

Biblioteca: `react-icons` (conjunto Feather, `react-icons/fi`; a única exceção é `FaGoogle`/`FaMicrosoft` de `react-icons/fa` em `pages/LojaOnlinePublico/ClienteLoginPage.tsx`). Ícones da navegação principal, conforme `components/layout/Sidebar/Sidebar.tsx`:

| Ícone | Item |
|-------|------|
| `FiHome` | Dashboard |
| `FiUsers` | Clientes |
| `FiGlobe` | Loja Online |
| `FiPackage` | Produtos |
| `FiTag` | Categorias |
| `FiBox` | Estoque |
| `FiShoppingCart` | Vendas |
| `FiDollarSign` | Financeiro |
| `FiGrid` | Plataforma |
| `FiSettings` | Configurações |
| `FiUser` | Meu Perfil |

`FiLogOut` (sair) fica na `Navbar`. A maioria dos ícones não recebe `size` e herda o tamanho da fonte (`1em`); não há escala de tamanhos padronizada.
