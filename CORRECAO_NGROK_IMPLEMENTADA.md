# Correção de Redirecionamento para Localhost com Ngrok

## 🎯 Problema Identificado

Após login via Ngrok, o sistema redirecionava para URLs localhost, impedindo o acesso correto ao sistema.

## 🔍 Causas Raiz

1. **`vite.config.ts`** - Proxy hardcoded para `http://localhost:8000`
2. **`vite.config.ts`** - HMR (Hot Module Replacement) configurado para `localhost`
3. **`env.ts`** - Usava `window.location` para detectar URL (removido)
4. **Falta de variáveis de ambiente** específicas para Ngrok

## ✅ Correções Implementadas

### 1. `frontend/vite.config.ts`

**Antes:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // ❌ Hardcoded
    changeOrigin: true,
  },
},
hmr: {
  protocol: 'ws',
  host: 'localhost',  // ❌ Hardcoded
}
```

**Depois:**
```typescript
hmr: {
  protocol: process.env.VITE_HMR_PROTOCOL || 'ws',  // ✅ Configurável
  host: process.env.VITE_HMR_HOST || 'localhost',   // ✅ Configurável
  port: parseInt(process.env.VITE_HMR_PORT || '3000'),
},
// Proxy condicional - apenas para desenvolvimento local
...(process.env.VITE_USE_PROXY !== 'false' && {
  proxy: {
    '/api': {
      target: process.env.VITE_API_URL || 'http://localhost:8000',  // ✅ Configurável
      changeOrigin: true,
    },
  },
}),
```

### 2. `frontend/src/config/env.ts`

**Antes:**
```typescript
// Detectar se está rodando via Ngrok
const isNgrok = window.location.hostname.includes('ngrok');  // ❌ Causa redirecionamento
const baseUrl = isNgrok 
  ? `${window.location.protocol}//${window.location.host}`
  : import.meta.env.VITE_API_URL;
```

**Depois:**
```typescript
export const env = {
  // API URL - usar variável de ambiente diretamente
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',  // ✅ Apenas variável
  oauth: {
    redirectUri: import.meta.env.VITE_OAUTH_REDIRECT_URI || 'http://localhost:3000/auth/callback',  // ✅ Apenas variável
  },
}
```

### 3. `frontend/.env.ngrok` (NOVO)

Criado template de configuração para Ngrok:

```env
# API Configuration for Ngrok
# IMPORTANTE: Substitua YOUR_NGROK_URL pela sua URL do ngrok
VITE_API_URL=https://YOUR_NGROK_URL/api

# OAuth Configuration
VITE_OAUTH_REDIRECT_URI=https://YOUR_NGROK_URL/auth/callback

# HMR Configuration for Ngrok
VITE_HMR_HOST=YOUR_NGROK_URL
VITE_HMR_PORT=443
VITE_HMR_PROTOCOL=wss

# Desabilitar proxy do Vite (Nginx fará o proxy)
VITE_USE_PROXY=false
```

## 📋 Próximos Passos (Usuário)

### 1. Obter URL do Ngrok

```bash
ngrok http 80
```

Copie a URL gerada (ex: `https://abc123.ngrok-free.dev`)

### 2. Configurar `.env.ngrok`

Edite `frontend/.env.ngrok` e substitua `YOUR_NGROK_URL` pela URL do Ngrok:

```env
VITE_API_URL=https://abc123.ngrok-free.dev/api
VITE_OAUTH_REDIRECT_URI=https://abc123.ngrok-free.dev/auth/callback
VITE_HMR_HOST=abc123.ngrok-free.dev
```

### 3. Copiar para `.env.local`

```bash
cd frontend
cp .env.ngrok .env.local
```

### 4. Reiniciar Servidor

```bash
npm run dev
```

### 5. Testar

1. Acesse via Ngrok: `https://abc123.ngrok-free.dev`
2. Faça login
3. Verifique se a URL permanece no Ngrok (não redireciona para localhost)
4. Verifique no DevTools (Network) se as requisições API vão para Ngrok

## 🔧 Arquivos Modificados

- ✅ `frontend/vite.config.ts` - Proxy e HMR configuráveis
- ✅ `frontend/src/config/env.ts` - Removido `window.location`
- ✅ `frontend/.env.ngrok` - Template criado

## 📝 Arquivos de Referência

- `frontend/.env.development` - Configuração para desenvolvimento local
- `nginx/nginx.conf` - Configuração do Nginx (OK)
- `.env.ngrok` (raiz) - Apenas token do Ngrok

## 🎯 Resultado Esperado

Após configurar corretamente:

1. ✅ Login via Ngrok mantém a URL do Ngrok
2. ✅ Todas as requisições API vão para Ngrok
3. ✅ OAuth funciona corretamente
4. ✅ HMR funciona via WebSocket Secure (WSS)
5. ✅ Não há redirecionamentos para localhost

## 🐛 Troubleshooting

### Ainda redireciona para localhost?

1. Verifique se `.env.local` foi criado corretamente
2. Verifique se substituiu `YOUR_NGROK_URL` pela URL real
3. Reinicie o servidor (`npm run dev`)
4. Limpe o cache do navegador (Ctrl+Shift+R)

### Requisições ainda vão para localhost?

1. Abra DevTools → Network
2. Verifique se `VITE_API_URL` está correto
3. Verifique se `VITE_USE_PROXY=false` está definido

### OAuth não funciona?

1. Verifique se `VITE_OAUTH_REDIRECT_URI` está correto
2. Verifique se a URL do Ngrok está registrada no Google/Microsoft OAuth
3. Verifique os logs do backend

## 📚 Documentação Relacionada

- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Ngrok Documentation](https://ngrok.com/docs)
- [Nginx Proxy Configuration](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
