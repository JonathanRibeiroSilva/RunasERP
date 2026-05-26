# ⚡ Quick Start - ERP Runas MVP

**Tempo estimado**: 5 minutos  
**Pré-requisitos**: Docker e Docker Compose instalados

---

## 🚀 Iniciar o MVP (3 comandos)

```bash
# 1. Subir todos os serviços
docker-compose up -d

# 2. Aguardar ~30 segundos e verificar status
docker-compose ps

# 3. Executar testes automatizados
bash tests/test-mvp.sh
```

**Pronto!** Se todos os testes passarem, o MVP está funcionando. ✅

---

## 🧪 Teste Manual Rápido (1 minuto)

### 1. Login e obter token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123"
```

**Copie o `access_token` da resposta!**

### 2. Criar um cliente

```bash
# Substitua SEU_TOKEN pelo token copiado acima
curl -X POST http://localhost:8000/api/clientes \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "cpf_cnpj": "12345678901",
    "email": "joao@example.com",
    "telefone": "+5511999999999",
    "tipo": "PESSOA_FISICA"
  }'
```

### 3. Listar clientes

```bash
curl -X GET http://localhost:8000/api/clientes \
  -H "Authorization: Bearer SEU_TOKEN"
```

**Sucesso!** Você acabou de testar o fluxo completo: autenticação → criação → listagem. 🎉

---

## 🖥️ Acessar Interfaces Web

| Interface | URL | Credenciais |
|-----------|-----|-------------|
| **API Docs (Swagger)** | http://localhost:8000/docs | - |
| **pgAdmin** | http://localhost:5050 | admin@runas.local / admin123 |
| **RabbitMQ** | http://localhost:15672 | guest / guest |
| **Evolution API** | http://localhost:8080 | - |

---

## 📊 Verificar Status dos Serviços

```bash
# Ver status de todos os containers
docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f api-gateway
docker-compose logs -f clientes
docker-compose logs -f produtos
```

---

## 🛑 Parar e Limpar

```bash
# Parar todos os serviços (mantém dados)
docker-compose down

# Parar e remover TUDO (incluindo dados)
docker-compose down -v

# Reiniciar um serviço específico
docker-compose restart api-gateway
```

---

## 🔧 Comandos Úteis

```bash
# Subir apenas infraestrutura (bancos, redis, rabbitmq)
docker-compose up -d db-gateway db-clientes db-produtos redis rabbitmq

# Subir apenas o MVP (gateway + clientes + produtos)
docker-compose up -d api-gateway clientes produtos

# Executar comando dentro de um container
docker-compose exec api-gateway bash
docker-compose exec clientes python seed.py

# Ver uso de recursos
docker stats
```

---

## 🐛 Problemas Comuns

### Container não sobe

```bash
# Ver o erro
docker-compose logs <nome-do-servico>

# Recriar o container
docker-compose up -d --force-recreate <nome-do-servico>
```

### Porta já em uso

```bash
# Descobrir qual processo está usando a porta
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# Matar o processo ou mudar a porta no docker-compose.yml
```

### Banco de dados não conecta

```bash
# Verificar se o banco está healthy
docker-compose ps

# Reiniciar o banco
docker-compose restart db-gateway

# Ver logs do banco
docker-compose logs db-gateway
```

### Token expirado (401 Unauthorized)

```bash
# Tokens expiram em 30 minutos
# Faça login novamente para obter um novo token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123"
```

---

## 📚 Documentação Completa

Para mais detalhes, consulte:

- **[docs/mvp/TESTE-MANUAL.md](./docs/mvp/TESTE-MANUAL.md)** - Guia completo de testes com exemplos de cURL
- **[docs/mvp/STATUS-FINAL.md](./docs/mvp/STATUS-FINAL.md)** - Status detalhado de todos os componentes
- **[docs/mvp/RESUMO-EXECUTIVO.md](./docs/mvp/RESUMO-EXECUTIVO.md)** - Visão geral do MVP
- **[README.md](./README.md)** - Documentação principal do projeto

---

## 🎯 Endpoints Principais

### Autenticação
- `POST /auth/login` - Login
- `POST /auth/refresh` - Renovar token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Dados do usuário

### Clientes (via /api/clientes)
- `GET /api/clientes` - Listar
- `POST /api/clientes` - Criar
- `GET /api/clientes/{id}` - Buscar
- `PUT /api/clientes/{id}` - Atualizar
- `DELETE /api/clientes/{id}` - Deletar

### Produtos (via /api/produtos)
- `GET /api/produtos` - Listar
- `POST /api/produtos` - Criar
- `GET /api/produtos/{id}` - Buscar
- `PUT /api/produtos/{id}` - Atualizar

### Categorias (via /api/categorias)
- `GET /api/categorias` - Listar
- `POST /api/categorias` - Criar

**Total**: 52 endpoints disponíveis

---

## 🔐 Credenciais Padrão

```
Admin API:
  Email: admin@runas.com
  Senha: Admin@123

pgAdmin:
  Email: admin@runas.local
  Senha: admin123

RabbitMQ:
  User: guest
  Pass: guest

PostgreSQL:
  User: erp
  Pass: erp
```

---

## ✅ Checklist Rápido

- [ ] `docker-compose up -d` executado
- [ ] Todos os containers com status "Up (healthy)"
- [ ] `bash tests/test-mvp.sh` passou todos os testes
- [ ] Login funciona e retorna token
- [ ] Criar cliente funciona
- [ ] Listar clientes funciona
- [ ] Swagger acessível em http://localhost:8000/docs

**Se todos os itens estão marcados, o MVP está 100% funcional!** 🎉

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0-MVP
