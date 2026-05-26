# Layouts e Responsividade - Design System Runas

> **Breakpoints, grid, containers, mobile first e filosofia visual**

---

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

---

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

---

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

---

## ✅ Checklist de Qualidade Visual

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

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 2.0.0  
**Status:** ✅ Design System Completo - Runas Identity
