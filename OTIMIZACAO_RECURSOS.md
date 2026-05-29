# 🚀 Otimização de Recursos - Runas ERP

> **Documento de análise e estratégias para redução de consumo de CPU/RAM**
> 
> **Última atualização**: 27/05/2026

---

## 📊 Problema Identificado

A arquitetura atual de microsserviços está consumindo muitos recursos (CPU/RAM), o que pode inviabilizar hospedagem em VPS de baixo custo.

### Arquitetura Atual

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Compose                        │
├─────────────────────────────────────────────────────────────┤
│  API Gateway (FastAPI)                                       │
│  ├─ Clientes Service (FastAPI + PostgreSQL)                 │
│  ├─ Produtos Service (FastAPI + PostgreSQL)                 │
│  ├─ Estoque Service (FastAPI + PostgreSQL)                  │
│  ├─ Vendas Service (FastAPI + PostgreSQL)                   │
│  ├─ Financeiro Service (FastAPI + PostgreSQL)               │
│  ├─ Notificações Service (FastAPI + PostgreSQL)             │
│  Frontend (Vite + React + Nginx)                            │
│  Redis (Cache)                                               │
│  PostgreSQL x6 (um por serviço)                             │
└─────────────────────────────────────────────────────────────┘

Total: ~14 containers rodando simultaneamente
```

### Consumo Estimado

| Componente | CPU (ocioso) | RAM | Observações |
|------------|-----------|-----|-------------|
| API Gateway | 5-10% | 100-150 MB | Python + FastAPI |
| Cada Microsserviço (x6) | 5-10% cada | 100-150 MB cada | Python + FastAPI |
| Cada PostgreSQL (x6) | 2-5% cada | 50-100 MB cada | Banco dedicado |
| Redis | 1-2% | 30-50 MB | Cache |
| Frontend (Nginx) | 1-2% | 20-30 MB | Servindo estáticos |
| **TOTAL** | **50-80%** | **1.2-1.8 GB** | **Sem ninguém usando!** |

> **Idle/Ocioso**: Sistema rodando mas sem usuários ativos, sem requisições sendo processadas.
> 
> **Em Carga**: Com usuários reais usando o sistema (fazendo cadastros, vendas, consultas).

**Problema**: Em uma VPS de 2 vCPU / 2GB RAM, o sistema já está no limite **mesmo sem ninguém usando**. Quando tiver usuários reais, o consumo será ainda maior!

---

## 🎯 Estratégias de Otimização

### Estratégia 1: Banco de Dados Unificado (Recomendado para MVP)

**Conceito**: Usar um único PostgreSQL com schemas separados ao invés de 6 instâncias.

#### Vantagens
- ✅ Reduz 5 containers PostgreSQL
- ✅ Economiza ~250-500 MB de RAM
- ✅ Reduz 10-25% de CPU
- ✅ Mantém isolamento lógico via schemas
- ✅ Facilita backups e manutenção
- ✅ Permite transações entre serviços (se necessário)

#### Desvantagens
- ⚠️ Menos isolamento (mas schemas ainda separam)
- ⚠️ Ponto único de falha (mas já é comum em MVP)

#### Implementação

**Como Funciona:**

Ao invés de ter 6 bancos PostgreSQL separados (um por microsserviço), você tem **1 único PostgreSQL** com **6 schemas separados** (como "pastas" dentro do banco).

```
┌─────────────────────────────────────────────────────────┐
│              PostgreSQL Único (Container)               │
├─────────────────────────────────────────────────────────┤
│  Schema: clientes                                       │
│    ├─ Tabela: clientes                                 │
│    ├─ Tabela: enderecos                                │
│    └─ Tabela: ...                                      │
│                                                         │
│  Schema: produtos                                       │
│    ├─ Tabela: categorias                               │
│    ├─ Tabela: produtos                                 │
│    ├─ Tabela: variantes                                │
│    └─ Tabela: ...                                      │
│                                                         │
│  Schema: estoque                                        │
│    ├─ Tabela: estoque                                  │
│    ├─ Tabela: movimentacoes                            │
│    └─ Tabela: ...                                      │
│                                                         │
│  Schema: vendas                                         │
│  Schema: financeiro                                     │
│  Schema: notificacoes                                   │
└─────────────────────────────────────────────────────────┘
```

**Cada microsserviço continua independente**, mas todos apontam para o mesmo PostgreSQL usando schemas diferentes:

```yaml
# docker-compose.yml
services:
  # UM ÚNICO POSTGRESQL
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: runas_erp
      POSTGRES_USER: runas
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-schemas.sql:/docker-entrypoint-initdb.d/init.sql

  # MICROSSERVIÇO DE CLIENTES - Usa schema "clientes"
  clientes-service:
    environment:
      DATABASE_URL: postgresql://runas:${DB_PASSWORD}@postgres:5432/runas_erp?options=-c%20search_path=clientes

  # MICROSSERVIÇO DE PRODUTOS - Usa schema "produtos"
  produtos-service:
    environment:
      DATABASE_URL: postgresql://runas:${DB_PASSWORD}@postgres:5432/runas_erp?options=-c%20search_path=produtos

  # MICROSSERVIÇO DE ESTOQUE - Usa schema "estoque"
  estoque-service:
    environment:
      DATABASE_URL: postgresql://runas:${DB_PASSWORD}@postgres:5432/runas_erp?options=-c%20search_path=estoque

  # E assim por diante...
