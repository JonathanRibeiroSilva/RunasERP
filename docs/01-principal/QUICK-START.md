# ⚡ Quick Start - Runas 

**Tempo estimado**: 5 minutos  
**Pré-requisitos**: Docker e Docker Compose instalados

---

## 🚀 Escolha seu Método de Inicialização

### 📍 Método 1: Localhost (Desenvolvimento Local)

**Use quando**: Testar localmente sem precisar de acesso externo

```bash
# 1. Subir todos os serviços
docker-compose up -d

# 2. Aguardar ~30 segundos e verificar status
docker-compose ps

# 3. Executar testes automatizados
bash tests/test-mvp.sh
```

**✅ Acesso**:
- Frontend: http://localhost:80
- API Gateway: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### 🌐 Método 2: Ngrok (Acesso Externo via Internet)

**Use quando**: Precisa de webhooks, OAuth, testes mobile ou demonstrações remotas

#### Pré-requisitos adicionais:
1. Conta ngrok (gratuita): https://ngrok.com/
2. Token de autenticação configurado no `.env.ngrok`

```bash
# 1. Configurar token do ngrok (primeira vez apenas)
# Edite .env.ngrok e adicione seu token:
# NGROK_AUTHTOKEN=seu-token-aqui

# 2. Subir com nginx + ngrok
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d

# 3. Aguardar ~30 segundos
sleep 30

# 4. Obter URL pública do ngrok
docker-compose logs ngrok | grep "url="
```

**✅ Acesso**:
- URL Pública: https://abc123-xyz456.ngrok-free.dev (copie dos logs)
- Dashboard ngrok: http://localhost:4040
- API via ngrok: https://abc123-xyz456.ngrok-free.dev/api

**⚠️ Importante**: Após obter a URL do ngrok, atualize `FRONTEND_URL` no `.env` e reinicie o API Gateway:
```bash
# Edite .env e mude:
FRONTEND_URL=https://abc123-xyz456.ngrok-free.dev

# Reinicie o gateway
docker-compose restart api-gateway
```

---

**Pronto!** Escolha o método adequado e siga os passos. ✅

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

### Método Localhost

#### Container não sobe

```bash
# Ver o erro
docker-compose logs <nome-do-servico>

# Recriar o container
docker-compose up -d --force-recreate <nome-do-servico>
```

#### Porta já em uso

```bash
# Descobrir qual processo está usando a porta
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000

# Matar o processo ou mudar a porta no docker-compose.yml
```

#### Banco de dados não conecta

```bash
# Verificar se o banco está healthy
docker-compose ps

# Reiniciar o banco
docker-compose restart db

# Ver logs do banco
docker-compose logs db
```

### Método Ngrok

#### ❌ "Bind for 0.0.0.0:80 failed: port is already allocated"

```bash
# Você subiu primeiro com docker-compose up -d
# O frontend já está usando a porta 80

# Solução: Parar tudo e subir com o método correto
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

#### ❌ "nginx: host not found in upstream"

```bash
# O nginx não encontra o container do API Gateway
# Verifique se o nome do container está correto

# Ver containers rodando
docker-compose ps

# Deve ter: erp-api-gateway (sem -dev)
```

#### ❌ "Token inválido" ao subir ngrok

```bash
# Verificar seu token
docker-compose logs ngrok

