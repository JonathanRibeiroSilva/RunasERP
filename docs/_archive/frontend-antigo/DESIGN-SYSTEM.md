# Design System - ERP Runas Frontend

## 🎨 Paleta de Cores - Runas Identity

> **Filosofia:** Clareza, inteligência e controle. Inspirado em Linear, Vercel, Stripe e Notion.

### Cores Base (Dark Mode First)

```scss
// Background - Base escura sofisticada
$background: #0F1115;           // Fundo principal
$surface: #171A21;              // Cards, modais, painéis
$surface-hover: #1F2430;        // Hover states

// Primary - Azul (ações principais, confiança)
$primary: #3B82F6;              // Azul vibrante mas profissional
$primary-hover: #2563EB;        // Hover mais escuro
$primary-active: #1D4ED8;       // Active state
$primary-light: rgba(59, 130, 246, 0.1);   // Backgrounds sutis
$primary-glow: rgba(59, 130, 246, 0.2);    // Glow suave

// Secondary - Ciano (modernidade, clareza)
$secondary: #22D3EE;            // Ciano vibrante
$secondary-hover: #06B6D4;      // Hover
$secondary-light: rgba(34, 211, 238, 0.1);
$secondary-glow: rgba(34, 211, 238, 0.15);

// Accent - Dourado (RARO - apenas destaques importantes)
$accent-gold: #D4A017;          // Dourado sofisticado
$accent-gold-hover: #B8860B;    // Hover
$accent-gold-light: rgba(212, 160, 23, 0.1);
$accent-gold-glow: rgba(212, 160, 23, 0.15);

// Text - Hierarquia clara
$text-primary: #E5E7EB;         // Texto principal (alta legibilidade)
$text-secondary: #94A3B8;       // Texto secundário
$text-tertiary: #64748B;        // Texto terciário (labels, hints)
$text-disabled: #475569;        // Disabled states

// Semantic Colors (ajustados para dark mode)
$success: #10B981;              // Verde - confirmações
$success-light: rgba(16, 185, 129, 0.1);

$warning: #F59E0B;              // Laranja - avisos (não amarelo)
$warning-light: rgba(245, 158, 11, 0.1);

$error: #EF4444;                // Vermelho - APENAS erros críticos
$error-light: rgba(239, 68, 68, 0.1);

$info: #22D3EE;                 // Usa o ciano secundário
$info-light: rgba(34, 211, 238, 0.1);
```

### Regras de Uso das Cores

#### 🔵 **Azul Primary (#3B82F6)**
**Usar para:**
- ✅ Botões de ação principal (Salvar, Confirmar, Criar)
- ✅ Links e navegação ativa
- ✅ Progress bars
- ✅ Badges de status positivo

**NÃO usar para:**
- ❌ Backgrounds grandes
- ❌ Textos longos

#### 🔷 **Ciano Secondary (#22D3EE)**
**Usar para:**
- ✅ Informações e dicas
- ✅ Badges informativos
- ✅ Ícones de ajuda
- ✅ Highlights sutis

**NÃO usar para:**
- ❌ Ações críticas
- ❌ Botões primários

#### 🟡 **Dourado Accent (#D4A017) - RARO!**
**Usar APENAS para:**
- ✅ Destaques premium (ex: "Plano Pro")
- ✅ Conquistas e marcos importantes
- ✅ CTAs especiais (ex: "Upgrade")
- ✅ Badges de destaque (ex: "Novo", "Popular")
- ✅ Números importantes (ex: "R$ 10.000 em vendas")

**NUNCA usar para:**
- ❌ Botões comuns
- ❌ Backgrounds
- ❌ Textos corridos
- ❌ Elementos repetitivos

**Regra de ouro:** Se você usa dourado mais de 3 vezes na mesma tela, está usando demais.

#### 🔴 **Vermelho Error (#EF4444) - CRÍTICO APENAS**
**Usar APENAS para:**
- ✅ Erros de validação
- ✅ Mensagens de erro críticas
- ✅ Ações destrutivas (deletar, cancelar)
- ✅ Alertas de segurança