```

**Script de Inicialização:**

```sql
-- init-schemas.sql
-- Cria os schemas (como "pastas") dentro do banco
CREATE SCHEMA IF NOT EXISTS clientes;
CREATE SCHEMA IF NOT EXISTS produtos;
CREATE SCHEMA IF NOT EXISTS estoque;
CREATE SCHEMA IF NOT EXISTS vendas;
CREATE SCHEMA IF NOT EXISTS financeiro;
CREATE SCHEMA IF NOT EXISTS notificacoes;

-- Garante permissões
GRANT ALL ON SCHEMA clientes TO runas;
GRANT ALL ON SCHEMA produtos TO runas;
GRANT ALL ON SCHEMA estoque TO runas;
GRANT ALL ON SCHEMA vendas TO runas;
GRANT ALL ON SCHEMA financeiro TO runas;
GRANT ALL ON SCHEMA notificacoes TO runas;
```

**O que muda no código dos microsserviços?**

**NADA!** O código continua exatamente igual. A única mudança é a connection string:

```python
# Antes (banco separado)
DATABASE_URL = "postgresql://user:pass@clientes-db:5432/clientes"

# Depois (banco unificado com schema)
DATABASE_URL = "postgresql://user:pass@postgres:5432/runas_erp?options=-c%20search_path=clientes"
```

O SQLAlchemy/Alembic automaticamente usa o schema correto. Suas tabelas continuam isoladas:

```python
# services/clientes/models/cliente.py
class Cliente(Base):
    __tablename__ = "clientes"  # Vai para schema "clientes"
    # ...

# services/produtos/models/produto.py  
class Produto(Base):
    __tablename__ = "produtos"  # Vai para schema "produtos"
    # ...
```

**Isolamento Mantido:**

- ✅ Cada microsserviço só vê suas próprias tabelas
- ✅ Não há risco de conflito de nomes (clientes.id vs produtos.id)
- ✅ Migrations continuam independentes por serviço
- ✅ Backups podem ser feitos por schema se necessário

**Vantagens:**

- ✅ Economiza 5 containers PostgreSQL
- ✅ Economiza ~400-500 MB de RAM
- ✅ Mais fácil fazer backup (um comando ao invés de 6)
- ✅ Mais fácil fazer restore
- ✅ Permite queries entre schemas se necessário (ex: relatórios)

**Desvantagens:**

- ⚠️ Se o PostgreSQL cair, todos os serviços ficam sem banco (mas isso já acontece em produção normalmente)
- ⚠️ Menos isolamento físico (mas schemas ainda isolam logicamente)


**Economia Estimada**: -400 MB RAM, -15% CPU

---

### Estratégia 2: Consolidar Microsserviços (Para VPS Pequenas)

**Conceito**: Agrupar serviços relacionados em um único processo.

#### Opção A: Monolito Modular (Mais Agressivo)

```
┌─────────────────────────────────────────┐
│         Runas ERP Backend               │
│  ┌───────────────────────────────────┐  │
│  │  FastAPI Application              │  │
│  │  ├─ /api/clientes                 │  │
│  │  ├─ /api/produtos                 │  │
│  │  ├─ /api/estoque                  │  │
│  │  ├─ /api/vendas                   │  │
│  │  ├─ /api/financeiro               │  │
│  │  └─ /api/notificacoes             │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

