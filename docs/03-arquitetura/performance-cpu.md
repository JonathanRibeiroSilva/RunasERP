# Performance e Consumo de CPU - RunasERP

## 🔥 Problema: Alto Consumo de CPU em VPS

### Sintomas
- Containers FastAPI consumindo 50-80% de CPU em idle na VPS
- Desenvolvimento local: 15-20% de CPU
- Sistema lento e travamentos

> **A CONFIRMAR: os percentuais acima não têm medição registrada no repositório.**
> Não há coleta de métricas (ver "O que NÃO voltar a recomendar"); são observações
> de quem abriu o problema, não números reproduzíveis.

---

## 🐛 Causas Identificadas

### 1. **Uvicorn `--reload` (Principal Culpado)**

**O que faz:**
```python
uvicorn main:app --reload  # ❌ sem --reload-delay: vale o padrão do uvicorn
```

- 🔴 Monitor de arquivos ativo em `--reload` (o `uvicorn[standard]==0.53.0` dos
  requirements traz `watchfiles`; A CONFIRMAR: se o reloader em uso é o
  `watchfiles` ou o de `stat` por polling, e qual o intervalo padrão efetivo)
- 🔴 São **8 containers Python** com watchdog próprio: o `api-gateway` e os 7 de
  `services/` — o custo do polling é pago 8 vezes, não uma
  (A CONFIRMAR: nº de arquivos varridos por container, não medido)
- 🔴 Varredura contínua consome CPU (A CONFIRMAR: quanto, não foi medido)

**Solução aplicada:**
```python
uvicorn main:app --reload --reload-delay 2  # ✅ delay de 2s entre checagens
```

**Redução esperada:** A CONFIRMAR — o "40-50%" que constava aqui não tem medição
no repositório.

---

### 2. **CHOKIDAR_USEPOLLING no Frontend**

**O que faz:**
```yaml
CHOKIDAR_USEPOLLING: "true"  # Polling de arquivos .js/.jsx/.tsx
CHOKIDAR_INTERVAL: "1000"    # A cada 1 segundo
```

- 🟡 Necessário para hot-reload no Docker/Windows
- 🟡 A CONFIRMAR: o custo em CPU (constava "~5-10%", sem medição no repo)

**Otimização:** Mantido em dev, removido em produção

---

### 3. **Volumes Montados (Docker + Windows)**

```yaml
volumes:
  - ./api-gateway:/app  # Windows → WSL2 → Docker
```

- 🟡 I/O lento entre sistemas
- 🟡 Inotify não funciona bem, força polling

**Solução:** Remover volumes em staging/produção

---

## ✅ Otimizações Aplicadas

### **Desenvolvimento (docker-compose.dev.yml)**

```yaml
api-gateway:
  # docker-compose.dev.yml:247 (os 7 services usam a mesma forma, portas 8001-8007)
  command: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-delay 2
```

**Características:**
- ✅ Hot-reload continua funcionando
- ✅ Delay de 2s entre checagens (`--reload-delay 2`; o valor padrão do uvicorn não
  está fixado em nenhum arquivo do repo)
- ⚠️ A CONFIRMAR: a redução de CPU não foi medida — não há coleta de métricas no repo

---

### **Produção (docker-compose.prod.yml)**

Não existe arquivo de staging: os compose do repo são `build`, `cloudflare`,
`dev` e `prod`. O que segue é o tuning real que roda na VPS.

**Sem `--reload` e sem `--workers`:** nenhum serviço sobrescreve `command:` em
`docker-compose.prod.yml` (só `db-backup`, `db-init`, `redis` e `cloudflared`
trazem `command:`), então vale o `CMD` da imagem — `uvicorn main:app --host
0.0.0.0 --port <porta>` (`api-gateway/Dockerfile:26` e os sete
`services/*/Dockerfile`). Sem `--workers`, uvicorn sobe **1 worker por
container**.

