# 🐳 Docker Compose - Guia de Uso

## 📋 Arquivos Disponíveis

Apenas **3 arquivos** de compose:

1. **`docker-compose.dev.yml`** - Base para desenvolvimento (com Cloudflare)
2. **`docker-compose.cloudflare.yml`** - Extensão para adicionar tunnel
3. **`docker-compose.prod.yml`** - Produção em VPS

---

## 🎯 Como Usar

### ✅ **Desenvolvimento/MVP (Padrão)**
```powershell
# Subir com Cloudflare Tunnel
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# Ver logs
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml logs -f

# Parar
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml down
```

**Acesso:**
- Frontend: https://runaserp.com.br
- API: https://runaserp.com.br/api
- PgAdmin: http://localhost:5050

---

## 🔐 Configuração Necessária

### 1. Cloudflare Tunnel Token

Edite o `.env.cloudflare` e adicione seu token:
```env
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiZjU4YzM0YTQtYjg5...
```

**Como obter o token:**
```powershell
# 1. Instalar CLI
winget install Cloudflare.cloudflared

# 2. Login
cloudflared tunnel login

# 3. Criar tunnel
cloudflared tunnel create runaserp-mvp

# 4. Configurar DNS
cloudflared tunnel route dns runaserp-mvp runaserp.com.br

# 5. Obter token
cloudflared tunnel token runaserp-mvp
```

---

## 📝 Credenciais Padrão

**Admin:** admin@runas.com / Admin@123
**Operador:** operador@runas.com / Operador@123
**PgAdmin:** admin@runas.com / Cabrito120!@#

---

## 🔍 Verificar Status

```powershell
# Ver containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Logs Cloudflare
docker logs erp-cloudflared -f
```
