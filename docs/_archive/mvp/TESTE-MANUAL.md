# 🧪 Guia de Teste Manual do MVP - ERP Runas

**Data**: 2026-05-14  
**Status**: ✅ MVP Pronto para Testes

---

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Portas disponíveis: 8000-8006, 5432, 6379, 5672, 15672, 5050, 8080
- Git Bash ou terminal com curl (Windows/Linux/Mac)

---

## 🚀 1. Subir o Ambiente

### Opção A: Usando Makefile (Recomendado)

```bash
# Subir todos os serviços
make up

# Ver logs em tempo real
make logs

# Ver status dos containers
make ps
```

### Opção B: Usando Docker Compose diretamente

```bash
# Subir em background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver status
docker-compose ps
```

### ⏱️ Tempo de Inicialização

- **Primeira vez**: ~3-5 minutos (download de imagens + build)
- **Subsequentes**: ~30-60 segundos

### ✅ Verificar se subiu corretamente

Todos os containers devem estar com status `healthy` ou `running`:

```bash
docker-compose ps
```

Esperado:
```
NAME                  STATUS
erp-api-gateway       Up (healthy)
erp-clientes          Up (healthy)
erp-produtos          Up (healthy)
erp-db-gateway        Up (healthy)
erp-db-clientes       Up (healthy)
erp-db-produtos       Up (healthy)
erp-redis             Up (healthy)
erp-rabbitmq          Up (healthy)
erp-pgadmin           Up
erp-evolution-api     Up (healthy)
```

---

## 🧪 2. Executar Testes Automatizados

```bash
# Dar permissão de execução (Linux/Mac)
chmod +x test-mvp.sh

# Executar testes
./test-mvp.sh
```

**No Windows (Git Bash)**:
```bash
bash test-mvp.sh
```

### Resultado Esperado

```
🧪 Iniciando testes do MVP - ERP Runas
========================================

📡 1. Testando Health Checks
----------------------------
Testing API Gateway Health... ✓ OK (HTTP 200)
Testing Clientes Service Health... ✓ OK (HTTP 200)
Testing Produtos Service Health... ✓ OK (HTTP 200)

🔐 2. Testando Autenticação
---------------------------
Login com admin... ✓ OK
   Token obtido: eyJhbGciOiJIUzI1NiIs...

👥 3. Testando Serviço de Clientes via Gateway
----------------------------------------------
GET /api/clientes... ✓ OK
POST /api/clientes (criar cliente)... ✓ OK
   Cliente criado com ID: 1

📦 4. Testando Serviço de Produtos via Gateway
----------------------------------------------
POST /api/categorias (criar categoria)... ✓ OK
   Categoria criada com ID: 1
POST /api/produtos (criar produto)... ✓ OK
   Produto criado com ID: 1
GET /api/produtos... ✓ OK

🔓 5. Testando Logout
--------------------
POST /auth/logout... ✓ OK

========================================
✅ Testes do MVP concluídos!
```

---

## 🔍 3. Testes Manuais com cURL

### 3.1. Health Checks

```bash
# API Gateway
curl http://localhost:8000/health

# Serviço Clientes
curl http://localhost:8001/health

# Serviço Produtos
curl http://localhost:8002/health
```

### 3.2. Autenticação

#### Login (obter token)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123"
```

**Resposta esperada**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**⚠️ Importante**: Copie o `access_token` para usar nos próximos comandos!

#### Definir variável de ambiente (facilita testes)

**Linux/Mac/Git Bash**:
```bash
export TOKEN="seu_access_token_aqui"
```

**Windows PowerShell**:
```powershell
$TOKEN = "seu_access_token_aqui"
```

### 3.3. CRUD de Clientes

#### Listar clientes

```bash
curl -X GET http://localhost:8000/api/clientes \
  -H "Authorization: Bearer $TOKEN"
