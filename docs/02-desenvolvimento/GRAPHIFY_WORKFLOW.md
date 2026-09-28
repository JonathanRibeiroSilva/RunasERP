# Graphify - Fluxo de Trabalho

Graphify mantém um **grafo de conhecimento** do projeto em `graphify-out/`
(componentes, relacionamentos e comunidades de código). Setup, arquivos
versionados e hook local: [GRAPHIFY_SETUP.md](GRAPHIFY_SETUP.md).

Os números do grafo (nós, edges, comunidades) mudam a cada update e não são
repetidos aqui: veja `## Summary` em `graphify-out/GRAPH_REPORT.md`.

## Atualização automática via GitHub Actions

**Workflow**: `.github/workflows/graphify-update.yml`

Quando o push é para `main` e toca código, o Actions atualiza o grafo e commita
`graphify-out/` de volta. Você **não** precisa rodar `graphify update` nem
commitar `graphify-out/` depois de cada commit.

### Gatilhos

- Push para **`main`** (somente; `Developer` e `master` não disparam, ver
  `graphify-update.yml:5-11`) com mudança em `**.py`, `**.ts`, `**.tsx`,
  `**.js`, `**.jsx` ou `**.vue`
- Execução manual (`workflow_dispatch`)

### Proteções anti-loop

- Não roda se a mensagem do commit contém `[skip graphify]` (o commit do bot já
  leva essa marca)
- Não roda `graphify update` se o último commit (`HEAD~1..HEAD`) não tocou
  arquivos de código
- O commit é feito por `github-actions[bot]`, e só se `graphify-out/` mudou

### Processo

1. Detecta código alterado no último commit
2. Remove `graphify-out/.graphify_root` e `graphify-out/.graphify_uncached.txt`
   (podem ter caminhos de Windows)
3. Executa `graphify update`
4. Verifica se `graphify-out/` mudou (`git status --porcelain`)
5. Commita `chore(graphify): auto-update knowledge graph [skip graphify]`
   (o corpo traz a contagem de arquivos, o SHA que disparou e a branch)
6. Faz push para a branch de origem

## Quando rodar manualmente

O Actions só roda em `main`. Na `Developer` ou em branch de feature o grafo não
é atualizado sozinho.

```powershell
# Explorar o código localmente antes de commitar
graphify update .
graphify query "como funciona o módulo de vendas?"
```

`graphify update` re-extrai só código (sem LLM). Para incluir docs e imagens é
preciso o skill `/graphify` com `--update`, dentro do Claude Code; `--update`
não é opção da CLI `graphify`. A CLI acima é a 0.9.30 (`graphify --version`);
A CONFIRMAR: qual versão o Actions instala (`pip install graphifyy` sem pin).

Grafo corrompido ou inconsistente: `graphify update . --force` sobrescreve o
`graph.json` mesmo que o rebuild tenha menos nós (útil depois de refactor que
apaga código). Como `graphify-out/` é versionado, para voltar ao estado anterior
use `git restore graphify-out/`.

## Quando o Actions NÃO atualiza

- Commit que não toca `.py/.ts/.tsx/.js/.jsx/.vue` (só `.md`, `.yml`, `.env`,
  `docker-compose.yml`, imagens)
- Push para qualquer branch que não seja `main`
- Commit com `[skip graphify]` na mensagem

Atenção: migrations e seeds são `.py`, então **disparam** o workflow.

## Troubleshooting

### Grafo não foi atualizado após push em main

1. Confirme que houve mudança em código (não só docs)
2. Veja a aba **Actions** no GitHub e os logs do workflow
3. Confirme que o push foi para `main`

### Grafo desatualizado localmente

```powershell
git pull                 # traz o grafo que o bot commitou
graphify update .        # ou atualize localmente
```

Para saber de qual commit o grafo local foi construído, veja `## Graph Freshness`
em `graphify-out/GRAPH_REPORT.md`.

### Loop de commits

Não deve ocorrer por causa do `[skip graphify]`. Se ocorrer, verifique se
alguém alterou o `if:` do job em `graphify-update.yml` e desabilite o workflow
na aba Actions enquanto investiga.

## Referências

- [Workflow](../../.github/workflows/graphify-update.yml)
- [GRAPHIFY_SETUP.md](GRAPHIFY_SETUP.md)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
