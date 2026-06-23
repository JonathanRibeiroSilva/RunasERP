# 🏢 Serviço de Empresas - Multi-tenancy

Microsserviço responsável pelo gerenciamento de empresas (multi-tenancy) no sistema ERP Runas.

## 📋 Visão Geral

Este serviço implementa a base do sistema multi-tenant, permitindo que múltiplas empresas usem o mesmo sistema de forma isolada. Cada empresa representa um **tenant** e todos os dados de clientes, produtos, vendas, etc. são isolados por `empresa_id`.

## 🎯 Funcionalidades

### Implementadas ✅

- ✅ CRUD completo de empresas
- ✅ Validação de CNPJ
- ✅ Sistema de slug único para URLs
- ✅ Suporte a Matriz e Filiais
- ✅ Configuração de catálogo público por empresa
- ✅ Configuração de tema (cores) por empresa
- ✅ Sistema de planos (BASICO, PRO, ENTERPRISE)
- ✅ Limites por plano (usuários, produtos, lojas)
- ✅ Soft delete (empresas inativas ficam invisíveis)
- ✅ Reativação automática ao recadastrar CNPJ
- ✅ Busca por razão social, nome fantasia, CNPJ
- ✅ Filtros por tipo, status, UF

### Planejadas 🔴

- 🔴 Integração com outros serviços via eventos
- 🔴 Middleware de identificação de tenant
- 🔴 Isolamento de dados por tenant nos outros serviços
- 🔴 Dashboard de métricas por empresa
- 🔴 Gestão de assinaturas/cobrança (SaaS)

## 📊 Modelo de Dados

### Empresa

```python
{
    "id": 1,
    "slug": "distribuidora-central",              # Usado na URL do catálogo
    "razao_social": "Distribuidora Central LTDA",
    "nome_fantasia": "Distribuidora Central",
    "tipo": "MATRIZ",                             # MATRIZ ou FILIAL
    "status": "ATIVA",                            # ATIVA, INATIVA, SUSPENSA
    "cnpj": "12.345.678/0001-90",
    "inscricao_estadual": "123456789",
    "inscricao_municipal": null,
    "regime_tributario": "SIMPLES_NACIONAL",      # SIMPLES_NACIONAL, LUCRO_PRESUMIDO, LUCRO_REAL, MEI
    
    # Endereço
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "numero": "1000",
    "complemento": "Sala 101",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP",
    
    # Contato
    "telefone": "(11) 3000-0001",
    "celular": "(11) 99000-0001",
    "email": "contato@empresa.com.br",
    "site": "https://empresa.com.br",
    
    # Configurações visuais
    "logo_url": "https://cdn.empresa.com/logo.png",
    "cor_primaria": "#3B82F6",
    "cor_secundaria": "#10B981",
    
    # Catálogo público
    "catalogo_ativo": true,
    "catalogo_titulo": "Catálogo Online",
    "catalogo_descricao": "Alimentos e bebidas com os melhores preços!",
    "catalogo_whatsapp": "(11) 99000-0001",
    
    # Planos e limites
    "plano": "PRO",                               # BASICO, PRO, ENTERPRISE
    "max_usuarios": 20,
    "max_produtos": null,                          # null = ilimitado
    "max_lojas": 5,
    
    # Matriz/Filial
    "empresa_matriz_id": null,                     # null se for matriz
    
    # Controle
    "ativo": true,
    "criado_em": "2026-06-08T23:30:00Z",
    "atualizado_em": "2026-06-08T23:30:00Z",
    "criado_por": 1,
    "atualizado_por": 1
}
```

## 🔌 Endpoints

### Criar Empresa
```http
POST /empresas
Content-Type: application/json

{
    "slug": "minha-empresa",
    "razao_social": "Minha Empresa LTDA",
    "nome_fantasia": "Minha Empresa",
    "cnpj": "12.345.678/0001-90",
    "regime_tributario": "SIMPLES_NACIONAL",
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "numero": "1000",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP"
}
```

### Listar Empresas
```http
GET /empresas?skip=0&limit=100&busca=central&tipo=MATRIZ&status=ATIVA&uf=SP
```

### Buscar por ID
```http
GET /empresas/1
```

### Buscar por Slug
```http
GET /empresas/slug/minha-empresa
```

### Buscar Informações Públicas (Catálogo)
```http
GET /empresas/publico/minha-empresa
```

### Atualizar Empresa
```http
PUT /empresas/1
Content-Type: application/json

{
    "nome_fantasia": "Novo Nome",
    "catalogo_ativo": true
}
```

