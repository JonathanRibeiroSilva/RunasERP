# Infraestrutura e Acesso ao Sistema

## 🌐 Domínio e Túnel

O sistema RunasERP está configurado para usar **Cloudflare Tunnel** com o domínio:

**Domínio principal**: `www.runaserp.com.br`

### URLs de Acesso

- **Frontend**: `https://www.runaserp.com.br`
- **API Gateway**: `https://www.runaserp.com.br/api`
- **Health Check**: `https://www.runaserp.com.br/api/health`

## ⚠️ IMPORTANTE: Implementações Obsoletas

### ❌ **NUNCA referenciar (DELETADAS)**:

#### Ngrok (substituído por Cloudflare)
- URLs ngrok (como `pretty-dissuade-brunette.ngrok-free.dev`)
- API do ngrok (`localhost:4040`)
- Comandos para obter URL do ngrok
- Configurações de ngrok
- `docker-compose.nginx.yml` (não existe mais)
- `.env.ngrok` (obsoleto)

#### Nginx (removido - não precisamos mais)
- Pasta `nginx/` (deletada)
- Configurações nginx
- Referências ao nginx como proxy reverso
- Docker compose com nginx

#### PgAdmin (removido - usar ferramentas externas)
- Pasta `pgadmin/` (deletada)
- Container pgadmin no docker-compose
- URLs localhost:5050

### ✅ **SEMPRE usar (IMPLEMENTAÇÃO ATUAL)**:

#### Cloudflare Tunnel
- Domínio fixo: `www.runaserp.com.br`
- URLs fixas e previsíveis
- Túnel configurado via `docker-compose.cloudflare.yml`
- Cloudflared como proxy reverso

#### Docker Compose Files
- `docker-compose.dev.yml` - Desenvolvimento local
- `docker-compose.prod.yml` - Produção
- `docker-compose.cloudflare.yml` - Túnel Cloudflare (usar com --profile proxy)

#### Acesso a Banco de Dados
- Usar DBeaver, pgAdmin desktop, ou qualquer cliente PostgreSQL
- Conectar em: `localhost:5432` (porta exposta no docker-compose.dev.yml)
- Credentials: `.env` (POSTGRES_USER, POSTGRES_PASSWORD)

## 🧪 Testar APIs

**Comando correto**:
```powershell
# Health check
Invoke-WebRequest -Uri "https://www.runaserp.com.br/api/health" -UseBasicParsing

# Produtos
Invoke-WebRequest -Uri "https://www.runaserp.com.br/api/produtos" -UseBasicParsing

# Com variável (recomendado)
$domain = "https://www.runaserp.com.br"
Invoke-WebRequest -Uri "$domain/api/health" -UseBasicParsing
```

**Comando ERRADO** (não usar):
```powershell
# ❌ Não usar ngrok
$ngrokUrl = (Invoke-WebRequest -Uri "http://localhost:4040/api/tunnels").tunnels[0].public_url

# ❌ Não testar diretamente nos serviços
Invoke-WebRequest -Uri "http://localhost:8000/api/produtos"
```

## 🔧 Configuração do Cloudflare

**Arquivo**: `docker-compose.cloudflare.yml`

**Variáveis de ambiente necessárias** (`.env`):
```env
CLOUDFLARE_TUNNEL_TOKEN=seu_token_aqui
FRONTEND_URL=https://www.runaserp.com.br
API_BASE_URL=https://www.runaserp.com.br/api
```

**Iniciar com Cloudflare**:
```powershell
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d
```

## 🎯 OAuth2 Configuration

**Google Console** - Authorized redirect URIs:
```
https://www.runaserp.com.br/auth/callback
https://www.runaserp.com.br/auth/callback/google
```

**Microsoft Azure** - Redirect URIs:
```
https://www.runaserp.com.br/auth/callback
https://www.runaserp.com.br/auth/callback/microsoft
```

## 💳 Mercado Pago Webhooks

**URL do webhook**:
```
https://www.runaserp.com.br/api/vendas/webhook/mercadopago
```

**Configurar no painel do Mercado Pago**:
1. Acessar: https://www.mercadopago.com.br/developers/panel/webhooks
2. URL de notificação: `https://www.runaserp.com.br/api/vendas/webhook/mercadopago`
3. Eventos: `payment.created`, `payment.updated`

## 📊 Monitoramento

**Logs dos serviços**:
```powershell
# Ver logs do API Gateway
docker logs erp-api-gateway-dev -f

# Ver logs do Cloudflare Tunnel
docker logs erp-cloudflared-dev -f

# Ver logs de um microserviço específico
docker logs erp-vendas-dev -f
```

**Verificar status**:
```powershell
# Status de todos os containers
docker-compose -f docker-compose.dev.yml ps

# Verificar se o túnel está ativo
docker ps | Select-String "cloudflared"

# Health check do API Gateway
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

## 🚀 Vantagens do Cloudflare vs Alternativas Antigas

| Recurso | Cloudflare | Ngrok (removido) | Nginx Local (removido) |
|---------|-----------|------------------|------------------------|
| **URL fixa** | ✅ `www.runaserp.com.br` | ❌ Muda a cada restart | 🟡 Localhost apenas |
| **Custo** | ✅ Gratuito | ❌ Plano pago para custom domain | ✅ Gratuito |
| **Configuração** | ✅ Token no `.env` | ❌ Reconfigurar OAuth sempre | 🟡 Sem acesso externo |
| **Performance** | ✅ CDN global | 🟡 Depende do plano | 🟡 Local |
| **DDoS Protection** | ✅ Incluso | 🟡 Depende do plano | ❌ Não |
| **Analytics** | ✅ Dashboard completo | 🟡 Básico no plano free | ❌ Não |
| **Webhooks** | ✅ Funciona perfeitamente | ✅ Funciona | ❌ Não funciona |
| **OAuth2** | ✅ URL fixa | ❌ URL muda | ❌ Não funciona |

## 📝 Checklist de Migração (Concluído)

- [x] Cloudflare Tunnel configurado
- [x] Domínio `www.runaserp.com.br` apontando para o túnel
- [x] OAuth2 atualizado (Google + Microsoft)
- [x] Mercado Pago webhook atualizado
- [x] Variáveis de ambiente atualizadas
- [x] Docker Compose configurado
- [x] Documentação atualizada
- [x] Steering files atualizados
- [x] **Ngrok removido** (substituído por Cloudflare)
- [x] **Nginx removido** (Cloudflare faz proxy)
- [x] **PgAdmin removido** (usar clientes externos)
