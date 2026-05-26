# ✅ Checklist de Validação - MVP ERP Runas

**Data**: 2026-05-14  
**Versão**: 1.0.0-MVP  
**Objetivo**: Validar que o MVP está 100% funcional

---

## 📋 Como Usar Este Checklist

1. Execute cada item na ordem
2. Marque com `[x]` quando passar
3. Se falhar, consulte a seção de Troubleshooting
4. Todos os itens devem estar marcados para considerar o MVP validado

---

## 🚀 Fase 1: Preparação do Ambiente

### Pré-requisitos

- [ ] Docker instalado (versão 20.10+)
- [ ] Docker Compose instalado (versão 2.0+)
- [ ] Git Bash ou terminal Unix-like (Windows)
- [ ] Portas disponíveis: 8000-8006, 5432, 6379, 5672, 15672, 5050, 8080

### Verificação de Arquivos

- [ ] Arquivo `.env` existe na raiz do projeto
- [ ] Arquivo `docker-compose.yml` existe
- [ ] Arquivo `test-mvp.sh` existe e tem permissão de execução
- [ ] Pasta `api-gateway/` existe
- [ ] Pasta `services/clientes/` existe
- [ ] Pasta `services/produtos/` existe

---

## 🐳 Fase 2: Inicialização dos Serviços

### Subir Containers

```bash
docker-compose up -d
```

- [ ] Comando executou sem erros
- [ ] Aguardou ~30-60 segundos para inicialização

### Verificar Status dos Containers

```bash
docker-compose ps
```

Todos devem estar com status `Up` ou `Up (healthy)`:

- [ ] `erp-api-gateway` - Up (healthy)
- [ ] `erp-clientes` - Up (healthy)
- [ ] `erp-produtos` - Up (healthy)
- [ ] `erp-db-gateway` - Up (healthy)
- [ ] `erp-db-clientes` - Up (healthy)
- [ ] `erp-db-produtos` - Up (healthy)
- [ ] `erp-redis` - Up (healthy)
- [ ] `erp-rabbitmq` - Up (healthy)
- [ ] `erp-pgadmin` - Up
- [ ] `erp-evolution-api` - Up (healthy)

### Verificar Logs (Sem Erros Críticos)

```bash
docker-compose logs api-gateway | grep -i error
docker-compose logs clientes | grep -i error
docker-compose logs produtos | grep -i error
```

- [ ] API Gateway sem erros críticos
- [ ] Serviço Clientes sem erros críticos
- [ ] Serviço Produtos sem erros críticos

---

## 🧪 Fase 3: Testes Automatizados

### Executar Script de Testes

```bash
bash test-mvp.sh
```

- [ ] Script executou sem erros
- [ ] Todos os health checks passaram (✓ OK)
- [ ] Login funcionou e retornou token
- [ ] Criação de cliente funcionou
- [ ] Listagem de clientes funcionou
- [ ] Criação de categoria funcionou
- [ ] Criação de produto funcionou
- [ ] Listagem de produtos funcionou
- [ ] Logout funcionou

---

## 🔍 Fase 4: Testes Manuais Básicos

### 4.1. Health Checks

```bash
curl http://localhost:8000/health
```
- [ ] Retornou `{"status":"healthy","service":"api-gateway"}`

```bash
curl http://localhost:8001/health
```
- [ ] Retornou `{"status":"healthy","service":"clientes"}`

```bash
curl http://localhost:8002/health
```
- [ ] Retornou `{"status":"healthy","service":"produtos"}`

### 4.2. Autenticação

#### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123"
```

- [ ] Retornou status 200
- [ ] Retornou `access_token`
- [ ] Retornou `refresh_token`
- [ ] Retornou `token_type: bearer`

**Copie o `access_token` para os próximos testes!**

#### Verificar Usuário Logado

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou dados do usuário admin
- [ ] Email: admin@runas.com
- [ ] Role: ADMIN

### 4.3. CRUD de Clientes

#### Listar Clientes (Vazio Inicialmente)

```bash
curl -X GET http://localhost:8000/api/clientes \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou status 200
- [ ] Retornou lista (pode estar vazia)

