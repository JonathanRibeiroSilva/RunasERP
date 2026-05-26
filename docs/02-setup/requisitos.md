# Requisitos do Sistema - Runas

> **Requisitos de hardware, software e configurações mínimas**

---

## 💻 Requisitos de Hardware

### Ambiente de Desenvolvimento

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 8 GB | 16+ GB |
| **Disco** | 20 GB livres | 50+ GB SSD |
| **Rede** | 10 Mbps | 100+ Mbps |

### Ambiente de Produção (MVP)

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 2 vCPUs | 4+ vCPUs |
| **RAM** | 4 GB | 8+ GB |
| **Disco** | 50 GB SSD | 100+ GB SSD |
| **Rede** | 100 Mbps | 1 Gbps |
| **Backup** | Diário | Contínuo |

**Observações:**
- Requisitos aumentam conforme volume de dados e usuários
- SSD é **obrigatório** para PostgreSQL (performance)
- Backup automático é **essencial** para dados de produção

---

## 🖥️ Requisitos de Software

### Sistema Operacional

#### Desenvolvimento

| SO | Versão | Status |
|----|--------|--------|
| **Linux** | Ubuntu 22.04+, Debian 12+ | ✅ Recomendado |
| **macOS** | 13+ (Ventura) | ✅ Suportado |
| **Windows** | 10/11 com WSL2 | ⚠️ Suportado (via WSL2) |

#### Produção

| SO | Versão | Status |
|----|--------|--------|
| **Linux** | Ubuntu 22.04 LTS, Debian 12 | ✅ Recomendado |
| **Docker** | Qualquer SO com Docker | ✅ Recomendado |

**Importante:**
- Windows **requer WSL2** para desenvolvimento
- Produção **deve usar Linux** ou Docker
- macOS é suportado mas não recomendado para produção

### Docker e Docker Compose

| Software | Versão Mínima | Instalação |
|----------|---------------|------------|
| **Docker** | 24.0+ | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| **Docker Compose** | 2.23+ | Incluído no Docker Desktop |

**Verificar instalação:**

```bash
docker --version
# Docker version 24.0.0 ou superior

docker compose version
# Docker Compose version v2.23.0 ou superior
```

### Python (Apenas para desenvolvimento sem Docker)

