# 🌐 Configuração com Cloudflare Tunnel (Local + Domínio)

## O que é Cloudflare Tunnel?

Expõe seu servidor **local** para a internet **sem abrir portas** e com **SSL automático**.

```
[PC Local] → [Cloudflare Tunnel] → [Internet] → [runaserp.com.br]
```

**Vantagens:**
- ✅ SSL/HTTPS automático
- ✅ Sem IP público estático
- ✅ Sem abrir portas no firewall
- ✅ DDoS protection gratuito
- ✅ **Totalmente gratuito!**

---

## Passos Rápidos

### 1. Criar Conta Cloudflare (5 min)
https://dash.cloudflare.com/sign-up

### 2. Adicionar Domínio (5 min)
1. Adicionar `runaserp.com.br`
2. Cloudflare fornece 2 nameservers

### 3. Atualizar DNS no Registro.br (10 min)
Substituir nameservers pelos do Cloudflare

### 4. Instalar Cloudflared (Windows)

```powershell
# PowerShell como Administrador
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"

New-Item -ItemType Directory -Path "C:\Program Files\cloudflared" -Force
Move-Item -Path "cloudflared.exe" -Destination "C:\Program Files\cloudflared\cloudflared.exe" -Force

[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\cloudflared", "Machine")

# Reiniciar PowerShell e verificar
cloudflared --version
```

### 5. Autenticar

```powershell
cloudflared tunnel login
```

### 6. Criar Tunnel

```powershell
cloudflared tunnel create runas-erp
# Anotar o TUNNEL_ID retornado!
```

### 7. Configurar Tunnel

Criar `C:\Users\SEU_USUARIO\.cloudflared\config.yml`:

```yaml
tunnel: runas-erp
credentials-file: C:\Users\SEU_USUARIO\.cloudflared\TUNNEL_ID.json

ingress:
  - hostname: runaserp.com.br
    service: http://localhost:80
  - hostname: www.runaserp.com.br
    service: http://localhost:80
  - service: http_status:404
```

### 8. Configurar DNS

```powershell
cloudflared tunnel route dns runas-erp runaserp.com.br
cloudflared tunnel route dns runas-erp www.runaserp.com.br
```

### 9. Atualizar .env

```env
FRONTEND_URL=https://runaserp.com.br
API_BASE_URL=https://runaserp.com.br/api
```

### 10. Subir Sistema Localmente

```powershell
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

### 11. Iniciar Tunnel

```powershell
# Testar
cloudflared tunnel run runas-erp

# Instalar como serviço Windows
cloudflared service install
Start-Service cloudflared
Set-Service -Name cloudflared -StartupType Automatic
```

### 12. Configurar OAuth2

**Google**: https://console.cloud.google.com/apis/credentials  
**Microsoft**: https://portal.azure.com

Redirect URI: `https://runaserp.com.br/auth/callback`

**Mercado Pago**: `https://runaserp.com.br/api/vendas/webhook/mercadopago`

---

## 🎯 Arquitetura

```
PC Local (Docker) → Cloudflare Tunnel → Internet → runaserp.com.br
```

---

## 🔧 Comandos Úteis

```powershell
# Status
cloudflared tunnel list

# Logs (Serviço Windows)
Get-EventLog -LogName Application -Source cloudflared -Newest 50

# Reiniciar
Restart-Service cloudflared
```

---

## 💰 Custo

**GRATUITO** ✅ (Plano Free do Cloudflare)

---

## ✅ Pronto!

Acesse: **https://runaserp.com.br** 🚀
