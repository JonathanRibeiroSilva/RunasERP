# Jobs de Automação - Serviço de Vendas

Este diretório contém jobs de automação para o serviço de vendas da loja online.

---

## 📋 Lista de Jobs

### 1. `limpar_reservas.py`
**Propósito**: Limpa reservas temporárias de estoque expiradas.

**Frequência**: A cada 1 minuto

**Descrição**: Remove reservas temporárias (carrinho e checkout) que expiraram do banco de dados, liberando estoque para outros clientes.

**Comando**:
```bash
python jobs/limpar_reservas.py
```

---

### 2. `verificar_timeouts_separacao.py`
**Propósito**: Verifica timeouts de separação de vendas CONFIRMADAS.

**Frequência**: A cada 1 hora

**Descrição**: 
- **12h**: Alerta no log (aviso para separar)
- **24h**: Alerta crítico no log
- **48h**: **Auto-cancelamento** da venda + liberação de estoque + notificação ao cliente

**Comando**:
```bash
python jobs/verificar_timeouts_separacao.py
```

---

### 3. `limpar_carrinhos_abandonados.py`
**Propósito**: Limpa carrinhos abandonados do Redis (>7 dias sem acesso).

**Frequência**: Diariamente (recomendado: 3h da manhã)

**Descrição**: Remove carrinhos que não foram acessados há mais de 7 dias, liberando memória do Redis.

**Comando**:
```bash
python jobs/limpar_carrinhos_abandonados.py
```

---

### 4. `verificar_pagamentos_pendentes.py`
**Propósito**: Cancela vendas com pagamento online pendente que expiraram (>5min).

**Frequência**: A cada 5 minutos

**Descrição**: Vendas com status `PENDENTE_PAGAMENTO` (aguardando pagamento Mercado Pago) que não receberam confirmação em 5 minutos são automaticamente canceladas, liberando estoque e notificando o cliente.

**Comando**:
```bash
python jobs/verificar_pagamentos_pendentes.py
```

---

## ⚙️ Configuração

### Opção 1: Cron (Linux/MacOS)

Editar crontab:
```bash
crontab -e
```

Adicionar as seguintes linhas:
```bash
# Limpar reservas temporárias expiradas (a cada 1 minuto)
* * * * * cd /path/to/services/vendas && python jobs/limpar_reservas.py >> /var/log/vendas/limpar_reservas.log 2>&1

# Verificar timeouts de separação (a cada 1 hora)
0 * * * * cd /path/to/services/vendas && python jobs/verificar_timeouts_separacao.py >> /var/log/vendas/timeouts_separacao.log 2>&1

# Limpar carrinhos abandonados (diariamente às 3h)
0 3 * * * cd /path/to/services/vendas && python jobs/limpar_carrinhos_abandonados.py >> /var/log/vendas/carrinhos_abandonados.log 2>&1

# Verificar pagamentos pendentes (a cada 5 minutos)
*/5 * * * * cd /path/to/services/vendas && python jobs/verificar_pagamentos_pendentes.py >> /var/log/vendas/pagamentos_pendentes.log 2>&1
```

**Nota**: Substitua `/path/to/services/vendas` pelo caminho absoluto do serviço.

---

### Opção 2: Task Scheduler (Windows)

#### Job 1: Limpar Reservas (1 minuto)
1. Abrir **Task Scheduler** (Agendador de Tarefas)
2. Criar Tarefa Básica
3. Nome: "Vendas - Limpar Reservas"
4. Gatilho: **Diariamente**, Repetir a cada: **1 minuto**, Duração: **Indefinidamente**
5. Ação: **Iniciar um programa**
   - Programa: `python.exe`
   - Argumentos: `jobs\limpar_reservas.py`
   - Iniciar em: `E:\GitHub\ERP\RunasERP\services\vendas`

#### Job 2: Verificar Timeouts (1 hora)
1. Nome: "Vendas - Timeouts Separação"
2. Gatilho: **Diariamente**, Repetir a cada: **1 hora**, Duração: **Indefinidamente**
3. Ação: 
   - Programa: `python.exe`
   - Argumentos: `jobs\verificar_timeouts_separacao.py`
   - Iniciar em: `E:\GitHub\ERP\RunasERP\services\vendas`

#### Job 3: Limpar Carrinhos (Diário)
1. Nome: "Vendas - Limpar Carrinhos"
2. Gatilho: **Diariamente às 3:00**
3. Ação: 
   - Programa: `python.exe`
   - Argumentos: `jobs\limpar_carrinhos_abandonados.py`
   - Iniciar em: `E:\GitHub\ERP\RunasERP\services\vendas`

