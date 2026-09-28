# 🏢 Serviço de Empresas - Multi-tenancy

Microsserviço responsável pelo cadastro de empresas (tenants) do ERP Runas. Porta **8007**.

## 📋 Visão Geral

Cada empresa é um **tenant**. Os demais serviços isolam seus dados por `empresa_id`; este serviço guarda o cadastro, a configuração do catálogo público e os campos de plano/limites de cada empresa.

O serviço não autentica usuário. Ele confia nos headers que o api-gateway injeta:

| Header | Quem injeta | Para quê |
|--------|-------------|----------|
| `X-Empresa-Id` | gateway, a partir do usuário autenticado | tenant do chamador (`exigir_tenant`: sem ele → 400) |
| `X-Plataforma: 1` + `X-Plataforma-Token` | só o router `/plataforma` do gateway, depois do `require_super_admin` | rotas de administração da plataforma (`exigir_plataforma`: sem `X-Plataforma: 1` → 403) |
| `X-Servico-Interno-Token` | chamadas internas (`interno.auth_interno`) | prova de origem interna, validada pelo middleware de `interno.py` em toda rota exceto `/health` |

`X-Servico-Interno-Token` e `X-Plataforma-Token` são **fail-open** enquanto `SERVICO_INTERNO_TOKEN` / `PLATAFORMA_INTERNO_TOKEN` estiverem vazios (ou o header não vier): o serviço loga `servico_interno.ausente` / `plataforma.sem_segredo` e deixa passar. Token presente e errado → 403.

## 🎯 Funcionalidades

### Implementadas ✅

- ✅ Criação, leitura, atualização e desativação (soft delete) de empresas
- ✅ Validação de CNPJ (formato e dígitos verificadores, via `validate-docbr`)
- ✅ Slug único; gerado a partir do `nome_fantasia` quando omitido na criação
- ✅ Slug regerado automaticamente quando o `catalogo_titulo` muda sem slug explícito no PUT
- ✅ Criação de filial (`tipo=FILIAL` + `empresa_matriz_id`), limitada por `max_lojas` da matriz
- ✅ Configuração de catálogo público e de tema (cores) por empresa
- ✅ Campos de plano e limites (`plano`, `max_usuarios`, `max_produtos`, `max_lojas`)
- ✅ Reativação ao recadastrar o CNPJ de uma empresa inativa
- ✅ Isolamento por tenant: lojista só lê/altera/desativa a própria empresa
- ✅ Rotas de plataforma (criar tenant, alterar plano, listar todos) separadas das do lojista

### Não implementado 🔴

- 🔴 Publicação de eventos: `events/publisher.py` define `EventPublisher` (RabbitMQ), mas nenhum código chama `event_publisher.publish`
- 🔴 Rota de listagem de filiais: `EmpresaService.listar_filiais` existe, mas nenhum router a expõe
- 🔴 Checagem de dados dependentes antes de desativar (TODO em `services/empresa_service.py`)

## 📊 Modelo de Dados

Tabela `empresas.empresas` (schema `empresas`), modelo em `models/empresa.py`. Exemplo de resposta (`EmpresaResponse`):

```python
{
    "id": 1,                                      # inteiro, autoincrement
    "slug": "distribuidora-central",              # endereço público do catálogo
    "razao_social": "Distribuidora Central LTDA",
    "nome_fantasia": "Distribuidora Central",
    "tipo": "MATRIZ",                             # MATRIZ ou FILIAL (default MATRIZ)
    "status": "ATIVA",                            # ATIVA, INATIVA, SUSPENSA (default ATIVA)
    "cnpj": "12.345.678/0001-90",                 # único, formatado
    "inscricao_estadual": "123456789",
    "inscricao_municipal": None,
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
    "logo_url": None,
    "cor_primaria": "#3B82F6",                    # default
    "cor_secundaria": "#10B981",                  # default

    # Catálogo público
    "catalogo_ativo": True,                       # default True
    "catalogo_titulo": None,
    "catalogo_descricao": "Alimentos e bebidas com os melhores preços!",
    "catalogo_whatsapp": "(11) 99000-0001",

    # Plano e limites (string livre; defaults do model)
    "plano": "BASICO",                            # default "BASICO"
    "max_usuarios": 5,                            # default 5
    "max_produtos": None,                         # None = ilimitado
    "max_lojas": 1,                               # default 1

    # Matriz/Filial
    "empresa_matriz_id": None,                    # só para filiais

    # Controle
    "ativo": True,                                # False = soft delete
    "criado_em": "2026-06-08T23:30:00Z",
    "atualizado_em": "2026-06-08T23:30:00Z",
    "criado_por": None,
    "atualizado_por": None
}
```

