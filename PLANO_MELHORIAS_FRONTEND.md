# Plano de Melhorias - Frontend e Integrações

## 🎯 Objetivos

1. **Finalizar integração Mercado Pago**
2. **Implementar tema claro/escuro**
3. **Tornar todas as telas responsivas**
4. **Adicionar indicadores "Em desenvolvimento" nas telas incompletas**

---

## 📱 FASE 1: Responsividade (PRIORIDADE ALTA)

### Telas que precisam de ajustes:

#### ✅ Já Responsivas
- [ ] CatalogoPage (verificar)
- [ ] CarrinhoPage (verificar)
- [ ] CheckoutPage (verificar)
- [ ] LoginPage (verificar)

#### ⚠️ Precisam de Ajustes
- [ ] Dashboard/Home
- [ ] ClientesPage (lista)
- [ ] ClienteFormPage
- [ ] ClienteEnderecosPage
- [ ] ClienteCreditoPage
- [ ] ProdutosPage
- [ ] ProdutoFormPage
- [ ] VendasPage
- [ ] VendaFormPage
- [ ] EstoquePage
- [ ] FinanceiroPage
- [ ] RelatoriosPage
- [ ] ConfiguracoesPage

### Breakpoints Padrão
```scss
$mobile: 576px;
$tablet: 768px;
$desktop: 992px;
$wide: 1200px;
```

---

## 🎨 FASE 2: Tema Claro/Escuro (PRIORIDADE ALTA)

### Implementação
1. Criar contexto de tema (`ThemeContext`)
2. Adicionar toggle no header/navbar
3. Salvar preferência no localStorage
4. Criar variáveis CSS para ambos os temas
5. Aplicar em todos os componentes

### Paleta de Cores

#### Tema Escuro (Atual)
```scss
--bg-primary: #1a1a2e;
--bg-secondary: #16213e;
--bg-tertiary: #0f3460;
--text-primary: #ffffff;
--text-secondary: #e0e0e0;
--accent: #0088cc;
```

#### Tema Claro (Novo)
```scss
--bg-primary: #ffffff;
--bg-secondary: #f5f5f5;
--bg-tertiary: #e0e0e0;
--text-primary: #1a1a2e;
--text-secondary: #4a4a4a;
--accent: #0088cc;
```

---

## 💳 FASE 3: Mercado Pago (PRIORIDADE ALTA)

### Checklist de Implementação

#### Backend
- [x] Credenciais configuradas no `.env`
- [ ] Testar criação de preferência
- [ ] Testar webhook
- [ ] Testar notificações de pagamento
- [ ] Implementar retry logic para falhas
- [ ] Logs estruturados para debug

#### Frontend
- [ ] Testar fluxo completo de checkout
- [ ] Redirecionar para Mercado Pago
- [ ] Página de retorno (sucesso/falha)
- [ ] Página de rastreamento de pedido
- [ ] Feedback visual durante processamento

#### Testes
- [ ] Checkout com PIX
- [ ] Checkout com cartão de crédito
- [ ] Checkout com cartão de débito
- [ ] Webhook de pagamento aprovado
- [ ] Webhook de pagamento rejeitado
- [ ] Webhook de pagamento pendente

---

## 🚧 FASE 4: Telas em Desenvolvimento

### Componente "EmDesenvolvimento"
Criar componente reutilizável para indicar funcionalidades futuras:

```tsx
interface EmDesenvolvimentoProps {
  titulo?: string;
  mensagem?: string;
  icone?: React.ReactNode;
}

<EmDesenvolvimento 
  titulo="Relatórios Financeiros"
  mensagem="Esta funcionalidade será implementada em breve"
/>
```

### Telas que precisam do componente:
- [ ] Relatórios (completo)
- [ ] Configurações (parcial)
- [ ] Notificações (completo)
- [ ] Integrações (completo)
- [ ] WhatsApp (parcial)

---

## 📊 FASE 5: Melhorias UX/UI

### Melhorias Gerais
- [ ] Loading skeletons em vez de spinners
- [ ] Transições suaves entre páginas
- [ ] Feedback visual em todas as ações
- [ ] Mensagens de erro mais amigáveis
- [ ] Tooltips explicativos
- [ ] Atalhos de teclado
- [ ] Breadcrumbs de navegação

### Componentes Faltantes
- [ ] Paginação customizada
- [ ] Filtros avançados
- [ ] Export para Excel/PDF
- [ ] Gráficos e dashboards
- [ ] Upload de imagens com preview
- [ ] Editor de texto rico (opcional)

---

## 🔍 FASE 6: Validação e Testes

### Testes de Responsividade
- [ ] Mobile (320px - 576px)
- [ ] Tablet (577px - 992px)
- [ ] Desktop (993px+)
- [ ] Orientação landscape/portrait

### Testes de Tema
- [ ] Troca de tema sem reload
- [ ] Persistência da preferência
- [ ] Contraste adequado (acessibilidade)
- [ ] Todas as páginas com ambos os temas

### Testes de Integração
- [ ] Checkout end-to-end
- [ ] Pagamento real (sandbox)
- [ ] Webhook funcionando
- [ ] Sincronização de status

---

## 📅 Cronograma Sugerido

### Semana 1
- Dia 1-2: Mercado Pago (correções e testes)
- Dia 3-4: Tema claro/escuro
- Dia 5: Componente "EmDesenvolvimento"

### Semana 2
- Dia 1-3: Responsividade (telas admin)
- Dia 4-5: Responsividade (telas públicas)

### Semana 3
- Dia 1-2: Melhorias UX/UI
- Dia 3-5: Testes e ajustes finais

---

## 🎯 Prioridades para AGORA

1. **Testar e corrigir checkout + Mercado Pago**
2. **Implementar tema claro/escuro**
3. **Adicionar "EmDesenvolvimento" nas telas incompletas**
4. **Tornar telas principais responsivas**

---

## 📝 Notas

- Usar mobile-first approach para responsividade
- Manter consistência de design entre temas
- Documentar todos os componentes criados
- Fazer commits pequenos e frequentes