```dockerfile
# api-gateway/Dockerfile:24-26
# No --reload: this is the production image. The dev stack overrides the
# command with its own --reload in docker-compose.dev.yml.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Teto por container** — anchor `x-limits` (`docker-compose.prod.yml:16-20`):

```yaml
x-limits: &limits
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
```

O anchor alcança o `api-gateway`, os 7 microsserviços (via `x-service`,
`docker-compose.prod.yml:25`), `redis` (`:258`), `rabbitmq` (`:280`),
`frontend` (`:519`) e `cloudflared` (`:569`). O `db` **não** usa o anchor, mas
também não é ilimitado: tem o próprio bloco com `cpus: '1.0'` e `memory: 1G`
(`docker-compose.prod.yml:79-83`) — 1.0 porque o Docker recusa um limite de
CPU acima do total de cores do host.

**Hospedagem:** a VPS é de **1 vCPU / 4 GB** (cabeçalho do
`docker-compose.prod.yml:4`) e por isso não constrói imagem nenhuma — o CI
publica no ghcr e o host só faz `pull`.

**Sem volume de código:** produção usa a imagem, não bind mount, então nada de
polling de arquivo (causas nº 2 e nº 3 acima não existem aqui).

---

### **Healthchecks: cadência curta só no boot**

`start_interval` é o intervalo *antes* do primeiro `healthy`; `interval` só
passa a valer depois. A combinação em produção é **`start_interval: 5s` +
`interval: 60s`** (`docker-compose.prod.yml:333-356` para o gateway):

```yaml
start_interval: 5s
interval: 60s
start_period: 60s
timeout: 10s
retries: 3
```

Por que não sondar de 5 em 5 para sempre: cada probe é um `exec` via dockerd, e
12 exec/min nesta VPS de 1 vCPU levaram **o daemon sozinho a 89% de CPU**. O
deploy rápido só precisa da cadência curta até o primeiro `healthy` — depois
disso, 60s bastam.

Por que não voltar `interval` para 30s: no deploy `u143gkg9hauofqlaojmw0adz` o
gateway levou 31,0s entre `Started` e `Healthy`. Passado o `start_period`,
`interval: 5s` com `retries: 3` marca o container como unhealthy com 15s de
atraso — e o `frontend`, que depende dele healthy, nunca sobe. Numa VPS de
1 vCPU subindo os containers ao mesmo tempo, 15s de variação é rotina.

Quem usa `start_interval` hoje: `db`, `redis`, `rabbitmq`, `api-gateway-prod` e
`frontend-prod` — exatamente os que alguém espera para subir. Os 7
microsserviços ficam só com `interval: 60s`.

---

## 🚀 Aplicando as Mudanças

### **1. Desenvolvimento (aplicado):**
```bash
# --reload-delay 2 já está no `command:` do docker-compose.dev.yml; um `restart`
# não relê o compose, então recrie os containers
docker compose -f docker-compose.dev.yml up -d
```

**Redução de consumo esperada:** A CONFIRMAR (sem medição no repo).

---

## 🎯 Alvos de Performance

Resgatados de `GUIA_PERFORMANCE.md` (apagado). São **alvos**, não medições: o
projeto não tem coleta de métricas (nenhum Prometheus, Grafana ou APM no repo),
então não existe coluna "atual" com fonte verificável.

| Métrica | Alvo |
|---------|------|
| Tempo de resposta API | < 200ms |
| Tempo de carregamento frontend | < 3s |
| Consumo de CPU (dev) | < 15% |
| Consumo de CPU (prod) | < 10% |
| Queries SQL | < 50ms |
| Bundle size | < 500KB |

### Por que o alvo é por serviço, mas o orçamento não é

Os alvos acima valem **por container**, e a stack de produção sobe 13
containers de longa duração (`api-gateway` + os 7 de `services/`, mais
`db`, `redis`, `rabbitmq`, `frontend` e `cloudflared`; `db-backup` e `db-init`
rodam uma vez e saem). Todos dividem **1 vCPU / 4 GB**, com o teto por
container descrito em [Produção](#produção-docker-composeprodyml).
É a mesma multiplicação que aparece na causa nº 1 acima: o custo de qualquer
otimização — ou de qualquer desperdício — é pago 8 vezes, não uma.

---

## ⚠️ O que NÃO voltar a recomendar aqui

O `GUIA_PERFORMANCE.md` foi apagado porque suas recomendações eram contraditas
pelo próprio código. Esta página é a fonte que prevalece; não reintroduza:

- **Celery** — `celery==5.6.3` está nos sete `services/*/requirements.txt`, mas
  **nenhum `.py` do repo importa celery** e não há container de worker/beat em
  `docker-compose.prod.yml`: é dependência morta, não arquitetura. O que
  roda para trabalho periódico é (a) cron do host batendo num endpoint (ver
  comentário em `api-gateway/routers/plataforma.py:489`) e (b) dois loops
  `asyncio` dentro do próprio processo do `vendas` (`services/vendas/main.py`,
  `lifespan`: pagamentos pendentes a cada 60s, reconciliação de estoque a cada
  120s) — nenhum dos dois usa Celery. **Publicação de eventos
  em RabbitMQ também não roda**: `services/*/events/publisher.py` existe, mas
  nenhum código chama `publish()` fora da própria definição — ver
  `docs/03-arquitetura/comunicacao.md`, seção 2.
- **Prometheus / Grafana / APM** — não há coleta de métricas no projeto. Foi
  por isso que a tabela de alvos acima não tem coluna "atual".
- **Exemplos de SQLAlchemy síncrono** — os serviços são FastAPI async; um
  exemplo bloqueante copiado daquele guia trava o único worker do container.

Se uma dessas ferramentas for adotada um dia, o gatilho é o código entrar no
repo primeiro — e a VPS de 1 vCPU é o limite prático para qualquer
monitoramento self-hosted.

