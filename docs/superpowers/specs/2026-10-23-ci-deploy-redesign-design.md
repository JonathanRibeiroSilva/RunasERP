> **Substituído em 2026-10-26** por `docs/superpowers/specs/2026-10-26-esteira-ci-cd-design.md`. Mantido só como histórico.

# Redesenho de CI e Deploy — spec

Data: 2026-10-23. Status: aguardando revisao. Nao commitado (regra do usuario).

## 1. Problema

Medido nos arquivos de hoje (`ci.yml`, `deploy.yml`, `docker-compose.build.yml`):

1. **Todo PR roda 12 jobs** (build, frontend, backend, 8 legs de servico, migration-replay
   pulado), mesmo quando o diff toca um servico so.
2. **O mesmo commit e testado ate 3 vezes**: no PR, no push em `Developer`, no push em `main`.
3. **As 9 imagens sao construidas duas vezes**: job `build` da CI (com `.env.production.example`)
   e `deploy.yml` (com `PROD_ENV`).
4. **O deploy nao espera a CI.** `ci.yml` e `deploy.yml` disparam juntos no push em `main`;
   CI vermelha nao impede o deploy.
5. **Nao ha branch protection**: o repo e privado em plano gratuito (`gh api .../protection`
   devolve 403 "Upgrade to GitHub Pro"). Nenhum check e *required*. O unico portao possivel
   e o proprio pipeline do merge.

## 2. Objetivo

Cada commit e testado o minimo necessario, uma vez em cada estagio, e o deploy so sobe o que
passou. Sem aumentar o downtime de producao (a janela de queda e na VPS, depois do disparo da
Coolify; os testes rodam antes, no runner).

## 3. Fora de escopo

- Declarar `ARG VITE_*` no `frontend/Dockerfile`. Hoje nenhum `VITE_*` chega ao bundle
  (Dockerfile sem `ARG`, sem `.env` no build), entao a imagem do frontend e a mesma em qualquer
  ambiente e pode ser promovida. Consequencia observada: `googleClientId` e `microsoftClientId`
  ficam `''` em producao. **Vira card proprio.**
- Teste de integracao entre servicos (contrato HTTP). Nenhum leg sobe outros servicos hoje.
- Reduzir o downtime da Coolify (~80s, ver memoria `downtime-baseline-deploy`).
- Branch protection (exige plano pago ou repo publico).

## 4. Desenho

### 4.1 Merge em `main` — `deploy.yml`

```
push em main (paths-ignore igual ao de hoje) | workflow_dispatch(tag)
  ├─ test     chama ci.yml com full: true     (if: tag vazio)
  ├─ publish  build 9 imagens com PROD_ENV,
  │           smoke de auth, push SO de :<sha> (if: tag vazio)
  └─ deploy   needs: [test, publish]
              promove :<sha> -> :latest, dispara Coolify, espera
```

- `concurrency: deploy-production`, `cancel-in-progress: false`, no **workflow inteiro**. Motivo:
  com o grupo so no `deploy`, testes de duracoes diferentes permitem que o `deploy` do merge A
  entre depois do de B e leve a producao de volta ao codigo de A. Com o grupo no workflow, os
  merges saem em ordem; o GitHub guarda so o pendente mais novo, que contem os anteriores.
- **`:latest` so avanca no `deploy`.** A Coolify e o `cache_from` leem `:latest`; promover antes
  dos testes deixaria uma imagem nao testada acessivel a um restart ou redeploy.
- **Promocao** = `docker buildx imagetools create -t <img>:latest <img>:<sha>` por imagem, so no
  registry, sem pull nem rebuild. O `deploy` escreve o `.env` de build de novo, porque
  `docker compose config --images` exige as entradas `${VAR:?}`.
- **Rollback** (`workflow_dispatch` com `tag` preenchido): `test` e `publish` sao pulados por
  `if: inputs.tag == ''`; o `deploy` roda com `if: ${{ !failure() && !cancelled() }}` (senao
  `needs` pulado pula o `deploy`) e promove o sha informado. Mesmo passo da promocao normal.
- `tag` vazio no dispatch roda o pipeline completo para o commit atual.
- Smoke de auth: o trecho de `ci.yml` (passlib/bcrypt nas imagens `api-gateway-prod` e
  `vendas-prod`) vai para `scripts/ci-smoke-auth.sh`, usado pelo job `build` do PR e pelo
  `publish`. No `publish` roda **antes do push**: imagem quebrada nao chega ao registry.
