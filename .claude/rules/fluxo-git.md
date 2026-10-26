# Fluxo Developer → main e worktrees

- Promova em lotes pequenos: abra o PR `Developer` → `main` quando um card relevante fecha, em horário de pouco uso (cada deploy deixa o stack fora por ~80s). Antes, `git log origin/main..origin/Developer --oneline`; se houver migration, revise-a (revision nova roda no boot; constraint que falha = crashloop).
- PR sempre com base `Developer`. O CI só dispara para base `main` ou `Developer` (`.github/workflows/ci.yml`); PR empilhado em outra branch fica sem checks, e "no checks reported" não é "rodando". Decisão de 26/10/2026: manter a regra em vez de abrir o filtro.
- Antes de abrir o PR, `git fetch` + `git rebase origin/Developer` no worktree: o conflito com um chat paralelo aparece aí, não no segundo PR.
- Pós-merge, rode de FORA da pasta do worktree: `git -C <RunasERP> worktree remove .claude/worktrees/<nome>` (+ `rmdir` se a pasta sobrar), `git branch -d <branch>` e `git push origin --delete <branch>`. No Windows, remover de dentro da pasta (ou com um shell aberto nela) dá "Permission denied": o git desregistra o worktree, mas a pasta vazia fica.
- Worktree de branch já mergeada se apaga, não se atualiza. De vez em quando, `git worktree list` + `git worktree prune`.
