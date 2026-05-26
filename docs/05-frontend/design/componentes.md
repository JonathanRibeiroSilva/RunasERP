# Componentes - Design System Runas

> **Especificação de componentes UI: botões, cards, inputs, modais, tabelas e badges**

---

## 🔲 Botões

### Tamanhos

```scss
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
```

### Variantes (Dark Mode)

```scss
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

---

## 📇 Cards

### Estilos Base

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

---

## 📝 Inputs

### Estilos Base

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

---

## 🪟 Modais

### Estilos Base

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

---

## 📊 Tabelas

### Estilos Base

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

---

## 🏷️ Badges

### Estilos Base

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

---

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

---

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

---

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

---

## 📚 Exemplos de Uso Correto

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

---

## ❌ Exemplos de Uso INCORRETO

```tsx
// ❌ Uso excessivo de dourado
<Card className="border-accent-gold">  // NÃO!
  <h3 className="text-accent-gold">Título</h3>  // NÃO!
  <Button className="bg-accent-gold">Ação</Button>  // NÃO!
</Card>

// ❌ Vermelho para status neutro
<Badge variant="error">Pendente</Badge>  // NÃO! Use cinza

// ❌ Glassmorphism em tudo
<Card className="glass-effect">  // NÃO! Use apenas em overlays
  <CardContent />
</Card>
```

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 2.0.0
