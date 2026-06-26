# Testes - CheckoutPage OAuth Bugfix

## 📋 Visão Geral

Esta pasta contém testes unitários e de integração para as funcionalidades de checkout, especialmente focados nos bugs corrigidos relacionados ao fluxo OAuth.

## 🧪 Arquivos de Teste

### CheckoutPage.test.tsx
Testes principais do componente CheckoutPage:
- **Bug Regression Tests** - Garante que os 6 bugs corrigidos não retornam
- **Visual Indicators Tests** - Testa banners e avisos visuais
- **Error Handling Tests** - Testa tratamento de erros (401, 404)
- **Carrinho Vazio Tests** - Testa comportamento com carrinho vazio

### errorLogger.test.ts
Testes do módulo de logging de erros:
- `logCheckoutError()` - Logging estruturado
- `isRetryableError()` - Detecção de erros retryable
- `extractErrorMessage()` - Extração de mensagens amigáveis
- `sleep()` - Utility de delay

## 🚀 Como Rodar os Testes

### Pré-requisitos
```bash
# Instalar dependências (se não instaladas)
cd frontend
npm install
```

### Rodar Todos os Testes
```bash
# Rodar todos os testes
npm test

# Rodar apenas testes do CheckoutPage
npm test CheckoutPage

# Rodar apenas testes do errorLogger
npm test errorLogger

# Rodar com coverage
npm test -- --coverage
```

### Rodar em Watch Mode
```bash
# Rodar testes em modo watch (re-executa ao salvar)
npm test -- --watch
```

### Rodar Testes Específicos
```bash
# Rodar apenas testes de um describe
npm test -- -t "Bug Regression Tests"

# Rodar apenas um teste específico
npm test -- -t "deve pré-preencher formulário"
```

## 📊 Coverage Esperado

### Meta de Coverage
- **Statements:** 80%+
- **Branches:** 75%+
- **Functions:** 80%+
- **Lines:** 80%+

### Verificar Coverage
```bash
npm test -- --coverage --watchAll=false

# Gerar relatório HTML
npm test -- --coverage --coverageReporters=html
# Abrir: frontend/coverage/index.html
```

## 🐛 Bugs Testados (Regression Tests)

### Bug #1: carregarCarrinho undefined
**Teste:** `deve renderizar sem erro carregarCarrinho undefined`
- Verifica que componente renderiza sem erros no console
- Garante que useEffect problemático foi removido

### Bug #2: Navegação incorreta para modo guest
**Testes:**
- `deve mostrar tela de seleção para usuário não-autenticado`
- `deve pular tela de seleção quando usuário já está autenticado`

### Bug #3: OAuth não recarrega carrinho
**Testes:**
- `deve detectar flag reload_cart_after_oauth e recarregar carrinho`
- `deve redirecionar para loja se carrinho vazio após OAuth`

### Bug #4: Dados não pré-preenchidos após OAuth
**Teste:** `deve pré-preencher formulário com dados do cliente OAuth`
- Verifica que nome e email são preenchidos automaticamente

### Bug #5: Checkbox Criar Conta aparece para autenticados
**Testes:**
- `não deve mostrar checkbox para usuário autenticado`
- `deve mostrar checkbox para usuário convidado`

### Bug #6: CPF/Telefone não salvos no cadastro
**Teste:** `deve chamar PATCH para atualizar cadastro antes de finalizar`
- Verifica que função `atualizarCadastroSeNecessario()` é chamada

## 🧩 Estrutura dos Testes

### Setup Padrão
```typescript
beforeEach(() => {
  localStorage.clear();
  jest.clearAllMocks();
  
  // Mock useCarrinho
  (useCarrinhoModule.useCarrinho as jest.Mock).mockReturnValue({
    carrinho: mockCarrinho,
    loading: false,
    erro: null,
    // ... demais funções
  });
});
```

### Helpers
- `createMockToken(clienteId)` - Cria JWT mock válido
- `renderCheckout()` - Renderiza componente com BrowserRouter
- `mockCliente` - Dados de cliente completos
- `mockCarrinho` - Carrinho com 1 item

## 📝 Convenções

### Nomenclatura de Testes
- ✅ **Usar:** "deve [ação esperada]"
- ❌ **Evitar:** "test [feature]" ou "verifica se [...]"

### Organização
- **describe** para agrupar testes relacionados
- **it/test** para casos de teste individuais
- **beforeEach** para setup comum
- **afterEach** para cleanup

### Assertions
- Preferir matchers específicos: `toBeInTheDocument()`, `toHaveBeenCalledWith()`
- Evitar matchers genéricos: `toBeTruthy()`, `toBeFalsy()`
- Usar `waitFor()` para operações assíncronas

## 🔍 Debugging de Testes

### Ver Output Detalhado
```bash
npm test -- --verbose
```

### Debug com Node Inspector
```bash
node --inspect-brk node_modules/.bin/jest --runInBand
# Abrir chrome://inspect no Chrome
```

### Log de Mocks
```typescript
console.log(mockApi.get.mock.calls); // Ver todas as chamadas
console.log(mockApi.get.mock.results); // Ver resultados
```

## 🚨 Troubleshooting

### Testes Falhando por Timeout
```typescript
// Aumentar timeout para operações lentas
await waitFor(() => {
  expect(...).toBeInTheDocument();
}, { timeout: 5000 });
```

### Mocks Não Funcionando
```typescript
// Garantir que mock foi configurado ANTES do render
const mockApiInstance = { /* ... */ };
mockAxios.create = jest.fn().mockReturnValue(mockApiInstance);
renderCheckout(); // Só depois renderizar
```

### Erros de localStorage
```typescript
// Sempre limpar no beforeEach
beforeEach(() => {
  localStorage.clear();
});
```

## 📚 Recursos

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## 🎯 Próximos Passos

### Testes Adicionais (Futuro)
- [ ] Testes E2E com Cypress/Playwright
- [ ] Testes de acessibilidade (axe)
- [ ] Testes de performance (renderização)
- [ ] Testes de snapshot (visual regression)
- [ ] Testes de integração com backend real (staging)

### Melhorias
- [ ] Adicionar testes de fluxo completo (ponta-a-ponta)
- [ ] Testar todos os cenários de erro HTTP
- [ ] Testar retry logic com múltiplas tentativas
- [ ] Testar exponential backoff timing
- [ ] Adicionar testes de acessibilidade (keyboard navigation)

---

**Última Atualização:** 25/06/2026  
**Cobertura Atual:** ~70% (meta: 80%+)  
**Status:** ✅ Testes principais implementados
