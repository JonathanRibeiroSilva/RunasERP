# 🧪 Guia de Testes Automatizados - ERP Runas

> **Última atualização**: 23/06/2026
> 
> Guia completo para implementar testes automatizados com pytest em todos os serviços do ERP.
> **Status**: 🔴 Testes não implementados | **Cobertura Alvo**: 80%+

---

## 📋 Visão Geral

### Status Atual - Junho 2026

| Serviço | Backend | Endpoints | Testes Unit | Testes Integr | Cobertura |
|---------|---------|-----------|-------------|---------------|-----------|
| **API Gateway** | ✅ 100% | 15 | 🔴 0% | 🔴 0% | 🔴 0% |
| **Clientes** | ✅ 100% | 12 | 🔴 0% | 🔴 0% | 🔴 0% |
| **Produtos** | ✅ 100% | 25 | 🔴 0% | 🔴 0% | 🔴 0% |
| **Estoque** | ✅ 100% | 19 | 🔴 0% | 🔴 0% | 🔴 0% |
| **Vendas** | ✅ 100% | 14 | 🔴 0% | 🔴 0% | 🔴 0% |
| **Loja Online** | ✅ 100% | 26 | 🔴 0% | 🔴 0% | 🔴 0% |

**Total**: 111 endpoints funcionais | 0% testados

### Objetivos MVP
- ✅ 80%+ cobertura unitária
- ✅ 70%+ cobertura integração  
- ✅ 100% endpoints críticos
- ✅ CI/CD com testes automatizados

### Escopo Prioritário

**Serviços MVP** (para apresentação):
1. ✅ **Clientes** - 12 endpoints
2. ✅ **Produtos** - 25 endpoints  
3. ✅ **Vendas** - 14 endpoints
4. ✅ **Loja Online** - 26 endpoints

**Total MVP**: 77 endpoints (70% do sistema)

---

## 🎯 Pirâmide de Testes

```
                /\
               /  \
              / E2E \ ← 10%
             /______\
            /        \
           / INTEGR.  \ ← 30%
          /____________\
         /              \
        /   UNITÁRIOS    \ ← 60%
       /__________________\
```

### Tipos

1. **Unitários (60%)** - Testam isoladamente
   - Services (lógica de negócio)
   - Repositories (queries)
   - Validators (regras)
   - Utils (auxiliares)

2. **Integração (30%)** - Testam APIs
   - Routers (endpoints)
   - Auth e RBAC
   - Middlewares
   - Database

3. **E2E (10%)** - Testam fluxos
   - Jornadas completas
   - Integração serviços
   - Gateway + serviços

---

## 🛠️ Stack

### Bibliotecas

```bash
pip install pytest==7.4.3 pytest-asyncio==0.21.1 pytest-cov==4.1.0 pytest-mock==3.12.0 httpx==0.25.2 faker==20.1.0 factory-boy==3.3.0 freezegun==1.4.0
```

### Estrutura

```
services/clientes/
├── app/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   └── routers/
├── tests/
│   ├── conftest.py
│   ├── factories.py
│   ├── unit/
│   │   ├── test_services.py
│   │   └── test_repositories.py
│   └── integration/
│       └── test_routers.py
└── pytest.ini
```

---

## ⚙️ Configuração

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
markers =
    unit: Testes unitários
    integration: Testes de integração
    e2e: Testes end-to-end
```

### .coveragerc

```ini
[run]
source = app
omit = */tests/*, */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

---

## 🧪 Exemplos

### 1. Teste Unitário - Service

```python
# tests/unit/test_cliente_service.py
import pytest
from app.services.cliente_service import ClienteService
from app.schemas.cliente import ClienteCreate

@pytest.mark.asyncio
async def test_criar_cliente_sucesso(db_session):
    service = ClienteService(db_session)
    dados = ClienteCreate(
        nome='João Silva',
        cpf='12345678909'
    )
    
    cliente = await service.criar(1, dados)
    
    assert cliente.nome == 'João Silva'
    assert cliente.cpf == '12345678909'

@pytest.mark.asyncio
async def test_criar_cliente_cpf_duplicado(db_session):
    service = ClienteService(db_session)
    await service.criar(1, ClienteCreate(nome='João', cpf='123'))
    
    with pytest.raises(ConflictError):
        await service.criar(1, ClienteCreate(nome='Maria', cpf='123'))
```

### 2. Teste Integração - Router

```python
# tests/integration/test_cliente_router.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_criar_cliente_endpoint(client, auth_headers):
    payload = {'nome': 'João', 'cpf': '12345678909'}
    
    response = await client.post(
        '/clientes',
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    assert response.json()['nome'] == 'João'

@pytest.mark.asyncio
async def test_listar_clientes(client, auth_headers):
    response = await client.get('/clientes', headers=auth_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### 3. Factories

```python
# tests/factories.py
import factory
from app.models.cliente import Cliente

class ClienteFactory(factory.Factory):
    class Meta:
        model = Cliente
    
    id = factory.Faker('uuid4')
    empresa_id = 1
    nome = factory.Faker('name')
    cpf = factory.Sequence(lambda n: f'{n:011d}')
    ativo = True