### Desativar Empresa
```http
DELETE /empresas/1
```

### Listar Filiais de uma Matriz
```http
GET /empresas/1/filiais
```

## 🔒 Validações

### CNPJ
- Formato: `XX.XXX.XXX/XXXX-XX`
- Validação de dígitos verificadores
- Unicidade (mesmo entre empresas inativas)
- Reativação automática se CNPJ já existe inativo

### Slug
- Apenas letras minúsculas, números e hífen
- Não pode começar ou terminar com hífen
- Não pode ter hífens consecutivos
- Deve ser único

### CEP
- Formato: `XXXXX-XXX`
- Validação de formato (8 dígitos)

### UF
- Deve ser uma UF válida do Brasil

### Cores
- Formato hexadecimal: `#RRGGBB`

### Filiais
- Deve informar `empresa_matriz_id`
- Matriz deve existir e ser do tipo MATRIZ
- Respeita limite de filiais do plano da matriz

## 🎨 Sistema de Planos

### BASICO
- 5 usuários
- 500 produtos
- 1 loja

### PRO
- 20 usuários
- Produtos ilimitados
- 5 lojas

### ENTERPRISE
- Usuários ilimitados
- Produtos ilimitados
- Lojas ilimitadas

## 🔄 Soft Delete

Empresas desativadas:
- Não aparecem em listagens
- Não podem ser buscadas por slug
- Catálogo público fica indisponível
- Podem ser reativadas ao recadastrar o CNPJ

## 🚀 Como Usar

### 1. Instalar Dependências
```bash
cd services/empresas
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
```bash
# .env
DATABASE_URL=postgresql+asyncpg://erp:erp@localhost:5432/erp
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
REDIS_URL=redis://localhost:6379/0
```

### 3. Criar Tabelas
```bash
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
```

### 4. Popular Dados de Teste
```bash
python seed.py
```

### 5. Iniciar Serviço
```bash
uvicorn main:app --host 0.0.0.0 --port 8007 --reload
```

### 6. Acessar Documentação
```
http://localhost:8007/docs
```

## 🐳 Docker

### Build
```bash
docker build -t erp-empresas .
```

### Run
```bash
docker run -p 8007:8007 \
  -e DATABASE_URL=postgresql+asyncpg://erp:erp@db:5432/erp \
  -e RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/ \
  -e REDIS_URL=redis://redis:6379/0 \
  erp-empresas
```

## 📁 Estrutura do Projeto

```
services/empresas/
├── alembic/                 # Migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── events/                  # Publicação de eventos
│   ├── __init__.py
│   └── publisher.py
├── models/                  # Modelos SQLAlchemy
│   ├── __init__.py
│   └── empresa.py
├── repositories/            # Camada de dados
│   ├── __init__.py
│   └── empresa_repository.py
├── routers/                 # Endpoints FastAPI
│   ├── __init__.py
│   └── empresas.py
├── schemas/                 # Pydantic schemas
│   ├── __init__.py
│   └── empresa.py
├── services/                # Lógica de negócio
│   ├── __init__.py
│   └── empresa_service.py
├── tests/                   # Testes
│   ├── __init__.py
│   └── conftest.py
├── utils/                   # Utilitários
│   ├── __init__.py
│   └── validators.py
├── .dockerignore
├── alembic.ini
├── config.py               # Configurações
├── database.py             # Setup do banco
├── Dockerfile
├── main.py                 # App FastAPI
├── README.md
├── requirements.txt
└── seed.py                 # Dados de teste
```

## 🧪 Testes

```bash
# Instalar pytest
pip install pytest pytest-asyncio

# Executar testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html
```

## 🔮 Roadmap

### Fase 1 - Multi-tenancy Base ✅
- [x] CRUD de empresas
- [x] Validações
- [x] Soft delete
- [x] Sistema de planos

### Fase 2 - Integração com Sistema 🔄
- [ ] Adicionar `empresa_id` em todos os modelos
- [ ] Middleware de identificação de tenant
- [ ] Isolamento de dados por tenant
- [ ] Migração de dados existentes

### Fase 3 - Funcionalidades Avançadas 🔴
- [ ] Dashboard de métricas
- [ ] Gestão de assinaturas
- [ ] Cobrança automatizada
- [ ] API de webhooks

## 📞 Suporte

Para dúvidas ou problemas, consulte a documentação principal do projeto.

---

**Versão**: 1.0.0  
**Última atualização**: 08/06/2026  
**Status**: ✅ Implementado e funcional
