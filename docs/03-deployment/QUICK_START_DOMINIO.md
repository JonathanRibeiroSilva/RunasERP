# 🚀 Quick Start - Configuração do Domínio runaserp.com.br

## Passo 1: Configurar DNS (5 minutos)

No painel do seu provedor de domínio, adicione:

```
Tipo: A
Nome: @
Valor: SEU_IP_DO_SERVIDOR
TTL: 300

Tipo: A
Nome: www
Valor: SEU_IP_DO_SERVIDOR
TTL: 300
```

**Verificar propagação:**
```powershell
nslookup runaserp.com.br
```

---

## Passo 2: Gerar Certificado SSL (10 minutos)

```powershell
# 1. Criar volumes
docker volume create letsencrypt-certs
docker volume create letsencrypt-www

# 2. Gerar certificado
docker run --rm `
  -v letsencrypt-certs:/etc/letsencrypt `
  -v letsencrypt-www:/var/www/certbot `
  -p 80:80 -p 443:443 `
  certbot/certbot certonly --standalone `
  -d runaserp.com.br `
  -d www.runaserp.com.br `
  --email seu-email@example.com `
  --agree-tos `
  --non-interactive
```

---

## Passo 3: Atualizar .env (2 minutos)

Edite o arquivo `.env` e atualize:

```env
FRONTEND_URL=https://runaserp.com.br
API_BASE_URL=https://runaserp.com.br/api
MP_ENVIRONMENT=production
```

---

## Passo 4: Deploy Automatizado (5 minutos)

```powershell
# Deploy completo (recomendado)
.\scripts\deploy-prod.ps1

# OU deploy sem SSL (para testar)
.\scripts\deploy-prod.ps1 -SkipSSL

# OU deploy pulando migrations
.\scripts\deploy-prod.ps1 -SkipMigrations
```

---

## Passo 5: Verificar (2 minutos)

**Testar HTTPS:**
```powershell
Invoke-WebRequest -Uri "https://runaserp.com.br/api/health" -UseBasicParsing
```

**Abrir no navegador:**
- https://runaserp.com.br
- https://runaserp.com.br/login

---

## Passo 6: Configurar OAuth2 (5 minutos)

### Google
1. Ir para: https://console.cloud.google.com/apis/credentials
2. Editar "OAuth 2.0 Client IDs"
3. Adicionar em "Authorized redirect URIs":
   ```
   https://runaserp.com.br/auth/callback
   ```

### Microsoft
1. Ir para: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps
2. Editar aplicativo
3. Em "Authentication" → "Redirect URIs", adicionar:
   ```
   https://runaserp.com.br/auth/callback
   ```

---

## Passo 7: Configurar Webhooks (5 minutos)

### Mercado Pago
1. Ir para: https://www.mercadopago.com.br/developers/panel
2. Configurar webhook:
   ```
   URL: https://runaserp.com.br/api/vendas/webhook/mercadopago
   Eventos: payment.created, payment.updated
   ```

---

## 🎉 Pronto!

Seu ERP está rodando em produção com SSL em: **https://runaserp.com.br**

---

## 🔧 Comandos Úteis

```powershell
# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Ver status
docker-compose -f docker-compose.prod.yml ps

# Reiniciar serviço
docker restart erp-nginx-prod

# Parar produção
docker-compose -f docker-compose.prod.yml down

# Voltar para desenvolvimento
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

---

## 📚 Documentação Completa

Para mais detalhes, consulte: `docs/03-deployment/CONFIGURACAO_DOMINIO.md`

---

## ⚠️ Troubleshooting

### Erro: SSL certificate problem

```powershell
# Renovar certificado
docker run --rm -v letsencrypt-certs:/etc/letsencrypt certbot/certbot renew
docker restart erp-nginx-prod
```

### Erro: 502 Bad Gateway

```powershell
# Verificar API Gateway
docker logs erp-api-gateway-prod --tail 50
docker restart erp-api-gateway-prod
```

### Erro: CORS

Verifique se `FRONTEND_URL` no `.env` está correto: `https://runaserp.com.br`
