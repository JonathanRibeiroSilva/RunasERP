# 🚀 Migração: Local → VPS (com Cloudflare Tunnel)

## 📋 Visão Geral

Migração do ERP rodando **localmente** para **VPS na nuvem**, mantendo o **Cloudflare Tunnel**.

**Vantagens:**
- ✅ Setup idêntico ao local
- ✅ Online 24/7
- ✅ Sem reconfigurar DNS ou SSL
- ✅ Mesmos comandos

---

## 🎯 Pré-requisitos

- [ ] VPS contratada (Ubuntu 20.04+ ou Debian 11+)
- [ ] Acesso SSH ao servidor
- [ ] IP público da VPS
- [ ] Credenciais do Cloudflare Tunnel (do PC local)

---

## 🖥️ Provedores VPS Recomendados

| Provedor | Plano | Custo/mês | RAM | CPU |
|----------|-------|-----------|-----|-----|
| DigitalOcean | Basic | ~$6 USD | 1GB | 1 vCPU |
| Vultr | Regular | ~$6 USD | 1GB | 1 vCPU |
| Linode | Nanode | ~$5 USD | 1GB | 1 vCPU |
| Contabo | Cloud VPS S | ~€5 EUR | 4GB | 2 vCPU |

**Recomendação:** Mínimo 2GB RAM

---

## 📦 Passo 1: Preparar VPS (15 min)

### 1.1. Conectar via SSH

```bash
ssh root@SEU_IP_VPS
```

### 1.2. Atualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano htop
```

### 1.3. Instalar Docker

```bash
# Docker
curl -fsSL https://get.docker.com | sh

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verificar
docker --version
docker-compose --version
```

---

## 📁 Passo 2: Transferir Projeto (10 min)

### Opção A: Via Git

```bash
cd /opt
sudo git clone https://github.com/seu-usuario/RunasERP.git
cd RunasERP
```

### Opção B: Via SCP

```powershell
# No PC
cd E:\GitHub\ERP\RunasERP
tar -czf runas-erp.tar.gz --exclude=node_modules --exclude=__pycache__ .
scp runas-erp.tar.gz usuario@SEU_IP_VPS:/opt/
```

```bash
# Na VPS
cd /opt
tar -xzf runas-erp.tar.gz
cd RunasERP
```

---

## 🔐 Passo 3: Transferir Credenciais Tunnel (5 min)

```powershell
# No PC
cd $env:USERPROFILE
tar -czf cloudflared-creds.tar.gz .cloudflared
scp cloudflared-creds.tar.gz usuario@SEU_IP_VPS:~/
```

```bash
# Na VPS
cd ~
tar -xzf cloudflared-creds.tar.gz
ls -la .cloudflared/
# Deve ter: cert.pem, config.yml, tunnel-id.json
```

---

## ⚙️ Passo 4: Configurar .env (5 min)

```bash
cd /opt/RunasERP
cp .env.example .env
nano .env
```

**Alterar:**
```env
# URLs (MANTER iguais)
FRONTEND_URL=https://runaserp.com.br
API_BASE_URL=https://runaserp.com.br/api

# Senhas (MUDAR!)
POSTGRES_PASSWORD=SENHA_FORTE_AQUI
SECRET_KEY=GERAR_NOVA_CHAVE  # openssl rand -hex 32

# Mercado Pago (PRODUÇÃO!)
MP_ENVIRONMENT=production
```

---

## 🐳 Passo 5: Subir Containers (10 min)

```bash
# Criar network
docker network create runaserp_erp-network

# Subir
docker-compose up -d

# Verificar
docker-compose ps

# Migrations
docker exec -it erp-api-gateway alembic upgrade head
docker exec -it erp-empresas alembic upgrade head
docker exec -it erp-clientes alembic upgrade head
docker exec -it erp-produtos alembic upgrade head
docker exec -it erp-estoque alembic upgrade head
docker exec -it erp-vendas alembic upgrade head
docker exec -it erp-financeiro alembic upgrade head
docker exec -it erp-notificacoes alembic upgrade head

# Admin
docker exec -it erp-api-gateway python seed.py
```

---

## 🚇 Passo 6: Instalar Cloudflared (5 min)

```bash
# Baixar
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Instalar
sudo dpkg -i cloudflared-linux-amd64.deb

# Verificar
cloudflared --version
```

---

## ⚡ Passo 7: Configurar Tunnel como Serviço (5 min)

```bash
# Instalar serviço
sudo cloudflared service install

# Iniciar
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Status
sudo systemctl status cloudflared

# Logs
sudo journalctl -u cloudflared -f
```

**Deve mostrar:**
```
Registered tunnel connection connIndex=0
Registered tunnel connection connIndex=1
Registered tunnel connection connIndex=2
Registered tunnel connection connIndex=3
```

✅ Tunnel conectado!

---

## 🧪 Passo 8: Testar

```bash
# Localmente na VPS
curl http://localhost/health
```

**No navegador:**
- https://runaserp.com.br ✅

---

## 🔐 Passo 9: Segurança Básica (10 min)

```bash
# Firewall
sudo apt install ufw -y
sudo ufw allow 22/tcp
sudo ufw enable

# Fail2Ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban

# Desabilitar root SSH
sudo nano /etc/ssh/sshd_config
# Mudar: PermitRootLogin no
sudo systemctl restart sshd
```

---

## 🔄 Passo 10: Backup Automático

```bash
# Script
sudo nano /opt/backup-erp.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
docker exec erp-db pg_dump -U erp -d erp | gzip > $BACKUP_DIR/db_$DATE.sql.gz
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
```

```bash
# Tornar executável
sudo chmod +x /opt/backup-erp.sh

# Agendar (crontab)
sudo crontab -e
# Adicionar: 0 3 * * * /opt/backup-erp.sh >> /var/log/backup-erp.log 2>&1
```

---

## ✅ Checklist

- [ ] VPS acessível via SSH
- [ ] Docker instalado
- [ ] Projeto transferido
- [ ] Credenciais tunnel transferidas
- [ ] .env configurado
- [ ] Containers rodando
- [ ] Migrations executadas
- [ ] Admin criado
- [ ] Cloudflared instalado
- [ ] Tunnel como serviço
- [ ] Site acessível (https://runaserp.com.br)
- [ ] Firewall configurado
- [ ] Backup configurado

---

## 🆘 Troubleshooting

### Container não sobe
```bash
docker logs erp-api-gateway --tail 100
docker-compose restart
```

### Tunnel não conecta
```bash
sudo journalctl -u cloudflared -f
sudo systemctl restart cloudflared
```

### Site não abre
```bash
docker-compose ps
curl http://localhost/health
docker-compose restart
```

---

## 💰 Custos

| Item | Custo |
|------|-------|
| VPS (2GB) | ~R$ 30-50/mês |
| Cloudflare | R$ 0 |
| SSL | R$ 0 |
| **TOTAL** | **~R$ 30-50/mês** |

---

## 🎉 Pronto!

Seu ERP está em produção:
- ✅ Online 24/7
- ✅ SSL automático
- ✅ Backup configurado
- ✅ https://runaserp.com.br 🚀