# Uso
cliente = ClienteFactory.create()
clientes = ClienteFactory.create_batch(10)
```

### 4. Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def db_session():
    engine = create_async_engine('postgresql+asyncpg://test:test@localhost/test')
    
    async with AsyncSession(engine) as session:
        yield session
    
    await engine.dispose()

@pytest.fixture
async def client(db_session):
    async with AsyncClient(app=app, base_url='http://test') as c:
        yield c

@pytest.fixture
def auth_headers():
    return {
        'Authorization': 'Bearer token',
        'X-Empresa-Id': '1'
    }
```

---

## 📊 Executar

```bash
# Todos
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Apenas unitários
pytest -m unit

# Apenas integração
pytest -m integration

# Verbose
pytest -v

# Parar no erro
pytest -x

# Teste específico
pytest tests/unit/test_cliente_service.py::test_criar_cliente_sucesso
```

---

## 🎯 Plano MVP (4 semanas)

### Semana 1: Clientes
- [ ] 15 testes unit (services)
- [ ] 10 testes unit (repositories)
- [ ] 12 testes integr (routers)
- [ ] Cobertura: 80%+

### Semana 2: Produtos
- [ ] 25 testes unit
- [ ] 25 testes integr
- [ ] Cobertura: 80%+

### Semana 3: Vendas
- [ ] 20 testes unit
- [ ] 14 testes integr
- [ ] 5 testes E2E
- [ ] Cobertura: 80%+

### Semana 4: Loja Online
- [ ] 30 testes unit
- [ ] 26 testes integr
- [ ] 10 testes E2E (checkout)
- [ ] Cobertura: 80%+

**Total**: ~180 testes

---

## 🔍 Casos de Teste Críticos

### Clientes
- [ ] Criar cliente com CPF válido
- [ ] Rejeitar CPF duplicado na mesma empresa
- [ ] Validar CPF inválido
- [ ] Bloquear cliente
- [ ] Gerenciar crédito
- [ ] Multi-tenancy (empresa_id)

### Produtos
- [ ] Criar produto com variantes
- [ ] SKU único por empresa
- [ ] Calcular preço (custo + markup)
- [ ] Categorias hierárquicas
- [ ] Soft delete
- [ ] Multi-tenancy

### Vendas
- [ ] Criar venda com itens
- [ ] Validar estoque disponível
- [ ] Aplicar desconto
- [ ] Múltiplos pagamentos
- [ ] Workflow status (6 estados)
- [ ] Reservar/liberar estoque
- [ ] Validar crédito cliente (FIADO)

### Loja Online
- [ ] Adicionar ao carrinho
- [ ] Checkout completo (3 steps)
- [ ] Validar CEP
- [ ] Calcular frete
- [ ] Criar pedido
- [ ] Rastreamento
- [ ] Cliente convidado

---

## 📚 Cobertura por Componente

### API Gateway
- [ ] Login (email/senha)
- [ ] Refresh token
- [ ] Logout (blacklist)
- [ ] RBAC (roles)
- [ ] Rate limiting
- [ ] Proxy para serviços

### Validadores
- [ ] CPF (dígitos verificadores)
- [ ] CNPJ
- [ ] Email
- [ ] Telefone
- [ ] CEP

### Repositories
- [ ] Criar
- [ ] Buscar por ID
- [ ] Listar com paginação
- [ ] Atualizar
- [ ] Soft delete
- [ ] Filtros (empresa_id, ativo)

### Services
- [ ] Regras de negócio
- [ ] Exceções customizadas
- [ ] Transações ACID
- [ ] Integrações HTTP

---

## 🚀 CI/CD

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install deps
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 📝 Boas Práticas

### Nomear Testes

```python
# ✅ BOM
def test_criar_cliente_com_cpf_valido_retorna_201():
    pass

def test_criar_cliente_com_cpf_duplicado_retorna_409():
    pass

# ❌ RUIM
def test_cliente():
    pass
```

### Arrange-Act-Assert

```python
def test_algo():
    # Arrange - Preparar dados
    dados = {...}
    
    # Act - Executar ação
    resultado = funcao(dados)
    
    # Assert - Verificar resultado
    assert resultado == esperado
```

### Um assert por teste

```python
# ✅ BOM
def test_nome_obrigatorio():
    with pytest.raises(ValidationError):
        criar_cliente(nome=None)

def test_cpf_obrigatorio():
    with pytest.raises(ValidationError):
        criar_cliente(cpf=None)

# ❌ RUIM (múltiplos asserts)
def test_validacoes():
    with pytest.raises(ValidationError):
        criar_cliente(nome=None)
    with pytest.raises(ValidationError):
        criar_cliente(cpf=None)
```

---

## 📚 Referências

- **Pytest**: https://docs.pytest.org
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Factory Boy**: https://factoryboy.readthedocs.io
- **Faker**: https://faker.readthedocs.io

---

## ✨ Próximos Passos

1. 🔴 **Criar estrutura** - `tests/` em cada serviço
2. 🔴 **Instalar deps** - pytest, httpx, faker, etc
3. 🔴 **Configurar** - pytest.ini, conftest.py
4. 🔴 **Implementar testes** - seguir plano MVP
5. 🔴 **CI/CD** - GitHub Actions
6. 🔴 **Métricas** - Codecov/SonarQube

---

**Versão**: 1.0.0  
**Última atualização**: 23/06/2026  
**Status**: 📋 Documento completo | 🔴 Testes pendentes de implementação
