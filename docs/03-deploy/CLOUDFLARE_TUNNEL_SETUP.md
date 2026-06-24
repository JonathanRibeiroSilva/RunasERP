# 🚀 Setup Cloudflare Tunnel com www.runaserp.com.br

Guia para configurar o domínio real com tunnel gratuito do Cloudflare.

## ✅ Resumo

Nginx roda **local no seu PC**, Cloudflare cria tunnel HTTPS e associa ao domínio `www.runaserp.com.br`.

**Vantagens:**
- GRÁTIS ilimitado
- HTTPS automático
- URL fixa
- DDoS protection
- OAuth funciona (Google/Microsoft)

## 🛠️ Setup Rápido

### 1. Instalar CLI
```powershell
winget install Cloudflare.cloudflared
```

### 2. Login
```powershell
cloudflared tunnel login
```

### 3. Criar Tunnel
```powershell
cloudflared tunnel create runaserp-mvp
cloudflared tunnel route dns runaserp-mvp www.runaserp.com.br
cloudflared tunnel token runaserp-mvp
```

### 4. Configurar
```powershell
Copy-Item .env.cloudflare.example .env.cloudflare
notepad .env.cloudflare  # Colar o token
```

### 5. Subir
```powershell
docker-compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d
```

### 6. Testar
```powershell
Start-Process "https://www.runaserp.com.br"
```

## 📄 Documentação Completa

Veja guia detalhado em: `CLOUDFLARE_TUNNEL_SETUP.md` (em desenvolvimento)
