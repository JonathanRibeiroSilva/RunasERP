# 🎯 Qual Docker Compose Usar?

Guia rápido para escolher o compose correto para cada cenário.

---

## 📋 Os 4 Composes

| Arquivo | Quando usar | Comando |
|---------|-------------|---------|
| **docker-compose.dev.yml** | Desenvolvimento local sem proxy | `docker-compose -f docker-compose.dev.yml up -d` |
| **docker-compose.dev.yml + nginx** | Desenvolvimento local COM proxy | `docker-compose -f docker-compose.dev.yml --profile proxy up -d` |
| **docker-compose.dev.yml + cloudflare** | MVP com domínio real (Cloudflare) | `docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d` |
| **docker-compose.yml** | ❌ NÃO USAR sozinho | (Frontend produção sem API) |
| **docker-compose.prod.yml** | 🚀 Produção em VPS | `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d` |

---

## 🎯 Cenários Comuns

### 1️⃣ **Desenvolvimento Local Simples** (Sem proxy)
```powershell
docker-compose -f docker-compose.dev.yml up -d
```

**Acessar:**
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Serviços: localhost:8001-8007

**Use quando:**
- Desenvolvimento local
- Hot reload do Vite
- Não precisa de OAuth

---

### 2️⃣ **MVP com Domínio Real** (Cloudflare Tunnel) ⭐ RECOMENDADO
```powershell
# 1. Configurar token do Cloudflare
Copy-Item .env.cloudflare.example .env.cloudflare
notepad .env.cloudflare  # Adicionar CLOUDFLARE_TUNNEL_TOKEN

# 2. Subir com Cloudflare
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
```

**Acessar:**
- Frontend: https://www.runaserp.com.br
- API: https://www.runaserp.com.br/api

**Use quando:**
- Testar OAuth (Google/Microsoft)
- Demonstrar para clientes
- MVP público

---

### 3️⃣ **Desenvolvimento com Ngrok** (URL temporária)
```powershell
docker-compose -f docker-compose.dev.yml --profile proxy up -d
```

**Acessar:**
- Frontend: Via URL do ngrok (muda a cada restart)
- Ngrok Dashboard: http://localhost:4040

**Use quando:**
- Teste rápido de webhooks
- Demonstração temporária

---

### 4️⃣ **Produção em VPS** (Deploy real)
```powershell
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**Características:**
- Containers otimizados ("-prod")
- Frontend build estático
- SSL via Let's Encrypt (manual)

---

## 🚨 Erro Comum: "404 Not Found" no Login

**Problema:**
Você está usando `docker-compose.yml` sozinho (frontend produção sem API proxy).

**Solução:**
```powershell
# Parar
docker-compose down

# Usar o compose CORRETO
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
```

---

## 📊 Resumo Rápido

**Para MVP com www.runaserp.com.br:**
```powershell
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
```

**Para desenvolvimento local:**
```powershell
docker-compose -f docker-compose.dev.yml up -d
```

**Para produção VPS:**
```powershell
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 🔍 Como Saber Qual Está Rodando?

```powershell
# Ver containers ativos
docker ps --format "table {{.Names}}\t{{.Image}}"

# Se vir "erp-*-dev" = Ambiente de desenvolvimento ✅
# Se vir "erp-*" (sem -dev) = Ambiente de produção ⚠️
# Se vir "erp-cloudflared" = Cloudflare Tunnel ativo ✅
# Se vir "erp-ngrok" = Ngrok ativo ⚠️
```

---

## 📝 Credenciais de Acesso

**Admin:**
- Email: `admin@runas.com`
- Senha: `Admin@123`

**Operador:**
- Email: `operador@runas.com`
- Senha: `Operador@123`
