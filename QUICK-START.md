# ⚡ Quick Start - Runas 

**Tempo estimado**: 5 minutos  
**Pré-requisitos**: Docker e Docker Compose instalados

---

## 🚀 Escolha seu Método de Inicialização

### 📍 Método 1: Localhost (Desenvolvimento Local)

**Use quando**: Testar localmente sem precisar de acesso externo

```powershell
# 1. Subir todos os serviços
docker-compose -f docker-compose.dev.yml up -d

# 2. Aguardar ~30 segundos e verificar status
docker-compose -f docker-compose.dev.yml ps

# 3. Verificar logs
docker logs erp-api-gateway-dev -f
```

**✅ Acesso**:
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PgAdmin: http://localhost:5050

---

### 🌐 Método 2: Cloudflare Tunnel (Acesso Externo via Internet)

**Use quando**: Precisa de webhooks, OAuth, testes mobile ou demonstrações remotas

#### Pré-requisitos adicionais:
1. Token Cloudflare Tunnel configurado no `.env.cloudflare`
2. Domínio configurado (www.runaserp.com.br)

```powershell
# 1. Subir com Cloudflare Tunnel
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# 2. Verificar status do túnel
docker logs erp-cloudflared-dev -f

# 3. Acessar via domínio
```

**✅ Acesso**:
- Frontend: https://www.runaserp.com.br
- API Gateway: https://www.runaserp.com.br/api
- API Docs: https://www.runaserp.com.br/api/docs

**⚠️ Importante**: OAuth2 e webhooks já estão configurados para o domínio Cloudflare.

---

**Pronto!** Escolha o método adequado e siga os passos. ✅

---

## 🧪 Teste Manual Rápido (1 minuto)

### 1. Login e obter token

```powershell
# Localhost
Invoke-WebRequest -Uri "http://localhost:8000/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=admin@runas.com&password=Admin@123"

# Cloudflare
Invoke-WebRequest -Uri "https://www.runaserp.com.br/api/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=admin@runas.com&password=Admin@123"
```

**Copie o `access_token` da resposta!**

### 2. Criar um cliente

```powershell
$token = "SEU_TOKEN_AQUI"

# Localhost
Invoke-WebRequest -Uri "http://localhost:8000/api/clientes" `
  -Method POST `
  -Headers @{
    "Authorization"="Bearer $token"
    "Content-Type"="application/json"
  } `
  -Body '{
    "nome": "João Silva",
    "cpf_cnpj": "12345678901",
    "email": "joao@example.com",
    "telefone": "+5511999999999",
    "tipo": "PESSOA_FISICA"
  }'
```

### 3. Listar produtos

```powershell
# Localhost
Invoke-WebRequest -Uri "http://localhost:8000/api/produtos" `
  -Headers @{"Authorization"="Bearer $token"}

# Cloudflare
Invoke-WebRequest -Uri "https://www.runaserp.com.br/api/produtos" `
  -Headers @{"Authorization"="Bearer $token"}
```

---

## 🔧 Troubleshooting

### ❌ "Port already in use"

```powershell
# Verificar qual processo está usando a porta
netstat -ano | findstr :8000

# Parar todos os containers e tentar novamente
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

### ❌ "Container exited with code 1"

```powershell
# Ver logs do container problemático
docker logs erp-api-gateway-dev
docker logs erp-db-dev

# Verificar .env está configurado
cat .env
```

### ❌ "Cannot connect to database"

```powershell
# Verificar se o banco está rodando
docker ps | Select-String "postgres"

# Verificar logs do banco
docker logs erp-db-dev

# Aguardar healthcheck do banco (30 segundos)
Start-Sleep -Seconds 30
```

### ❌ Frontend não carrega

```powershell
# Verificar se o container está rodando
docker ps | Select-String "frontend"

# Ver logs
docker logs erp-frontend-dev -f

# Rebuild do frontend se necessário
docker-compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev
```

---

## 📚 Próximos Passos

1. **Frontend**: Acesse http://localhost:3000 e faça login com `admin@runas.com` / `Admin@123`
2. **Explorar API**: Visite http://localhost:8000/docs para ver todos os endpoints
3. **Criar Seed Data**: Rode `docker-compose -f docker-compose.dev.yml exec api-gateway python seed.py`
4. **Documentação Completa**: Veja `docs/README.md` para detalhes

---

## 🛠️ Comandos Úteis

```powershell
# Parar todos os serviços
docker-compose -f docker-compose.dev.yml down

# Ver logs de um serviço específico
docker logs erp-api-gateway-dev -f

# Restartar um serviço específico
docker-compose -f docker-compose.dev.yml restart api-gateway

# Ver status de todos os serviços
docker-compose -f docker-compose.dev.yml ps

# Limpar tudo (incluindo volumes)
docker-compose -f docker-compose.dev.yml down -v

# Rebuild de um serviço
docker-compose -f docker-compose.dev.yml up -d --build api-gateway
```

---

## 🎯 Estrutura do Projeto

```
RunasERP/
├── api-gateway/              # Gateway de autenticação e proxy
├── services/                 # Microserviços
│   ├── clientes/
│   ├── produtos/
│   ├── estoque/
│   ├── vendas/
│   ├── financeiro/
│   └── notificacoes/
├── frontend/                 # React + TypeScript
├── shared/                   # Código compartilhado
├── tests/                    # Testes pytest
├── docker-compose.dev.yml    # Desenvolvimento
├── docker-compose.prod.yml   # Produção
└── docker-compose.cloudflare.yml  # Cloudflare Tunnel
```

---

<div align="center">

**Quick Start Completo** | Junho 2026  
**Documentação**: `docs/README.md` | **Suporte**: Issues no GitHub

</div>