#### Criar Cliente

```bash
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

- [ ] Retornou status 201 ou 200
- [ ] Retornou objeto com `id`
- [ ] Nome: "João Silva"
- [ ] CPF: "12345678901"

**Copie o `id` do cliente criado!**

#### Buscar Cliente por ID

```bash
curl -X GET http://localhost:8000/api/clientes/1 \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou status 200
- [ ] Retornou dados do cliente criado

#### Atualizar Cliente

```bash
curl -X PUT http://localhost:8000/api/clientes/1 \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva Santos",
    "email": "joao.santos@example.com"
  }'
```

- [ ] Retornou status 200
- [ ] Nome atualizado para "João Silva Santos"

#### Adicionar Endereço

```bash
curl -X POST http://localhost:8000/api/clientes/1/enderecos \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "logradouro": "Rua das Flores",
    "numero": "123",
    "bairro": "Centro",
    "cidade": "São Paulo",
    "estado": "SP",
    "cep": "01234567",
    "tipo": "ENTREGA",
    "principal": true
  }'
```

- [ ] Retornou status 201 ou 200
- [ ] Endereço criado com sucesso

### 4.4. CRUD de Produtos

#### Criar Categoria

```bash
curl -X POST http://localhost:8000/api/categorias \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Eletrônicos",
    "descricao": "Produtos eletrônicos",
    "ativo": true
  }'
```

- [ ] Retornou status 201 ou 200
- [ ] Retornou objeto com `id`

**Copie o `id` da categoria!**

#### Listar Categorias

```bash
curl -X GET http://localhost:8000/api/categorias \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou status 200
- [ ] Lista contém a categoria criada

#### Criar Produto

```bash
curl -X POST http://localhost:8000/api/produtos \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Notebook Dell",
    "descricao": "Notebook Dell Inspiron 15",
    "sku": "DELL-NB-001",
    "categoria_id": 1,
    "preco_venda": 3500.00,
    "preco_custo": 2800.00,
    "ativo": true
  }'
```

- [ ] Retornou status 201 ou 200
- [ ] Retornou objeto com `id`
- [ ] Margem de lucro calculada automaticamente

**Copie o `id` do produto!**

#### Listar Produtos

```bash
curl -X GET http://localhost:8000/api/produtos \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou status 200
- [ ] Lista contém o produto criado

#### Buscar Produto por ID

```bash
curl -X GET http://localhost:8000/api/produtos/1 \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou status 200
- [ ] Retornou dados do produto criado

#### Criar Variante de Produto

```bash
curl -X POST http://localhost:8000/api/produtos/1/variantes \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Notebook Dell - 16GB RAM",
    "sku": "DELL-NB-001-16GB",
    "atributos": {"ram": "16GB"},
    "preco_adicional": 500.00,
    "ativo": true
  }'
```

- [ ] Retornou status 201 ou 200
- [ ] Variante criada com sucesso

#### Criar Fornecedor

```bash
curl -X POST http://localhost:8000/api/fornecedores \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Tech Distribuidora",
    "cnpj": "12345678000190",
    "email": "contato@tech.com",
    "telefone": "+5511999998888",
    "ativo": true
  }'
```

- [ ] Retornou status 201 ou 200
- [ ] Fornecedor criado com sucesso

### 4.5. Logout

```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou status 200
- [ ] Mensagem de logout bem-sucedido

