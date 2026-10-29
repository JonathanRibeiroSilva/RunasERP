# Como contribuir

Guia curto e verificado. Toda afirmação daqui foi lida do código ou da config;
onde o leitor pode precisar conferir, a fonte vem como `arquivo:linha`.

---

## 1. A base do PR tem de ser `Developer`

> **Se a base do PR não for `Developer`, a CI não roda. Nenhum job.
> O PR fica com "no checks reported", que não é a mesma coisa que "rodando".**

O gatilho é explícito:

```yaml
on:
  pull_request:
    branches: [Developer]
```

`.github/workflows/ci.yml:7-8`

Essa lista é a lista de **branches de destino**. Um PR empilhado sobre outra
branch de feature (base `feat/algo`, por exemplo) não casa com `Developer`,
então o GitHub não agenda job nenhum — e a tela do PR mostra ausência de checks,
não falha de checks. O PR de promoção `Developer` → `main` também fica sem CI,
mas por desenho: o merge em `main` dispara o `deploy.yml`, que roda a CI inteira
antes de publicar (`.github/workflows/ci.yml:4-6`).

Para pré-checar uma branch antes do PR, rode o workflow **CI** à mão
(**Actions** → **CI** → **Run workflow**): o `workflow_dispatch` roda todos os
escopos (`.github/workflows/ci.yml:10`). Já custou tempo ao time: esperar um verde que nunca ia
chegar. Antes de esperar, confira a base do PR.

Se você já abriu com a base errada, troque a base pela UI do GitHub ("Edit" ao
lado do título) e confira a aba Checks.

A CONFIRMAR: se a troca de base, sozinha, agenda os jobs. O gatilho não declara
`types:` (`.github/workflows/ci.yml:7-8`), e sem `types:` o `pull_request` do
GitHub cobre apenas `opened`, `synchronize` e `reopened` — trocar a base é outra
atividade. Se os checks não aparecerem, um push novo na branch resolve.

### Fluxo de duas branches

