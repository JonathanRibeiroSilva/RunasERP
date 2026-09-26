# Scripts Utilitários - RunasERP

Scripts auxiliares de desenvolvimento, segurança e operação. **Nada aqui roda em
produção dentro de um container**: `scripts/**` está em `paths-ignore` do
`.github/workflows/deploy.yml` (linha 47, dentro do bloco `paths-ignore:` da
linha 42) porque nenhum Dockerfile copia deste diretório — os build contexts são
`./api-gateway`, `./services/*` e `./frontend`. Mudar um script daqui não
dispara deploy nem gera janela de indisponibilidade.

---

## Os 8 scripts

| Script | O que faz | Como roda |
|--------|-----------|-----------|
| `check-secrets.sh` | Bloqueia segredos nas **linhas adicionadas** do diff staged. É o que o `.git/hooks/pre-commit` executa. | Automático no `git commit`; manual: `bash scripts/check-secrets.sh` |
| `test-check-secrets.sh` | Autoteste do anterior: monta um repo git descartável, encena 11 casos e compara o exit code. | `bash scripts/test-check-secrets.sh` |
| `medir-downtime.sh` | Sonda produção de fora, 1x/s, e mede o downtime **real** de um deploy. | `./scripts/medir-downtime.sh` (Ctrl-C imprime o resumo) |
| `resgate-vps.sh` | Roda **na VPS, antes de destruir qualquer coisa**: gera `/tmp/resgate-vps.tar.gz` com inventário e o que não está no git. | `./scripts/resgate-vps.sh` na VPS |
| `provisionar-lojista.ps1` | Wrapper de `POST /plataforma/tenants` (cria empresa + usuário ADMIN). Exige token de `SUPER_ADMIN`. | `.\scripts\provisionar-lojista.ps1 -Token ... ` |
| `test-carrinho-recovery.ps1` | Teste **manual** de recuperação de carrinho: 5 cenários contra os endpoints `/api/loja/*`. | `.\scripts\test-carrinho-recovery.ps1` |
| `graphify-smart.ps1` | Wrapper de `graphify query/path/explain` com expansão de keywords e filtro por camada. | `.\scripts\graphify-smart.ps1 query "webhook" -Layer backend` |
| `setup-graphify-hook.ps1` | Instala/remove/desativa o hook `post-commit` que atualiza o grafo Graphify. | `.\scripts\setup-graphify-hook.ps1 status` |

Os quatro `.sh` estão com bit de execução (755); os `.ps1` são chamados pelo
PowerShell.

---

## Segurança

### `check-secrets.sh`

O hook `.git/hooks/pre-commit` é um shim de duas linhas — a lógica vive aqui
para ficar versionada, revisável e testável:

```sh
#!/bin/sh
exec "$(git rev-parse --show-toplevel)/scripts/check-secrets.sh"
```

Duas verificações, nessa ordem:

1. **Arquivos `.env` por nome** — `git diff --cached --name-only --diff-filter=AM`
   contra `(^|/)\.env(\.local|\.ngrok|\.cloudflare|\.production|\.coolify)?$`.
   `graphify-out/` e qualquer `*.example` ficam de fora. Deleção não bloqueia.
2. **Padrões sensíveis nas linhas adicionadas** — `git diff --cached -U0
   --diff-filter=ACM`, filtrado por `^+[^+]`. Cobre Mercado Pago, Stripe, Google
   API key, AWS access key id, token de túnel Cloudflare, PAT do GitHub, DSNs
   (`postgresql://`, `postgresql+asyncpg://`, `mongodb://`, `mysql://`) e
   atribuições genéricas de `token`/`api_key`/`secret`.

Qualquer acerto termina com `exit 1` e o commit não acontece. Escaneia linhas
adicionadas, não arquivos inteiros: um DSN que já está no arquivo há um ano não
trava todo commit que toca nesse arquivo.

`scripts/test-check-secrets.sh` está excluído do escaneamento de propósito —
ele existe para guardar segredos falsos. O custo é real: uma chave de verdade
colada **nesse arquivo** passa. Ele é fixture de teste, mantenha assim.

### `test-check-secrets.sh`