# Se vir erro, regere o token em: https://dashboard.ngrok.com/get-started/your-authtoken
# Atualize .env.ngrok e rode:
docker-compose restart ngrok
```

### Ambos os Métodos

### Ambos os Métodos

#### Token expirado (401 Unauthorized)

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

## 🌐 Configuração Avançada do Ngrok

### Por que usar ngrok?

O ngrok permite expor seu servidor local para a internet, essencial para:
- ✅ **Webhooks**: Receber notificações do Mercado Pago e WhatsApp
- ✅ **OAuth**: Callbacks de autenticação externa (Google, Microsoft)
- ✅ **Testes Mobile**: Acessar a API de dispositivos móveis
- ✅ **Demonstrações**: Mostrar o sistema para clientes remotos

---

### 📋 Checklist Completo de Setup

- [ ] 1. Criar conta ngrok (https://ngrok.com/)
- [ ] 2. Copiar token de autenticação (https://dashboard.ngrok.com/get-started/your-authtoken)
- [ ] 3. Atualizar `.env.ngrok` com seu token
- [ ] 4. Subir com `docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d`
- [ ] 5. Obter URL pública: `docker-compose logs ngrok | grep "url="`
- [ ] 6. Atualizar `FRONTEND_URL` no `.env` com a URL do ngrok
- [ ] 7. Reiniciar API Gateway: `docker-compose restart api-gateway`
- [ ] 8. Se usar OAuth, registrar redirect URIs nos provedores

---

### 🔐 Configuração de OAuth (Opcional)

Se você usa Google, Microsoft ou outro provedor OAuth:

#### Google Cloud Console
1. Acesse https://console.cloud.google.com/
2. Vá para "Credenciais" → "OAuth 2.0 Client IDs"
3. Edite seu cliente
4. Em "URIs de redirecionamento autorizados", adicione:
   ```
   https://sua-url-ngrok.ngrok-free.dev/auth/google/callback
   ```
5. Salve

#### Microsoft Azure
1. Acesse https://portal.azure.com/
2. Vá para "Azure Active Directory" → "App registrations"
3. Edite seu app
4. Em "Authentication" → "Redirect URIs", adicione:
   ```
   https://sua-url-ngrok.ngrok-free.dev/auth/microsoft/callback
   ```
5. Salve

#### Atualizar `.env`
```env
# OAuth Credentials
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-secret
MICROSOFT_CLIENT_ID=seu-client-id
MICROSOFT_CLIENT_SECRET=seu-secret

# Frontend URL (URL do ngrok)
FRONTEND_URL=https://sua-url-ngrok.ngrok-free.dev

# CORS Origins
CORS_ORIGINS=https://sua-url-ngrok.ngrok-free.dev,http://localhost:3000
```

---

### ✅ Verificação Rápida

Testar se tudo está funcionando:

```bash
# 1. Testar autenticação via ngrok
curl -X POST https://sua-url-ngrok.ngrok-free.dev/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123"

# Deve retornar um token

# 2. Testar endpoint público
curl https://sua-url-ngrok.ngrok-free.dev/api/categorias

# 3. Acessar dashboard do ngrok
# URL: http://localhost:4040
# Verá todas as requisições em tempo real
```

---

### 🔧 Troubleshooting Ngrok

#### ❌ OAuth com erro "redirect_uri_mismatch"
```
A URL do ngrok no seu provedor (Google/Microsoft) é diferente da que você está usando.

Solução:
1. Verificar URL exata: docker-compose logs ngrok | grep "url="
2. Registrar EXATAMENTE essa URL no provedor OAuth
3. Usar EXATAMENTE essa URL no .env (FRONTEND_URL)
```

#### ❌ Cookies não funcionam
```
Certifique-se que:
- FRONTEND_URL no .env está com https://
- Cookie secure flag está configurado (já está por padrão)
- Está acessando via URL do ngrok, não localhost
```

#### ❌ CORS errors
```
Adicionar URL do ngrok em CORS_ORIGINS no .env:
CORS_ORIGINS=https://sua-url-ngrok.ngrok-free.dev,http://localhost:3000

Reiniciar API Gateway:
docker-compose restart api-gateway
```

#### ❌ URL do ngrok muda toda vez
```
Plano gratuito do ngrok gera URL aleatória a cada restart.

Soluções:
1. Usar ngrok pago (URL fixa)
2. Ou atualizar .env e provedores OAuth toda vez que reiniciar
```

---

### 📚 Documentação Adicional

Para mais detalhes sobre OAuth com ngrok:
- **[docs/09-troubleshooting/oauth-issues.md](./docs/09-troubleshooting/oauth-issues.md)** - Guia completo de troubleshooting OAuth

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0-MVP