| Software | Versão | Instalação |
|----------|--------|------------|
| **Python** | 3.12+ | [python.org](https://www.python.org/downloads/) |
| **pip** | 23.0+ | Incluído no Python |
| **venv** | Built-in | Incluído no Python |

**Verificar instalação:**

```bash
python --version
# Python 3.12.0 ou superior

pip --version
# pip 23.0 ou superior
```

### Node.js (Frontend)

| Software | Versão | Instalação |
|----------|--------|------------|
| **Node.js** | 20 LTS+ | [nodejs.org](https://nodejs.org/) |
| **npm** | 10.0+ | Incluído no Node.js |

**Verificar instalação:**

```bash
node --version
# v20.0.0 ou superior

npm --version
# 10.0.0 ou superior
```

### Git

| Software | Versão | Instalação |
|----------|--------|------------|
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com/downloads) |

**Verificar instalação:**

```bash
git --version
# git version 2.40.0 ou superior
```

---

## 🔧 Configurações do Sistema

### Limites do Sistema (Linux)

Para produção, ajustar limites do sistema:

```bash
# /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
```

### Configurações do Docker

```bash
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
```

### Portas Necessárias

| Serviço | Porta | Protocolo | Acesso |
|---------|-------|-----------|--------|
| **Frontend** | 3000 | HTTP | Público |
| **API Gateway** | 8000 | HTTP | Público |
| **Clientes** | 8001 | HTTP | Interno |
| **Produtos** | 8002 | HTTP | Interno |
| **Estoque** | 8003 | HTTP | Interno |
| **Vendas** | 8004 | HTTP | Interno |
| **Financeiro** | 8005 | HTTP | Interno |
| **Notificações** | 8006 | HTTP | Interno |
| **PostgreSQL** | 5432 | TCP | Interno |
| **Redis** | 6379 | TCP | Interno |
| **RabbitMQ** | 5672 | TCP | Interno |
| **RabbitMQ Management** | 15672 | HTTP | Interno |
| **pgAdmin** | 5050 | HTTP | Interno |
| **Evolution API** | 8080 | HTTP | Interno |

**Firewall:**
- Produção: Apenas portas 80 (HTTP) e 443 (HTTPS) públicas
- Desenvolvimento: Todas as portas acima acessíveis localmente

---

## 🌐 Requisitos de Rede

### Desenvolvimento

- **Internet**: Necessária para download de dependências
- **Velocidade**: 10 Mbps mínimo
- **Latência**: Não crítica

### Produção

- **Internet**: Necessária para integrações (Mercado Pago, WhatsApp)
- **Velocidade**: 100 Mbps mínimo
- **Latência**: < 50ms para usuários finais
- **Uptime**: 99.9% recomendado

### Domínio e SSL

- **Domínio**: Necessário para produção (ex: `erp.suaempresa.com`)
- **SSL/TLS**: Obrigatório (Let's Encrypt gratuito)
- **DNS**: Configurado corretamente (A record para servidor)

---

## 📦 Dependências Externas

### Serviços Obrigatórios

| Serviço | Finalidade | Custo |
|---------|------------|-------|
| **Mercado Pago** | Pagamentos PIX | Gratuito (taxa por transação) |
| **Evolution API** | WhatsApp | Self-hosted (gratuito) |

### Serviços Opcionais

| Serviço | Finalidade | Custo |
|---------|------------|-------|
| **Sentry** | Monitoramento de erros | Gratuito até 5k eventos/mês |
| **Google Analytics** | Analytics | Gratuito |
| **Cloudflare** | CDN e proteção DDoS | Gratuito (plano básico) |

---

## 🔐 Requisitos de Segurança

### Certificados SSL/TLS

- **Desenvolvimento**: Não obrigatório
- **Produção**: **Obrigatório** (Let's Encrypt)

### Variáveis de Ambiente

- **SECRET_KEY**: Mínimo 32 caracteres aleatórios
- **Senhas**: Mínimo 12 caracteres, complexas
- **Tokens**: Gerados automaticamente, nunca hardcoded

### Backup

- **Frequência**: Diário (mínimo)
- **Retenção**: 30 dias (mínimo)
- **Localização**: Fora do servidor principal
- **Teste de restore**: Mensal

---

## 📱 Requisitos do Cliente (Navegador)

### Navegadores Suportados

| Navegador | Versão Mínima | Status |
|-----------|---------------|--------|
| **Chrome** | 100+ | ✅ Recomendado |
| **Firefox** | 100+ | ✅ Suportado |
| **Safari** | 15+ | ✅ Suportado |
| **Edge** | 100+ | ✅ Suportado |
| **Opera** | 85+ | ⚠️ Suportado |
| **IE 11** | - | ❌ Não suportado |

### Requisitos do Navegador

- **JavaScript**: Habilitado (obrigatório)
- **Cookies**: Habilitados (obrigatório)
- **LocalStorage**: Habilitado (obrigatório)
- **WebSockets**: Suportado (opcional, para notificações em tempo real)

### Resolução de Tela

| Dispositivo | Resolução Mínima | Status |
|-------------|------------------|--------|
| **Desktop** | 1366x768 | ✅ Suportado |
| **Tablet** | 768x1024 | ✅ Suportado |
| **Mobile** | 375x667 | ✅ Suportado |

---

## 🧪 Requisitos para Desenvolvimento

### IDE Recomendado

| IDE | Plugins Recomendados |
|-----|---------------------|
| **VS Code** | Python, Pylance, ESLint, Prettier, Docker, GitLens |
| **PyCharm** | FastAPI, Docker, Database Tools |
| **WebStorm** | ESLint, Prettier, Tailwind CSS IntelliSense |

### Ferramentas de Desenvolvimento

| Ferramenta | Finalidade |
|------------|------------|
| **Postman/Insomnia** | Testar APIs |
| **pgAdmin/DBeaver** | Gerenciar PostgreSQL |
| **Redis Commander** | Gerenciar Redis |
| **Docker Desktop** | Gerenciar containers |

---

## ✅ Checklist de Verificação

Antes de iniciar o desenvolvimento, verifique:

### Sistema

- [ ] Sistema operacional compatível
- [ ] Espaço em disco suficiente (20+ GB)
- [ ] RAM suficiente (8+ GB)
- [ ] Conexão com internet estável

### Software

- [ ] Docker instalado e funcionando
- [ ] Docker Compose instalado
- [ ] Git instalado
- [ ] Node.js 20+ instalado (para frontend)
- [ ] Python 3.12+ instalado (opcional, para dev sem Docker)

### Rede

- [ ] Portas 3000, 8000-8006, 5432, 6379, 5672, 15672, 5050, 8080 disponíveis
- [ ] Firewall configurado (se necessário)
- [ ] Acesso à internet para download de dependências

### Contas e Credenciais

- [ ] Conta no Mercado Pago (produção)
- [ ] Número de WhatsApp Business (produção)
- [ ] Domínio registrado (produção)
- [ ] Certificado SSL configurado (produção)

---

## 🆘 Problemas Comuns

### Docker não inicia

**Problema**: Docker daemon não está rodando

**Solução**:
```bash
# Linux
sudo systemctl start docker

# macOS/Windows
# Abrir Docker Desktop
```

### Porta já em uso

**Problema**: `Error: Port 8000 is already in use`

**Solução**:
```bash
# Encontrar processo usando a porta
lsof -i :8000

# Matar processo
kill -9 <PID>
```

### Permissão negada (Linux)

**Problema**: `Permission denied` ao rodar Docker

**Solução**:
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Fazer logout e login novamente
```

---

## 📚 Próximos Passos

Após verificar todos os requisitos:

1. Consulte o [Guia de Instalação](./README.md)
2. Configure as [Variáveis de Ambiente](./README.md#variáveis-de-ambiente)
3. Execute o [Quick Start](../../QUICK-START.md)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