Rode depois de mexer em qualquer padrão. Cria um repo em `mktemp -d`, stagia um
arquivo por caso e confere o exit code contra o esperado. Casos que **devem
passar** (falso positivo é pior que hook nenhum, porque ensina `--no-verify`):
`postgresql://user:password@...`, `postgresql://erp:erp@db:5432/erp`, sha de
commit, `.env.example`. Casos que **devem bloquear**: AWS key, Stripe live, PAT
do GitHub, DSN com senha longa, arquivo `.env`, e segredo em arquivo com espaço
no nome. O exit code é o número de falhas.

Detalhe de contexto: ver `docs/02-desenvolvimento/SECURITY_HOOKS.md`.

---

## Operação

### `medir-downtime.sh`

```bash
./scripts/medir-downtime.sh                 # sonda até Ctrl-C, imprime o resumo
./scripts/medir-downtime.sh resumo x.csv    # reanalisa um csv já gravado
./scripts/medir-downtime.sh teste           # autoteste do agrupamento de janelas
```

Dois alvos, para separar as camadas:

| Alvo | Cobre |
|------|-------|
| `/health` | túnel + container do frontend |
| `/api/health` | túnel + frontend + api-gateway (o caminho real do usuário) |

Variáveis: `BASE` (padrão `https://app.runaserp.com.br`), `INTERVALO` (padrão
`1`s), `TIMEOUT` (padrão `3`s). Grava um CSV
`downtime-AAAAMMDD-HHMMSS.csv` com `epoch,iso,alvo,codigo,tempo_s` e, no
Ctrl-C, imprime as janelas fora do ar e a disponibilidade por alvo.

Leitura dos códigos:

| Código | Significado |
|--------|-------------|
| `200` | ok |
| `502`/`504` | túnel de pé, container do frontend sumiu |
| `530` | cloudflared caiu (Cloudflare error 1033: nenhum origin registrado) |
| `000` | a sonda não conectou (rede local / DNS) — não é downtime do site |
| `403` | o WAF respondeu no lugar do site: **a amostra é mentira** |

O `-A` com User-Agent de navegador não é enfeite: a zona tem regra de WAF que
desafia qualquer UA com `curl`/`wget` e devolve 403 do próprio edge, sem tocar
a VPS. Sem esse UA a sonda mede o Cloudflare, não o ERP.

### `resgate-vps.sh`

Rode **na VPS, antes** de remover containers, volumes ou stacks. Produz
`/tmp/resgate-vps.tar.gz` com:

- `containers.txt`, `volumes.txt`, `networks.txt` — inventário do que existe
- `stacks.txt` — `working_dir` + `config_files` de cada stack compose, ou seja
  qual compose subiu o banco
- cópia de `nginx`, `.env`, `docker-compose*.yml`, `cloudflared-config.yml`
  (o que faltar vai para `faltando.txt`)
- `dump-completo.sql` — `pg_dumpall` do primeiro container que casa
  `db|postgres`, com `${POSTGRES_USER:-erp}`
- `letsencrypt.tar.gz` — conteúdo do volume `letsencrypt-certs`

Baixe com `scp` antes de destruir qualquer coisa. Ver
`docs/06-operacao/runbook-producao.md`.

### `provisionar-lojista.ps1`

Wrapper de `POST /plataforma/tenants`. A lógica — inclusive a compensação
quando a criação do admin falha — vive em `api-gateway/routers/plataforma.py`;
o script só monta o payload e imprime o resultado.

```powershell
.\scripts\provisionar-lojista.ps1 -Token "eyJ..." -RazaoSocial "Padaria X LTDA" `
    -NomeFantasia "Padaria X" -Slug "padaria-x" -Cnpj "12.345.678/0001-90" `
    -Email "dono@padariax.com" -Senha "Senha@123"
```

- Token de `SUPER_ADMIN`, obtido em `POST /auth/login` com
  `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD`.
- Senha: 8-20 caracteres, com maiúscula, minúscula, número e caractere especial.
- Endereço tem defaults (`-Cep`, `-Logradouro`, `-Numero`, `-Bairro`,
  `-Cidade`, `-Uf`) e pode ser completado depois na plataforma.
- `-GatewayUrl` padrão `http://localhost:8000`.
- A loja nasce **desabilitada**; habilite em Configurações da Loja.

