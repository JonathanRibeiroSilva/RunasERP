# Persistência e Durabilidade dos Dados

> Decisão de arquitetura sobre onde o banco vive, como ele sobrevive a deploys
> e o que ainda falta para o dado ser realmente durável.
>
> **Status:** ameaça 3 resolvida (todo serviço migra por Alembic). Existe um dump
> local antes de cada deploy (`erp-db-backup-prod`). As ameaças 1 e 2 **não estão
> resolvidas em produção**: o compose declara `db_data` como `external: true`, mas
> o Coolify descarta essa declaração (ver [abaixo](#1-volume-órfão)). Backup fora
> da máquina e PITR continuam planejados.
> **Contexto:** decidido enquanto a produção ainda roda só com dados de seed —
> a janela mais barata para mudar isso.

---

## O modelo de ameaça

Backup não é a primeira defesa. Das cinco formas de perder os dados, as três
mais prováveis são configuração, não catástrofe:

| # | Como o dado se perde | Chance | Estrago | Defesa | Estado |
|---|----------------------|--------|---------|--------|--------|
| 1 | Volume órfão por troca do nome do projeto Compose | alta | total | bind mount absoluto do `db` | **aberto** (o Coolify descarta o `external: true` e também o `name:` do volume; medido em 2026-10-23, ver abaixo) |
| 2 | `docker compose down -v` / remoção do projeto | média | total | bind mount absoluto do `db` | **aberto**, mesma causa |
| 3 | Drift do `create_all` → migration destrutiva | média | parcial | Alembic dono do schema | resolvido |
| 4 | VPS morre / falha de disco / provedor | baixa | total | backup fora da máquina | aberto (o dump atual fica no mesmo disco) |
| 5 | Query ou migration errada em produção | baixa | parcial | backup + PITR | parcial: dump antes de cada deploy, sem PITR |

### 1. Volume órfão

Volume declarado sem `name:` recebe o nome do projeto como prefixo:
`<projeto>_db_data`. Quando o Coolify assume a stack, ele usa o nome de projeto
dele; pede um volume que não existe; o Docker cria um **novo e vazio**. O sistema
sobe funcionando e sem nenhum registro. Parece instalação nova.

A correção pensada originalmente foi fixar o nome e marcar o volume como externo.
É o que `docker-compose.prod.yml` ainda declara:

```yaml
volumes:
  db_data:
    name: runaserp_db_data
    external: true
```

`external: true` significaria "esse volume não é do Compose": ele não cria e o
`down -v` não apaga, e a criação passa a ser um ato deliberado
(`docker volume create runaserp_db_data`).

**Em produção isso não vale.** O próprio compose registra, no comentário do
serviço `db-backup`, que o Coolify reescreve a seção `volumes` e descarta o
`external:` — "db_data below is not protected the way it looks" — enquanto repassa
bind mounts sem mexer. Por isso o backup (abaixo) usa bind mount absoluto e o
banco ainda não.

**Medido na VPS em 2026-10-23 (Coolify 4.4.7; a primeira medição foi em
2026-08-24, com o mesmo resultado):** o container do banco (no Coolify chama-se
`db-yd9rf7vub6mdcgd8qa7t7g9j`, não `erp-db-prod`) monta o volume comum
`yd9rf7vub6mdcgd8qa7t7g9j_db-data` (`docker inspect <container> --format
'{{json .Mounts}}'`). Ou seja, o `name:` fixo **também** é descartado: o volume
tem o prefixo do projeto do Coolify e vive no ciclo de vida dele. O
`runaserp_db_data` existe, está vazio (0 itens) e nenhum container o usa
(`docker ps -a --filter volume=runaserp_db_data` volta vazio). O `name:` da
**rede** é respeitado: o banco está em `runaserp_erp-network`.

**Correção pendente:** trocar `db_data:/var/lib/postgresql/data` por um bind
mount absoluto no host (o mesmo padrão de `/data/erp/backups`), migrando os dados
do volume atual antes. Até lá, um redeploy que recrie o projeto no Coolify pode
subir o banco vazio.

Redis e RabbitMQ ficam de propósito sob o ciclo de vida do Compose
(`runaserp_redis_data`, `runaserp_rabbitmq_data`, sem `external`): o compose os
trata como descartáveis — Redis é cache LRU (`--appendonly yes --maxmemory 256mb
--maxmemory-policy allkeys-lru`) e as filas do RabbitMQ são reconstruídas a
partir do banco.

No `docker-compose.dev.yml` nenhum volume tem `name:` (`db_data`, `redis_data`,
`rabbitmq_data`, `pgadmin_data`): lá o nome é `<projeto>_db_data` e
`docker compose down -v` apaga o banco de dev. Aceitável para dev, e é o motivo
de não usar esse compose como referência de durabilidade.

### 3. Drift do `create_all` (resolvido)

`create_all` não apaga nada — ele cria tabela que falta. O dano é indireto: o
schema passa a ser construído por um caminho que o Alembic não registrou. O
Alembic acredita estar na revisão X, a realidade é outra, e a próxima migration
autogerada compara os dois e "corrige" a diferença com `drop_column`.
**A perda acontece na migration seguinte, não no `create_all`.**

Hoje nenhum serviço chama `Base.metadata.create_all` fora de testes. O `init_db()`
do gateway e dos 7 serviços roda `alembic upgrade head` como subprocesso no boot
(ver `services/*/database.py` e `api-gateway/database.py`), e falha se
`alembic/versions/` vier vazio na imagem. A convenção está em `CLAUDE.md` →
Database Migrations. `financeiro` e `notificacoes`, que antes não tinham migration
nenhuma, ganharam baseline (`20260919_baseline.py`).

Revisions versionadas por serviço (sem contar `__init__.py`):

| Serviço | Revisions |
|---------|----------:|
| api-gateway | 7 |
| empresas | 3 |
| clientes | 2 |
| produtos | 3 |
| estoque | 3 |
| vendas | 4 |
| financeiro | 1 |
| notificacoes | 1 |

Na CI, o job `services` de `.github/workflows/ci.yml` aplica
`postgres/init-schemas.sql` e roda `alembic upgrade head` num banco vazio antes
dos testes de cada serviço.

---

## O banco como unidade de deploy separada

Objetivo declarado: rodar o banco num servidor à parte, no futuro.

**Boa parte disso já existe.** Todo serviço alcança o banco por uma string de
conexão: no compose de prod cada um recebe `DATABASE_URL` a partir de
`DATABASE_URL_<SERVICO>` (`DATABASE_URL_GATEWAY`, `DATABASE_URL_EMPRESAS`, ...).
Nenhum deles sabe que o Postgres é um container vizinho. O que ainda amarra é o
banco estar no mesmo arquivo de deploy do app.

### Três unidades em vez de duas (planejado)

| Arquivo | Contém | Muda quando | Lido por | Existe? |
|---------|--------|-------------|----------|---------|
| `docker-compose.data.yml` | Postgres, Redis, RabbitMQ | quase nunca | Coolify | não, planejado |
| `docker-compose.prod.yml` | hoje: dados (`db`, `db-backup`, `db-init`, `redis`, `rabbitmq`) + os 9 apps (gateway, 7 serviços, frontend) + cloudflared | todo merge | Coolify | sim |
| `docker-compose.build.yml` | overlay de build | — | GitHub Actions | sim |

As stacks se comunicariam pela rede `runaserp_erp-network`, que já tem `name:`
fixo no compose de prod.

**Hoje:** tudo num único compose na mesma VPS. O app encontra `db:5432` pela rede
Docker.

**Depois:** a stack `data` vai para outro host. Muda-se `DATABASE_URL_*` e
acrescenta-se `sslmode=require`. O compose do app não precisaria mudar.

### O que se ganha

- deploy do app deixa de poder derrubar o banco — hoje pode: o Coolify remove
  todos os containers do app antes do `up -d` (comentário do `db-backup` no
  compose de prod)
- atualizar a versão do Postgres não redeploya 9 aplicações
- `down -v` no app não alcança os volumes do banco
- migrar de host vira mudança de variável, não refatoração

### O que custa

O `depends_on: db` sai (hoje o anchor `x-service` depende de `db`, `db-init`,
`redis` e `rabbitmq` com `condition`). Os apps passam a subir antes do banco estar
pronto e reiniciam até conseguir conectar. Isso é o comportamento **correto**: não
existe `depends_on` para um host remoto, e `restart: unless-stopped` (já no
`x-service`) cobre. É a mesma resiliência que será obrigatória quando o banco
estiver do outro lado da rede — melhor adquiri-la enquanto ele ainda está do lado.

Esse split também perderia o encadeamento `db-backup` → `db-init` → serviços
descrito abaixo; ele teria de ser refeito na nova unidade.

---

## Backup

### O que existe hoje

O serviço `db-backup` (container `erp-db-backup-prod`) em `docker-compose.prod.yml`:

- roda a cada deploy (`restart: "no"`, one-shot; o Coolify remove e recria todos
  os containers do app em cada deploy, então ele sempre roda de novo);
- faz `pg_dump -Fc` para `/backups/.parcial.dump`, valida com
  `pg_restore --list` e só então renomeia para `erp-<AAAAMMDDTHHMMSSZ>.dump`;
- mantém os **14 dumps mais recentes** (`ls -1t ... | tail -n +15 | xargs -r rm -f`);
- grava em **bind mount absoluto** `/data/erp/backups:/backups` — não em volume
  nomeado, justamente porque o Coolify descarta `external:`;
- é **fail-closed**: `db-init` espera `db-backup` terminar com sucesso
  (`service_completed_successfully`) e todo serviço espera `db-init`. Deploy que
  não consegue fazer backup não migra.

Esse encadeamento é guardado por `tests/unit/test_backup_antes_da_migration.py`.
Restore e verificação: [runbook de produção](../06-operacao/runbook-producao.md),
seções "Backup: é ele que autoriza a migration" e "RESTORE do dump".

### O que falta

O dump fica **no mesmo disco** do banco: protege contra migration ou escrita
errada, não contra a VPS morrer. Precisa sair da máquina. O projeto já usa
Cloudflare, então **R2** é o alvo natural: compatível com S3, barato, sem taxa de
saída. Nada disso está implementado.

**Backup nunca restaurado não é backup, é esperança.** O ensaio de restauração
é parte do trabalho, não um extra.

### Limite do dump atual

O dump só acontece em deploy. Entre dois deploys não há cópia nenhuma: num
desastre perde-se tudo desde o último deploy — pode ser mais que um dia. Para um
ERP com vendas e financeiro isso pode ser inaceitável quando houver dinheiro real.
Um dump agendado reduz a janela; não a elimina.

O que elimina a categoria inteira é Postgres gerenciado com PITR (recuperação a
qualquer segundo): Neon, Supabase, DigitalOcean Managed. Custa mensalidade e
tira a administração do banco de cima de uma VPS de 1 vCPU — provavelmente
vantagem dupla. **Decisão adiada.**

---

## Ordem de execução

| Fase | O quê | Estado |
|------|-------|--------|
| — | Nomes fixos de volume e rede no compose de prod | feito no compose; em prod o `external:` do `db_data` é descartado pelo Coolify |
| — | Deploy automático (`.github/workflows/deploy.yml` builda e publica as imagens no GHCR a cada push em `main` e aciona o Coolify) | feito |
| — | Migrations iniciais de `financeiro`/`notificacoes`, remoção do `create_all` | feito |
| — | Dump local antes de cada deploy (`db-backup`) | feito |
| 1 | Banco em bind mount absoluto (fecha as ameaças 1 e 2 de verdade) | pendente |
| 2 | Split do `docker-compose.data.yml` | pendente |
| 3 | Backup automático para R2 (fora da máquina) | pendente |
| 4 | **Ensaio de desastre**: backup → destruir tudo → restaurar → conferir | pendente |
| 5 | Avaliar Postgres gerenciado com PITR | pendente |

A fase 4 é a única que prova alguma coisa. As outras existem para ela poder
acontecer — e ela deve rodar enquanto os dados ainda são de seed, quando o custo
de errar é rodar o seed de novo.