#### Job 4: Pagamentos Pendentes (5 minutos)
1. Nome: "Vendas - Pagamentos Pendentes"
2. Gatilho: **Diariamente**, Repetir a cada: **5 minutos**, Duração: **Indefinidamente**
3. Ação: 
   - Programa: `python.exe`
   - Argumentos: `jobs\verificar_pagamentos_pendentes.py`
   - Iniciar em: `E:\GitHub\ERP\RunasERP\services\vendas`

---

### Opção 3: Docker + Supervisor

Se estiver usando Docker, adicione o Supervisor para gerenciar os jobs:

**supervisord.conf**:
```ini
[program:limpar_reservas]
command=python jobs/limpar_reservas.py
directory=/app
autostart=true
autorestart=true
startsecs=60
stdout_logfile=/var/log/supervisor/limpar_reservas.log
stderr_logfile=/var/log/supervisor/limpar_reservas.err.log

[program:verificar_timeouts]
command=python jobs/verificar_timeouts_separacao.py
directory=/app
autostart=true
autorestart=true
startsecs=3600
stdout_logfile=/var/log/supervisor/verificar_timeouts.log
stderr_logfile=/var/log/supervisor/verificar_timeouts.err.log

[program:limpar_carrinhos]
command=python jobs/limpar_carrinhos_abandonados.py
directory=/app
autostart=true
autorestart=true
startsecs=86400
stdout_logfile=/var/log/supervisor/limpar_carrinhos.log
stderr_logfile=/var/log/supervisor/limpar_carrinhos.err.log

[program:verificar_pagamentos]
command=python jobs/verificar_pagamentos_pendentes.py
directory=/app
autostart=true
autorestart=true
startsecs=300
stdout_logfile=/var/log/supervisor/verificar_pagamentos.log
stderr_logfile=/var/log/supervisor/verificar_pagamentos.err.log
```

---

### Opção 4: Celery (Futuro)

Para produção, recomenda-se usar **Celery** com **Redis** como broker:

```python
# celery_app.py
from celery import Celery
from celery.schedules import crontab

app = Celery('vendas_jobs', broker='redis://localhost:6379/0')

app.conf.beat_schedule = {
    'limpar-reservas-a-cada-minuto': {
        'task': 'jobs.limpar_reservas',
        'schedule': 60.0,  # 1 minuto
    },
    'verificar-timeouts-a-cada-hora': {
        'task': 'jobs.verificar_timeouts',
        'schedule': crontab(minute=0),  # A cada hora
    },
    'limpar-carrinhos-diariamente': {
        'task': 'jobs.limpar_carrinhos',
        'schedule': crontab(hour=3, minute=0),  # 3h da manhã
    },
    'verificar-pagamentos-5min': {
        'task': 'jobs.verificar_pagamentos',
        'schedule': 300.0,  # 5 minutos
    },
}
```

---

## 📊 Monitoramento

### Logs Estruturados

Todos os jobs usam **structlog** para logs estruturados. Exemplo de saída:

```json
{
  "event": "job_limpar_reservas_concluido",
  "reservas_removidas": 15,
  "timestamp": "2026-06-11T14:30:00Z"
}
```

### Métricas Importantes

- **limpar_reservas**: `reservas_removidas`
- **verificar_timeouts**: `alertas_12h`, `alertas_24h`, `canceladas_48h`
- **limpar_carrinhos**: `carrinhos_verificados`, `carrinhos_removidos`
- **verificar_pagamentos**: `vendas_verificadas`, `vendas_canceladas`

---

## 🔧 Troubleshooting

### Job não está rodando
1. Verificar se o Python está no PATH
2. Verificar se as dependências estão instaladas: `pip install -r requirements.txt`
3. Verificar logs de erro
4. Testar manualmente: `python jobs/<nome_do_job>.py`

### Erros de conexão com banco
1. Verificar `DATABASE_URL` no `.env`
2. Verificar se o banco está acessível
3. Verificar credenciais

### Erros de conexão com Redis
1. Verificar `REDIS_URL` no `.env`
2. Verificar se o Redis está rodando: `redis-cli ping`

---

## 🧪 Testes

Para testar um job manualmente:

```bash
cd /path/to/services/vendas
python jobs/limpar_reservas.py
```

Verificar saída no log e confirmar que funcionou corretamente.

---

## 📝 Notas

- Todos os jobs são **idempotentes**: podem ser executados múltiplas vezes sem causar problemas
- Jobs usam transações do SQLAlchemy para garantir consistência
- Erros são logados mas não param a execução dos próximos itens
- Jobs são **stateless**: não dependem de estado anterior

---

## 🚀 Próximos Passos

- [ ] Implementar sistema de notificações internas para alertas de 12h/24h
- [ ] Adicionar métricas para Prometheus/Grafana
- [ ] Implementar retry automático em caso de falha
- [ ] Adicionar health check para monitorar se jobs estão rodando
