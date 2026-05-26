# Debug OAuth Redirect Issue

## Problema
Após login OAuth bem-sucedido, o usuário é redirecionado para `/login` em vez de `/dashboard`.

## Logs de Diagnóstico Adicionados

### 1. AuthContext (`frontend/src/contexts/AuthContext.tsx`)
- Log ao iniciar verificação de autenticação
- Log ao verificar se há tokens
- Log ao carregar usuário atual
- Log ao chamar `setAuthUser`

### 2. OAuthCallbackPage (`frontend/src/pages/Auth/OAuthCallbackPage.tsx`)
- Log ao chamar `setAuthUser`
- Log ao navegar para dashboard

### 3. ProtectedRoute e PublicRoute (`frontend/src/App.tsx`)
- Log do estado de autenticação (isAuthenticated, isLoading, user)
- Log das decisões de redirecionamento

## Passos para Testar

### Teste 1: Login OAuth do Zero

1. **Limpar tudo:**
   ```javascript
   // No console do navegador (F12)
   localStorage.clear();
   sessionStorage.clear();
   location.reload();
   ```

2. **Ir para login:**
   - Acesse `http://localhost:3000/login`
   - Observe os logs do `[PublicRoute]` e `[AuthContext]`

3. **Clicar em "Entrar com Google":**
   - Observe os logs do OAuth flow
   - Após callback, observe os logs em ordem:
     - `[OAuthCallback]` - processamento do callback
     - `[OAuthCallback]` - chamando setAuthUser
     - `[AuthContext]` - setAuthUser chamado
     - `[OAuthCallback]` - navegando para /dashboard
     - `[ProtectedRoute]` ou `[PublicRoute]` - decisão de rota

4. **Verificar resultado:**
   - ✅ Deve ir direto para `/dashboard`
   - ❌ Se voltar para `/login`, copie TODOS os logs do console

### Teste 2: Reload com Tokens Salvos

1. **Após login bem-sucedido:**
   - Pressione F5 para recarregar a página
   - Observe os logs do `[AuthContext]` ao iniciar

2. **Verificar:**
   - `[AuthContext]` deve encontrar tokens
   - `[AuthContext]` deve buscar usuário atual
   - `[AuthContext]` deve definir isLoading = false
   - `[ProtectedRoute]` deve permitir acesso ao dashboard

## O Que Procurar nos Logs

### Cenário Esperado (Sucesso)
```
[AuthContext] Iniciando verificação de autenticação...
[AuthContext] tokenService.hasTokens(): false
[AuthContext] Nenhum token encontrado
[AuthContext] Verificação concluída, isLoading = false
[PublicRoute] Estado: {isAuthenticated: false, isLoading: false, user: null}
[PublicRoute] Não autenticado, renderizando children (página pública)

// Após clicar em "Entrar com Google" e callback:
[OAuthCallback] Chamando setAuthUser com: {id: "...", email: "...", nome: "...", role: "..."}
[AuthContext] setAuthUser chamado com: {id: "...", email: "...", nome: "...", role: "..."}
[AuthContext] Estado do usuário atualizado
[OAuthCallback] setAuthUser executado
[OAuthCallback] Navegando para /dashboard
[OAuthCallback] navigate() executado
[ProtectedRoute] Estado: {isAuthenticated: true, isLoading: false, user: {...}}
[ProtectedRoute] Autenticado, renderizando children
```

### Cenário com Problema
Se você ver algo diferente, especialmente:
- `isAuthenticated: false` após `setAuthUser`
- Múltiplas execuções do callback
- `[PublicRoute]` sendo chamado após o callback em vez de `[ProtectedRoute]`

## Próximos Passos

Após executar os testes, envie:
1. **Todos os logs do console** (copie tudo)
2. **Qual teste falhou** (Teste 1 ou Teste 2)
3. **URL final** onde você acabou (login ou dashboard)
4. **Conteúdo do localStorage:**
   ```javascript
   // No console do navegador
   console.log('access_token:', localStorage.getItem('access_token'));
   console.log('refresh_token:', localStorage.getItem('refresh_token'));
   ```

## Hipóteses

### Hipótese 1: React StrictMode causando race condition
- Múltiplas execuções do useEffect
- `setAuthUser` sendo chamado mas estado não persistindo
- **Solução**: Flag `processed` já adicionada

### Hipótese 2: Navigate acontecendo antes do estado atualizar
- `setAuthUser` é síncrono mas React pode batchear updates
- `navigate` pode executar antes do estado propagar
- **Solução possível**: Usar callback ou useEffect para navegar

### Hipótese 3: AuthContext reinicializando
- Componente remontando após callback
- Estado sendo perdido
- **Solução possível**: Verificar estrutura de componentes

## Arquivos Modificados

1. `frontend/src/contexts/AuthContext.tsx` - Logs de diagnóstico
2. `frontend/src/pages/Auth/OAuthCallbackPage.tsx` - Logs de diagnóstico
3. `frontend/src/App.tsx` - Logs em ProtectedRoute e PublicRoute