## 🔌 Endpoints

Todas as rotas ficam sob o prefixo `/empresas` (`routers/empresas.py`), mais `GET /health` em `main.py`.

| Verbo | Caminho | Guarda | O que faz |
|-------|---------|--------|-----------|
| `POST` | `/empresas` | plataforma | cria empresa (201) |
| `GET` | `/empresas` | tenant | lista **só a empresa do chamador** (filtros `skip`, `limit` ≤ 1000, `busca`, `tipo`, `status`, `uf`) |
| `GET` | `/empresas/{empresa_id}` | tenant | dados completos; `empresa_id` diferente do tenant → 403 |
| `GET` | `/empresas/slug/{slug}` | tenant | dados completos pelo slug; empresa de outro tenant → 403 |
| `GET` | `/empresas/publico/{slug}` | nenhuma | dados públicos para o catálogo (`EmpresaPublicInfo`) |
| `PUT` | `/empresas/{empresa_id}` | tenant | atualiza dados cadastrais, visuais e de catálogo (`EmpresaUpdate`) |
| `DELETE` | `/empresas/{empresa_id}` | tenant | soft delete (`ativo=false`, `status=INATIVA`) |
| `PATCH` | `/empresas/{empresa_id}/plano` | plataforma | altera `plano`, `max_usuarios`, `max_produtos`, `status`, `ativo` (`EmpresaPlanoUpdate`) |
| `GET` | `/empresas/plataforma/todas` | plataforma | todas as empresas ativas, `{"items": [...], "total": n}` |
| `GET` | `/health` | nenhuma | `{"status": "healthy", "service": "empresas"}` |

"tenant" = `exigir_tenant` (header `X-Empresa-Id`); "plataforma" = `exigir_plataforma` (headers `X-Plataforma` e `X-Plataforma-Token`). `EmpresaUpdate` e `EmpresaPlanoUpdate` são disjuntos: o lojista não consegue alterar o próprio plano pelo PUT.

### Pelo gateway

O api-gateway (porta 8000) expõe apenas parte dessas rotas (`api-gateway/routers/proxy.py`):

- `GET /empresas/publico/{path}` — sem autenticação;
- `GET /empresas` e `GET|PUT|DELETE /empresas/{path}` — com `require_admin`;
- `POST /empresas`, `PATCH /empresas/{id}/plano` e `GET /empresas/plataforma/todas` só são chamadas pelo router `/plataforma` do gateway (`api-gateway/routers/plataforma.py`, protegido por `require_super_admin`). Esse router também chama `DELETE /empresas/{id}` (soft delete) na empresa recém-criada quando o provisionamento do admin do tenant falha.

### Exemplo: criar empresa (chamada da plataforma)

```http
POST /empresas
Content-Type: application/json
X-Plataforma: 1
X-Plataforma-Token: SEU_TOKEN

{
    "razao_social": "Minha Empresa LTDA",
    "nome_fantasia": "Minha Empresa",
    "cnpj": "12.345.678/0001-95",
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "numero": "1000",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP"
}
```