Total: 3 containers (Backend + PostgreSQL + Redis)
```

**Economia Estimada**: -800 MB RAM, -40% CPU

#### Opção B: Microsserviços Agrupados (Moderado)

```
┌─────────────────────────────────────────┐
│  Core Service (Clientes + Produtos)    │
│  Inventory Service (Estoque)           │
│  Sales Service (Vendas + Financeiro)   │
│  Notifications Service                  │
└─────────────────────────────────────────┘

Total: 6 containers (4 serviços + PostgreSQL + Redis)
```

**Economia Estimada**: -400 MB RAM, -20% CPU

---

### Estratégia 3: Otimizações de Runtime

#### 3.1. Usar Imagens Alpine

```dockerfile
# Antes
FROM python:3.11

# Depois
FROM python:3.11-alpine

# Economia: ~50-100 MB por container
```

#### 3.2. Limitar Recursos no Docker Compose

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

#### 3.3. Configurar Workers do Uvicorn

```python
# main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Reduzir de 4 para 1 em ambiente de baixo recurso
        log_level="warning"  # Reduzir logs
    )
```

#### 3.4. Otimizar Pool de Conexões PostgreSQL

```python
# database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,        # Reduzir de 20 para 5
    max_overflow=5,     # Reduzir de 10 para 5
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

#### 3.5. Configurar PostgreSQL para Baixo Consumo

```conf
# postgresql.conf
shared_buffers = 128MB          # Padrão: 128MB
effective_cache_size = 256MB    # Padrão: 4GB
maintenance_work_mem = 64MB     # Padrão: 64MB
work_mem = 4MB                  # Padrão: 4MB
max_connections = 50            # Padrão: 100
```

**Economia Estimada**: -200 MB RAM, -10% CPU

---

### Estratégia 4: Lazy Loading de Serviços

**Conceito**: Não iniciar todos os serviços, apenas os essenciais.

```yaml
# docker-compose.prod-minimal.yml
services:
  postgres:
    # ...
  
  redis:
    # ...
  
  api-gateway:
    # ...
  
  clientes-service:
    # ...
  
  produtos-service:
    # ...
  
  # Comentar serviços não essenciais inicialmente
  # vendas-service:
  # financeiro-service:
  # notificacoes-service:
```

**Economia Estimada**: -300 MB RAM por serviço desabilitado

---

## 📋 Plano de Ação Recomendado

### Fase 1: Otimizações Rápidas (1-2 horas)

1. ✅ **Banco de Dados Unificado**
   - Criar `init-schemas.sql`
   - Atualizar `docker-compose.yml`
   - Atualizar variáveis de ambiente
   - Testar migração

2. ✅ **Imagens Alpine**
   - Atualizar todos os Dockerfiles
   - Rebuild das imagens

3. ✅ **Limites de Recursos**
   - Adicionar `deploy.resources` no docker-compose
   - Testar com carga

4. ✅ **Reduzir Workers**
   - Configurar `workers=1` em todos os serviços
   - Ajustar pool de conexões

**Economia Esperada**: -600 MB RAM, -25% CPU

---

### Fase 2: Otimizações Médias (1 dia)

1. ✅ **Consolidar Microsserviços Relacionados**
   - Agrupar Vendas + Financeiro
   - Agrupar Clientes + Produtos (opcional)

2. ✅ **Otimizar PostgreSQL**
   - Aplicar configurações de baixo consumo
   - Ajustar autovacuum

3. ✅ **Implementar Cache Agressivo**
   - Cache de queries frequentes no Redis
   - TTL adequado por tipo de dado

**Economia Esperada**: -400 MB RAM, -15% CPU adicional

---

### Fase 3: Refatoração Profunda (1 semana)

1. ✅ **Monolito Modular**
   - Consolidar todos os serviços em um único FastAPI
   - Manter estrutura modular internamente
   - Facilitar deploy e manutenção

2. ✅ **Otimizar Queries**
   - Adicionar índices estratégicos
   - Usar select_related/joinedload
   - Implementar paginação eficiente

