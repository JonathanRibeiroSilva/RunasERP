# Troubleshooting - Runas

> **Soluções para problemas comuns** durante setup e desenvolvimento local.
> Para produção (VPS, Coolify, Cloudflare) use `runbook-producao.md`.

Convenções deste documento (conferidas em `docker-compose.dev.yml` e `erp.ps1`):

- Compose de dev: `docker-compose.dev.yml`. Não existe `docker-compose.yml` nem `Makefile` na raiz; use `docker compose` (v2) com `-f docker-compose.dev.yml` ou o `.\erp.ps1` (`up`, `down`, `restart`, `logs`, `ps`, `health`, `rebuild`, `prune`, `shell`).
- Nomes de serviço no compose: `db`, `redis`, `rabbitmq`, `api-gateway`, `clientes`, `produtos`, `estoque`, `vendas`, `financeiro`, `notificacoes`, `empresas`, `frontend` e `evolution-api` (este só sobe com `--profile whatsapp`).
- Nomes de container: `erp-<servico>-dev` (ex.: `erp-db-dev`, `erp-vendas-dev`, `erp-api-gateway-dev`).
- Portas no host: gateway `8000`, clientes `8001`, produtos `8002`, estoque `8003`, vendas `8004`, financeiro `8005`, notificacoes `8006`, empresas `8007` (estas sete publicadas só em `127.0.0.1`), frontend `3000`, Postgres `5432`, Redis `6379`, RabbitMQ `5672`/`15672`.
- Há **um único** Postgres (`erp-db-dev`, usuário/banco padrão `erp`) com um schema por serviço; não existem containers `db-clientes` ou `db-gateway`.

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
docker compose -f docker-compose.dev.yml up -d
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

⚠️ `down -v` apaga o volume `db_data`: você perde o banco de dev inteiro.
```bash
docker compose -f docker-compose.dev.yml down -v
docker system prune -a
docker compose -f docker-compose.dev.yml up -d
```

3. **Verificar logs do container**
```bash
docker compose -f docker-compose.dev.yml logs <nome-do-servico>
# ou, pelo script:
.\erp.ps1 logs <nome-do-servico>
```

---

### Problema: Erro "no space left on device"

**Sintomas:**
```
Error: no space left on device
```

**Soluções:**

