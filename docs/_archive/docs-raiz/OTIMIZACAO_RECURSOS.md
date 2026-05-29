# 🚀 Otimização de Recursos - Runas ERP

> **Documento de análise e estratégias para redução de consumo de CPU/RAM**
> 
> **Última atualização**: 27/05/2026
> **Arquivado em**: 28/05/2026 — Itens pendentes absorvidos em `CHECKLIST_DESENVOLVIMENTO.md` e `FEATURES-FUTURAS.md`

---

## 📊 Problema Identificado

A arquitetura de microsserviços consome muitos recursos em VPS de baixo custo.

### Consumo Estimado (Antes da Consolidação)

| Componente | RAM | Observações |
|------------|-----|-------------|
| API Gateway | 100-150 MB | Python + FastAPI |
| Cada Microsserviço (x6) | 100-150 MB cada | Python + FastAPI |
| Cada PostgreSQL (x6) | 50-100 MB cada | Banco dedicado |
| Redis | 30-50 MB | Cache |
| Frontend (Nginx) | 20-30 MB | Servindo estáticos |
| **TOTAL** | **~1.2-1.8 GB** | **Sem ninguém usando** |

---

## ✅ Estratégia 1: Banco de Dados Unificado — IMPLEMENTADO

**Economia**: ~228 MB RAM, 85% de redução nos containers de banco  
**Status**: Concluído em 27/05/2026

Um único PostgreSQL com schemas separados por serviço:
- `gateway`, `clientes`, `produtos`, `estoque`, `vendas`, `financeiro`, `notificacoes`, `evolution`

Connection string com `search_path`:
```
postgresql+asyncpg://erp:erp@db:5432/erp?options=-csearch_path%3Dgateway
```

---

## 🔴 Estratégia 2: Otimizações de Runtime (Pendente)

### Imagens Alpine
```dockerfile
# Antes
FROM python:3.11
# Depois
FROM python:3.11-alpine
# Economia: ~50-100 MB por container
```

### Limitar Workers do Uvicorn
```python
uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1, log_level="warning")
```

### Otimizar Pool de Conexões
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### Limites de Recursos no Docker Compose
```yaml
services:
  clientes-service:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.25'
          memory: 128M
```

### Configurar PostgreSQL para Baixo Consumo
```conf
shared_buffers = 128MB
effective_cache_size = 256MB
work_mem = 4MB
max_connections = 50
```

**Economia estimada**: -200 MB RAM, -10% CPU

---

## 🔴 Estratégia 3: Consolidar Microsserviços (Para VPS Pequenas)

### Opção A: Monolito Modular
Consolidar todos os serviços em um único FastAPI com módulos internos.  
**Economia**: -800 MB RAM, -40% CPU  
**Custo**: 1 semana de refatoração

### Opção B: Microsserviços Agrupados
- Core Service (Clientes + Produtos)
- Inventory Service (Estoque)
- Sales Service (Vendas + Financeiro)
- Notifications Service

**Economia**: -400 MB RAM, -20% CPU  
**Custo**: 1 dia

---

## 🎯 Configurações por Tipo de VPS

### VPS Pequena (1 vCPU / 1GB RAM)
**Recomendação**: Monolito Modular  
**Consumo alvo**: ~900 MB RAM

### VPS Média (2 vCPU / 2GB RAM)
**Recomendação**: Banco Unificado + Microsserviços Agrupados  
**Consumo alvo**: ~1.8 GB RAM

### VPS Grande (4 vCPU / 4GB RAM)
**Recomendação**: Microsserviços com Banco Unificado (arquitetura atual)

---

## 📊 Comparativo de Estratégias

| Estratégia | Economia RAM | Economia CPU | Complexidade | Tempo |
|------------|--------------|--------------|--------------|-------|
| Banco Unificado | 400 MB | 15% | Baixa | ✅ FEITO |
| Imagens Alpine | 300 MB | 5% | Baixa | 1h |
| Limites Docker | 0 MB* | 0%* | Baixa | 30min |
| Reduzir Workers | 200 MB | 10% | Baixa | 1h |
| Microsserviços Agrupados | 400 MB | 20% | Média | 1 dia |
| Monolito Modular | 800 MB | 40% | Alta | 1 semana |

---

## 🔍 Comandos de Monitoramento

```bash
# Ver consumo por container
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Quando escalar verticalmente (aumentar VPS):
# CPU > 80% consistente
# RAM > 90% consistente
# Swap sendo usado
# Latência > 500ms
```

---

**Documento criado em**: 27/05/2026  
**Arquivado em**: 28/05/2026
