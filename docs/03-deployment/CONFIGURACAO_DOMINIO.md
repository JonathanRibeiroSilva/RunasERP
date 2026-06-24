# Configuração do Domínio runaserp.com.br

## 📋 Índice

1. [Configuração DNS](#1-configuração-dns)
2. [Certificado SSL com Let's Encrypt](#2-certificado-ssl-com-lets-encrypt)
3. [Configuração do Nginx para Produção](#3-configuração-do-nginx-para-produção)
4. [Deploy em Produção](#4-deploy-em-produção)
5. [Verificação e Testes](#5-verificação-e-testes)
6. [Manutenção e Troubleshooting](#6-manutenção-e-troubleshooting)

---

## 1. Configuração DNS

### 1.1. Criar Registros DNS

No painel do seu provedor de domínio (e.g., Registro.br, GoDaddy, Hostinger), configure:

```dns
# Tipo A - Aponta o domínio para o IP do servidor
@           A       300     SEU_IP_SERVIDOR
www         A       300     SEU_IP_SERVIDOR

# Tipo AAAA (Opcional - se tiver IPv6)
@           AAAA    300     SEU_IPV6_SERVIDOR
www         AAAA    300     SEU_IPV6_SERVIDOR
```

**Substitua:**
- `SEU_IP_SERVIDOR` pelo IP público do servidor onde o ERP está rodando

### 1.2. Verificar Propagação DNS

```powershell
# Windows - Verificar se o domínio está apontando corretamente
nslookup runaserp.com.br
nslookup www.runaserp.com.br

# Deve retornar o IP do seu servidor
```

⏰ **Atenção:** A propagação DNS pode levar de 5 minutos a 48 horas.

---

## 2. Certificado SSL com Let's Encrypt

### 2.1. Instalar Certbot no Servidor

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

**CentOS/RHEL:**
```bash
sudo yum install certbot python3-certbot-nginx -y
```

**Windows (via Docker):**
```powershell
# Usar container do Certbot (recomendado)
docker pull certbot/certbot
```

### 2.2. Gerar Certificado SSL

**Opção 1: Automático com Nginx (Recomendado)**

```bash
# Certbot configura automaticamente o Nginx
sudo certbot --nginx -d runaserp.com.br -d www.runaserp.com.br

# Siga as instruções:
# 1. Digite seu email
# 2. Aceite os termos de serviço
# 3. Escolha se quer receber emails promocionais
# 4. Escolha redirecionamento HTTP -> HTTPS (opção 2)
```

**Opção 2: Manual (para Docker/Windows)**

```bash
# 1. Gerar certificado apenas (sem configurar Nginx)
sudo certbot certonly --standalone \
  -d runaserp.com.br \
  -d www.runaserp.com.br \
  --email seu-email@example.com \
  --agree-tos \
  --non-interactive

# 2. Certificados ficam em:
# /etc/letsencrypt/live/runaserp.com.br/fullchain.pem
# /etc/letsencrypt/live/runaserp.com.br/privkey.pem
```

**Opção 3: Via Docker (Windows)**

```powershell
# Criar volumes para certificados
docker volume create letsencrypt-certs
docker volume create letsencrypt-www

# Gerar certificado
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

### 2.3. Renovação Automática

```bash
# Testar renovação (dry-run)
sudo certbot renew --dry-run

# Configurar cron para renovação automática (Linux)
sudo crontab -e

# Adicionar linha (renova 2x por dia):
0 0,12 * * * certbot renew --quiet --deploy-hook "docker restart erp-nginx"
```

**Windows (Task Scheduler):**
```powershell
# Criar tarefa agendada para renovação
schtasks /create /tn "Certbot Renewal" /tr "docker run --rm -v letsencrypt-certs:/etc/letsencrypt certbot/certbot renew && docker restart erp-nginx" /sc daily /st 02:00
```

---

## 3. Configuração do Nginx para Produção

### 3.1. Criar Configuração de Produção

Veja o arquivo `nginx/nginx.prod.conf` que será criado.

### 3.2. Configurar Docker Compose para Produção

Veja o arquivo `docker-compose.prod.yml` que será criado.

### 3.3. Atualizar Variáveis de Ambiente

```powershell
# Editar .env
code .env
```

Adicionar/atualizar:

```env
# ============================================
# DOMÍNIO E URLs DE PRODUÇÃO
# ============================================
FRONTEND_URL=https://runaserp.com.br
API_BASE_URL=https://runaserp.com.br/api

# ============================================
# OAUTH2 (URLs de Callback Produção)
# ============================================
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-client-secret

MICROSOFT_CLIENT_ID=seu-client-id
MICROSOFT_CLIENT_SECRET=seu-client-secret
MICROSOFT_TENANT_ID=common

# ============================================
# MERCADO PAGO (Webhooks Produção)
# ============================================
MP_ACCESS_TOKEN=seu-token-producao
MP_PUBLIC_KEY=sua-public-key-producao
MP_ENVIRONMENT=production

# ============================================
# EMAIL (Produção)
# ============================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
SMTP_FROM_NAME=Runas ERP
```

---

## 4. Deploy em Produção

### 4.1. Preparar Ambiente

```powershell
# 1. Parar containers de desenvolvimento
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml down

# 2. Fazer backup do banco de dados
docker exec erp-db pg_dump -U erp -d erp > backup_pre_producao.sql

# 3. Criar network (se não existir)
docker network create runaserp_erp-network
```

### 4.2. Build e Deploy

```powershell
# 1. Build das imagens
docker-compose -f docker-compose.prod.yml build

# 2. Subir serviços em produção
docker-compose -f docker-compose.prod.yml up -d

# 3. Verificar logs
docker-compose -f docker-compose.prod.yml logs -f nginx

# 4. Verificar saúde dos containers
docker-compose -f docker-compose.prod.yml ps
```

### 4.3. Executar Migrations

```powershell
# API Gateway
docker exec -it erp-api-gateway alembic upgrade head

# Cada serviço
docker exec -it erp-empresas alembic upgrade head
docker exec -it erp-clientes alembic upgrade head
docker exec -it erp-produtos alembic upgrade head
docker exec -it erp-estoque alembic upgrade head
docker exec -it erp-vendas alembic upgrade head
docker exec -it erp-financeiro alembic upgrade head
docker exec -it erp-notificacoes alembic upgrade head
```

### 4.4. Criar Usuário Admin

```powershell
# Executar seed do API Gateway
docker exec -it erp-api-gateway python seed.py
```

---

## 5. Verificação e Testes

### 5.1. Testar HTTPS

```powershell
# Verificar certificado SSL
Invoke-WebRequest -Uri "https://runaserp.com.br" -UseBasicParsing

# Verificar redirecionamento HTTP -> HTTPS
Invoke-WebRequest -Uri "http://runaserp.com.br" -UseBasicParsing

# Verificar API
Invoke-WebRequest -Uri "https://runaserp.com.br/api/health" -UseBasicParsing
```

### 5.2. Testar SSL no Navegador

Abra no navegador:
- ✅ https://runaserp.com.br
- ✅ https://www.runaserp.com.br
- ✅ http://runaserp.com.br (deve redirecionar para HTTPS)

### 5.3. Verificar Nota SSL

- **SSL Labs:** https://www.ssllabs.com/ssltest/analyze.html?d=runaserp.com.br
- **Meta esperada:** A ou A+

### 5.4. Testar OAuth2

```
1. Ir para https://runaserp.com.br/login
2. Clicar em "Login com Google"
3. Autorizar
4. Verificar redirecionamento para /dashboard
```

**⚠️ Importante:** Atualizar Redirect URIs nos consoles:
- **Google:** https://console.cloud.google.com/apis/credentials
  - Adicionar: `https://runaserp.com.br/auth/callback`
- **Microsoft:** https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps
  - Adicionar: `https://runaserp.com.br/auth/callback`

### 5.5. Testar Webhooks do Mercado Pago

```powershell
# Configurar webhook no Mercado Pago
# URL: https://runaserp.com.br/api/vendas/webhook/mercadopago

# Testar manualmente
curl -X POST https://runaserp.com.br/api/vendas/webhook/mercadopago `
  -H "Content-Type: application/json" `
  -d '{
    "action": "payment.created",
    "data": {
      "id": "123456789"
    }
  }'
```

---

## 6. Manutenção e Troubleshooting

### 6.1. Verificar Logs

```powershell
# Nginx
docker logs erp-nginx-prod -f

# API Gateway
docker logs erp-api-gateway-prod -f

# Todos os serviços
docker-compose -f docker-compose.prod.yml logs -f
```

### 6.2. Renovar Certificado Manualmente

```bash
# Linux
sudo certbot renew
sudo docker restart erp-nginx-prod

# Windows (Docker)
docker run --rm `
  -v letsencrypt-certs:/etc/letsencrypt `
  certbot/certbot renew

docker restart erp-nginx-prod
```

### 6.3. Reverter para Desenvolvimento

```powershell
# Parar produção
docker-compose -f docker-compose.prod.yml down

# Subir desenvolvimento
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

### 6.4. Problemas Comuns

#### Erro: "SSL certificate problem"

```bash
# Verificar validade do certificado
sudo certbot certificates

# Forçar renovação
sudo certbot renew --force-renewal
docker restart erp-nginx-prod
```

#### Erro: "502 Bad Gateway"

```powershell
# Verificar se API Gateway está rodando
docker ps | findstr api-gateway

# Ver logs do API Gateway
docker logs erp-api-gateway-prod --tail 100

# Reiniciar API Gateway
docker restart erp-api-gateway-prod
```

#### Erro: "CORS Error" em Produção

```nginx
# Verificar se nginx.prod.conf tem os headers CORS corretos
# Verificar se FRONTEND_URL no .env está correto
```

#### DNS não propaga

```powershell
# Limpar cache DNS local
ipconfig /flushdns

# Verificar com DNS público
nslookup runaserp.com.br 8.8.8.8
```

### 6.5. Monitoring

**Instalar Uptime Monitoring (Opcional):**

- **UptimeRobot:** https://uptimerobot.com/
- **Pingdom:** https://www.pingdom.com/
- **StatusCake:** https://www.statuscake.com/

Monitorar:
- ✅ https://runaserp.com.br
- ✅ https://runaserp.com.br/api/health

---

## 📚 Recursos Adicionais

- **Let's Encrypt Docs:** https://letsencrypt.org/docs/
- **Certbot Docs:** https://certbot.eff.org/
- **Nginx SSL Config Generator:** https://ssl-config.mozilla.org/
- **SSL Best Practices:** https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices

---

## ✅ Checklist de Deploy

- [ ] Registros DNS configurados (A e AAAA)
- [ ] DNS propagado e verificado
- [ ] Certificado SSL gerado e instalado
- [ ] Renovação automática configurada
- [ ] nginx.prod.conf configurado
- [ ] docker-compose.prod.yml configurado
- [ ] Variáveis de ambiente atualizadas (.env)
- [ ] OAuth2 Redirect URIs atualizados
- [ ] Mercado Pago Webhooks atualizados
- [ ] Build das imagens executado
- [ ] Containers em produção rodando
- [ ] Migrations executadas
- [ ] Usuário admin criado
- [ ] HTTPS funcionando
- [ ] Redirecionamento HTTP -> HTTPS funcionando
- [ ] API acessível via HTTPS
- [ ] OAuth2 testado
- [ ] Webhooks testados
- [ ] Monitoring configurado
- [ ] Backup agendado

---

**⚠️ IMPORTANTE:**
- Sempre faça backup antes de fazer deploy em produção
- Teste todas as features críticas após o deploy
- Mantenha os certificados SSL atualizados
- Monitore os logs regularmente
