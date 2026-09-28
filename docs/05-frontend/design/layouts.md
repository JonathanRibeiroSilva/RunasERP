# Layouts e Responsividade - Design System Runas

> **Breakpoints, estrutura do layout autenticado, mobile e filosofia visual**
>
> Fonte da verdade: `frontend/src/styles/` (`variables.scss`, `mixins.scss`, `global.scss`) e `frontend/src/components/layout/`. Se este documento divergir do código, vale o código.

---

## 📱 Breakpoints Responsivos

### Mixins do projeto

`frontend/src/styles/mixins.scss` define cinco mixins (não há `xxl`):

```scss
@mixin media-xs { @media (max-width: 575px) { @content; } }
@mixin media-sm { @media (min-width: 576px) { @content; } }
@mixin media-md { @media (min-width: 768px) { @content; } }
@mixin media-lg { @media (min-width: 992px) { @content; } }
@mixin media-xl { @media (min-width: 1200px) { @content; } }
```

E `variables.scss` mantém os valores como variáveis legadas:

```scss
$breakpoint-xs: 0;
$breakpoint-sm: 576px;
$breakpoint-md: 768px;
$breakpoint-lg: 992px;
$breakpoint-xl: 1200px;
```

Os componentes `Responsive*` usam essas variáveis no formato desktop-first, por exemplo `@media (max-width: #{$breakpoint-md - 1px})`.

### Breakpoints do Bootstrap

O Bootstrap entra compilado (`import 'bootstrap/dist/css/bootstrap.min.css'` em `frontend/src/main.tsx`), então o projeto não redefine `$grid-breakpoints`, `$container-max-widths` nem `$grid-columns`. As classes utilitárias e de grid do Bootstrap (`col-md-*`, `d-lg-none` etc.) seguem os valores padrão do Bootstrap 5.3, que incluem `xxl` (1400px).

### Pontos de quebra usados de fato no layout

| Largura | Onde | Efeito |
|---------|------|--------|
| `< 768px` | `MainLayout.tsx` (JS, `window.innerWidth < 768`) | Modo mobile: sidebar vira drawer com backdrop |
| `≤ 767px` | `Navbar.scss` | Esconde o texto "RUNAS" e o nome do usuário |
| `≤ 992px` | `Navbar.scss` | Esconde os rótulos dos botões (só ícones) |
| `≤ 1024px` | `DashboardPage.scss` | Linhas do dashboard passam para 1 coluna |
| `≤ 575px` | `MainLayout.scss` | Padding do conteúdo cai de 16px para 12px |

---

## 📐 Layout autenticado

Toda rota protegida renderiza dentro de `MainLayout` (`frontend/src/components/layout/MainLayout/`):

```
.main-layout (100vh, coluna, overflow hidden)
├── Navbar (.navbar, 64px, sticky)
├── .sidebar-backdrop (só mobile com sidebar aberta)
└── .layout-container (flex)
    ├── Sidebar (aside.sidebar, 220px)
    └── main.main-content (rolagem própria)
        └── .content-wrapper (max-width 1600px, centralizado)
            └── ErrorBoundary → <Outlet />
```

Não há footer nem breadcrumbs.

### Navbar (header)

`frontend/src/components/layout/Navbar/`:
- Altura **64px**, `position: sticky; top: 0`, `z-index: $z-index-fixed` (300), padding lateral de 1.5rem.
- Conteúdo numa "cápsula" (`.navbar-capsule`) com fundo `$surface`, borda `$border-default`, cantos inferiores arredondados (12px) e `backdrop-filter: blur(12px)`.
- Esquerda: botão que alterna a sidebar (rótulo "DASHBOARD"; ícone `FiX` com a sidebar aberta, `FiArrowLeft` fechada), divisor e marca (logo `img/logo1.png` + "RUNAS").
- Centro: vazio.
- Direita: bloco do usuário (gradiente `$primary`, leva a `/perfil`) e botão "LOGOUT" (hover em `$error`).

### Sidebar

