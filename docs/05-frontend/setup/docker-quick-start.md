# 🐳 Docker Quick Start - Frontend

**Data:** 2026-05-25  
**Versão:** 1.0.0  
**Status:** ✅ Recomendado

---

## 🚀 Início Rápido com Docker (5 minutos)

### Pré-requisito

```bash
# Verificar Docker
docker --version
docker-compose --version
```

Se não tiver Docker instalado, acesse: https://www.docker.com/products/docker-desktop

### Passo 1: Clonar/Atualizar Repositório

```bash
cd c:\Users\jonat\Documents\GitHub\ERP\RunasERP
git pull origin main
```

### Passo 2: Iniciar Backend

```bash
docker-compose -f docker-compose.dev.yml up api-gateway
```

**Esperado:**
```
api-gateway_1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verificar:** http://localhost:8000/docs

### Passo 3: Iniciar Frontend (em outro terminal)

```bash
docker-compose -f docker-compose.dev.yml up frontend-dev
```

**Esperado:**
```
frontend-dev_1  | VITE v4.x.x  ready in xxx ms
frontend-dev_1  | ➜  Local:   http://localhost:3000/
```

**Verificar:** http://localhost:3000

### Passo 4: Testar

Abra http://localhost:3000 e faça login:
```
Email: admin@runas.com
Senha: Admin@123
```

---

## 📊 Comandos Úteis

### Iniciar Tudo

```bash
# Iniciar backend e frontend
docker-compose -f docker-compose.dev.yml up

# Ou em background
docker-compose -f docker-compose.dev.yml up -d
```

### Parar Tudo

```bash
# Parar todos os containers
docker-compose -f docker-compose.dev.yml down

# Parar e remover volumes
docker-compose -f docker-compose.dev.yml down -v
```

### Ver Logs

```bash
# Ver logs do frontend
docker-compose -f docker-compose.dev.yml logs -f frontend-dev

# Ver logs do backend
docker-compose -f docker-compose.dev.yml logs -f api-gateway

# Ver logs de tudo
docker-compose -f docker-compose.dev.yml logs -f
```

### Executar Comandos

```bash
# Executar comando no frontend
docker-compose -f docker-compose.dev.yml exec frontend-dev npm run build

# Executar comando no backend
docker-compose -f docker-compose.dev.yml exec api-gateway python -m pytest
```

### Reconstruir Imagens

```bash
# Reconstruir imagens
docker-compose -f docker-compose.dev.yml build

# Reconstruir e iniciar
docker-compose -f docker-compose.dev.yml up --build
```

---

## 🔍 Troubleshooting

### "Cannot connect to Docker daemon"

**Solução:**
1. Abra Docker Desktop
2. Aguarde inicializar (pode levar alguns minutos)
3. Tente novamente

### "Port 3000 already in use"

**Solução:**
```bash
# Parar containers anteriores
docker-compose -f docker-compose.dev.yml down

# Ou usar porta diferente
docker-compose -f docker-compose.dev.yml up -e VITE_PORT=3001
```

### "Port 8000 already in use"

**Solução:**
```bash
# Parar containers anteriores
docker-compose -f docker-compose.dev.yml down

# Ou usar porta diferente
docker-compose -f docker-compose.dev.yml up -e API_PORT=8001
```

### "Out of memory"

**Solução:**
1. Abra Docker Desktop
2. Vá em Settings > Resources
3. Aumente a memória disponível
4. Reinicie Docker

### "Build failed"

**Solução:**
```bash
# Limpar cache e reconstruir
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up
```

---

## 📁 Estrutura Docker

### docker-compose.dev.yml

```yaml
version: '3.8'

services:
  # Frontend (React + Vite)
  frontend-dev:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
    environment:
      - VITE_API_URL=http://localhost:8000

  # Backend (FastAPI)
  api-gateway:
    build:
      context: ./api-gateway
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - SECRET_KEY=...
    depends_on:
      - postgres

  # Database (PostgreSQL)
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=erp_runas
      - POSTGRES_PASSWORD=...
```

---

## 🎯 Vantagens do Docker

✅ **Sem Instalações Manuais**
- Não precisa instalar Node.js, Python, PostgreSQL
- Tudo vem pronto na imagem

✅ **Ambiente Consistente**
- Funciona igual em qualquer máquina
- Sem problemas de versão

✅ **Fácil de Compartilhar**
- Compartilhe o docker-compose.yml
- Todos têm o mesmo ambiente

✅ **Pronto para Produção**
- Mesma imagem em dev e prod
- Sem surpresas ao fazer deploy

✅ **Hot Reload**
- Mudanças no código refletem automaticamente
- Não precisa reiniciar container

✅ **Isolado**
- Não afeta seu sistema
- Fácil de limpar (docker-compose down -v)

---

## 🚀 Próximos Passos

1. ✅ Iniciar com Docker
2. ✅ Testar autenticação
3. ✅ Consultar [QUICK-TEST-GUIDE.md](./QUICK-TEST-GUIDE.md)
4. ✅ Configurar OAuth (se necessário)

---

## 📞 Suporte

### Documentação Relacionada

- [QUICK-TEST-GUIDE.md](./QUICK-TEST-GUIDE.md) - Guia de testes
- [PREREQUISITES.md](./PREREQUISITES.md) - Pré-requisitos
- [DOCKER.md](./DOCKER.md) - Documentação completa de Docker

### Comandos Rápidos

```bash
# Iniciar tudo
docker-compose -f docker-compose.dev.yml up

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f

# Parar tudo
docker-compose -f docker-compose.dev.yml down
```

---

**Última Atualização:** 2026-05-25  
**Versão:** 1.0.0

---

<div align="center">

**[QUICK-TEST-GUIDE.md](./QUICK-TEST-GUIDE.md) → [PREREQUISITES.md](./PREREQUISITES.md) → [DOCKER.md](./DOCKER.md)**

Feito com ❤️ pela equipe Deneb Corp

</div>