**NUNCA usar para:**
- ❌ Destaques visuais
- ❌ Badges de status
- ❌ Decoração

### Cores Neutras (Dark Mode)

```scss
// Borders e Dividers
$border-subtle: rgba(255, 255, 255, 0.05);
$border-default: rgba(255, 255, 255, 0.1);
$border-strong: rgba(255, 255, 255, 0.2);

// Overlays
$overlay-light: rgba(0, 0, 0, 0.5);
$overlay-heavy: rgba(0, 0, 0, 0.8);

// Glassmorphism (uso sutil)
$glass-bg: rgba(23, 26, 33, 0.8);
$glass-border: rgba(255, 255, 255, 0.1);
$glass-blur: blur(10px);
```

### Cores Semânticas por Contexto

> **Importante:** Vermelho APENAS para erros críticos. Use azul/ciano para status neutros/positivos.

```scss
// Status de Pedidos (comunicam progresso, não urgência)
$status-pendente: #94A3B8;      // Cinza - aguardando ação
$status-confirmado: #3B82F6;    // Azul - confirmado
$status-separando: #22D3EE;     // Ciano - em processo
$status-enviado: #8B5CF6;       // Roxo - em trânsito
$status-entregue: #10B981;      // Verde - concluído
$status-cancelado: #EF4444;     // Vermelho - erro/cancelado

// Status de Estoque (clareza operacional)
$estoque-ok: #10B981;           // Verde - estoque saudável
$estoque-baixo: #F59E0B;        // Laranja - atenção necessária
$estoque-zerado: #EF4444;       // Vermelho - crítico
$estoque-excesso: #22D3EE;      // Ciano - acima do ideal

// Status Financeiro (inteligência, não alarme)
$conta-quitada: #10B981;        // Verde - pago
$conta-parcial: #22D3EE;        // Ciano - pagamento parcial
$conta-aberta: #3B82F6;         // Azul - em aberto (normal)
$conta-vencida: #F59E0B;        // Laranja - vencida (atenção)
$conta-inadimplente: #EF4444;   // Vermelho - inadimplência crítica

// Status de Cliente (relacionamento)
$cliente-ativo: #10B981;        // Verde - ativo
$cliente-novo: #22D3EE;         // Ciano - novo cliente
$cliente-vip: #D4A017;          // Dourado - cliente premium (RARO)
$cliente-inativo: #64748B;      // Cinza - inativo
$cliente-bloqueado: #EF4444;    // Vermelho - bloqueado

// Prioridades (quando necessário)
$prioridade-baixa: #64748B;     // Cinza
$prioridade-media: #3B82F6;     // Azul
$prioridade-alta: #F59E0B;      // Laranja
$prioridade-urgente: #EF4444;   // Vermelho
```

### Badges de Status - Exemplos de Uso

```tsx
// ✅ CORRETO - Status de pedido
<Badge variant="confirmed">Confirmado</Badge>      // Azul
<Badge variant="delivered">Entregue</Badge>        // Verde
<Badge variant="cancelled">Cancelado</Badge>       // Vermelho

// ✅ CORRETO - Cliente VIP (uso raro de dourado)
<Badge variant="vip">Cliente VIP</Badge>           // Dourado

// ❌ ERRADO - Não use vermelho para status neutros
<Badge variant="error">Pendente</Badge>            // NÃO!

// ✅ CORRETO - Use cinza para status neutros
<Badge variant="neutral">Pendente</Badge>          // Cinza
```

## 📝 Tipografia

### Fonte

```scss
$font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 
                   'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 
                   'Droid Sans', 'Helvetica Neue', sans-serif;

$font-family-monospace: 'Fira Code', 'Courier New', monospace;
```

### Tamanhos

```scss
// Base
$font-size-base: 1rem;          // 16px
$font-size-sm: 0.875rem;        // 14px
$font-size-lg: 1.125rem;        // 18px
$font-size-xs: 0.75rem;         // 12px

// Headings
$h1-font-size: 2.5rem;          // 40px
$h2-font-size: 2rem;            // 32px
$h3-font-size: 1.75rem;         // 28px
$h4-font-size: 1.5rem;          // 24px
$h5-font-size: 1.25rem;         // 20px
$h6-font-size: 1rem;            // 16px

// Display (títulos grandes)
$display-1: 6rem;               // 96px
$display-2: 5.5rem;             // 88px
$display-3: 4.5rem;             // 72px
$display-4: 3.5rem;             // 56px
```

