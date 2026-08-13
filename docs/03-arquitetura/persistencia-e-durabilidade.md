# Persistência e Durabilidade dos Dados

> Decisão de arquitetura sobre onde o banco vive, como ele sobrevive a deploys
> e o que ainda falta para o dado ser realmente durável.
>
> **Status:** ameaças 1 e 2 resolvidas (volumes com nome fixo, `db_data` external).
> O resto é planejado.
> **Contexto:** decidido enquanto a produção ainda roda só com dados de seed —
> a janela mais barata para mudar isso.

---

## O modelo de ameaça

Backup não é a primeira defesa. Das cinco formas de perder os dados, as três
mais prováveis são configuração, não catástrofe:

| # | Como o dado se perde | Chance | Estrago | Defesa |
|---|----------------------|--------|---------|--------|
| 1 | Volume órfão por troca do nome do projeto Compose | alta | total | `name:` fixo + `external: true` |
| 2 | `docker compose down -v` | média | total | `external: true` |
| 3 | Drift do `create_all` → migration destrutiva | média | parcial | Alembic dono do schema |
| 4 | VPS morre / falha de disco / provedor | baixa | total | backup fora da máquina |
| 5 | Query errada em produção | baixa | parcial | backup + PITR |

### 1. Volume órfão

Volume declarado sem `name:` recebe o nome do projeto como prefixo:
`<projeto>_db_data`. Quando o Coolify assume a stack, ele usa o nome de projeto
dele; pede um volume que não existe; o Docker cria um **novo e vazio**. O sistema
sobe funcionando e sem nenhum registro. Parece instalação nova.

Correção — 6 linhas, mata as ameaças 1 e 2:

```yaml
volumes:
  db_data:
    name: runaserp_db_data
    external: true
```

`external: true` significa "esse volume não é do Compose": ele não cria e o
`down -v` não apaga. A criação passa a ser um ato deliberado
(`docker volume create runaserp_db_data`), uma vez só.

### 3. Drift do `create_all`

Cinco serviços chamam `init_db()` → `Base.metadata.create_all` no startup:
`clientes`, `empresas`, `estoque`, `financeiro`, `notificacoes`. A convenção do
projeto proíbe isso explicitamente (ver CLAUDE.md → Database Migrations).

`create_all` não apaga nada — ele cria tabela que falta. O dano é indireto: o
schema passa a ser construído por um caminho que o Alembic não registrou. O
Alembic acredita estar na revisão X, a realidade é outra, e a próxima migration
autogerada compara os dois e "corrige" a diferença com `drop_column`.
**A perda acontece na migration seguinte, não no `create_all`.**

**Pré-requisito para remover:** `financeiro` e `notificacoes` têm **0 migrations**
— o `create_all` é a única coisa criando o schema deles. Remover antes de gerar
as migrations iniciais faz as tabelas nunca existirem.

| Serviço | Migrations | Chama `create_all` |
|---------|-----------:|--------------------|
| api-gateway | 3 | não |
| empresas | 2 | sim |
| clientes | 3 | sim |
| produtos | 4 | não |
| estoque | 4 | sim |
| vendas | 5 | não |
| financeiro | **0** | sim |
| notificacoes | **0** | sim |

---

## O banco como unidade de deploy separada

Objetivo declarado: rodar o banco num servidor à parte, no futuro.

**Isso já está 90% pronto.** Todo serviço alcança o banco por
`DATABASE_URL_<SERVICO>` — nenhum deles sabe que o Postgres é um container
vizinho. Para eles é uma string de conexão. O que ainda amarra é o banco estar
no mesmo arquivo de deploy do app.

### Três unidades em vez de duas

| Arquivo | Contém | Muda quando | Lido por |
|---------|--------|-------------|----------|
| `docker-compose.data.yml` | Postgres, Redis, RabbitMQ | quase nunca | Coolify |
| `docker-compose.prod.yml` | os 9 apps | todo merge | Coolify |
| `docker-compose.build.yml` | overlay de build | — | GitHub Actions |

As stacks se comunicam pela rede `runaserp_erp-network`, que já tem `name:` fixo
no compose — metade do trabalho já existe.

**Hoje:** as duas na mesma VPS. O app encontra `db:5432` exatamente como agora,
porque compartilham a rede Docker.

**Depois:** a stack `data` vai para outro host. Muda-se `DATABASE_URL_*` e
acrescenta-se `sslmode=require`. **O compose do app não muda uma linha.**

### O que se ganha

- deploy do app deixa de poder derrubar o banco — hoje pode
- atualizar a versão do Postgres não redeploya 9 aplicações
- `down -v` no app não alcança os volumes do banco
- migrar de host vira mudança de variável, não refatoração

### O que custa

O `depends_on: db` sai. Os apps passam a subir antes do banco estar pronto e
reiniciam até conseguir conectar. Isso é o comportamento **correto**: não existe
`depends_on` para um host remoto, e `restart: unless-stopped` já cobre. É a
mesma resiliência que será obrigatória quando o banco estiver do outro lado da
rede — melhor adquiri-la enquanto ele ainda está do lado.

---

## Backup

Backup no mesmo disco de 50 GB protege contra `DROP TABLE`, não contra a VPS
morrer. Precisa sair da máquina. O projeto já usa Cloudflare, então **R2** é o
alvo natural: compatível com S3, barato, sem taxa de saída.

**Backup nunca restaurado não é backup, é esperança.** O ensaio de restauração
é parte do trabalho, não um extra.

### Limite do dump periódico

Dump diário significa, num desastre, perder até 24h de movimento. Para um ERP
com vendas e financeiro isso pode ser inaceitável quando houver dinheiro real.

O que elimina a categoria inteira é Postgres gerenciado com PITR (recuperação a
qualquer segundo): Neon, Supabase, DigitalOcean Managed. Custa mensalidade e
tira a administração do banco de cima de uma VPS de 1 vCPU — provavelmente
vantagem dupla. **Decisão adiada** até o deploy automático estar fechado.

---

## Ordem de execução

O deploy automático vem primeiro; a infra de banco depois.

| Fase | O quê |
|------|-------|
| ✅ | Volumes com nome fixo, `db_data` external — feito junto com o deploy, já que é o deploy que decide esses nomes |
| — | **Deploy automático completo** (Coolify + GHCR) |
| 1 | Split do `docker-compose.data.yml` |
| 2 | Migrations iniciais de `financeiro`/`notificacoes`, depois remover `create_all` |
| 3 | Backup automático para R2 |
| 4 | **Ensaio de desastre**: backup → destruir tudo → restaurar → conferir |
| 5 | Avaliar Postgres gerenciado com PITR |

A fase 4 é a única que prova alguma coisa. As outras existem para ela poder
acontecer — e ela deve rodar enquanto os dados ainda são de seed, quando o custo
de errar é rodar o seed de novo.
