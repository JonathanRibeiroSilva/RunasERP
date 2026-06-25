# ✅ URLs OAuth Corretas - Google & Microsoft

## 🎯 URLs de Redirect (CORRETAS!)

### Para Produção (Cloudflare Tunnel)

**Google:**
```
https://runaserp.com.br/auth/callback/google
```

**Microsoft:**
```
https://runaserp.com.br/auth/callback/microsoft
```

⚠️ **ATENÇÃO:** O caminho é `/auth/callback/google` e **NÃO** `/oauth/google/callback`!

---

## 1️⃣ Google Cloud Console

**Acessar:** https://console.cloud.google.com/apis/credentials

### Configurar Client ID

1. Clicar no Client ID existente
2. **Authorized JavaScript origins:**
   ```
   http://localhost:3000
   https://runaserp.com.br
   https://www.runaserp.com.br
   ```

3. **Authorized redirect URIs:**
   ```
   http://localhost:3000/auth/callback/google
   https://runaserp.com.br/auth/callback/google
   https://www.runaserp.com.br/auth/callback/google
   ```

4. **SALVAR**

---

## 2️⃣ Microsoft Azure Portal

**Acessar:** https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade

### Configurar App Registration

1. Selecionar o App: **Runas ERP**
2. Menu lateral → **Authentication**
3. Section: **Platform configurations → Web**
4. **Redirect URIs:**
   ```
   http://localhost:3000/auth/callback/microsoft
   https://runaserp.com.br/auth/callback/microsoft
   https://www.runaserp.com.br/auth/callback/microsoft
   ```

5. **Front-channel logout URL:**
   ```
   https://runaserp.com.br
   ```

6. **Implicit grant and hybrid flows:**
   - ✅ ID tokens (used for implicit and hybrid flows)

7. **SAVE**

---

## 🔍 Como Verificar se Está Correto

### Teste 1: Verificar URL gerada pelo backend

```powershell
$body = @{ 
    redirect_uri = "https://runaserp.com.br/auth/callback/google"
    empresa_id = 4 
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "https://runaserp.com.br/api/auth/cliente/oauth/google/init" `
    -Method POST `
    -Body $body `
    -ContentType "application/json" `
    -UseBasicParsing

$data = $response.Content | ConvertFrom-Json
Write-Host $data.auth_url
```

**A URL deve conter:**
```
redirect_uri=https://runaserp.com.br/auth/callback/google
```

### Teste 2: Tentar acessar no navegador

Cole esta URL no navegador:

**Google:**
```
https://accounts.google.com/o/oauth2/v2/auth?client_id=658854956136-c9grsbglelicgtlj9oa4dg034flc7mvm.apps.googleusercontent.com&redirect_uri=https://runaserp.com.br/auth/callback/google&response_type=code&scope=openid+email+profile&state=teste123&access_type=offline&prompt=consent
```

**Resultado esperado:**
- ✅ Abre tela de login do Google
- ❌ Se der erro "redirect_uri_mismatch" → URL não está configurada
- ❌ Se der erro "invalid request" → App não publicado ou domínio não autorizado

---

## 📝 Resumo das Diferenças

### ❌ URLs ERRADAS (que eu passei antes - DESCULPA!)

```
https://runaserp.com.br/oauth/google/callback    ❌
https://runaserp.com.br/oauth/microsoft/callback ❌
```

### ✅ URLs CORRETAS

```
https://runaserp.com.br/auth/callback/google     ✅
https://runaserp.com.br/auth/callback/microsoft  ✅
```

---

## 🚀 Checklist Final

### Google Cloud Console
- [ ] Redirect URI: `https://runaserp.com.br/auth/callback/google` (**SEM** `/oauth/`)
- [ ] JavaScript origin: `https://runaserp.com.br`
- [ ] OAuth Consent Screen: App publicado (PUBLISH APP)
- [ ] Authorized domain: `runaserp.com.br`

### Microsoft Azure Portal
- [ ] Redirect URI: `https://runaserp.com.br/auth/callback/microsoft` (**SEM** `/oauth/`)
- [ ] Account type: Personal + Organizational
- [ ] ID tokens: ✅ Enabled
- [ ] Access tokens: ✅ Enabled

### Backend (.env)
- [ ] `GOOGLE_CLIENT_ID` correto
- [ ] `GOOGLE_CLIENT_SECRET` correto
- [ ] `MICROSOFT_CLIENT_ID` correto
- [ ] `MICROSOFT_CLIENT_SECRET` correto
- [ ] `FRONTEND_URL=https://runaserp.com.br`

---

## 🔧 Após Corrigir

1. **Salvar** as alterações no Google/Microsoft
2. **Aguardar 5 minutos** (cache)
3. **Limpar cache do navegador** ou usar aba anônima
4. **Testar login OAuth** em: `https://runaserp.com.br/c/distribuidora-central/checkout`

---

## 🙏 Pedido de Desculpas

Peço desculpas pelo erro na documentação anterior! As URLs corretas são `/auth/callback/google` e `/auth/callback/microsoft`.

O código do frontend sempre esteve correto, o erro foi apenas na documentação que forneci. 🙏