### Pesos

```scss
$font-weight-light: 300;
$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-semibold: 600;
$font-weight-bold: 700;
```

### Line Height

```scss
$line-height-base: 1.5;
$line-height-sm: 1.25;
$line-height-lg: 2;
```

## 📏 Espaçamento

### Sistema de Espaçamento (8px base)

```scss
$spacer: 1rem;  // 16px

$spacers: (
  0: 0,                    // 0px
  1: $spacer * 0.25,       // 4px
  2: $spacer * 0.5,        // 8px
  3: $spacer,              // 16px
  4: $spacer * 1.5,        // 24px
  5: $spacer * 3,          // 48px
  6: $spacer * 4,          // 64px
  7: $spacer * 5,          // 80px
);
```

### Uso

```scss
// Margin
.mt-3 { margin-top: 16px; }
.mb-4 { margin-bottom: 24px; }
.mx-2 { margin-left: 8px; margin-right: 8px; }

// Padding
.pt-3 { padding-top: 16px; }
.pb-4 { padding-bottom: 24px; }
.px-2 { padding-left: 8px; padding-right: 8px; }

// Gap (flexbox/grid)
.gap-3 { gap: 16px; }
```

## 🔲 Componentes

### Botões

```scss
// Tamanhos
$btn-padding-y-sm: 0.25rem;     // 4px
$btn-padding-x-sm: 0.5rem;      // 8px

$btn-padding-y: 0.5rem;         // 8px
$btn-padding-x: 1rem;           // 16px

$btn-padding-y-lg: 0.75rem;     // 12px
$btn-padding-x-lg: 1.5rem;      // 24px

// Border radius (mais arredondado, moderno)
$btn-border-radius: 0.5rem;     // 8px
$btn-border-radius-sm: 0.375rem; // 6px
$btn-border-radius-lg: 0.75rem;  // 12px

// Font
$btn-font-size: 0.875rem;       // 14px
$btn-font-size-sm: 0.75rem;     // 12px
$btn-font-size-lg: 1rem;        // 16px
$btn-font-weight: 500;          // Medium

// Variantes (Dark Mode)
$btn-primary-bg: $primary;
$btn-primary-hover: $primary-hover;
$btn-primary-text: $text-primary;

$btn-secondary-bg: $surface-hover;
$btn-secondary-hover: rgba(255, 255, 255, 0.1);
$btn-secondary-text: $text-primary;
$btn-secondary-border: $border-default;

$btn-ghost-bg: transparent;
$btn-ghost-hover: $surface-hover;
$btn-ghost-text: $text-secondary;

$btn-danger-bg: $error;
$btn-danger-hover: #DC2626;
$btn-danger-text: $text-primary;
```

### Cards

```scss
$card-border-radius: 0.75rem;   // 12px (mais arredondado)
$card-border-width: 1px;
$card-border-color: $border-default;
$card-bg: $surface;
$card-spacer-y: 1.5rem;         // 24px
$card-spacer-x: 1.5rem;         // 24px

// Sombras sutis para dark mode
$card-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
$card-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.4);

// Glassmorphism (opcional, uso sutil)
$card-glass-bg: $glass-bg;
$card-glass-border: $glass-border;
$card-glass-backdrop: $glass-blur;
```

### Inputs

```scss
$input-padding-y: 0.625rem;     // 10px
$input-padding-x: 0.875rem;     // 14px
$input-font-size: 0.875rem;     // 14px
$input-border-radius: 0.5rem;   // 8px
$input-border-width: 1px;

// Dark mode colors
$input-bg: $surface;
$input-border-color: $border-default;
$input-text-color: $text-primary;
$input-placeholder-color: $text-tertiary;

// Focus state
$input-focus-border-color: $primary;
$input-focus-bg: $surface-hover;
$input-focus-box-shadow: 0 0 0 3px $primary-light;

// Disabled state
$input-disabled-bg: rgba(255, 255, 255, 0.02);
$input-disabled-text: $text-disabled;
$input-disabled-border: $border-subtle;
```

