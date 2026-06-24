# 🚀 Guias de Deploy - Runas ERP

## Escolha Seu Cenário

### 🏠 Rodando Localmente (Seu PC/Servidor Local)

#### ✅ Opção 1: Cloudflare Tunnel (RECOMENDADO)
- **Custo**: GRATUITO ✅
- **SSL**: Automático
- **IP Público**: Não precisa
- **Firewall**: Não precisa abrir portas
- **Velocidade**: Rápido (CDN global)
- **DDoS**: Protection incluído

📄 **Guia**: [CLOUDFLARE_TUNNEL.md](./CLOUDFLARE_TUNNEL.md)

---

#### Opção 2: Ngrok com Domínio Próprio
- **Custo**: $8-20/mês 💰
- **SSL**: Automático
- **IP Público**: Não precisa
- **Firewall**: Não precisa abrir portas

📄 **Guia**: [DOMINIO_COM_NGROK.md](./DOMINIO_COM_NGROK.md)

---

### 🌍 Servidor com IP Público (VPS, Cloud, etc.)

#### Opção 3: Deploy Tradicional (Nginx + Let's Encrypt)
- **Custo**: Custo do servidor (VPS/Cloud)
- **SSL**: Let's Encrypt (gratuito)
- **IP Público**: Necessário
- **Controle Total**: Sim

📄 **Guias**:
- [CONFIGURACAO_DOMINIO.md](./CONFIGURACAO_DOMINIO.md) - Guia completo
- [QUICK_START_DOMINIO.md](./QUICK_START_DOMINIO.md) - Guia rápido

---

## 🎯 Comparação Rápida

| | Cloudflare Tunnel | Ngrok Pago | VPS + Let's Encrypt |
|---|---|---|---|
| **Custo** | Gratuito ✅ | $8-20/mês | VPS ~$5-50/mês |
| **Setup** | 15 min | 10 min | 30-60 min |
| **SSL** | Auto | Auto | Manual (1x) |
| **IP Público** | ❌ Não precisa | ❌ Não precisa | ✅ Necessário |
| **Firewall** | ❌ Não mexe | ❌ Não mexe | ✅ Abrir portas |
| **DDoS** | Incluído | Limitado | Você gerencia |
| **CDN** | Sim | Não | Opcional |
| **Controle** | Médio | Baixo | Total |
| **Local/Cloud** | Local | Local | Cloud |

---

## 💡 Recomendação por Caso de Uso

### 🧪 **Desenvolvimento/Teste**
→ Use **ngrok free** (já configurado)
```powershell
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

### 🏢 **Produção (Budget Limitado)**
→ Use **Cloudflare Tunnel** (gratuito)
- Melhor custo-benefício
- Produção-ready
- SSL e DDoS inclusos

### 🚀 **Produção (Empresa Grande)**
→ Use **VPS + Let's Encrypt**
- Controle total
- Performance máxima
- Escalabilidade

### 🎯 **MVP/Startup**
→ Use **Cloudflare Tunnel**
- Zero custo adicional
- Fácil de migrar depois
- Foco no produto, não infraestrutura

---

## 📚 Arquivos de Configuração

### Para Deploy Local (Cloudflare/Ngrok)
```
docker-compose.yml                 # Base
docker-compose.nginx.yml           # + Nginx + Proxy
.env                               # Variáveis
```

### Para Deploy em VPS/Cloud
```
docker-compose.prod.yml            # Produção otimizada
nginx/nginx.prod.conf              # Nginx com SSL
.env.production.example            # Template
scripts/deploy-prod.ps1            # Script automático
```

---

## 🎬 Quick Start por Cenário

### Cenário 1: Local + Cloudflare (15 min)
```powershell
# 1. Instalar cloudflared
# 2. Autenticar
cloudflared tunnel login

# 3. Criar tunnel
cloudflared tunnel create runas-erp

# 4. Configurar (ver CLOUDFLARE_TUNNEL.md)

# 5. Subir sistema
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d

# 6. Iniciar tunnel
cloudflared tunnel run runas-erp
```

### Cenário 2: VPS + Let's Encrypt (30 min)
```powershell
# 1. Configurar DNS (Tipo A para IP do VPS)

# 2. Gerar SSL
docker run --rm -v letsencrypt-certs:/etc/letsencrypt certbot/certbot certonly --standalone -d runaserp.com.br

# 3. Deploy
.\scripts\deploy-prod.ps1
```

---

## 🆘 Precisa de Ajuda?

### Troubleshooting Geral
1. Verificar logs: `docker-compose logs -f`
2. Verificar saúde: `docker-compose ps`
3. Testar local: `Invoke-WebRequest http://localhost/api/health`

### Suporte por Cenário
- **Cloudflare**: [docs/03-deployment/CLOUDFLARE_TUNNEL.md#troubleshooting](./CLOUDFLARE_TUNNEL.md)
- **VPS/Cloud**: [docs/03-deployment/CONFIGURACAO_DOMINIO.md#troubleshooting](./CONFIGURACAO_DOMINIO.md)
- **Ngrok**: [docs/03-deployment/DOMINIO_COM_NGROK.md](./DOMINIO_COM_NGROK.md)

---

## 📞 Contato

Para dúvidas sobre deploy, abra uma issue no GitHub ou consulte a documentação específica de cada cenário.

---

**🎉 Boa sorte com o deploy do seu ERP!**
