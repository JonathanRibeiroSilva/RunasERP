# Guia Rápido de Testes - Autenticação Frontend

**Data:** 2026-05-25  
**Versão:** 1.0.0  
**Status:** ✅ Pronto para Testes

---

## 🚀 Início Rápido (5 minutos)

### 1. Verificar Pré-requisitos

```bash
# Verificar Docker (recomendado)
docker --version
docker-compose --version

# Ou verificar Node.js (alternativa)
node --version  # v18+ recomendado
npm --version   # v9+ recomendado
```

### 2. Clonar/Atualizar Repositório

```bash
cd c:\Users\jonat\Documents\GitHub\ERP\RunasERP
git pull origin main
```

### 3. Iniciar Backend

**Opção A: Com Docker (Recomendado)**
```bash
docker-compose -f docker-compose.dev.yml up api-gateway
```

**Opção B: Sem Docker**
```bash
cd api-gateway
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verificar:** http://localhost:8000/docs (Swagger UI)

### 4. Iniciar Frontend

**Opção A: Com Docker (Recomendado)**
```bash
docker-compose -f docker-compose.dev.yml up frontend-dev
```

**Opção B: Sem Docker**
```bash
cd frontend
npm install
npm run dev
```

**Verificar:** http://localhost:3000

---

## 🧪 Testes Básicos (10 minutos)

### Teste 1: Login Tradicional

1. Abra http://localhost:3000/login
2. Digite:
   - Email: `admin@runas.com`
   - Senha: `Admin@123`
3. Clique em "Entrar"
4. **Esperado:** Redirecionamento para dashboard

**Verificação:**
- ✅ Página de login carrega
- ✅ Campos de email e senha aparecem
- ✅ Botão "Entrar" funciona
- ✅ Redirecionamento para dashboard
- ✅ Navbar mostra nome do usuário

### Teste 2: Logout

1. Clique no avatar do usuário (canto superior direito)
2. Clique em "Sair"
3. **Esperado:** Redirecionamento para login

**Verificação:**
- ✅ Menu de usuário aparece
- ✅ Opção "Sair" funciona
- ✅ Redirecionamento para login
- ✅ Tokens removidos do localStorage

### Teste 3: Proteção de Rotas

1. Faça logout
2. Tente acessar http://localhost:3000/dashboard
3. **Esperado:** Redirecionamento para login

**Verificação:**
- ✅ Rotas protegidas redirecionam para login
- ✅ Não é possível acessar dashboard sem autenticação

### Teste 4: Refresh Token

1. Faça login
2. Abra DevTools (F12) > Application > Local Storage
3. Copie o `access_token`
4. Aguarde 1 minuto
5. Faça uma ação que chame a API (ex: atualizar página)
6. **Esperado:** Novo `access_token` gerado

**Verificação:**
- ✅ Token antigo é diferente do novo
- ✅ Usuário continua logado
- ✅ Sem necessidade de fazer login novamente

---

## 🔐 Testes OAuth (15 minutos)

### Pré-requisito: Configurar Credenciais

Antes de testar OAuth, você precisa:

1. **Google OAuth:**
   - Criar projeto em https://console.cloud.google.com/
   - Obter Client ID
   - Adicionar ao `.env.development`:
     ```env
     VITE_GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
     ```

2. **Microsoft OAuth:**
   - Criar app em https://portal.azure.com/
   - Obter Client ID
   - Adicionar ao `.env.development`:
     ```env
     VITE_MICROSOFT_CLIENT_ID=seu-client-id
     ```

3. **Backend:**
   - Adicionar credenciais ao `.env` do backend:
     ```env
     GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
     GOOGLE_CLIENT_SECRET=seu-client-secret
     MICROSOFT_CLIENT_ID=seu-client-id
     MICROSOFT_CLIENT_SECRET=seu-client-secret
     ```

### Teste 5: Login com Google

1. Abra http://localhost:3000/login
2. Clique em "Continuar com Google"
3. Faça login com sua conta Google
4. Autorize o aplicativo
5. **Esperado:** Redirecionamento para dashboard

**Verificação:**
- ✅ Botão "Continuar com Google" aparece
- ✅ Redirecionamento para Google funciona
- ✅ Retorno para `/auth/callback` funciona
- ✅ Redirecionamento para dashboard
- ✅ Tokens salvos no localStorage
- ✅ Usuário criado/atualizado no banco

### Teste 6: Login com Microsoft

1. Abra http://localhost:3000/login
2. Clique em "Continuar com Microsoft"
3. Faça login com sua conta Microsoft
4. Autorize o aplicativo
5. **Esperado:** Redirecionamento para dashboard

**Verificação:**
- ✅ Botão "Continuar com Microsoft" aparece
- ✅ Redirecionamento para Microsoft funciona
- ✅ Retorno para `/auth/callback` funciona
- ✅ Redirecionamento para dashboard
- ✅ Tokens salvos no localStorage
- ✅ Usuário criado/atualizado no banco

### Teste 7: Múltiplos Logins

1. Faça login com Google
2. Logout
3. Faça login com email/senha
4. Logout
5. Faça login com Microsoft
6. **Esperado:** Todos os métodos funcionam

**Verificação:**
- ✅ Todos os métodos de login funcionam
- ✅ Mesmo usuário é criado/atualizado
- ✅ Sem conflitos entre métodos

---

## 🔍 Verificações no DevTools

### Verificar Tokens

1. Abra DevTools (F12)
2. Vá em **Application** > **Local Storage** > **http://localhost:3000**
3. Procure por:
   - `access_token`: JWT token (começa com `eyJ...`)
   - `refresh_token`: JWT token (começa com `eyJ...`)

### Decodificar JWT

1. Copie o `access_token`
2. Acesse https://jwt.io
3. Cole o token no campo "Encoded"
4. Verifique:
   - **Header:** `{ "alg": "HS256", "typ": "JWT" }`
   - **Payload:** `{ "sub": "user_id", "email": "...", "exp": ... }`
   - **Signature:** Válida

### Verificar Network

1. Abra DevTools (F12)
2. Vá em **Network**
3. Faça login
4. Procure por requisições:
   - `POST /auth/login` (email/senha)
   - `POST /auth/oauth/callback` (OAuth)
   - `POST /auth/refresh` (refresh token)

**Esperado:**
- ✅ Status 200 para login bem-sucedido
- ✅ Response contém `access_token` e `refresh_token`
- ✅ Headers contêm `Authorization: Bearer <token>`

### Verificar Console

1. Abra DevTools (F12)
2. Vá em **Console**
3. Procure por erros ou warnings
4. **Esperado:** Sem erros relacionados a autenticação

---

## 📊 Checklist de Testes

### Autenticação Básica
- [ ] Login com email/senha funciona
- [ ] Logout funciona
- [ ] Proteção de rotas funciona
- [ ] Refresh token funciona
- [ ] Tokens salvos no localStorage

### OAuth Google
- [ ] Botão "Continuar com Google" aparece
- [ ] Redirecionamento para Google funciona
- [ ] Retorno para callback funciona
- [ ] Usuário criado/atualizado
- [ ] Tokens salvos corretamente

### OAuth Microsoft
- [ ] Botão "Continuar com Microsoft" aparece
- [ ] Redirecionamento para Microsoft funciona
- [ ] Retorno para callback funciona
- [ ] Usuário criado/atualizado
- [ ] Tokens salvos corretamente

### Segurança
- [ ] CSRF protection ativa (state parameter)
- [ ] Tokens não expostos em URLs
- [ ] Secrets não expostos no frontend
- [ ] HTTPS em produção (quando aplicável)

### UI/UX
- [ ] Página de login é responsiva
- [ ] Botões OAuth aparecem corretamente
- [ ] Loading states aparecem
- [ ] Mensagens de erro são claras
- [ ] Redirecionamentos são suaves

---

## 🐛 Troubleshooting Rápido

### "Botões OAuth não aparecem"
```bash
# Solução:
1. Verifique .env.development
2. Reinicie o frontend: npm run dev
3. Limpe cache: Ctrl+Shift+Delete
```

### "redirect_uri_mismatch"
```bash
# Solução:
1. Verifique se http://localhost:3000/auth/callback está configurado
2. Verifique se não há espaços extras
3. Aguarde alguns minutos para propagação
```

### "invalid_client"
```bash
# Solução:
1. Verifique Client ID e Secret no .env do backend
2. Verifique se não há espaços extras
3. Reinicie o backend
```

### "CORS error"
```bash
# Solução:
1. Verifique se backend está rodando: http://localhost:8000/docs
2. Verifique CORS no backend
3. Verifique se frontend URL está autorizada
```

### "Tokens não salvos"
```bash
# Solução:
1. Verifique DevTools > Network > Response
2. Verifique se response contém access_token
3. Verifique se localStorage está habilitado
```

---

## 📞 Próximos Passos

Após confirmar que tudo está funcionando:

1. ✅ **Testes Passaram?** Ótimo! Você pode começar a testar os módulos
2. ❌ **Testes Falharam?** Verifique o troubleshooting acima
3. 📝 **Documentar Issues:** Crie issues no GitHub com detalhes

---

## 📚 Documentação Relacionada

- [OAUTH-SETUP.md](./OAUTH-SETUP.md) - Configuração detalhada de OAuth
- [STATUS.md](./STATUS.md) - Status geral do frontend
- [DOCKER.md](./DOCKER.md) - Guia de Docker
- [API-EXAMPLES.md](./API-EXAMPLES.md) - Exemplos de integração com API

---

**Última Atualização:** 2026-05-25  
**Versão:** 1.0.0
