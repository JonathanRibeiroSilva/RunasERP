# ⚙️ Setup e Instalação - Runas

Guias completos para configurar o ambiente de desenvolvimento do Runas.

---

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

### Obrigatórios
- **Docker Desktop** 4.20+ ([Download](https://www.docker.com/products/docker-desktop))
- **Docker Compose** 2.18+ (incluído no Docker Desktop)
- **Git** 2.40+ ([Download](https://git-scm.com/downloads))

### Recomendados
- **VS Code** ([Download](https://code.visualstudio.com/))
- **Node.js** 18+ (para desenvolvimento frontend)
- **Python** 3.11+ (para desenvolvimento backend)

### Recursos Mínimos
- **RAM**: 8 GB (16 GB recomendado)
- **Disco**: 10 GB livres
- **CPU**: 4 cores (8 cores recomendado)

---

## 🚀 Quick Start

### 1. Clonar o Repositório

```bash
git clone https://github.com/denebcorp/runas.git
cd runas
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas configurações
# Windows: notepad .env
# Linux/Mac: nano .env
```

### 3. Iniciar com Docker

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f
```

### 4. Acessar o Sistema

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050
- **RabbitMQ**: http://localhost:15672

---

## 📚 Guias Detalhados

### [Requisitos do Sistema](./requisitos.md)
Requisitos de hardware, software e recursos necessários.

### [Instalação Local](./instalacao-local.md)
Como instalar e configurar o ambiente sem Docker.

### [Instalação com Docker](./instalacao-docker.md)
Guia completo de instalação usando Docker Compose.

### [Variáveis de Ambiente](./variaveis-ambiente.md)
Documentação completa de todas as variáveis de configuração.

---

## 🔧 Configuração Inicial

### 1. Criar Usuário Admin

```bash
# Acessar container do API Gateway
docker-compose exec api-gateway bash

# Executar seed
python seed.py
```

**Credenciais padrão**:
- Email: `admin@runas.com`
- Senha: `admin123`

⚠️ **Importante**: Altere a senha padrão em produção!

### 2. Configurar OAuth (Opcional)

Para habilitar login com Google/Microsoft:

1. Criar aplicação no [Google Cloud Console](https://console.cloud.google.com/)
2. Criar aplicação no [Azure Portal](https://portal.azure.com/)
3. Adicionar credenciais no `.env`:

```env
GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_CLIENT_SECRET=seu_client_secret

MICROSOFT_CLIENT_ID=seu_client_id
MICROSOFT_CLIENT_SECRET=seu_client_secret
```

### 3. Configurar WhatsApp (Opcional)

Para habilitar notificações via WhatsApp:

1. Acessar Evolution API: http://localhost:8080
2. Criar instância
3. Conectar WhatsApp via QR Code
4. Adicionar API Key no `.env`:

```env
EVOLUTION_API_KEY=sua_api_key
EVOLUTION_INSTANCE_NAME=sua_instancia
```

---

## 🐳 Comandos Docker Úteis

### Gerenciamento de Containers

```bash
# Iniciar todos os serviços
docker-compose up -d

# Parar todos os serviços
docker-compose down

# Reiniciar um serviço específico
docker-compose restart api-gateway

# Ver logs de um serviço
docker-compose logs -f api-gateway

# Ver status dos containers
docker-compose ps

# Executar comando em um container
docker-compose exec api-gateway bash
```

### Limpeza

```bash
# Parar e remover containers
docker-compose down

# Remover volumes (⚠️ apaga dados)
docker-compose down -v

# Limpar imagens não utilizadas
docker system prune -a
```

### Rebuild

```bash
# Rebuild de um serviço específico
docker-compose build api-gateway

# Rebuild de todos os serviços
docker-compose build

# Rebuild e restart
docker-compose up -d --build
```

---

## 🔍 Verificação de Instalação

### 1. Verificar Serviços

```bash
# Todos os containers devem estar "Up"
docker-compose ps
```

Saída esperada:
```
NAME                STATUS
api-gateway         Up
db_gateway          Up
redis               Up
rabbitmq            Up
pgadmin             Up
evolution-api       Up
```

### 2. Testar API Gateway

```bash
# Health check
curl http://localhost:8000/health

# Resposta esperada:
# {"status": "healthy"}
```

### 3. Testar Banco de Dados

```bash
# Acessar pgAdmin
# URL: http://localhost:5050
# Email: admin@runas.com
# Senha: admin
```

### 4. Testar RabbitMQ

```bash
# Acessar Management UI
# URL: http://localhost:15672
# Usuário: guest
# Senha: guest
```

---

## ❌ Problemas Comuns

### Porta já em uso

**Erro**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solução**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### Falta de memória

**Erro**: `Container killed due to OOM`

**Solução**:
- Aumentar memória do Docker Desktop (Settings → Resources)
- Mínimo recomendado: 8 GB

### Permissões no Linux

**Erro**: `Permission denied`

**Solução**:
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Fazer logout e login novamente
```

---

## 📚 Próximos Passos

Após a instalação:

1. **[Explorar a Arquitetura](../03-arquitetura/)** - Entenda como o sistema funciona
2. **[Ler as Regras de Negócio](../11-regras-negocio/)** - Conheça as regras implementadas
3. **[Consultar a API](../10-api-reference/)** - Veja os endpoints disponíveis
4. **[Contribuir](../07-desenvolvimento/)** - Aprenda a desenvolver no projeto

---

## 🆘 Precisa de Ajuda?

- **Problemas comuns**: [Troubleshooting](../09-troubleshooting/)
- **Dúvidas sobre APIs**: [Referência de APIs](../10-api-reference/)
- **Erros de OAuth**: [OAuth Issues](../09-troubleshooting/oauth-issues.md)
- **Problemas com Docker**: [Docker Issues](../09-troubleshooting/docker-issues.md)

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