`frontend/src/components/layout/Sidebar/`:
- Largura **220px**, fundo `rgba(16, 20, 29, 0.6)` com `blur(20px)`, borda direita `$border-default`.
- Fixa abaixo da navbar (`top: 64px`); abre e fecha por `transform: translateX(...)`.
- Itens com `min-height: 44px`; item ativo com gradiente `$primary-light` e barra interna de 3px em `$primary`. Subitens com `min-height: 36px`.
- Menus com submenu: Loja Online, Produtos, Plataforma e Configurações. Plataforma tem "Visão Geral" (`/plataforma`, com `end: true`, para não ficar ativo junto com `/plataforma/tenants`) e "Lojistas" (`/plataforma/tenants`); subitens aceitam o campo opcional `end`, repassado ao `NavLink`. O estado de expansão é manual; na primeira renderização expande o grupo da rota atual.
- Visibilidade por papel via `podeVer(role, requiredRole)` (testado em `Sidebar/__tests__/podeVer.test.ts`): item sem `requiredRole` é de tenant e fica oculto para `SUPER_ADMIN`; Financeiro e Configurações só para `ADMIN`; Plataforma só para `SUPER_ADMIN` (os subitens repetem `requiredRole: ['SUPER_ADMIN']`, senão seriam tratados como itens de tenant e sumiriam para ele); Meu Perfil para os três papéis.
- "Minha Loja" abre `/c/<slug>` em nova aba.

### Área de conteúdo

- `.main-content`: `flex: 1`, `overflow-y: auto`, scrollbar customizada (`custom-scrollbar`). No desktop com sidebar aberta, `margin-left: 220px` (transição `$transition-base`, 250ms).
- `.content-wrapper`: `padding: $spacer-4` (16px; 12px abaixo de 576px), `max-width: 1600px`, `margin: 0 auto`, animação de entrada `fadeSlideUp`.

### Z-index

Escala em `variables.scss`: dropdown 100, sticky 200, fixed 300, modal-backdrop 400, modal 500, tooltip 600. A navbar usa `fixed`; sidebar desktop e backdrop usam `sticky`; a sidebar mobile usa `modal`.

---

## 📱 Mobile

### Comportamento implementado (< 768px)

- A sidebar começa fechada e vira drawer sobre o conteúdo, com fundo sólido `$surface` e `$shadow-lg`.
- Backdrop `rgba(8, 10, 15, 0.8)` com `blur(4px)` abaixo da navbar; clicar nele (ou Enter/Espaço) fecha o menu.
- Botão de fechar (`FiX`) dentro da sidebar.
- Clicar num link fecha a sidebar.
- Com a sidebar aberta, o `body` fica com `overflow: hidden`.
- Ao voltar para ≥ 768px, a sidebar reabre sozinha.

### Diretrizes (não garantidas pelo código)

- Touch targets de pelo menos 44x44px (os itens principais da sidebar já seguem isso; subitens têm 36px).
- Formulários em 1 coluna.
- Tabelas com scroll horizontal: `ResponsiveTable` impõe `min-width: 600px` abaixo de 768px, mas hoje nenhuma página usa `ResponsiveTable`, `ResponsiveCard` ou `ResponsiveContainer`; cada página tem SCSS próprio.

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

---

## ✅ Checklist de Qualidade Visual

Antes de considerar um componente pronto, verifique:

- [ ] Contraste de texto adequado (WCAG AA)
- [ ] Foco visível em todos os elementos interativos (`focus-ring` / `focus-glow`)
- [ ] Touch targets mínimo 44x44px em mobile
- [ ] Transições com os tokens `$transition-fast` (150ms), `$transition-base` (250ms) ou `$transition-slow` (400ms)
- [ ] Estados hover/active/disabled claros
- [ ] Espaçamento com os tokens `$spacer-*` de `variables.scss`
- [ ] Cores só via tokens de `variables.scss` (nada de hex solto)
- [ ] Vermelho (`$error`) apenas para erros e ações destrutivas
- [ ] Glassmorphism (`glass-panel`) usado com moderação
- [ ] Gradientes sutis (não vibrantes)
- [ ] Testado abaixo de 576px, abaixo de 768px e em desktop
- [ ] Loading states para ações assíncronas
- [ ] Empty states com ação clara
- [ ] Error states com retry

---

## 📚 Recursos Adicionais

### Ferramentas Recomendadas

- **Contrast Checker**: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- **Color Palette**: [Coolors.co](https://coolors.co/)
- **Icons**: [React Icons](https://react-icons.github.io/react-icons/) (o projeto usa o conjunto Feather, `react-icons/fi`)
- **Fonts**: [Google Fonts - Inter](https://fonts.google.com/specimen/Inter)

### Referências de Design

- [Linear](https://linear.app/)
- [Vercel Design](https://vercel.com/design)
- [Stripe Design](https://stripe.com/docs/design)
- [Notion](https://www.notion.so/)

### Documentos relacionados

- [Design Document](./design.md)
- [Cores e Tipografia](./cores-tipografia.md)
- [Componentes](./componentes.md)