#### Verificar Blacklist (Deve Falhar)

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer SEU_TOKEN"
```

- [ ] Retornou status 401 (Unauthorized)
- [ ] Token foi blacklisted com sucesso

---

## 🖥️ Fase 5: Interfaces Web

### pgAdmin

- [ ] Acessível em http://localhost:5050
- [ ] Login funciona (admin@runas.local / admin123)
- [ ] Servidores pré-configurados aparecem
- [ ] Consegue conectar no banco `gateway`
- [ ] Consegue conectar no banco `clientes`
- [ ] Consegue conectar no banco `produtos`
- [ ] Tabelas foram criadas automaticamente

### RabbitMQ Management

- [ ] Acessível em http://localhost:15672
- [ ] Login funciona (guest / guest)
- [ ] Dashboard carrega corretamente
- [ ] Exchanges estão criadas
- [ ] Queues estão criadas (se houver)

### Swagger UI (API Docs)

- [ ] Acessível em http://localhost:8000/docs
- [ ] Documentação carrega corretamente
- [ ] Todos os endpoints estão listados
- [ ] Consegue testar endpoints via interface

---

## 🔐 Fase 6: Segurança e Validações

### Autenticação

- [ ] Endpoint protegido sem token retorna 401
- [ ] Token inválido retorna 401
- [ ] Token expirado retorna 401
- [ ] Token blacklisted retorna 401

### Validações de Dados

#### Cliente

- [ ] CPF inválido é rejeitado
- [ ] Email inválido é rejeitado
- [ ] Telefone em formato errado é rejeitado
- [ ] CPF duplicado é rejeitado

#### Produto

- [ ] SKU duplicado é rejeitado
- [ ] Preço negativo é rejeitado
- [ ] Categoria inexistente é rejeitada

---

## 📊 Fase 7: Performance e Estabilidade

### Health Checks Contínuos

```bash
# Executar 10 vezes
for i in {1..10}; do curl http://localhost:8000/health; done
```

- [ ] Todas as requisições retornaram 200
- [ ] Tempo de resposta < 100ms

### Carga Básica

```bash
# Criar 10 clientes
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/clientes \
    -H "Authorization: Bearer SEU_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"nome\":\"Cliente $i\",\"cpf_cnpj\":\"1234567890$i\",\"email\":\"cliente$i@example.com\",\"telefone\":\"+551199999999$i\",\"tipo\":\"PESSOA_FISICA\"}"
done
```

- [ ] Todos os clientes foram criados
- [ ] Sem erros de timeout
- [ ] Sem erros de conexão

### Logs Limpos

```bash
docker-compose logs --tail=50
```

- [ ] Sem erros críticos nos logs
- [ ] Sem stack traces não tratados
- [ ] Logs estruturados (JSON)

---

## 🎯 Fase 8: Validação Final

### Checklist Geral

- [ ] Todos os containers estão rodando
- [ ] Todos os health checks passam
- [ ] Script de testes automatizados passa 100%
- [ ] Login e autenticação funcionam
- [ ] CRUD de clientes funciona completamente
- [ ] CRUD de produtos funciona completamente
- [ ] Interfaces web acessíveis
- [ ] Validações de dados funcionam
- [ ] Logs estão limpos
- [ ] Performance aceitável

### Documentação

- [ ] README.md está atualizado
- [ ] QUICK-START.md está claro
- [ ] MVP-TESTE-MANUAL.md está completo
- [ ] Todos os arquivos de documentação existem

---

## ✅ Resultado Final

### Se TODOS os itens estão marcados:

🎉 **PARABÉNS! O MVP está 100% funcional e validado!**

Você pode:
- Começar a usar o sistema
- Demonstrar para stakeholders
- Partir para implementação dos próximos serviços

### Se ALGUM item falhou:

⚠️ **Consulte o Troubleshooting**

1. Veja a seção de problemas em **[MVP-TESTE-MANUAL.md](./MVP-TESTE-MANUAL.md)**
2. Verifique os logs: `docker-compose logs -f`
3. Tente recriar o container: `docker-compose up -d --force-recreate <servico>`
4. Em último caso, limpe tudo: `docker-compose down -v` e suba novamente

---

## 📊 Estatísticas de Validação

Preencha após completar o checklist:

- **Total de itens**: 100+
- **Itens validados**: ___
- **Itens falhados**: ___
- **Taxa de sucesso**: ___%
- **Tempo total de validação**: ___ minutos
- **Data da validação**: ___________
- **Validado por**: ___________

---

## 📝 Observações

Use este espaço para anotar problemas encontrados ou observações:

```
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________
```

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0-MVP  
**Status**: ✅ Pronto para uso