- Passos do `deploy` apos a promocao (disparo da Coolify, polling de 90x10s, tolerancia a 530,
  `-A Mozilla`, `COOLIFY_URL` pelo hostname Cloudflare) ficam **identicos** a hoje.

### 4.2 PR — `ci.yml`

- Gatilhos: `pull_request` (`main`, `Developer`), `workflow_dispatch`, `workflow_call`
  (entrada `full: boolean`). **Sai o gatilho de `push`**: `main` e coberto por 4.1;
  `Developer` ja foi testado no PR. No `workflow_dispatch` da propria CI nao ha diff de PR, entao
  roda como `full`.
- Job `changes` (`dorny/paths-filter`, versao fixada, sem secrets) calcula os filtros. Com
  `full: true` o filtro e ignorado e tudo roda.
- Filtros (ancoras YAML para os conjuntos compartilhados):

| Job | Roda quando muda |
|---|---|
| `services` (matriz) | `services/<x>/**` ou `api-gateway/**` (so aquele leg); OU `postgres/**`, `tests/requirements.txt`, `.github/workflows/ci.yml` (todos) |
| `build` (imagens) | diretorio da imagem (so ela); OU `docker-compose.prod.yml`, `docker-compose.build.yml`, `.env.production.example`, `ci.yml` (todas) |
| `frontend` | `frontend/**` |
| `backend` (`tests/unit`) | sempre (le fontes e compose de todos; barato) |
| validacao de compose | sempre (`docker compose config`) |
| `migration-replay` | nunca em PR; roda em `workflow_call`/`workflow_dispatch` |

- `migration-replay` mantem `if: github.event_name != 'pull_request'`. Em `workflow_call`,
  `event_name` e o do chamador (`push`/`workflow_dispatch`), entao roda.
- No pipeline do merge o job `build` da CI nao roda (`full` + `publish` o substituem); a
  validacao de compose continua.
- Mudanca em `api-gateway/**` roda so o leg do gateway (nenhum leg sobe outros servicos).
- PR `Developer` -> `main` e comparado contra a base `main`: o diff acumulado e o que vale.
- PR so de docs roda `backend` + validacao de compose.

## 5. Falhas

| Falha | Efeito |
|---|---|
| `test` ou `publish` vermelho | `deploy` nao roda; producao intacta; `:<sha>` orfas no ghcr, inofensivas |
| Coolify falha apos a promocao | igual a hoje; rollback = dispatch com o `tag` anterior |
| Dois merges seguidos | em fila pelo `concurrency` do workflow; o pendente mais novo vence |

## 6. Validacao (o que NAO da para executar localmente)

Workflow nao roda local e nao ha Docker/Postgres local. Eu valido sintaxe do YAML e
`docker compose config`; **o comportamento so se prova no GitHub**, em ordem:

1. PR so em `services/estoque`: so esse leg e essa imagem rodam.
2. PR so de docs: so `backend` + validacao de compose.
3. O PR deste redesenho muda so `.github/**` (e `scripts/**`), ambos no `paths-ignore` do
   deploy: o merge **nao dispara deploy** e o pipeline novo nao e exercitado.
4. Primeira prova real: `workflow_dispatch` com `tag` vazio — teste, build, promocao e deploy
   de verdade, com ~80s de queda. Fazer de proposito, em horario calmo.
5. Prova do rollback: dispatch com o sha atual (so promove e redeploya).

## 7. Documentacao a atualizar na implementacao

`.github/workflows/README.md`, `docs/06-operacao/deploy.md` e o `CLAUDE.md` (secao Git/Infra)
citam `arquivo:linha` de `ci.yml`/`deploy.yml`. Reescrever esses workflows muda as linhas:
re-medir toda referencia com `git grep -n` antes de fechar (memoria `docs-citam-arquivo-linha`).

## 8. Riscos

- `workflow_call` com `full` e a parte mais nova; um erro de `if`/`needs` pode pular o deploy
  em silencio. Mitigacao: a prova 4 antes de confiar no pipeline.
- Filtro de paths incompleto deixa um servico sem teste num PR. Mitigacao: conjuntos
  compartilhados listados acima; o merge roda tudo de qualquer forma.
- `dorny/paths-filter` e dependencia de terceiros. Roda num job sem secrets; Dependabot
  mantem a versao.