`slug` é opcional: omitido, é gerado a partir do `nome_fantasia` (sem acentos, kebab-case, sufixo `-2`, `-3`... em caso de conflito). O CNPJ precisa ter dígitos verificadores válidos, senão a requisição volta 422 (o `12.345.678/0001-90` do seed, por exemplo, é recusado na criação).

### Exemplo: atualizar a própria empresa

```http
PUT /empresas/1
Content-Type: application/json
X-Empresa-Id: 1

{
    "nome_fantasia": "Novo Nome",
    "catalogo_ativo": true
}
```

## 🔒 Validações

Schemas em `schemas/empresa.py`, regras de negócio em `services/empresa_service.py`.

### CNPJ
- Formato `XX.XXX.XXX/XXXX-XX` e dígitos verificadores, validados no schema de criação (422)
- No PUT, se alterado: dígitos verificados no service (400) e unicidade (409)
- Único na tabela, inclusive entre inativas; CNPJ de empresa **ativa** já cadastrado → 409
- CNPJ de empresa **inativa** → a empresa é reativada (`ativo=true`, `status=ATIVA`) e o slug e os dados cadastrais, de endereço e de contato são sobrescritos; plano, limites e configurações visuais/catálogo são mantidos

### Slug
- Apenas letras minúsculas, números e hífen; 3 a 100 caracteres
- Não pode começar ou terminar com hífen nem ter hífens consecutivos
- Único: o service checa conflito entre empresas ativas (409); a coluna também é `UNIQUE` no banco, inclusive para inativas

### CEP
- Formato `XXXXX-XXX` (validado só na criação)

### UF
- Uma das 27 UFs do Brasil (validado só na criação)

### Cores
- Hexadecimal `#RRGGBB` (validado só na criação)

### Filiais
- `tipo=FILIAL` exige `empresa_matriz_id` (400)
- A matriz deve existir e estar ativa (404) e ser do tipo `MATRIZ` (400)
- Número de filiais ativas da matriz deve ser menor que `max_lojas` da matriz (409)

## 🎨 Planos e Limites

`plano` é uma string livre (`String(50)`); o comentário do model cita `BASICO`, `PRO` e `ENTERPRISE`, mas o código não associa limites a um nome de plano. Os limites são campos independentes, com estes defaults: `max_usuarios=5`, `max_produtos=None` (ilimitado), `max_lojas=1`. Quem muda os valores é a plataforma, via `PATCH /empresas/{id}/plano` (que não inclui `max_lojas`).

Onde cada limite é aplicado:

- `max_usuarios` — no gateway, ao criar usuário (`api-gateway/routers/auth_admin.py`, `_limite_de_usuarios`)
- `max_lojas` — aqui, na criação de filial
- `max_produtos` — **não é aplicado em lugar nenhum**: o serviço de produtos não o lê; ele só é editado pela plataforma e exibido no frontend (`EmpresaPage.tsx`, `PlataformaPage.tsx`)

## 🔄 Soft Delete

Empresas desativadas (`ativo=false`):
- não aparecem em `GET /empresas` nem em `GET /empresas/plataforma/todas`
- não são encontradas por ID nem por slug (404)
- não servem o catálogo público (`GET /empresas/publico/{slug}` → 404)
- são reativadas ao recadastrar o mesmo CNPJ

O catálogo público também responde 404 quando `status` não é `ATIVA`. Com `catalogo_ativo=false` a rota pública **continua respondendo** (para a página de manutenção mostrar a marca); o bloqueio de catálogo, carrinho e checkout é feito nos serviços de produtos e vendas.

## 🚀 Como Usar

### Com o stack de desenvolvimento (recomendado)

Na raiz do repositório:

```bash
docker compose -f docker-compose.dev.yml up -d empresas
```

Sobe `db`, `rabbitmq` e `redis` como dependências e o container `erp-empresas-dev` com `--reload`, publicado em `127.0.0.1:8007`. As variáveis vêm do `.env` da raiz (`DATABASE_URL_EMPRESAS`, `SERVICO_INTERNO_TOKEN`, `PLATAFORMA_INTERNO_TOKEN`; ver `.env.example`).