**Status:** o docstring de `api-gateway/routers/plataforma.py` (linha 4) diz que
o router "substitui `scripts/provisionar-lojista.ps1`, que batia direto nos
containers em dois endpoints sem autenticação". Essa frase se refere à versão
antiga do script: a atual já é só um wrapper autenticado do endpoint. O caminho
oficial é a própria rota (ou a UI da plataforma); este script é atalho de linha
de comando e deve ser tratado como obsoleto — não escreva código novo em cima
dele. Ver `docs/10-api-reference/plataforma-api.md`.

---

## Testes manuais

### `test-carrinho-recovery.ps1`

Cinco cenários contra `/api/loja/*`: criar carrinho + checkout, simular perda de
sessão, pedidos pendentes, recuperar carrinho de um pedido e retentar pagamento.

```powershell
.\scripts\test-carrinho-recovery.ps1                                    # http://localhost:3000
.\scripts\test-carrinho-recovery.ps1 -Domain https://www.runaserp.com.br
```

**Precisa ser editado antes de rodar.** O script tem valores fixos de
placeholder: `$empresaSlug = "empresa-teste"` e `$produtoId =
"produto-uuid-aqui"`. Sem trocá-los por IDs reais do ambiente, o cenário 1
falha na adição do item. Não é um teste automatizado e não roda no CI — é um
roteiro de verificação manual.

---

## Graphify

### `graphify-smart.ps1`

Wrapper de `graphify`. Aceita `query`, `path` e `explain` (`path` exige dois
argumentos). Expande a query com keywords conhecidas (`mercadopago`, `webhook`,
`carrinho`, `checkout`, `pagamento`) e, em `query`, reagrupa a saída em
BACKEND / FRONTEND / DOCUMENTAÇÃO.

```powershell
.\scripts\graphify-smart.ps1 query "webhook payment" -Layer backend
.\scripts\graphify-smart.ps1 explain "MercadoPagoService"
```

Parâmetros: `-Layer` (`backend`, `frontend`, `docs`, `services`, `routers`,
`all`), `-Exclude` (lista de regex), `-CodeOnly` (esconde docs e frontend).

### `setup-graphify-hook.ps1`

Gerencia o hook `.git/hooks/post-commit` que roda `graphify update` depois de um
commit que mexeu em código (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`).

```powershell
.\scripts\setup-graphify-hook.ps1 status      # padrão, se nenhuma ação for passada
.\scripts\setup-graphify-hook.ps1 install
.\scripts\setup-graphify-hook.ps1 disable     # renomeia para post-commit.disabled
.\scripts\setup-graphify-hook.ps1 enable
.\scripts\setup-graphify-hook.ps1 uninstall
```

O hook termina sempre com `exit 0`: se o `graphify` não estiver no PATH, ele
avisa e o commit segue. `disable`/`enable` são renomeação de arquivo
(`post-commit` ⇄ `post-commit.disabled`) — útil durante refatoração grande.

Instalação do `graphify` e uso no dia a dia:
`docs/02-desenvolvimento/GRAPHIFY_WORKFLOW.md` e
`docs/02-desenvolvimento/GRAPHIFY_SETUP.md`.

---

## Documentação Relacionada

- `docs/02-desenvolvimento/SECURITY_HOOKS.md` — hooks de segurança em detalhe
- `docs/02-desenvolvimento/GRAPHIFY_WORKFLOW.md` — Graphify no dia a dia
- `docs/06-operacao/runbook-producao.md` — procedimentos de produção
- `docs/06-operacao/deploy.md` — pipeline de deploy
- `docs/10-api-reference/plataforma-api.md` — rotas `/plataforma`
- `graphify-out/GRAPH_REPORT.md` — relatório do grafo atual

---

## Ao adicionar um script

1. Header no próprio arquivo: o que faz, como rodar, e o **porquê** se houver
   uma armadilha (o UA do `medir-downtime.sh` é o exemplo).
2. Uma linha na tabela dos 8 acima — atualize a contagem no título.
3. Lógica não trivial deixa um autoteste rodável ao lado
   (`test-check-secrets.sh`, ou o modo `teste` do `medir-downtime.sh`).
4. Commit: `chore(scripts): ...`