```

#### Criar cliente

```bash
curl -X POST http://localhost:8000/api/clientes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Maria Santos",
    "cpf_cnpj": "12345678901",
    "email": "maria@example.com",
    "telefone": "+5511988887777",
    "tipo": "PESSOA_FISICA",
    "limite_credito": 5000.00
  }'
```

#### Buscar cliente por ID

```bash
curl -X GET http://localhost:8000/api/clientes/1 \
  -H "Authorization: Bearer $TOKEN"
```

#### Atualizar cliente

```bash
curl -X PUT http://localhost:8000/api/clientes/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Maria Santos Silva",
    "email": "maria.silva@example.com",
    "telefone": "+5511988887777"
  }'
```

#### Adicionar endereço ao cliente

```bash
curl -X POST http://localhost:8000/api/clientes/1/enderecos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "logradouro": "Rua das Flores",
    "numero": "123",
    "complemento": "Apto 45",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01234567",
    "tipo": "ENTREGA",
    "principal": true
  }'
```

### 3.4. CRUD de Produtos

#### Criar categoria

```bash
curl -X POST http://localhost:8000/api/categorias \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Eletrônicos",
    "descricao": "Produtos eletrônicos e tecnologia",
    "ativo": true
  }'
```

#### Listar categorias

```bash
curl -X GET http://localhost:8000/api/categorias \
  -H "Authorization: Bearer $TOKEN"
```

#### Criar produto

```bash
curl -X POST http://localhost:8000/api/produtos \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Smartphone Samsung Galaxy",
    "descricao": "Smartphone Samsung Galaxy S23",
    "sku": "SAMSUNG-S23-001",
    "categoria_id": 1,
    "preco_venda": 2999.90,
    "preco_custo": 2200.00,
    "margem_lucro": 36.36,
    "ativo": true,
    "destaque": true
  }'
```

#### Listar produtos

```bash
curl -X GET http://localhost:8000/api/produtos \
  -H "Authorization: Bearer $TOKEN"
```

#### Buscar produto por ID

```bash
curl -X GET http://localhost:8000/api/produtos/1 \
  -H "Authorization: Bearer $TOKEN"
```

#### Criar variante de produto

```bash
curl -X POST http://localhost:8000/api/produtos/1/variantes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Galaxy S23 - 128GB Preto",
    "sku": "SAMSUNG-S23-128-BLK",
    "atributos": {
      "cor": "Preto",
      "armazenamento": "128GB"
    },
    "preco_adicional": 0.00,
    "ativo": true
  }'
```

#### Criar fornecedor

```bash
curl -X POST http://localhost:8000/api/fornecedores \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Tech Distribuidora LTDA",
    "cnpj": "12345678000190",
    "email": "contato@techdist.com",
    "telefone": "+5511999998888",
    "ativo": true
  }'
