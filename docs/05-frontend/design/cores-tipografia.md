# Cores e Tipografia - Design System Runas

> **Paleta de cores, tipografia, espaçamentos e sombras**

---

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

---

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

---

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

---

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

---

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

---

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

---

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

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 2.0.0