### Local, fora do Docker

```bash
cd services/empresas
pip install -r requirements.txt
```

Variáveis obrigatórias (`config.py`); o serviço também lê um `.env` no próprio diretório:

```bash
DATABASE_URL=postgresql+asyncpg://erp:erp@localhost:5432/erp
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
REDIS_URL=redis://localhost:6379/0
# opcionais; vazios = fail-open
SERVICO_INTERNO_TOKEN=
PLATAFORMA_INTERNO_TOKEN=
```

O schema `empresas` precisa existir no banco (criado por `postgres/init-schemas.sql` no dev). As tabelas vêm do Alembic: o `init_db()` roda `alembic upgrade head` no startup, ou rode à mão:

```bash
alembic upgrade head
python seed.py                                          # opcional: empresas de exemplo, só se a tabela estiver vazia
uvicorn main:app --host 0.0.0.0 --port 8007 --reload
```

Documentação interativa: `http://localhost:8007/docs`.

## 🐳 Docker

O `Dockerfile` (Python 3.12-slim) roda `uvicorn main:app --host 0.0.0.0 --port 8007` sem `--reload`. Em produção a imagem é construída pelo workflow `.github/workflows/deploy.yml` e publicada no GHCR; `docker-compose.prod.yml` só faz pull (container `erp-empresas-prod`).

```bash
docker build -t erp-empresas services/empresas
```

## 📁 Estrutura do Projeto

```
services/empresas/
├── alembic/
│   ├── versions/            # 3 revisions (initial, fix_enum_types, auditoria)
│   ├── env.py
│   └── script.py.mako
├── events/
│   ├── __init__.py
│   └── publisher.py         # EventPublisher (RabbitMQ), sem uso
├── models/
│   ├── __init__.py
│   └── empresa.py
├── repositories/
│   ├── __init__.py
│   └── empresa_repository.py
├── routers/
│   ├── __init__.py
│   └── empresas.py          # rotas + exigir_tenant / exigir_plataforma
├── schemas/
│   ├── __init__.py
│   └── empresa.py
├── services/
│   ├── __init__.py
│   └── empresa_service.py   # regras de negócio
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_base.py
│   └── test_plataforma_com_prova.py
├── utils/
│   ├── __init__.py
│   └── validators.py        # validar_cnpj, formatar_cnpj, limpar_cnpj
├── .dockerignore
├── alembic.ini
├── config.py
├── database.py              # engine, get_db, init_db (alembic upgrade head)
├── Dockerfile
├── exceptions.py            # ValidationError (400), NotFoundError (404), ConflictError (409)
├── interno.py               # middleware X-Servico-Interno-Token
├── main.py
├── README.md
├── requirements.txt
└── seed.py
```

## 🧪 Testes

Os testes usam **Postgres de verdade** com o schema construído pelas migrations (sem `create_all`, sem SQLite). Por padrão o `conftest.py` aponta para o banco do stack dev (`localhost:5432`, `erp/erp`) e Redis no db 15.

```bash
# banco de pé, schema empresas criado e migrations aplicadas
docker compose -f docker-compose.dev.yml up -d db
cd services/empresas
pip install -r requirements.txt -r ../../tests/requirements.txt
alembic upgrade head
pytest tests -p no:cacheprovider
```

É o mesmo que o leg `services/empresas` do job `services` em `.github/workflows/ci.yml` faz, a partir de um banco vazio.

- `test_base.py` — o app responde `/health` e o schema das migrations serve a todos os models
- `test_plataforma_com_prova.py` — `exigir_plataforma`: 403 sem `X-Plataforma`, token certo passa, token errado ou não-ASCII → 403, fail-open sem segredo configurado

Cobertura: `pytest-cov` está em `tests/requirements.txt` (`pytest tests --cov=.`).