3. ✅ **Implementar Lazy Loading**
   - Carregar dados sob demanda
   - Evitar N+1 queries

**Economia Esperada**: -800 MB RAM, -40% CPU adicional

---

## 🎯 Configurações por Tipo de VPS

### VPS Pequena (1 vCPU / 1GB RAM)

**Recomendação**: Monolito Modular

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 256M
  
  redis:
    deploy:
      resources:
        limits:
          memory: 64M
  
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
  
  frontend:
    deploy:
      resources:
        limits:
          memory: 64M
```

**Consumo Total**: ~900 MB RAM, 60-70% CPU em carga

> **Em carga**: Com 5-10 usuários simultâneos fazendo operações normais (cadastros, consultas, vendas)

---

### VPS Média (2 vCPU / 2GB RAM)

**Recomendação**: Banco Unificado + Microsserviços Agrupados

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 512M
  
  redis:
    deploy:
      resources:
        limits:
          memory: 128M
  
  core-service:  # Clientes + Produtos
    deploy:
      resources:
        limits:
          memory: 384M
  
  inventory-service:  # Estoque
    deploy:
      resources:
        limits:
          memory: 256M
  
  sales-service:  # Vendas + Financeiro
    deploy:
      resources:
        limits:
          memory: 384M
  
  notifications-service:
    deploy:
      resources:
        limits:
          memory: 128M
```

**Consumo Total**: ~1.8 GB RAM, 50-60% CPU em carga

> **Em carga**: Com 10-20 usuários simultâneos fazendo operações normais

---

### VPS Grande (4 vCPU / 4GB RAM)

**Recomendação**: Microsserviços com Banco Unificado

```yaml
# Arquitetura atual com banco unificado
# Todos os microsserviços separados
# Limites mais generosos
```

**Consumo Total**: ~2.5 GB RAM, 40-50% CPU em carga

---

## 🔍 Monitoramento de Recursos

### Comandos Úteis

```bash
# Ver consumo de recursos por container
docker stats

# Ver consumo detalhado
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Logs de um serviço específico
docker-compose logs -f clientes-service

# Verificar health dos containers
docker-compose ps
```

### Métricas a Monitorar

- **CPU**: Deve ficar abaixo de 70% em operação normal
- **RAM**: Deve ter pelo menos 20% livre
- **Disco**: Monitorar crescimento do banco de dados
- **Rede**: Latência entre serviços

---

## 📊 Comparativo de Estratégias

| Estratégia | Economia RAM | Economia CPU | Complexidade | Tempo |
|------------|--------------|--------------|--------------|-------|
| Banco Unificado | 400 MB | 15% | Baixa | 2h |
| Imagens Alpine | 300 MB | 5% | Baixa | 1h |
| Limites Docker | 0 MB* | 0%* | Baixa | 30min |
| Reduzir Workers | 200 MB | 10% | Baixa | 1h |
| Microsserviços Agrupados | 400 MB | 20% | Média | 1 dia |
| Monolito Modular | 800 MB | 40% | Alta | 1 semana |

*Limites Docker não economizam, mas previnem overconsumption

---

## ✅ Checklist de Implementação

### Otimizações Imediatas
- [ ] Implementar banco de dados unificado
- [ ] Migrar para imagens Alpine
- [ ] Adicionar limites de recursos no docker-compose
- [ ] Reduzir workers do Uvicorn para 1
- [ ] Otimizar pool de conexões PostgreSQL
- [ ] Configurar PostgreSQL para baixo consumo
- [ ] Reduzir nível de logs para WARNING

### Otimizações de Médio Prazo
- [ ] Consolidar serviços relacionados
- [ ] Implementar cache agressivo no Redis
- [ ] Otimizar queries com índices
- [ ] Implementar paginação eficiente
- [ ] Lazy loading de dados

### Otimizações de Longo Prazo
- [ ] Avaliar migração para monolito modular
- [ ] Implementar CDN para assets estáticos
- [ ] Considerar serverless para serviços esporádicos
- [ ] Implementar auto-scaling (se necessário)

---

## 🚨 Alertas e Considerações

### ⚠️ Trade-offs

