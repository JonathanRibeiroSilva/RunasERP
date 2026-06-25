# Guia de Teste Manual - Checkout OAuth

## 🎯 Objetivo
Testar o fluxo completo de checkout com OAuth (Google/Microsoft) após as correções implementadas.

---

## 🔧 Pré-requisitos

### 1. Serviços Rodando
```bash
docker ps
# Verificar que todos estão "Up" e "healthy"
```

### 2. Limpar Estado Anterior
```javascript
// No DevTools Console (F12)
localStorage.clear()
location.reload()
```

---

## 📝 Cenários de Teste

### ✅ Cenário 1: Fluxo OAuth Google - Novo Usuário

**Objetivo:** Testar login OAuth com usuário sem cadastro prévio

**Steps:**
1. **Limpar localStorage**
   ```javascript
   localStorage.clear()
   ```

2. **Acessar loja**
   - URL: `https://www.runaserp.com.br/distribuidora-central`
   - Verificar que loja carrega

3. **Adicionar produto ao carrinho**
   - Clicar em qualquer produto
   - Clicar "Adicionar ao Carrinho"
   - Verificar toast "Produto adicionado"

4. **Ir para checkout**
   - Clicar no ícone do carrinho (topo direito)
   - Clicar "Finalizar Compra"
   - **Verificar:** Tela de seleção aparece (2 cards)

5. **Iniciar login OAuth**
   - Clicar "Fazer Login"
   - Clicar "Entrar com Google"
   - **Verificar:** Redirect para Google

6. **Completar OAuth Google**
   - Fazer login com conta Google
   - Aceitar permissões
   - **Verificar:** Redirect de volta para checkout

7. **Verificar retorno ao checkout**
   - **Esperado:**
     - ✅ Toast "Login realizado com sucesso!"
     - ✅ Carrinho mantido (produtos visíveis no resumo lateral)
     - ✅ Formulário Step 1 visível
     - ✅ Banner verde "Login realizado com sucesso!" no topo
     - ✅ Nome pré-preenchido (do Google)
     - ✅ Email pré-preenchido (do Google)
     - ✅ Campos editáveis (pode mudar)
     - ✅ CPF e Telefone vazios
     - ✅ Aviso amarelo "Recomendamos preencher estes dados"
     - ✅ Checkbox "Criar Conta" NÃO aparece

8. **Preencher dados adicionais**
   - Telefone: `(11) 98765-4321`
   - CPF: `123.456.789-01`
   - **Verificar:** Aviso amarelo desaparece

9. **Continuar para Step 2**
   - Clicar "Continuar"
   - Selecionar tipo de entrega
   - Preencher endereço (se delivery)
   - Clicar "Continuar"

10. **Finalizar no Step 3**
    - Selecionar forma de pagamento
    - Clicar "Finalizar Pedido"
    - **Verificar:** Pedido criado com sucesso

**Acceptance Criteria:**
- [ ] Carrinho mantido após OAuth
- [ ] Dados pré-preenchidos (nome, email)
- [ ] Banner OAuth visível
- [ ] Campos editáveis
- [ ] Aviso CPF/Telefone aparece e desaparece
- [ ] Checkbox "Criar Conta" não aparece
- [ ] Pedido finaliza com sucesso
- [ ] CPF/Telefone salvos no cadastro

---

### ✅ Cenário 2: Fluxo OAuth - Usuário Existente

**Objetivo:** Testar retorno de usuário já cadastrado via OAuth

**Steps:**
1. **Limpar localStorage** (simular nova sessão)
   ```javascript
   localStorage.clear()
   location.reload()
   ```

2. **Adicionar produto ao carrinho**

3. **Ir para checkout**
   - **Verificar:** Tela de seleção aparece

4. **Fazer login OAuth**
   - Clicar "Fazer Login"
   - Clicar "Entrar com Google"
   - Usar MESMA conta do Cenário 1
   - **Verificar:** Redirect de volta

5. **Verificar dados pré-preenchidos**
   - **Esperado:**
     - ✅ Nome pré-preenchido
     - ✅ Email pré-preenchido
     - ✅ CPF pré-preenchido (do cadastro anterior)
     - ✅ Telefone pré-preenchido (do cadastro anterior)
     - ✅ Aviso amarelo NÃO aparece (dados completos)
     - ✅ Banner verde visível