### Modais

```scss
$modal-backdrop-bg: $overlay-heavy;
$modal-backdrop-opacity: 0.8;
$modal-border-radius: 1rem;     // 16px (mais arredondado)
$modal-padding: 1.5rem;         // 24px
$modal-bg: $surface;
$modal-border: $border-default;
$modal-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);

// Header
$modal-header-padding: 1.5rem;
$modal-header-border: $border-default;

// Footer
$modal-footer-padding: 1.5rem;
$modal-footer-border: $border-default;
```

### Tabelas

```scss
$table-cell-padding-y: 0.75rem;  // 12px
$table-cell-padding-x: 1rem;     // 16px

// Dark mode colors
$table-bg: transparent;
$table-border-color: $border-default;
$table-striped-bg: rgba(255, 255, 255, 0.02);
$table-hover-bg: $surface-hover;

// Header
$table-header-bg: $surface;
$table-header-text: $text-secondary;
$table-header-font-weight: 600;
$table-header-text-transform: uppercase;
$table-header-font-size: 0.75rem;  // 12px
$table-header-letter-spacing: 0.05em;
```

### Badges

```scss
$badge-padding-y: 0.25rem;      // 4px
$badge-padding-x: 0.625rem;     // 10px
$badge-font-size: 0.75rem;      // 12px
$badge-font-weight: 500;
$badge-border-radius: 0.375rem; // 6px

// Variantes (seguindo a paleta Runas)
$badge-primary-bg: $primary-light;
$badge-primary-text: $primary;
$badge-primary-border: $primary;

$badge-success-bg: $success-light;
$badge-success-text: $success;

$badge-warning-bg: $warning-light;
$badge-warning-text: $warning;

$badge-error-bg: $error-light;
$badge-error-text: $error;

$badge-gold-bg: $accent-gold-light;
$badge-gold-text: $accent-gold;

$badge-neutral-bg: rgba(255, 255, 255, 0.05);
$badge-neutral-text: $text-secondary;
```

## 📱 Breakpoints Responsivos

```scss
$grid-breakpoints: (
  xs: 0,        // Mobile portrait
  sm: 576px,    // Mobile landscape
  md: 768px,    // Tablet portrait
  lg: 992px,    // Tablet landscape / Desktop
  xl: 1200px,   // Desktop
  xxl: 1400px   // Large desktop
);
```

### Media Queries

```scss
// Mobile first
@media (min-width: 576px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 992px) { /* lg */ }
@media (min-width: 1200px) { /* xl */ }
@media (min-width: 1400px) { /* xxl */ }

// Desktop first
@media (max-width: 575.98px) { /* xs */ }
@media (max-width: 767.98px) { /* sm */ }
@media (max-width: 991.98px) { /* md */ }
@media (max-width: 1199.98px) { /* lg */ }
@media (max-width: 1399.98px) { /* xl */ }
```

## 🎭 Sombras (Dark Mode)

```scss
// Sombras sutis para dark mode (mais escuras e pronunciadas)
$box-shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.3);
$box-shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.4);
$box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5);
$box-shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.6);
$box-shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.7);

// Glow effects (uso sutil)
$glow-primary: 0 0 20px rgba(59, 130, 246, 0.3);
$glow-secondary: 0 0 20px rgba(34, 211, 238, 0.25);
$glow-gold: 0 0 20px rgba(212, 160, 23, 0.2);  // RARO

// Inner shadows (depth)
$inner-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
```

### Quando Usar Glow

```scss
// ✅ CORRETO - Hover em botões primários
.btn-primary:hover {
  box-shadow: $glow-primary;
}

// ✅ CORRETO - Destaque em cards importantes (RARO)
.card-featured {
  box-shadow: $glow-gold;  // Apenas para cards premium
}

// ❌ ERRADO - Não use glow em tudo
.card {
  box-shadow: $glow-primary;  // NÃO! Muito exagerado
}
```

## 🔄 Transições

