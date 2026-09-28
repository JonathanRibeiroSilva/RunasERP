# Setup do Graphify - Knowledge Graph Automation

**Ultima revisao**: 2026-09-26
**Status**: ativo (workflow `.github/workflows/graphify-update.yml`)

---

## O que e o Graphify?

Sistema de grafo de conhecimento que mapeia a arquitetura do projeto (arquivos,
classes, funcoes, imports, chamadas) em `graphify-out/`.

Os numeros do grafo (nos, edges, comunidades) mudam a cada update e por isso nao
sao repetidos aqui. O numero atual esta sempre na secao `## Summary` de
[`graphify-out/GRAPH_REPORT.md`](../../graphify-out/GRAPH_REPORT.md), junto com o
commit de onde o grafo foi construido (`## Graph Freshness`) - use-o para saber
se o grafo local esta velho:

```powershell
git rev-parse HEAD                              # commit atual
Select-String -Path graphify-out/GRAPH_REPORT.md -Pattern 'Built from commit'
```

---

## Automacao via GitHub Actions

**Workflow**: `.github/workflows/graphify-update.yml`

Dispara em **push para `main`** que toque `**.py`, `**.ts`, `**.tsx`, `**.js`,
`**.jsx` ou `**.vue`, e tambem manualmente via `workflow_dispatch`. Nao roda na
`Developer`: o bot commita o `graphify-out/` regenerado na branch onde executa, e
rodar nas duas fazia todo merge colidir nos arquivos gerados (o racional esta em
`graphify-update.yml:5-9`).

O que ele faz, em ordem: instala `graphifyy` (Python 3.11), confere se o ultimo
commit realmente tocou codigo, roda `graphify update`, e - se `graphify-out/`
mudou - commita como `chore(graphify): auto-update knowledge graph
[skip graphify]` e faz push de volta. O `[skip graphify]` na mensagem e a
protecao anti-loop (`if: !contains(head_commit.message, '[skip graphify]')`).

Detalhes de gatilhos, troubleshooting e quando rodar `graphify update` na mao
estao em [GRAPHIFY_WORKFLOW.md](GRAPHIFY_WORKFLOW.md).

---

## Arquivos versionados

Rastreados no git dentro de `graphify-out/` (via `git ls-files graphify-out/`):

| Arquivo | Conteudo |
|---|---|
| `graph.json` | grafo completo |
| `graph.html` | visualizacao interativa |
| `GRAPH_REPORT.md` | relatorio legivel com as estatisticas |
| `manifest.json` | indice por caminho de arquivo analisado |
| `.graphify_labels.json` (+ `.sig`) | rotulo/hub de cada comunidade (`"0": "sqlalchemy_ext_asyncio"`) |
| `.graphify_root` | raiz relativa usada na build (hoje `.`) |

Ignorados pelo `.gitignore` (linhas 120-125):

- `graphify-out/cache/` - cache de AST por arquivo, regeneravel
- `graphify-out/20*/` - snapshots datados; nada os le e o historico do git ja
  guarda as versoes anteriores do `graph.json`

---

## Hook local opcional

`scripts/setup-graphify-hook.ps1` instala um hook `post-commit` que roda
`graphify update` em silencio depois de cada commit local:

```powershell
.\scripts\setup-graphify-hook.ps1 status      # ver estado (padrao)
.\scripts\setup-graphify-hook.ps1 install
.\scripts\setup-graphify-hook.ps1 disable     # ou enable / uninstall
```

`scripts/graphify-smart.ps1` e um wrapper para consultas com filtro de camada:

```powershell
.\scripts\graphify-smart.ps1 query "webhook payment" -Layer backend
.\scripts\graphify-smart.ps1 explain "MercadoPagoService"
```

---

## Arquivos relacionados

- [`.github/workflows/graphify-update.yml`](../../.github/workflows/graphify-update.yml)
- [`.github/workflows/README.md`](../../.github/workflows/README.md)
- [GRAPHIFY_WORKFLOW.md](GRAPHIFY_WORKFLOW.md)