6. **Editar CPF**
   - Mudar CPF para `987.654.321-00`
   - Continuar até Step 3
   - Finalizar pedido
   - **Verificar:** Cadastro atualizado com novo CPF

**Acceptance Criteria:**
- [ ] Dados completos pré-preenchidos
- [ ] Aviso não aparece (dados completos)
- [ ] Pode editar dados
- [ ] Atualização de CPF funciona
- [ ] Pedido finaliza

---

### ✅ Cenário 3: Acesso Direto Autenticado

**Objetivo:** Testar quando usuário já está logado e entra no checkout

**Steps:**
1. **Verificar token existe**
   ```javascript
   localStorage.getItem('cliente_token')
   // Deve retornar um token válido
   ```

2. **Adicionar produto ao carrinho**

3. **Ir para checkout**
   - **Verificar:** 
     - ✅ Tela de seleção NÃO aparece
     - ✅ Vai DIRETO para Step 1
     - ✅ Dados pré-preenchidos
     - ✅ Banner OAuth visível

4. **Continuar fluxo normalmente**

**Acceptance Criteria:**
- [ ] Pula tela de seleção
- [ ] Vai direto para Step 1
- [ ] Dados pré-preenchidos
- [ ] Fluxo normal funciona

---

### ✅ Cenário 4: Carrinho Vazio Após OAuth

**Objetivo:** Testar redirecionamento quando carrinho fica vazio

**Steps:**
1. **Preparar cenário**
   - Limpar localStorage
   - NÃO adicionar produto ao carrinho

2. **Acessar checkout diretamente**
   - URL: `https://www.runaserp.com.br/distribuidora-central/checkout`
   - **Verificar:** Mensagem "Carrinho vazio"

3. **Fazer login OAuth mesmo assim**
   - Clicar "Fazer Login" (se disponível)
   - Completar OAuth
   - **Verificar:**
     - ✅ Toast "Seu carrinho está vazio"
     - ✅ Redirect automático para loja (após 2s)

**Acceptance Criteria:**
- [ ] Detecta carrinho vazio
- [ ] Mostra warning toast
- [ ] Redireciona para loja
- [ ] Não trava na tela de checkout

---

### ❌ Cenário 5: Token Expirado

**Objetivo:** Testar comportamento com token inválido/expirado

**Steps:**
1. **Simular token expirado**
   ```javascript
   // Criar token com exp no passado
   const payload = { sub: 'fake-id', exp: 1000000000 }
   const base64 = btoa(JSON.stringify(payload))
   localStorage.setItem('cliente_token', `fake.${base64}.fake`)
   ```

2. **Adicionar produto e ir para checkout**
   - **Verificar:**
     - ✅ Toast "Sessão expirada"
     - ✅ localStorage limpo
     - ✅ Volta para tela de seleção
     - ✅ Pode fazer login novamente

**Acceptance Criteria:**
- [ ] Detecta token inválido (401)
- [ ] Limpa localStorage
- [ ] Mostra mensagem clara
- [ ] Permite fazer login novamente
- [ ] Não quebra aplicação

---

### ✅ Cenário 6: OAuth Microsoft

**Objetivo:** Testar fluxo com Microsoft ao invés de Google

**Steps:**
1-10. **Mesmos steps do Cenário 1**, mas usar "Entrar com Microsoft"

**Acceptance Criteria:**
- [ ] Fluxo idêntico ao Google
- [ ] Dados pré-preenchidos
- [ ] Carrinho mantido
- [ ] Pedido finaliza

---

### ✅ Cenário 7: Modo Convidado (Sem Mudanças)

**Objetivo:** Verificar que modo convidado ainda funciona

**Steps:**
1. **Limpar localStorage**

2. **Adicionar produto ao carrinho**

3. **Ir para checkout**
   - Clicar "Continuar como convidado"
   - **Verificar:** 
     - ✅ Vai para Step 1
     - ✅ Campos vazios
     - ✅ Banner OAuth NÃO aparece
     - ✅ Checkbox "Criar Conta" APARECE

4. **Preencher dados manualmente**
   - Nome, telefone, email, CPF
   - Marcar "Criar uma conta para mim"

5. **Finalizar pedido**
   - **Verificar:** Conta criada + Pedido finalizado