```scss
$transition-base: all 0.2s ease-in-out;
$transition-fast: all 0.15s ease-in-out;
$transition-slow: all 0.3s ease-in-out;
$transition-fade: opacity 0.2s ease-in-out;
$transition-collapse: height 0.35s ease;
$transition-transform: transform 0.2s ease-in-out;
```

### Animações Suaves

```scss
// Hover states
.interactive-element {
  transition: $transition-base;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: $box-shadow-lg;
  }
}

// Fade in
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

// Slide in
@keyframes slideIn {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}
```

## 🪟 Glassmorphism (Uso Sutil)

> **Importante:** Use glassmorphism com moderação. Não é cyberpunk, é elegância.

```scss
// Glassmorphism sutil (para modais, dropdowns, tooltips)
.glass-effect {
  background: rgba(23, 26, 33, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

// Glassmorphism mais forte (para sidebars, headers)
.glass-effect-strong {
  background: rgba(23, 26, 33, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
```

### Quando Usar Glassmorphism

```tsx
// ✅ CORRETO - Modal overlay
<Modal className="glass-effect">
  <ModalContent />
</Modal>

// ✅ CORRETO - Dropdown menu
<Dropdown className="glass-effect">
  <DropdownItems />
</Dropdown>

// ✅ CORRETO - Sidebar flutuante
<Sidebar className="glass-effect-strong">
  <Navigation />
</Sidebar>

// ❌ ERRADO - Não use em cards comuns
<Card className="glass-effect">  // NÃO! Use background sólido
  <CardContent />
</Card>
```

## 🌈 Gradientes (Uso Minimalista)

> **Importante:** Gradientes sutis, não arco-íris. Pense Linear/Vercel, não anos 90.

```scss
// Gradientes sutis para backgrounds
$gradient-primary: linear-gradient(135deg, 
  rgba(59, 130, 246, 0.1) 0%, 
  rgba(34, 211, 238, 0.05) 100%
);

$gradient-surface: linear-gradient(180deg,
  rgba(23, 26, 33, 1) 0%,
  rgba(15, 17, 21, 1) 100%
);

// Gradiente dourado (RARO - apenas para destaques premium)
$gradient-gold: linear-gradient(135deg,
  rgba(212, 160, 23, 0.2) 0%,
  rgba(212, 160, 23, 0.05) 100%
);

// Gradiente para texto (uso muito raro)
$gradient-text-primary: linear-gradient(135deg,
  #3B82F6 0%,
  #22D3EE 100%
);
```

### Quando Usar Gradientes

```tsx
// ✅ CORRETO - Background sutil em hero sections
<HeroSection style={{ background: gradientPrimary }}>
  <HeroContent />
</HeroSection>

// ✅ CORRETO - Card premium (RARO)
<PremiumCard style={{ background: gradientGold }}>
  <UpgradeOffer />
</PremiumCard>

// ✅ CORRETO - Texto de destaque (muito raro)
<h1 style={{ 
  background: gradientTextPrimary,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent'
}}>
  Bem-vindo ao Runas
</h1>

// ❌ ERRADO - Não use gradientes vibrantes demais
<Card style={{ 
  background: 'linear-gradient(red, blue, green)'  // NÃO!
}}>
```

### Regras de Gradientes

1. **Máximo 2 cores** por gradiente
2. **Opacidade baixa** (0.05 a 0.2)
3. **Transições suaves** (não abruptas)
4. **Uso estratégico** (não em todo lugar)
5. **Teste o contraste** (texto deve ser legível)

## ♿ Acessibilidade

### Contraste Mínimo (WCAG AA) - Dark Mode

- **Texto normal (16px)**: 4.5:1 mínimo
- **Texto grande (18px+ ou bold 14px+)**: 3:1 mínimo
- **Componentes UI**: 3:1 mínimo
- **Ícones interativos**: 3:1 mínimo

### Verificação de Contraste

