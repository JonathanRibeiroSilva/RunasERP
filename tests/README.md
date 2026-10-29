# Testes — Runas ERP

Este é o único README de `tests/`. Os outros cinco `.md` que existiam aqui
(`COVERAGE_ANALYSIS`, `IMPLEMENTATION_STATUS`, `READY_TO_RUN`, `RUN_TESTS`,
`TESTE-ESTOQUE`) foram apagados: descreviam uma suíte que não era a que roda.

---

## O que existe hoje

**62 arquivos `test_*.py` versionados, 256 funções `test_*`** (mais 3 scripts
manuais soltos em `tests/`, contados nos 62 mas fora das 256).

| Onde | Arquivos | Funções | Roda no CI? |
|---|---:|---:|---|
| `tests/unit/` | 17 | 85 | **sim** — passo "Unit tests" do job `checks` |
| `tests/integration/` | 9 | 33 | não |
| `tests/e2e/` | 1 | 1 | não |
| `services/*/tests/` + `api-gateway/tests/` | 32 | 137 | **sim** — job `services` (`scripts/ci-services.sh`) |

Quebra por serviço (os diretórios que o `scripts/ci-services.sh` percorre):

| Serviço | Arquivos | Funções |
|---|---:|---:|
| `api-gateway` | 5 | 21 |
| `services/vendas` | 10 | 40 |
| `services/produtos` | 7 | 45 |
| `services/estoque` | 5 | 17 |
| `services/empresas` | 2 | 8 |
| `services/clientes` | 1 | 2 |
| `services/financeiro` | 1 | 2 |
| `services/notificacoes` | 1 | 2 |

`tests/performance/` está vazio — não há `locustfile.py` nem teste de carga
nenhum. A pasta só não sumiu porque o git não versiona diretório vazio.

---

## ⚠️ `tests/integration/` e `tests/e2e/` NÃO são uma suíte

O CI nunca os executa, e não é descuido: eles não testam código, fazem HTTP
contra um **API Gateway de pé em `localhost:8000`** (`tests/conftest.py:27`,
fixture `api_base_url`) **já semeado com o admin** `admin@runas.com` /
`Admin@123` (`tests/conftest.py:42-49`, fixture `admin_token`, que dá `assert
response.status_code == 200` no login). Sem a stack subida e semeada, as 34
funções falham no setup.

Os 3 scripts soltos e o `tests/test-mvp.sh` também são roteiros manuais, não
testes de regressão — mas nem todos dependem de serviço vivo:

| Script | O que faz | Precisa de serviço de pé? |
|---|---|---|
| `tests/test_produtos_api.py` | `requests` contra `http://localhost:8002` | sim |
| `tests/test-mvp.sh` | roteiro de `curl` | sim |
| `tests/test_estrutura_simples.py` | valida arquivos e sintaxe via `ast`, offline | não |
| `tests/test_produtos_local.py` | importa os models de produtos por um `sys.path` montado à mão | não |

Só o `test_produtos_api.py` tem funções `test_*` (5, fora das 256). Os outros
dois rodam no nível do módulo e chamam `sys.exit(1)` quando algo falha.

Tratar essa pasta como cobertura é o erro que esta documentação já cometeu.

---

## Os três legs que o CI roda

`.github/workflows/ci.yml` roda **escopado pelo diff** e só em PR para `Developer`;
o dispatch manual e o `deploy.yml` (job `test`, no merge em `main`) rodam tudo. Três
jobs executam teste:

| Job | Comando | Escopo |
|---|---|---|
| `checks` (passo "Unit tests") | `pytest -c tests/pytest.ini tests/unit` | 85 funções; roda em todo PR |
| `services` | `bash scripts/ci-services.sh <diretórios>`, que roda `pytest tests -p no:cacheprovider` em cada serviço, do seu diretório | 137 funções; só os serviços que o diff toca |
| `frontend` | `npm run test -- --run` (vitest, em `frontend/`) | testes do React; só se o diff toca `frontend/` |

Os outros jobs não rodam teste de aplicação: o `checks` também valida os dois
composes; o `build` constrói as imagens afetadas e roda um smoke test do
`passlib`/`bcrypt` dentro das do `api-gateway` e do `vendas`; o `migration-replay`
sobe o stack inteiro contra um único Postgres vazio.

---

## Versões fixadas (`tests/requirements.txt`)

```
pytest==9.1.1          pytest-asyncio==1.4.0   pytest-cov==7.1.0
pytest-xdist==3.8.0    httpx==0.28.1           faker==40.39.0
factory-boy==3.3.3     freezegun==1.5.5        PyYAML==6.0.3
```

`pytest-mock` **não está instalado** — `mocker` não existe aqui; use
`unittest.mock`.

---

## Pré-requisitos

```bash
pip install -r tests/requirements.txt
```

Quem precisa de quê:

- **Leg 1 (`tests/unit`)** — nada subindo. Só o `tests/requirements.txt`.
- **Leg 2 (por serviço)** — Postgres e Redis de pé, e o serviço instalado com
  os **próprios** pins: `pip install -r requirements.txt` dentro do diretório
  dele, além do `tests/requirements.txt`. Localmente, o
  `docker compose -f docker-compose.dev.yml up -d` já publica Postgres e Redis
  no host, que é para onde os defaults do conftest apontam
  (`services/vendas/tests/conftest.py:16-18`).