1. **Limpar imagens e volumes não utilizados** (⚠️ `--volumes` também remove volumes órfãos com dados)
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
docker logs erp-<servico>-dev --tail 100
```

2. **Verificar health check**
```bash
docker inspect erp-<servico>-dev --format '{{json .State.Health}}'
```

3. **Verificar se as migrations estão falhando**

Cada serviço roda `alembic upgrade head` no startup (`init_db()` em `services/*/database.py`) e, se falhar, derruba o processo de propósito: o container reinicia em loop (os serviços têm `restart: unless-stopped`). O erro da migration aparece nos logs do passo 1.

4. **Desabilitar restart temporariamente**
```yaml
# docker-compose.dev.yml, no serviço em questão
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
docker ps --filter name=erp-db-dev
```

2. **Verificar variáveis de ambiente**
```bash
# .env (modelo: .env.example)
DATABASE_URL_CLIENTES=postgresql+asyncpg://erp:erp@db:5432/erp
```
Cada serviço tem a sua `DATABASE_URL_<SERVICO>`, todas apontando para o mesmo host `db` e banco `erp`.

3. **Testar conexão manualmente**
```bash
docker exec -it erp-db-dev psql -U erp -d erp
```

4. **Aguardar health check**
```bash
# O serviço pode estar iniciando
docker compose -f docker-compose.dev.yml logs db
```

---

### Problema: Migrations não aplicadas

**Sintomas:**
```
sqlalchemy.exc.ProgrammingError: relation "clientes.clientes" does not exist
```

**Soluções:**

1. **Reiniciar o serviço**

As migrations rodam sozinhas no boot de cada serviço (`alembic upgrade head`). Não existe `make migrate` nem serviço `migrate` no compose.
```bash
docker compose -f docker-compose.dev.yml restart clientes
docker compose -f docker-compose.dev.yml logs clientes --tail 100
```

2. **Verificar se as migrations existem**
```bash
docker exec -it erp-clientes-dev ls alembic/versions/
```
Se o diretório estiver sem revisions, o serviço se recusa a subir (`alembic/versions/ sem revisions`, ver `services/clientes/database.py`); confira o `.dockerignore` do serviço.

3. **Criar migration se necessário**
```bash
docker exec -it erp-clientes-dev alembic revision --autogenerate -m "descricao"
```

---

### Problema: Dados duplicados ou inconsistentes

**Sintomas:**
```
IntegrityError: duplicate key value violates unique constraint
```

**Soluções:**

1. **Reset completo do banco de dev** (⚠️ apaga todos os dados)
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
# depois os seeds: ver docs/06-operacao/SEED_DATA_COMPLETO.md
```

2. **Verificar constraints**
```sql
-- Conectar ao banco
docker exec -it erp-db-dev psql -U erp -d erp

-- Listar constraints (cada serviço tem seu schema)
\d+ clientes.clientes
```

---

## 🔧 Backend / API

### Problema: Erro 500 Internal Server Error

**Sintomas:**
```json
{
  "detail": "Erro interno do servidor"
}
```

**Soluções:**

1. **Verificar logs do serviço**
```bash
docker compose -f docker-compose.dev.yml logs clientes --tail 50
```

2. **Verificar variáveis de ambiente**
```bash
docker exec -it erp-clientes-dev env | grep DATABASE
```

3. **Testar endpoint diretamente**
```bash
curl http://localhost:8001/health
# {"status":"healthy","service":"clientes"}
```
`/health` é a única rota dos serviços que não exige o token interno (`services/clientes/interno.py`).

---

### Problema: Erro 401 Unauthorized

**Sintomas:**
```json
{
  "detail": "Token não fornecido"
}
```
Outras mensagens possíveis do gateway: `Credenciais inválidas` (token inválido ou expirado), `Usuário inativo` (`api-gateway/auth/oauth2.py`, `api-gateway/routers/auth.py`).

**Soluções:**

1. **Verificar se token está sendo enviado** (sempre via gateway, porta 8000)
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/clientes
```

2. **Verificar se token expirou**
```bash
# Access token expira em 30 minutos por padrão (ACCESS_TOKEN_EXPIRE_MINUTES)
# Fazer novo login
```

3. **Verificar SECRET_KEY no .env**

O gateway e os serviços precisam ler o mesmo valor.
```bash
# .env
SECRET_KEY=sua-chave-secreta-aqui
```

---

### Problema: Erro 422 Validation Error

**Sintomas:** (Pydantic v2, ver `services/clientes/requirements.txt`)
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "cpf"],
      "msg": "Field required"
    }
  ]
}
```

**Soluções:**

1. **Verificar schema esperado**

O Swagger dos serviços fica em `http://localhost:8001/docs` (clientes), `8002` (produtos) etc., publicados só em `127.0.0.1`. No gateway o `/docs` só existe com `DOCS_ENABLED=true` (padrão `false`, `api-gateway/config.py`).

2. **Validar JSON enviado** (campos de `services/clientes/schemas/cliente.py`)
```json
{
  "nome": "João Silva",
  "cpf": "30180957660",
  "telefone": "11987654321"
}
```
`cpf` (11 a 14 caracteres) e `telefone` são obrigatórios, e o CPF precisa ser válido (checagem dos dígitos verificadores). Os demais campos obrigatórios variam: confira o Swagger.

---

### Problema: RabbitMQ não conecta

**Sintomas:**
```
aio_pika.exceptions.AMQPConnectionError
```
Os serviços usam `aio-pika`, não `pika`.

**Soluções:**

1. **Verificar se RabbitMQ está rodando**
```bash
docker ps --filter name=erp-rabbitmq-dev
```

2. **Verificar URL no .env**
```bash
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

3. **Acessar painel de gerenciamento**
```
http://localhost:15672
# user/pass padrão: guest / guest (RABBITMQ_DEFAULT_USER / RABBITMQ_DEFAULT_PASS)
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
Em Docker o frontend roda no container `erp-frontend-dev` (porta 3000, `frontend/Dockerfile.dev`).

2. **Verificar versão do Node**
```bash
node --version  # as imagens do frontend usam node:22
```

---

### Problema: Erro de CORS

**Sintomas:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Soluções:**

1. **Verificar configuração do gateway** (`api-gateway/main.py`, bloco `# CORS`)

O gateway libera somente `settings.FRONTEND_URL` como origem. Confira que `FRONTEND_URL` no `.env` bate com a URL em que você abre o app (dev: `http://localhost:3000`).

2. **Verificar URL da API no frontend**
```bash
# frontend/.env (modelo: frontend/.env.example)
VITE_API_URL=/api
VITE_USE_PROXY=true
```
Com o proxy ligado o Vite encaminha `/api` para `http://api-gateway:8000` (ou `VITE_API_GATEWAY_TARGET`), então o navegador fala só com a origem `:3000` e não há CORS.

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
  "detail": "Email ou senha incorretos"
}
```

**Soluções:**

1. **Verificar se usuário existe**
```bash
docker exec -it erp-db-dev psql -U erp -d erp
SELECT id, email, role, ativo, empresa_id FROM gateway.usuarios WHERE email = 'admin@runas.com';
```

2. **Criar usuário admin**

Não há comando de seed: o gateway cria o admin (e `operador@runas.com`) sozinho no startup, se não existirem (`api-gateway/main.py`, `api-gateway/seed.py`). Reinicie o gateway e leia os logs:
```bash
docker compose -f docker-compose.dev.yml restart api-gateway
docker compose -f docker-compose.dev.yml logs api-gateway --tail 50
```

3. **Verificar senha**
```bash
# Padrão de dev: ADMIN_EMAIL=admin@runas.com / ADMIN_PASSWORD=Admin@123
# Se você definiu outros valores no .env, valem os do .env.
# O seed NÃO troca a senha de um admin que já existe.
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

2. **Refresh automático**

O interceptor do axios (`frontend/src/services/api/axios.ts`) reage a um 401 tentando renovar a sessão; se o refresh também falhar, o usuário precisa logar de novo. A CONFIRMAR: `VITE_TOKEN_REFRESH_THRESHOLD` aparece em `frontend/src/config/env.ts` mas nenhum código lê `tokenRefreshThreshold`.

---

## 🔌 Integrações Externas

### Problema: Evolution API não conecta

**Sintomas:**
```
ConnectionError: Failed to connect to Evolution API
```

**Soluções:**

1. **Verificar se Evolution está rodando**

No compose de dev ela está sob o profile `whatsapp` e **não sobe** no `up` padrão.
```bash
docker compose -f docker-compose.dev.yml --profile whatsapp up -d evolution-api
docker ps --filter name=erp-evolution-api-dev
```

2. **Verificar variáveis de ambiente**

Nomes em `.env.example` (para os serviços) e `docker-compose.dev.yml` (para o container da Evolution, que usa `EVOLUTION_API_KEY` e `EVOLUTION_SERVER_URL`):
```bash
EVOLUTION_URL=http://evolution-api:8080
EVOLUTION_API_KEY=sua-chave-aqui
EVOLUTION_INSTANCE=runas
```
No serviço de vendas os nomes são `EVOLUTION_API_URL`, `EVOLUTION_API_KEY` e `EVOLUTION_INSTANCE` (`services/vendas/config.py`).

3. **Testar conexão**

A CONFIRMAR: o caminho de teste da API da Evolution (o doc antigo citava `/instance/connect/runas`) não está no repositório; consulte a documentação da Evolution.

---

### Problema: Mercado Pago webhook não funciona

**Sintomas:**
```
Webhook não recebe notificações de pagamento
```

**Soluções:**

1. **Verificar URL do webhook**

A URL é montada por preference como `{API_BASE_URL}/loja/{empresa_slug}/webhook/mercadopago` (`services/vendas/services/mercadopago_service.py`). Em produção, `API_BASE_URL=https://app.runaserp.com.br/api` (`.env.production.example`). A rota precisa ser acessível publicamente (Cloudflare Tunnel). Rota de teste: `GET .../loja/{empresa_slug}/webhook/mercadopago/test`. Detalhes em `CONFIGURACAO_MERCADO_PAGO.md`.

2. **Verificar assinatura HMAC**

Se o lojista gravou o segredo do webhook, a rota valida o cabeçalho `x-signature` e responde **401** (`Assinatura do webhook inválida`) quando não confere (`services/vendas/routers/webhook.py`, `services/vendas/services/webhook_assinatura.py`). Sem segredo gravado, ou sem o cabeçalho, a notificação passa com warning nos logs.

3. **Verificar logs**
```bash
docker compose -f docker-compose.dev.yml logs vendas | grep webhook
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

2. **Adicionar índices** (via nova revision do Alembic do serviço)
```python
# alembic/versions/<nova_revision>.py
op.create_index('ix_clientes_nome', 'clientes', ['nome'], schema='clientes')
```
Em `clientes`, o CPF já tem índice (`services/clientes/models/cliente.py`).

3. **Verificar logs de queries**
```python
# database.py do serviço: hoje está echo=False
engine = create_async_engine(url, echo=True)  # Mostra queries (só em dev)
```

4. **Usar cache**
```python
# Redis (container erp-redis-dev, porta 6379) para dados frequentes
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

4. **Usar React Query cache** (`@tanstack/react-query`; o app já usa `staleTime` de 5 min em `frontend/src/main.tsx`)
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
docker compose -f docker-compose.dev.yml logs --tail 100
```

2. **Verificar status dos serviços**
```bash
docker compose -f docker-compose.dev.yml ps
# ou: .\erp.ps1 ps   /   .\erp.ps1 health
```

3. **Verificar variáveis de ambiente** (evite colar a saída em canais públicos: contém segredos)
```bash
cat .env
```

4. **Reset completo** (⚠️ apaga o banco de dev)
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d
# seeds: docs/06-operacao/SEED_DATA_COMPLETO.md
```

### Obter Ajuda

A CONFIRMAR: canais de suporte (issues, chat, e-mail). Os links do documento anterior não puderam ser verificados no repositório e foram removidos.

### Reportar Bug

Ao reportar um bug, inclua:
- Descrição do problema
- Passos para reproduzir
- Logs relevantes
- Versão do sistema
- Sistema operacional