```scss
// ✅ CORRETO - Contraste adequado
$text-primary: #E5E7EB;         // Contraste 12.6:1 com #0F1115
$text-secondary: #94A3B8;       // Contraste 7.2:1 com #0F1115

// ⚠️ ATENÇÃO - Contraste limite (use apenas para texto grande)
$text-tertiary: #64748B;        // Contraste 4.5:1 com #0F1115

// ❌ EVITAR - Contraste insuficiente
$text-disabled: #475569;        // Contraste 3.2:1 - apenas para disabled
```

### Foco Visível (Keyboard Navigation)

```scss
$focus-ring-width: 2px;
$focus-ring-offset: 2px;
$focus-ring-color: $primary;
$focus-ring-style: solid;

// Aplicação
*:focus-visible {
  outline: $focus-ring-width $focus-ring-style $focus-ring-color;
  outline-offset: $focus-ring-offset;
  border-radius: 0.25rem;
}

// Alternativa com box-shadow (para elementos arredondados)
.btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px $primary-light;
}
```

### Touch Targets (Mobile)

```scss
// Tamanho mínimo para elementos interativos
$touch-target-min: 44px;

.btn, .link, .icon-button {
  min-width: $touch-target-min;
  min-height: $touch-target-min;
}
```

### Screen Readers

```tsx
// Labels descritivos
<button aria-label="Adicionar novo cliente">
  <FiPlus />
</button>

// Status dinâmicos
<div role="status" aria-live="polite">
  {loading ? 'Carregando...' : 'Dados carregados'}
</div>

// Navegação por landmarks
<nav aria-label="Navegação principal">
  <ul>...</ul>
</nav>

<main aria-label="Conteúdo principal">
  {children}
</main>
```

### Redução de Movimento

```scss
// Respeitar preferência do usuário
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 🎨 Ícones

### React Icons

```typescript
import {
  FiHome,           // Home
  FiUsers,          // Clientes
  FiPackage,        // Produtos
  FiShoppingCart,   // Vendas
  FiBox,            // Estoque
  FiDollarSign,     // Financeiro
  FiSettings,       // Configurações
  FiLogOut,         // Logout
  FiPlus,           // Adicionar
  FiEdit,           // Editar
  FiTrash2,         // Deletar
  FiEye,            // Visualizar
  FiSearch,         // Buscar
  FiFilter,         // Filtrar
  FiDownload,       // Download
  FiUpload,         // Upload
  FiCheck,          // Confirmar
  FiX,              // Cancelar
  FiAlertCircle,    // Alerta
  FiInfo,           // Info
} from 'react-icons/fi';
```

### Tamanhos

```typescript
<FiHome size={16} />  // Pequeno
<FiHome size={20} />  // Médio (padrão)
<FiHome size={24} />  // Grande
<FiHome size={32} />  // Extra grande
```

## 📐 Layout

### Container

```scss
$container-max-widths: (
  sm: 540px,
  md: 720px,
  lg: 960px,
  xl: 1140px,
  xxl: 1320px
);
```

### Grid

```scss
$grid-columns: 12;
$grid-gutter-width: 1.5rem;  // 24px
```

## 🎯 Estados de Componentes

### Loading

- Skeleton loaders (react-loading-skeleton)
- Spinner para ações
- Progress bar para uploads

### Empty

- Ilustração + mensagem + ação
- Centralizado vertical e horizontalmente

### Error

- Mensagem clara
- Botão de retry
- Ícone de erro

### Success

- Toast notification (3 segundos)
- Cor verde
- Ícone de check

## 📱 Mobile First

### Princípios

1. Design para mobile primeiro
2. Progressive enhancement para desktop
3. Touch targets mínimo 44x44px
4. Espaçamento generoso em mobile
5. Navegação simplificada

### Adaptações Mobile

- Menu lateral → Drawer
- Tabelas → Cards ou scroll horizontal
- Formulários → 1 coluna
- Modais → Full screen
- Botões → Full width

---

## 🎨 Filosofia Visual Runas

### Inspirações

- **Linear**: Minimalismo, clareza, foco no conteúdo
- **Vercel**: Dark mode sofisticado, tipografia limpa
- **Stripe**: Profissionalismo, confiança, elegância
- **Notion**: Usabilidade, hierarquia clara, espaçamento generoso

### O Que Somos

✅ **Ferramenta operacional moderna**  
✅ **Interface inteligente e clara**  
✅ **Design profissional e confiável**  
✅ **Experiência fluida e eficiente**

### O Que NÃO Somos

❌ Software fiscal legado  
❌ Interface cyberpunk/neon  
❌ Design exagerado ou chamativo  
❌ Gradientes arco-íris  
❌ Glow effects excessivos

### Princípios de Design

1. **Clareza sobre estilo**: Função antes de forma
2. **Espaçamento generoso**: Respire, não sufoque
3. **Hierarquia visual clara**: Usuário sabe onde olhar
4. **Feedback imediato**: Toda ação tem resposta visual
5. **Consistência**: Mesmos padrões em todo o sistema
6. **Performance**: Animações suaves, carregamento rápido
7. **Acessibilidade**: Todos podem usar, sempre

### Checklist de Qualidade Visual

Antes de considerar um componente pronto, verifique:

- [ ] Contraste de texto adequado (WCAG AA)
- [ ] Foco visível em todos os elementos interativos
- [ ] Touch targets mínimo 44x44px em mobile
- [ ] Transições suaves (200-300ms)
- [ ] Estados hover/active/disabled claros
- [ ] Espaçamento consistente (múltiplos de 8px)
- [ ] Dourado usado no máximo 3x por tela
- [ ] Vermelho apenas para erros críticos
- [ ] Glassmorphism usado com moderação
- [ ] Gradientes sutis (não vibrantes)
- [ ] Responsivo em todos os breakpoints
- [ ] Loading states para ações assíncronas
- [ ] Empty states com ação clara
- [ ] Error states com retry

### Exemplos de Uso Correto

```tsx
// ✅ Card de Dashboard - Minimalista e funcional
<Card className="bg-surface border-default">
  <CardHeader>
    <h3 className="text-primary">Vendas do Mês</h3>
  </CardHeader>
  <CardContent>
    <p className="text-4xl font-bold text-primary">R$ 45.230</p>
    <p className="text-sm text-secondary">+12% vs mês anterior</p>
  </CardContent>
