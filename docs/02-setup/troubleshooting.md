# Troubleshooting - Runas

> **Soluções para problemas comuns** durante setup e desenvolvimento

---

## 🔍 Índice de Problemas

- [Docker e Containers](#docker-e-containers)
- [Banco de Dados](#banco-de-dados)
- [Backend / API](#backend--api)
- [Frontend](#frontend)
- [Autenticação](#autenticação)
- [Integrações Externas](#integrações-externas)
- [Performance](#performance)

---

## 🐳 Docker e Containers

### Problema: Containers não sobem

**Sintomas:**
```bash
docker-compose up -d
# Erro: Cannot start service X
```

**Soluções:**

1. **Verificar se as portas estão em uso**
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Matar processo se necessário
taskkill /PID <PID> /F
```

2. **Limpar containers e volumes antigos**
```bash
docker-compose down -v
docker system prune -a
docker-compose up -d
```

3. **Verificar logs do container**
```bash
docker-compose logs <nome-do-servico>
```

---

### Problema: Erro "no space left on device"

**Sintomas:**
```
Error: no space left on device
```

**Soluções:**

1. **Limpar imagens e volumes não utilizados**
```bash
docker system prune -a --volumes
```

2. **Verificar espaço em disco**
```bash
docker system df
```

---

### Problema: Container reiniciando constantemente

**Sintomas:**
```bash
docker ps
# Status: Restarting
```

**Soluções:**

1. **Verificar logs**
```bash
docker logs <container-id> --tail 100
```

2. **Verificar health check**
```bash
docker inspect <container-id> | grep -A 10 Health
```

3. **Desabilitar restart temporariamente**
```yaml
# docker-compose.yml
restart: "no"  # ao invés de "unless-stopped"
```

---

## 🗄️ Banco de Dados

### Problema: Erro de conexão com PostgreSQL

**Sintomas:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Soluções:**

1. **Verificar se o container está rodando**
```bash
docker ps | grep postgres
```

2. **Verificar variáveis de ambiente**
```bash
# .env
DATABASE_URL_CLIENTES=postgresql+asyncpg://erp:erp@db-clientes:5432/clientes
```

3. **Testar conexão manualmente**
```bash
docker exec -it db-clientes psql -U erp -d clientes
```

4. **Aguardar health check**
```bash
# O serviço pode estar iniciando
docker-compose logs db-clientes
```

---

### Problema: Migrations não aplicadas

**Sintomas:**
```
sqlalchemy.exc.ProgrammingError: relation "clientes" does not exist
```

**Soluções:**

1. **Executar migrations manualmente**
```bash
make migrate
# ou
docker-compose run --rm migrate
```

2. **Verificar se migrations existem**
```bash
docker exec -it clientes ls alembic/versions/
```

3. **Criar migration se necessário**
```bash
docker exec -it clientes alembic revision --autogenerate -m "initial"
```

---

### Problema: Dados duplicados ou inconsistentes

**Sintomas:**
```
IntegrityError: duplicate key value violates unique constraint
```

**Soluções:**

1. **Reset completo do banco**
```bash
make reset
make migrate
make seed
```

2. **Verificar constraints**
```sql
-- Conectar ao banco
docker exec -it db-clientes psql -U erp -d clientes

-- Listar constraints
\d+ clientes
```

---

## 🔧 Backend / API

### Problema: Erro 500 Internal Server Error

**Sintomas:**
```json
{
  "detail": "Internal Server Error"
}
```

**Soluções:**

1. **Verificar logs do serviço**
```bash
docker-compose logs clientes --tail 50
```

2. **Verificar variáveis de ambiente**
```bash
docker exec -it clientes env | grep DATABASE
```

3. **Testar endpoint diretamente**
```bash
curl -X GET http://localhost:8001/health
```

---

### Problema: Erro 401 Unauthorized

**Sintomas:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Soluções:**

1. **Verificar se token está sendo enviado**
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/clientes
```

2. **Verificar se token expirou**
```bash
# Token expira em 30 minutos
# Fazer novo login
```

3. **Verificar SECRET_KEY no .env**
```bash
# .env
SECRET_KEY=sua-chave-secreta-aqui
```

---

### Problema: Erro 422 Validation Error

**Sintomas:**
```json
{
  "detail": [
    {
      "loc": ["body", "cpf"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Soluções:**

1. **Verificar schema esperado**
```bash
# Acessar Swagger
http://localhost:8000/docs
```

2. **Validar JSON enviado**
```json
{
  "nome": "João Silva",
  "cpf": "12345678909",  // Obrigatório
  "telefone": "+5511999999999"  // Obrigatório
}
```

---

### Problema: RabbitMQ não conecta

**Sintomas:**
```
pika.exceptions.AMQPConnectionError
```

**Soluções:**

1. **Verificar se RabbitMQ está rodando**
```bash
docker ps | grep rabbitmq
```

2. **Verificar URL no .env**
```bash
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

3. **Acessar painel de gerenciamento**
```
http://localhost:15672
# user: guest
# pass: guest
```

---

## 💻 Frontend

### Problema: Erro ao iniciar dev server

**Sintomas:**
```
Error: Cannot find module 'vite'
```

**Soluções:**

1. **Reinstalar dependências**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

2. **Verificar versão do Node**
```bash
node --version  # Deve ser 18+
```

---

### Problema: Erro de CORS

**Sintomas:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Soluções:**

1. **Verificar configuração do backend**
```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. **Verificar URL da API no frontend**
```typescript
// .env.development
VITE_API_URL=http://localhost:8000
```

---

### Problema: Componentes não renderizam

**Sintomas:**
```
TypeError: Cannot read property 'map' of undefined
```

**Soluções:**

1. **Verificar se dados foram carregados**
```typescript
if (!data) return <Loading />;
```

2. **Verificar console do navegador**
```
F12 > Console
```

3. **Verificar React DevTools**
```
F12 > Components
```

---

## 🔐 Autenticação

### Problema: Login não funciona

**Sintomas:**
```json
{
  "detail": "Incorrect email or password"
}
```

**Soluções:**

1. **Verificar se usuário existe**
```bash
docker exec -it db-gateway psql -U erp -d gateway
SELECT * FROM usuarios WHERE email = 'admin@runas.local';
```

2. **Criar usuário admin**
```bash
make seed
```

3. **Verificar senha**
```bash
# Senha padrão: admin123
```

---

### Problema: Token expira muito rápido

**Sintomas:**
```
Token expira em menos de 30 minutos
```

**Soluções:**

1. **Verificar configuração no .env**
```bash
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

2. **Implementar refresh automático**
```typescript
// Interceptor axios
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      await refreshToken();
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

## 🔌 Integrações Externas

### Problema: Evolution API não conecta

**Sintomas:**
```
ConnectionError: Failed to connect to Evolution API
```

**Soluções:**

1. **Verificar se Evolution está rodando**
```bash
docker ps | grep evolution
```

2. **Verificar variáveis de ambiente**
```bash
EVOLUTION_URL=http://evolution-api:8080
EVOLUTION_API_KEY=sua-chave-aqui
EVOLUTION_INSTANCE=runas
```

3. **Testar conexão**
```bash
curl http://localhost:8080/instance/connect/runas
```

---

### Problema: Mercado Pago webhook não funciona

**Sintomas:**
```
Webhook não recebe notificações de pagamento
```

**Soluções:**

1. **Verificar URL do webhook**
```powershell
# Deve ser acessível publicamente via Cloudflare Tunnel
# Exemplo: https://www.runaserp.com.br/api/vendas/webhook/mercadopago
```

2. **Verificar assinatura HMAC**
```python
# Validar x-signature header
```

3. **Verificar logs**
```bash
docker-compose logs vendas | grep webhook
```

---

## ⚡ Performance

### Problema: API muito lenta

**Sintomas:**
```
Requisições demorando > 5 segundos
```

**Soluções:**

1. **Verificar queries N+1**
```python
# Use joinedload para eager loading
query = select(Cliente).options(joinedload(Cliente.enderecos))
```

2. **Adicionar índices**
```python
# Migration
op.create_index('ix_clientes_cpf', 'clientes', ['cpf'])
```

3. **Verificar logs de queries**
```python
# database.py
engine = create_async_engine(url, echo=True)  # Mostra queries
```

4. **Usar cache**
```python
# Redis para dados frequentes
```

---

### Problema: Frontend lento

**Sintomas:**
```
Página demora para carregar
```

**Soluções:**

1. **Usar React.memo**
```typescript
export const ClienteCard = React.memo(({ cliente }) => {
  // ...
});
```

2. **Lazy loading de rotas**
```typescript
const Dashboard = lazy(() => import('./pages/Dashboard'));
```

3. **Otimizar imagens**
```typescript
<img loading="lazy" src={url} />
```

4. **Usar React Query cache**
```typescript
useQuery({
  queryKey: ['clientes'],
  staleTime: 5 * 60 * 1000,  // 5 minutos
});
```

---

## 🆘 Ainda com Problemas?

### Passos Gerais de Diagnóstico

1. **Verificar logs**
```bash
docker-compose logs --tail 100
```

2. **Verificar status dos serviços**
```bash
docker-compose ps
```

3. **Verificar variáveis de ambiente**
```bash
cat .env
```

4. **Reset completo**
```bash
make reset
make up
make seed
```

### Obter Ajuda

- **GitHub Issues**: [github.com/denebcorp/runas/issues](https://github.com/denebcorp/runas/issues)
- **Discord**: [Link do servidor]
- **Email**: support@denebcorp.com

### Reportar Bug

Ao reportar um bug, inclua:
- Descrição do problema
- Passos para reproduzir
- Logs relevantes
- Versão do sistema
- Sistema operacional

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