- **Leg 3 (frontend)** — `npm ci` em `frontend/`.
- **`tests/integration` e `tests/e2e`** — a stack inteira de pé **e semeada**
  (veja a seção acima). O CI não roda esses.

---

## Comandos

São os mesmos legs de `.github/workflows/ci.yml` (o passo "Unit tests" do `checks`
e os jobs `services` e `frontend`). Rode exatamente assim:

```bash
# Leg 1 — unitários (passo "Unit tests" do job `checks` do CI)
pytest -c tests/pytest.ini tests/unit

# Leg 2 — por serviço (job `services` do CI, que roda scripts/ci-services.sh)
bash scripts/ci-services.sh services/produtos   # sem argumento = api-gateway + os 7 serviços
bash scripts/ci-services.sh --listar            # os diretórios que ele conhece
# O script cria banco e venv novos por serviço, aplica init-schemas + alembic e roda o
# pytest. Precisa de Postgres (usuário erp) e Redis em localhost, de createdb/psql no PATH
# e, no ambiente, do que o job `services` define (ci.yml:283-299): PGPASSWORD, SECRET_KEY
# e as *_URL do gateway.
# Só o pytest, com o banco já migrado:
cd services/produtos && pytest tests -p no:cacheprovider

# Leg 3 — frontend (job `frontend` do CI)
cd frontend && npm run test -- --run
```

O `--run` não é detalhe: `npm run test` sozinho é `vitest` em modo watch
(`frontend/package.json:12`) e nunca termina.

### Nunca rode `pytest` seco

`tests/pytest.ini` tem `testpaths = tests`, então um `pytest` sem caminho
coleta também `tests/test_estrutura_simples.py`, `tests/test_produtos_api.py` e
`tests/test_produtos_local.py`. `test_estrutura_simples.py` e
`test_produtos_local.py` rodam inteiros no import e chamam `sys.exit(1)` no
nível do módulo — isso aborta a coleta, não só o arquivo; `test_produtos_api.py`
faz HTTP contra `localhost:8002` e falha com o serviço fora. É exatamente por
isso que o CI passa o caminho `tests/unit` explicitamente.

### ⚠️ Os dois legs têm capacidades OPOSTAS

O detalhe que derruba quem move um teste de um leg para o outro:

| | `tests/unit` | `services/<nome>/tests` |
|---|---|---|
| **async** | automático (`asyncio_mode = auto` em `tests/pytest.ini`) | **não** — precisa de `@pytest.mark.asyncio` em cada teste |
| **fastapi** | **não instalado** (`tests/requirements.txt` não o lista) | instalado (vem do `requirements.txt` do próprio serviço) |

- O leg unit roda com `-c tests/pytest.ini`, que liga `asyncio_mode = auto`;
  mas o CI instala só `tests/requirements.txt`, que não tem `fastapi`. Um teste
  unitário que importe `fastapi` ou `TestClient` passa na sua máquina e quebra no CI.
- O leg por serviço roda de dentro do diretório do serviço, onde **não existe**
  `pytest.ini`/`pyproject.toml` — logo `pytest-asyncio` fica em modo estrito.
  Teste async sem `@pytest.mark.asyncio` é pulado/erra em vez de rodar.

### De onde vem o banco do leg por serviço

Não há `create_all` em lugar nenhum. O schema contra o qual esses 137 testes
rodam é o que as migrations constroem, na mesma ordem que a produção:

1. `psql -f postgres/init-schemas.sql` — schemas, grants e a função de auditoria
   compartilhada, o que o `db-init` faz antes de qualquer serviço bootar;
2. `alembic upgrade head` — a cadeia inteira contra um banco **vazio**;
3. só então `pytest tests`.

Testar contra `create_all` seria testar os models contra eles mesmos — foi
assim que a produção divergiu das migrations sem ninguém ver
(`services/vendas/tests/conftest.py:1-10`).

Cada teste roda dentro de uma transação que nunca é commitada de verdade: a
fixture `db` abre a conexão, começa a transação e entrega uma `AsyncSession`
com `join_transaction_mode="create_savepoint"`, então o `commit()` do código sob
teste vira `RELEASE SAVEPOINT` e o `rollback()` do `finally` desfaz tudo
(`services/vendas/tests/conftest.py:29-50`). Nenhum teste precisa limpar tabela.

SQLite não serve aqui: não tem `SELECT ... FOR UPDATE`, e parte do que esses
testes guardam é concorrência.

### Testar endpoints à mão

Em vez de roteiro de `curl` em markdown (que apodrece), use o Swagger de cada
serviço — `http://localhost:<porta>/docs`, sujeito a `DOCS_ENABLED`
(`api-gateway/config.py:84`, default `False`). O catálogo de endpoints
versionado está em [`docs/10-api-reference/`](../docs/10-api-reference/) — para
estoque, [`estoque-api.md`](../docs/10-api-reference/estoque-api.md).
Lembre do header obrigatório `X-Empresa-Id` nas rotas multi-tenant.

---

## Boas Práticas

Resgatado de `GUIA_TESTES_AUTOMATIZADOS.md` (apagado).

### Nomear testes

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

# ❌ RUIM (múltiplos asserts num teste só)
def test_validacoes():
    ...
```