</Card>

// ✅ Badge de Status - Cores semânticas corretas
<Badge variant="confirmed" className="bg-primary-light text-primary">
  Confirmado
</Badge>

// ✅ Botão Premium - Uso raro de dourado
<Button 
  variant="gold" 
  className="bg-accent-gold-light text-accent-gold border-accent-gold"
>
  <FiStar /> Upgrade para Pro
</Button>

// ✅ Input com foco - Feedback visual claro
<Input
  className="bg-surface border-default focus:border-primary focus:ring-primary-light"
  placeholder="Buscar cliente..."
/>
```

### Exemplos de Uso INCORRETO

```tsx
// ❌ Uso excessivo de dourado
<Card className="border-accent-gold">  // NÃO!
  <h3 className="text-accent-gold">Título</h3>  // NÃO!
  <Button className="bg-accent-gold">Ação</Button>  // NÃO!
</Card>

// ❌ Vermelho para status neutro
<Badge variant="error">Pendente</Badge>  // NÃO! Use cinza

// ❌ Gradiente vibrante demais
<div style={{ 
  background: 'linear-gradient(red, blue, green, yellow)'  // NÃO!
}}>

// ❌ Glassmorphism em tudo
<Card className="glass-effect">  // NÃO! Use apenas em overlays
  <CardContent />
</Card>
```

---

## 📚 Recursos Adicionais

### Ferramentas Recomendadas

- **Contrast Checker**: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- **Color Palette**: [Coolors.co](https://coolors.co/)
- **Icons**: [React Icons](https://react-icons.github.io/react-icons/)
- **Fonts**: [Google Fonts - Inter](https://fonts.google.com/specimen/Inter)

### Referências de Design

- [Linear Design System](https://linear.app/)
- [Vercel Design](https://vercel.com/design)
- [Stripe Design](https://stripe.com/docs/design)
- [Notion Design](https://www.notion.so/)

---

**Versão:** 2.0.0  
**Data:** 2026-05-25  
**Status:** ✅ Design System Completo - Runas Identity  
**Última Atualização:** Nova paleta de cores e filosofia visual