**Acceptance Criteria:**
- [ ] Modo convidado funciona
- [ ] Checkbox "Criar Conta" aparece
- [ ] Pode criar conta durante checkout
- [ ] Pedido finaliza

---

## 🐛 Debugging

### Ver Console Logs
Procure por emojis no console:
- `🔄 Retorno OAuth detectado`
- `✅ Dados do cliente carregados`
- `❌ Erro ao buscar dados`
- `📝 Atualizando cadastro`
- `⚠️ Continuando checkout sem atualizar cadastro`

### Verificar localStorage
```javascript
// Ver token
localStorage.getItem('cliente_token')

// Ver flags
localStorage.getItem('reload_cart_after_oauth')
localStorage.getItem('oauth_state')
localStorage.getItem('oauth_empresa_slug')

// Limpar tudo
localStorage.clear()
```

### Verificar Network
- GET `/empresas/publico/{slug}` - Deve retornar 200
- GET `/clientes/{id}` - Deve retornar 200 (ou 401 se token inválido)
- PATCH `/clientes/{id}` - Só chama se CPF/telefone mudaram
- POST `/loja/checkout` - Criação da venda

### Verificar React DevTools
Estados para inspecionar:
- `clienteAutenticado` - null ou objeto
- `modoCheckout` - 'selecao' | 'login' | 'guest'
- `currentStep` - 1 | 2 | 3
- `carregandoCliente` - true/false
- `retornoOAuth` - true/false

---

## 📊 Checklist de Aceitação

### Bugs Corrigidos
- [ ] ✅ Bug #1: Sem erro "carregarCarrinho undefined"
- [ ] ✅ Bug #2: Navegação correta (auth vs guest)
- [ ] ✅ Bug #3: OAuth recarrega carrinho
- [ ] ✅ Bug #4: Dados pré-preenchidos após OAuth
- [ ] ✅ Bug #5: Checkbox não aparece para autenticados
- [ ] ✅ Bug #6: CPF/Telefone salvos no cadastro

### UX/UI
- [ ] ✅ Banner OAuth verde visível
- [ ] ✅ Campos com borda verde (pré-preenchidos)
- [ ] ✅ Indicador "✓ Dados do OAuth"
- [ ] ✅ Aviso amarelo CPF/Telefone (quando vazios)
- [ ] ✅ Loading overlay durante busca
- [ ] ✅ Toasts informativos claros

### Error Handling
- [ ] ✅ Erro 401 limpa localStorage
- [ ] ✅ Erro 401 mostra mensagem clara
- [ ] ✅ Erro 404 tratado
- [ ] ✅ Timeout tratado (se ocorrer)
- [ ] ✅ Aplicação não quebra em erro

### Fluxos
- [ ] ✅ OAuth Google funciona
- [ ] ✅ OAuth Microsoft funciona
- [ ] ✅ Modo convidado funciona
- [ ] ✅ Usuário autenticado pula seleção
- [ ] ✅ Carrinho vazio redireciona
- [ ] ✅ Dados são atualizados no cadastro

---

## 🚨 Problemas Conhecidos

### Token Expira Rapidamente
**Sintoma:** Erro 401 ao buscar dados após OAuth

**Causa:** Token JWT tem TTL de 30 minutos

**Solução Temporária:**
1. Verificar que OAuth callback está salvando token corretamente
2. Verificar que token tem `exp` correto no payload
3. Se necessário, aumentar TTL no backend (api-gateway)

**Debug:**
```javascript
// Decodificar token
const token = localStorage.getItem('cliente_token')
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('Expira em:', new Date(payload.exp * 1000))
console.log('Agora:', new Date())
```

### Carrinho Perde Itens
**Sintoma:** Carrinho vazio após OAuth

**Causa:** Cookie de sessão perdido durante redirect

**Solução:** Verificar que:
1. Cookie tem `SameSite=Lax` ou `None`
2. HTTPS está ativo (ngrok)
3. Domain correto no cookie

---

## ✅ Resultado Esperado

Após todos os testes:
- ✅ Todos os 7 cenários passam
- ✅ Todos os bugs corrigidos verificados
- ✅ UX/UI melhorias visíveis
- ✅ Error handling funciona
- ✅ Zero crashes ou erros críticos

---

**Última Atualização:** 25/06/2026  
**Testador:** [Seu nome]  
**Ambiente:** Dev (ngrok)  
**Status:** 🟡 Em teste