1. **Banco Unificado**: Menos isolamento, mas muito mais eficiente
2. **Menos Workers**: Menor throughput, mas suficiente para MVP
3. **Monolito**: Perde benefícios de microsserviços, mas ganha simplicidade

### 🏢 Multi-Tenant

**Status Atual**: O sistema é **single-tenant** (uma empresa por instalação).

**O que isso significa:**
- Cada cliente precisa de sua própria instalação completa do Runas ERP
- Não há campo `empresa_id` ou `tenant_id` nas tabelas
- Não há isolamento de dados entre múltiplas empresas
- Cada instalação tem seu próprio banco de dados

**Arquitetura Atual (Single-Tenant):**
```
Empresa A                    Empresa B                    Empresa C
┌──────────────┐            ┌──────────────┐            ┌──────────────┐
│ Runas ERP    │            │ Runas ERP    │            │ Runas ERP    │
│ ├─ Banco A   │            │ ├─ Banco B   │            │ ├─ Banco C   │
│ └─ Serviços  │            │ └─ Serviços  │            │ └─ Serviços  │
└──────────────┘            └──────────────┘            └──────────────┘

3 empresas = 3 instalações completas = 3x recursos
```

**Multi-Tenant (Planejado para 2027 - Fase 6):**
```
┌─────────────────────────────────────────┐
│         Runas ERP (Compartilhado)       │
│  ┌───────────────────────────────────┐  │
│  │  Banco de Dados                   │  │
│  │  ├─ empresa_id: A (Empresa A)     │  │
│  │  ├─ empresa_id: B (Empresa B)     │  │
│  │  └─ empresa_id: C (Empresa C)     │  │
│  └───────────────────────────────────┘  │
│  └─ Serviços (compartilhados)           │
└─────────────────────────────────────────┘

3 empresas = 1 instalação = economia massiva de recursos
```

**Impacto nas Otimizações:**

- ✅ **Vantagem**: Como é single-tenant, você pode otimizar agressivamente para uma única empresa
- ✅ **Vantagem**: Não precisa se preocupar com isolamento entre tenants
- ⚠️ **Desvantagem**: Se quiser hospedar para múltiplos clientes, precisa de múltiplas VPS ou containers
- ⚠️ **Desvantagem**: Não pode compartilhar recursos entre clientes

**Recomendação para Agora:**

Se você vai hospedar apenas para **uma empresa** (uso próprio ou cliente único):
- ✅ Implemente todas as otimizações deste documento
- ✅ Use VPS pequena/média (1-2GB RAM)
- ✅ Considere monolito modular para máxima economia

Se você planeja hospedar para **múltiplos clientes**:
- ⚠️ Mantenha microsserviços separados
- ⚠️ Use Docker Swarm ou Kubernetes para orquestração
- ⚠️ Considere implementar multi-tenant antes (adicionar `empresa_id` em todas as tabelas)
- ⚠️ Ou use uma VPS/container por cliente (mais caro, mas mais simples)

**Roadmap Multi-Tenant:**

Implementação planejada para 2027 (Fase 6) incluirá:
- Campo `empresa_id` em todas as tabelas
- Middleware de isolamento de dados
- Autenticação por empresa
- Planos e assinaturas
- Billing por tenant

### 🎯 Quando Escalar Verticalmente

Considere aumentar recursos da VPS quando:
- CPU consistentemente acima de 80%
- RAM consistentemente acima de 90%
- Swap sendo usado frequentemente
- Latência de resposta > 500ms

### 🎯 Quando Escalar Horizontalmente

Considere múltiplas VPS quando:
- Mais de 1000 usuários simultâneos
- Necessidade de alta disponibilidade
- Separação geográfica de dados
- Compliance/regulamentação exige isolamento

---

## 📚 Recursos Adicionais

### Ferramentas de Monitoramento

- **Portainer**: Interface web para Docker
- **Grafana + Prometheus**: Métricas detalhadas
- **cAdvisor**: Monitoramento de containers
- **Netdata**: Monitoramento em tempo real

### Leitura Recomendada

- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [PostgreSQL Tuning](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)
- [Docker Resource Constraints](https://docs.docker.com/config/containers/resource_constraints/)

---

**Documento criado em**: 27/05/2026  
**Responsável**: Equipe de DevOps  
**Próxima revisão**: Após implementação das otimizações