```

### 3.5. Logout

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🖥️ 4. Acessar Interfaces Web

### pgAdmin (Gerenciamento de Banco de Dados)

- **URL**: http://localhost:5050
- **Email**: admin@runas.local
- **Senha**: admin123

**Servidores pré-configurados**:
- gateway (porta 5432)
- clientes (porta 5432)
- produtos (porta 5432)
- estoque (porta 5432)
- vendas (porta 5432)
- financeiro (porta 5432)
- notificacoes (porta 5432)
- evolution (porta 5432)

### RabbitMQ Management

- **URL**: http://localhost:15672
- **Usuário**: guest
- **Senha**: guest

### Evolution API (WhatsApp)

- **URL**: http://localhost:8080
- **API Key**: change-me-in-production (configurar no .env)

---

## 📊 5. Endpoints Disponíveis

### API Gateway (http://localhost:8000)

#### Autenticação
- `POST /auth/login` - Login
- `POST /auth/refresh` - Renovar token
- `POST /auth/logout` - Logout
- `GET /auth/me` - Dados do usuário logado

#### Proxy para Clientes
- `GET /api/clientes` - Listar clientes
- `POST /api/clientes` - Criar cliente
- `GET /api/clientes/{id}` - Buscar cliente
- `PUT /api/clientes/{id}` - Atualizar cliente
- `DELETE /api/clientes/{id}` - Deletar cliente
- `POST /api/clientes/{id}/enderecos` - Adicionar endereço
- `GET /api/clientes/{id}/enderecos` - Listar endereços

#### Proxy para Produtos
- `GET /api/categorias` - Listar categorias
- `POST /api/categorias` - Criar categoria
- `GET /api/produtos` - Listar produtos
- `POST /api/produtos` - Criar produto
- `GET /api/produtos/{id}` - Buscar produto
- `PUT /api/produtos/{id}` - Atualizar produto
- `POST /api/produtos/{id}/variantes` - Criar variante
- `GET /api/fornecedores` - Listar fornecedores
- `POST /api/fornecedores` - Criar fornecedor

### Serviço Clientes (http://localhost:8001)

Mesmos endpoints de clientes, mas acesso direto (sem autenticação via gateway).

### Serviço Produtos (http://localhost:8002)

Mesmos endpoints de produtos, mas acesso direto (sem autenticação via gateway).

---

## 🐛 6. Troubleshooting

### Container não sobe

```bash
# Ver logs do container específico
docker-compose logs api-gateway
docker-compose logs clientes
docker-compose logs produtos

# Recriar container
docker-compose up -d --force-recreate api-gateway
```

### Erro de conexão com banco de dados

```bash
# Verificar se o banco está healthy
docker-compose ps

# Reiniciar banco específico
docker-compose restart db-gateway
docker-compose restart db-clientes
docker-compose restart db-produtos
```

### Erro 401 Unauthorized

- Verifique se o token está correto
- Token pode ter expirado (30 minutos de validade)
- Faça login novamente para obter novo token

### Erro 503 Service Unavailable

- Serviço downstream pode não estar rodando
- Verifique: `docker-compose ps`
- Aguarde alguns segundos para o serviço inicializar

### Limpar tudo e recomeçar

```bash
# Parar e remover tudo (CUIDADO: apaga dados!)
make clean

# Ou
docker-compose down -v

# Subir novamente
make up
```

---

## 📝 7. Credenciais Padrão

### Usuário Admin (API Gateway)
- **Email**: admin@runas.com
- **Senha**: Admin@123
- **Role**: ADMIN

### PostgreSQL
- **Usuário**: erp
- **Senha**: erp

### Redis
- Sem autenticação (localhost apenas)

### RabbitMQ
- **Usuário**: guest
- **Senha**: guest

---

## ✅ 8. Checklist de Validação do MVP

- [ ] Todos os containers subiram com sucesso
- [ ] Health checks retornam 200 OK
- [ ] Login com admin funciona
- [ ] Token JWT é gerado corretamente
- [ ] Criar cliente via gateway funciona
- [ ] Listar clientes via gateway funciona
- [ ] Criar categoria funciona
- [ ] Criar produto funciona
- [ ] Listar produtos funciona
- [ ] Logout funciona
- [ ] pgAdmin conecta nos bancos
- [ ] RabbitMQ Management acessível

---

## 🎯 9. Próximos Passos

Após validar o MVP, você pode:

1. **Implementar Serviço de Estoque** (próximo na fila)
2. **Adicionar testes unitários** (pytest)
3. **Configurar CI/CD** (GitHub Actions)
4. **Implementar Serviço de Vendas**
5. **Integrar Evolution API** (WhatsApp)
6. **Adicionar monitoramento** (Prometheus + Grafana)

---

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs: `docker-compose logs -f`
2. Verifique o status: `docker-compose ps`
3. Consulte a documentação em `/docs`
4. Abra uma issue no repositório

---

**Última atualização**: 2026-05-14  
**Versão do MVP**: 1.0.0