- `Developer` é a branch de integração. Todo trabalho entra nela por PR.
- `main` só recebe `Developer` por PR. É de `main` que o deploy sai
  (`.github/workflows/deploy.yml:3-4`, comentário: *"Production deploys happen
  only from main. Developer is the integration branch; it reaches main through a
  pull request."*). Esse PR não tem CI próprio: o portão é o `deploy.yml`, que
  roda a CI inteira no merge (`.github/workflows/deploy.yml:15-17`).
- A branch de feature morre depois do merge — apague-a.

A CONFIRMAR: a regra de apagar a branch de feature após o merge é convenção do
time; não achei nenhum arquivo versionado do repositório que a documente ou a
automatize (não existe `.github/pull_request_template.md`, nem config de
auto-delete versionada).

---

## 2. Commits

Conventional Commits, mensagem **em inglês**, código e comentários em PT-BR.
A convenção está em `docs/02-desenvolvimento/README.md:89-102`:

```
feat(vendas): add PDV page
fix(estoque): correct stock calculation
docs(frontend): update implementation guide
```

O histórico segue isso na prática (`git log --oneline`):
`feat(g1b): X-Plataforma com prova de que saiu do gateway`,
`fix(g1b): marca os testes async com @pytest.mark.asyncio`.

### Descrição do PR

O corpo do PR **é** a revisão. Detalhe commit a commit — o que mudou e por quê —
não só as manchetes. Quem revisa lê a descrição antes do diff; uma descrição de
uma linha transfere para o revisor o trabalho de reconstruir sua intenção.

### Merge em `main` dispara deploy de produção

`.github/workflows/deploy.yml` roda em `push: branches: [main]`. Ele reconstrói
as nove imagens (em paralelo com a CI inteira), promove `:latest` e avisa o Coolify,
que **derruba a stack antiga antes de subir a nova** — ou seja, **todo deploy é uma janela de indisponibilidade**. O próprio
workflow registra o caso: o PR #26 mexeu só em arquivos que não rodam em
produção e o deploy que ele disparou abortou no meio, deixando a aplicação fora
por 25 minutos (`.github/workflows/deploy.yml`, comentário do bloco
`paths-ignore`).

Por isso `deploy.yml` ignora `landing-page/**`, `docs/**`, `**.md`, `.github/**`
e `scripts/**`: nada disso alcança um container rodando.

---

## 3. Rodar os testes localmente

Existem **dois legs** e eles têm capacidades **opostas**. Quem não sabe disso
escreve um teste que quebra sem entender por quê.

### Leg A — unitários (`tests/unit`)

```bash
pip install -r tests/requirements.txt
pytest -c tests/pytest.ini tests/unit
```

(mesmo comando do passo "Unit tests" do job `checks`, `.github/workflows/ci.yml:180-181`)

- **Tem asyncio automático.** `tests/pytest.ini:5` traz `asyncio_mode = auto`,
  então um `async def test_...` roda sem marcador nenhum.
- **NÃO tem FastAPI.** `tests/requirements.txt` instala pytest, pytest-asyncio,
  pytest-cov, pytest-xdist, httpx, faker, factory-boy, freezegun e PyYAML — e
  mais nada. Um teste em `tests/unit` que faça `from fastapi import ...` quebra
  com `ModuleNotFoundError`.
- Por isso os testes de `tests/unit` leem fonte e config em vez de importar o
  app (ex.: `tests/unit/test_service_urls_config.py` lê
  `docker-compose.prod.yml`).
- O escopo é `tests/unit` por caminho, de propósito: vários arquivos soltos
  direto em `tests/` são scripts manuais que chamam um serviço no localhost
  (`.github/workflows/ci.yml:176-179`).

### Leg B — por serviço (`cd services/<nome> && pytest tests`)

```bash
cd services/vendas
pip install -r requirements.txt -r ../../tests/requirements.txt
pytest tests -p no:cacheprovider
```

(mesma sequência que o job `services` roda por serviço, `scripts/ci-services.sh:51-67`;
`bash scripts/ci-services.sh services/vendas` faz tudo isso com banco novo)

- **Tem FastAPI** — `fastapi==0.141.1` está no `requirements.txt` de cada
  serviço (`services/vendas/requirements.txt:1`,
  `api-gateway/requirements.txt:1`). O conftest importa o app de verdade:
  `from main import app` (`services/vendas/tests/conftest.py`).
- **NÃO tem asyncio automático.** Não existe `pytest.ini`, `pyproject.toml`,
  `setup.cfg` nem `tox.ini` na raiz do repositório nem dentro dos diretórios de
  serviço — o `asyncio_mode = auto` de `tests/pytest.ini` **não** alcança este
  leg. Todo teste assíncrono aqui precisa de `@pytest.mark.asyncio` explícito, e
  toda fixture assíncrona de `@pytest_asyncio.fixture`. É o que os testes atuais
  fazem, e o commit `ac7ffa2` (`fix(g1b): marca os testes async com
  @pytest.mark.asyncio`) existe exatamente porque isso foi esquecido uma vez.
- Um leg por serviço, nunca dois no mesmo processo: os serviços importam flat
  (`from main import app`, `from config import settings`) e dois deles brigam
  por qual `main` fica primeiro no `sys.path`
  (`scripts/ci-services.sh:12-14`).

**Pré-requisito do leg B:** Postgres e Redis alcançáveis. Os defaults do conftest
são `postgresql+asyncpg://erp:erp@localhost:5432/erp` e
`redis://localhost:6379/15` (`services/vendas/tests/conftest.py`), que é o que o
compose de dev publica no host: serviço `db` em `5432:5432`
(`docker-compose.dev.yml:89-90`) e serviço `redis` em `6379:6379` (`:51-52`). O schema vem das
migrations (`alembic upgrade head`), não de `create_all` — o conftest do serviço
documenta o porquê: testar contra `create_all` é testar os models contra eles
mesmos.

### Frontend

```bash
cd frontend
npm ci
npm run lint
npm run build
npm run test -- --run
```

(job `frontend`, `.github/workflows/ci.yml:235-257`)

O `lint` está travado em `--max-warnings 115` (`frontend/package.json:10`): é a
contagem que existia quando o gate entrou. Ele bloqueia warning **novo** sem
exigir que o backlog seja tipado primeiro.

---

## 4. Antes do primeiro commit

### 4.1 `.env`

```bash
cp .env.example .env
```

`.env` e `.env.*` estão no `.gitignore` (bloco `# Environment`, `.gitignore:44-46`),
com exceção explícita para `!.env.example` e `!.env.*.example` logo abaixo, no
bloco `# Keep example env files` (`.gitignore:48-50`). `.env.example` e
`.env.production.example` existem na raiz.

### 4.2 Instalar o hook de segredos — nada no repositório faz isso por você

`.git/hooks/pre-commit` é um shim de duas linhas:

```sh
#!/bin/sh
exec "$(git rev-parse --show-toplevel)/scripts/check-secrets.sh"
```

E `.git/hooks/` não é versionado. Nenhum script, workflow ou postinstall do
repositório instala esse shim — procurei. Ou seja: **um clone novo fica sem
nenhuma proteção contra vazar segredo** até você instalar na mão:

```bash
cat > .git/hooks/pre-commit <<'SH'
#!/bin/sh
exec "$(git rev-parse --show-toplevel)/scripts/check-secrets.sh"
SH
chmod +x .git/hooks/pre-commit
```

A lógica de verdade mora em `scripts/check-secrets.sh`, que é versionado,
revisável e testável — é esse o motivo de o shim ser burro.

Para validar o script depois de mexer num padrão:

```bash
bash scripts/test-check-secrets.sh
```

Ele monta um repositório descartável, faz stage de segredos falsos e confere o
exit code caso a caso (`scripts/test-check-secrets.sh`).

O que `check-secrets.sh` bloqueia: arquivos `.env` por nome (exceto os
`.example`) e padrões sensíveis em **linhas adicionadas** — tokens de Mercado
Pago, Stripe, Google API key, AWS access key id, token de túnel Cloudflare, PAT
do GitHub, DSNs de postgres/mongodb/mysql com senha longa, e atribuições
genéricas de `token`/`api_key`/`secret`. Ele olha o diff em stage, não o arquivo
inteiro.

Uma exceção que vale saber: `scripts/test-check-secrets.sh` é excluído da
varredura porque existe para conter segredos falsos. Uma chave real colada
naquele arquivo passa direto. Ele é fixture de teste — mantenha assim.

### 4.3 AVISO: não confie no símbolo verde

> O hook já imprimiu `✅ Verificação de segurança concluída` sem ter verificado
> coisa nenhuma.

O cabeçalho de `scripts/check-secrets.sh` documenta o caso: a versão anterior
rodava `git diff --cached --name-only | grep -v "^graphify-out/" --diff-filter=AM`.
O `--diff-filter` pertence ao `git diff`, não ao `grep`; o grep morria com
"unknown option", a lista de arquivos saía vazia, todos os loops de padrão
rodavam sobre nada — e mesmo assim imprimia a linha de sucesso. Nunca bloqueou
nada, em commit nenhum.

A versão atual corrigiu isso, mas a lição fica: **num commit que toca muitos
arquivos, rode a verificação na mão** em vez de confiar no ✅ que passou voando:

```bash
bash scripts/check-secrets.sh
```

E leia a saída. Um hook que só pode falhar em silêncio é pior que hook nenhum.

---

## 5. O que a CI exige, job a job

Cinco jobs em `.github/workflows/ci.yml`. O `checks` roda sempre e decide o que os
outros fazem a partir do diff (`ci.yml:141-164`):

| Job | O que roda |
|---|---|
| `checks` | Decide o escopo; valida os dois composes com `--env-file` (`.env.production.example` + `docker-compose.prod.yml`; `.env.example` + `docker-compose.dev.yml`); `pip install -r tests/requirements.txt` e `pytest -c tests/pytest.ini tests/unit`, Python 3.12 (`ci.yml:39-181`) |
| `build` | Constrói só as imagens de produção que o diff toca e faz smoke test das primitivas de auth dentro de `api-gateway-prod` e `vendas-prod`, se uma delas foi reconstruída (`ci.yml:189-233`) |
| `frontend` | Só se o diff toca `frontend/`: `npm ci`, `npm run lint`, `npm run build`, `npm run test -- --run`, Node 22 (`ci.yml:235-257`) |
| `services` | Um job só: `scripts/ci-services.sh` percorre os serviços do escopo, cada um com venv e banco próprios, Postgres 15 e Redis 7 como service container, `postgres/init-schemas.sql`, `alembic upgrade head` a partir de banco vazio, e `pytest tests` (`ci.yml:263-316`) |
| `migration-replay` | Em PR só se o diff toca migration, `database.py`, `postgres/**` ou `docker-compose.dev.yml`: sobe o stack real num único Postgres vazio (`ci.yml:335-384`) |

O script do `services` roda todos os serviços e falha no fim
(`scripts/ci-services.sh:18`): o PR mostra todos os serviços quebrados de uma vez.

### Por que existe o smoke test de auth

Build verde só prova que o `pip` resolveu os requirements — não roda uma linha da
aplicação. `bcrypt 5.0` instalou perfeitamente e quebrou **todo login em
produção** no primeiro request: o passlib não conseguiu ler a versão do bcrypt e
o `hash()` passou a rejeitar uma senha de 9 caracteres como "longer than 72
bytes". Nada na CI chamava `hash()`, então foi para produção
(`scripts/ci-smoke-auth.sh:11-15`).

O passo roda a primitiva real, dentro da imagem real, com os pins reais, nos dois
serviços que autenticam: o gateway (operadores) e o vendas (clientes da loja).

A CI não tem `paths-ignore`: o escopo vem do diff (`ci.yml:141-164`). Um PR só de
`docs/` não constrói imagem nem roda serviço — só o `checks` roda. O
`workflow_dispatch` e o deploy rodam todos os escopos.

---

## Lacunas declaradas

- **A CONFIRMAR:** de onde sai a regra de apagar a branch de feature após o
  merge — nenhum arquivo versionado do repositório a documenta.
- **A CONFIRMAR:** se existe regra de proteção de branch em `main`/`Developer`
  ou número mínimo de aprovações. Isso é configuração do GitHub, não está no
  repositório e não consegui ler daqui.
- A seção de comandos de `tests/README.md` (`:107-136`) concorda com a seção 3
  deste arquivo — inclusive o aviso "Nunca rode `pytest` seco" (`:114`). O que
  está desatualizado lá é só a **árvore** do topo: ela lista
  `tests/unit/test_validators.py`, `test_schemas.py` e `test_utils.py`, que não
  existem (o `tests/unit/` real tem outros 17 arquivos). `tests/integration/` e
  `tests/e2e/` existem e batem com a árvore.
