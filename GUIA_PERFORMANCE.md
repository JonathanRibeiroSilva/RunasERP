# ⚡ Guia de Performance e Otimização - Runas ERP

> Boas práticas para maximizar o desempenho do sistema

**Última atualização**: Junho 2026

---

## 📋 Visão Geral

Este guia apresenta **técnicas de otimização** para backend, frontend e banco de dados do Runas ERP.

### Objetivos de Performance

| Métrica | Alvo | Atual |
|---------|------|-------|
| Tempo de resposta API | < 200ms | ~150ms |
| Tempo de carregamento frontend | < 3s | ~2.5s |
| Consumo de CPU (dev) | < 15% | ~10% |
| Consumo de CPU (prod) | < 10% | ~5-10% |
| Queries SQL | < 50ms | ~30ms |
| Bundle size | < 500KB | ~450KB |

---

## 🐍 Performance Backend (FastAPI)

### 1. Configuração do Uvicorn

#### Desenvolvimento (docker-compose.dev.yml)

```yaml
api-gateway:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-delay 2
```

**Características**:
- ✅ Hot-reload ativo (conveniente para desenvolvimento)
- ✅ Delay de 2s entre scans (reduz CPU em 40-50%)
- ⚠️ Single worker (suficiente para dev)


#### Produção (docker-compose.prod.yml)

```yaml
api-gateway:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Características**:
- ✅ 4 workers = processa 4 requests simultâneos
- ✅ CPU reduzida de 50-80% → 5-10%
- ✅ Melhor performance sob carga
- ❌ Precisa rebuild para mudanças (aceitável em prod)

**Cálculo de Workers**:
```python
# Fórmula recomendada: (2 × CPU cores) + 1
# Exemplo: VPS com 2 cores → (2 × 2) + 1 = 5 workers
# Ajustar conforme memória disponível
```

---

### 2. Otimização de Queries SQL

#### ❌ N+1 Problem (EVITAR)

```python
# RUIM: Faz 1 + N queries
@router.get("/vendas")
def listar_vendas(db: Session):
    vendas = db.query(Venda).all()  # 1 query
    
    for venda in vendas:
        venda.cliente  # N queries (lazy loading)
        venda.itens    # N queries
        
    return vendas
```

#### ✅ Eager Loading (USAR)

```python
# BOM: Faz apenas 1 query
from sqlalchemy.orm import joinedload

@router.get("/vendas")
def listar_vendas(db: Session):
    vendas = (
        db.query(Venda)
        .options(
            joinedload(Venda.cliente),
            joinedload(Venda.itens).joinedload(ItemVenda.produto)
        )
        .all()
    )
    return vendas
```


#### ✅ Paginação (SEMPRE USAR)

```python
@router.get("/produtos")
def listar_produtos(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    produtos = (
        db.query(Produto)
        .filter(Produto.ativo == True)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    total = db.query(Produto).filter(Produto.ativo == True).count()
    
    return {"items": produtos, "total": total}
```

#### ✅ Índices (CRIAR EM CAMPOS FREQUENTES)

```python
# alembic/versions/xxx_add_indexes.py
def upgrade():
    # Índice simples
    op.create_index('idx_produto_empresa', 'produtos', ['empresa_id'])
    op.create_index('idx_produto_ativo', 'produtos', ['ativo'])
    
    # Índice composto (consultas com múltiplos filtros)
    op.create_index(
        'idx_produto_empresa_ativo',
        'produtos',
        ['empresa_id', 'ativo']
    )
    
    # Índice para busca textual
    op.create_index(
        'idx_produto_nome',
        'produtos',
        ['nome'],
        postgresql_ops={'nome': 'gin_trgm_ops'},
        postgresql_using='gin'
    )
```

**Quando criar índices**:
- ✅ Campos em `WHERE` (empresa_id, ativo, cliente_id)
- ✅ Campos em `JOIN` (foreign keys)
- ✅ Campos em `ORDER BY` (data_venda, numero_venda)
- ✅ Campos de busca textual (nome, cpf, email)
- ❌ Campos raramente consultados
- ❌ Tabelas pequenas (< 1000 registros)


---

### 3. Caching com Redis

#### Configuração

```python
# config.py
import redis
from functools import wraps

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=6379,
    db=0,
    decode_responses=True
)
```

#### Cache de Queries Frequentes

```python
import json
from datetime import timedelta

def cache_result(ttl: int = 300):  # 5 minutos
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Gerar chave do cache
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Tentar buscar do cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Executar função
            result = await func(*args, **kwargs)
            
            # Salvar no cache
            redis_client.setex(
                cache_key,
                timedelta(seconds=ttl),
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

# Uso
@router.get("/produtos")
@cache_result(ttl=300)  # Cache por 5 minutos
def listar_produtos(db: Session):
    return db.query(Produto).all()
```

#### Invalidação de Cache

```python
@router.post("/produtos")
def criar_produto(produto: ProdutoCreate, db: Session):
    # Criar produto
    novo_produto = Produto(**produto.dict())
    db.add(novo_produto)
    db.commit()
    
    # Invalidar cache relacionado
    redis_client.delete("listar_produtos:*")
    
    return novo_produto
```


---

### 4. Processamento Assíncrono

#### Background Tasks (FastAPI)

```python
from fastapi import BackgroundTasks

def enviar_email_vendas(venda_id: int):
    # Envio de email pesado
    # ...
    pass

@router.post("/vendas")
async def criar_venda(
    venda: VendaCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Criar venda (rápido)
    nova_venda = vendas_service.criar(venda, db)
    
    # Enviar email em background (não bloqueia resposta)
    background_tasks.add_task(enviar_email_vendas, nova_venda.id)
    
    return nova_venda
```

#### Celery (Tarefas Agendadas)

```python
# tasks.py
from celery import Celery

celery_app = Celery('runas', broker='redis://redis:6379/0')

@celery_app.task
def calcular_comissoes_mensais():
    # Tarefa pesada executada todo dia 1º às 00:00
    # ...
    pass

@celery_app.task
def enviar_cobrancas_atrasadas():
    # Executada todo dia às 09:00
    # ...
    pass
```

---

### 5. Connection Pooling

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Máximo 10 conexões no pool
    max_overflow=20,       # Até 20 conexões extras em picos
    pool_pre_ping=True,    # Verifica conexão antes de usar
    pool_recycle=3600,     # Recicla conexões a cada 1h
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```


---

## ⚛️ Performance Frontend (React)

### 1. Code Splitting e Lazy Loading

#### ❌ Importação Estática (Bundle Grande)

```typescript
// RUIM: Todas as páginas no bundle inicial
import VendasPage from './pages/vendas/VendasPage';
import EstoquePage from './pages/estoque/EstoquePage';
import ProdutosPage from './pages/produtos/ProdutosPage';
```

#### ✅ Lazy Loading (USAR)

```typescript
// BOM: Carrega apenas quando necessário
import { lazy, Suspense } from 'react';

const VendasPage = lazy(() => import('./pages/vendas/VendasPage'));
const EstoquePage = lazy(() => import('./pages/estoque/EstoquePage'));
const ProdutosPage = lazy(() => import('./pages/produtos/ProdutosPage'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/vendas" element={<VendasPage />} />
        <Route path="/estoque" element={<EstoquePage />} />
        <Route path="/produtos" element={<ProdutosPage />} />
      </Routes>
    </Suspense>
  );
}
```

**Resultado**: Bundle inicial reduzido de ~800KB → ~200KB

---

### 2. Otimização de Renders

#### ❌ Re-renders Desnecessários

```typescript
// RUIM: Re-renderiza a cada digitação
function ProdutosList() {
  const [search, setSearch] = useState('');
  const [produtos, setProdutos] = useState([]);

  // Busca API a cada digitação
  useEffect(() => {
    fetchProdutos(search).then(setProdutos);
  }, [search]);

  return (
    <input onChange={(e) => setSearch(e.target.value)} />
    // ...
  );
}
```


#### ✅ Debounce + useMemo (USAR)

```typescript
// BOM: Busca apenas 500ms após parar de digitar
import { useState, useMemo } from 'react';
import { useDebounce } from '@/hooks/useDebounce';

function ProdutosList() {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 500);
  
  // Apenas re-busca quando debounced muda
  const { data: produtos } = useQuery(
    ['produtos', debouncedSearch],
    () => fetchProdutos(debouncedSearch)
  );

  // Memoiza cálculos pesados
  const produtosFiltrados = useMemo(() => {
    return produtos?.filter(p => p.ativo);
  }, [produtos]);

  return <input onChange={(e) => setSearch(e.target.value)} />;
}

// hooks/useDebounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

#### ✅ React.memo (Componentes Puros)

```typescript
// Componente filho que não precisa re-renderizar
const ProdutoCard = React.memo(({ produto }: { produto: Produto }) => {
  return (
    <div className="card">
      <h3>{produto.nome}</h3>
      <p>{produto.preco_venda}</p>
    </div>
  );
});
```

---

### 3. TanStack Query (React Query)

#### Cache Automático

```typescript
// services/api/produtos.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useProdutos(filters?: any) {
  return useQuery({
    queryKey: ['produtos', filters],
    queryFn: () => produtosApi.list(filters),
    staleTime: 5 * 60 * 1000, // Cache válido por 5 minutos
    cacheTime: 10 * 60 * 1000, // Mantém no cache por 10 minutos
  });
}

export function useCreateProduto() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: produtosApi.create,
    onSuccess: () => {
      // Invalida cache após criar
      queryClient.invalidateQueries({ queryKey: ['produtos'] });
    },
  });
}
```


---

### 4. Otimização de Bundle (Vite)

#### vite.config.ts

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({ open: true }) // Analisa tamanho do bundle
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Separa vendors grandes
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['react-bootstrap', 'react-icons'],
          'form-vendor': ['react-hook-form', 'zod'],
          'chart-vendor': ['chart.js', 'react-chartjs-2'],
        },
      },
    },
    chunkSizeWarningLimit: 1000, // Alerta se chunk > 1MB
  },
  server: {
    hmr: {
      overlay: false // Desabilita overlay de erros (opcional)
    }
  }
});
```

#### Análise de Bundle

```powershell
# Build com análise
npm run build

# Abre visualização do bundle
# stats.html será gerado automaticamente
```

---

### 5. Imagens Otimizadas

#### ✅ Lazy Loading de Imagens

```typescript
function ProdutoCard({ produto }: { produto: Produto }) {
  return (
    <img
      src={produto.foto_url}
      alt={produto.nome}
      loading="lazy"  // Lazy load nativo
      width={200}
      height={200}
    />
  );
}
```

#### ✅ WebP e Fallback

```typescript
function ProdutoImage({ produto }: { produto: Produto }) {
  return (
    <picture>
      <source srcSet={`${produto.foto_url}.webp`} type="image/webp" />
      <source srcSet={`${produto.foto_url}.jpg`} type="image/jpeg" />
      <img src={produto.foto_url} alt={produto.nome} />
    </picture>
  );
}
```


---

### 6. Virtualização de Listas

Para listas muito grandes (> 500 itens), use virtualização:

```typescript
import { FixedSizeList } from 'react-window';

function ProdutosList({ produtos }: { produtos: Produto[] }) {
  const Row = ({ index, style }: any) => (
    <div style={style}>
      <ProdutoCard produto={produtos[index]} />
    </div>
  );

  return (
    <FixedSizeList
      height={600}
      itemCount={produtos.length}
      itemSize={100}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

**Resultado**: Renderiza apenas itens visíveis (50-100), não todos os 10.000

---

## 🗄️ Performance do Banco de Dados

### 1. Análise de Queries Lentas

#### Habilitar Log de Queries

```python
# config.py
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Usar EXPLAIN ANALYZE

```sql
-- Identificar queries lentas
EXPLAIN ANALYZE
SELECT v.*, c.nome as cliente_nome
FROM vendas v
LEFT JOIN clientes c ON v.cliente_id = c.id
WHERE v.empresa_id = 1 AND v.ativo = true
ORDER BY v.data_venda DESC
LIMIT 50;

-- Resultado mostrará:
-- - Tempo de execução
-- - Uso de índices
-- - Scans sequenciais (ruim)
```

---

### 2. Otimizações Específicas

#### ✅ Índices Compostos para Queries Frequentes

```sql
-- Query: Listar vendas de uma empresa (ativas, ordenadas)
CREATE INDEX idx_vendas_empresa_ativo_data 
ON vendas(empresa_id, ativo, data_venda DESC);
```


#### ✅ Partial Index (Para Soft Delete)

```sql
-- Índice apenas para registros ativos (economiza espaço)
CREATE INDEX idx_produtos_ativo 
ON produtos(empresa_id, nome) 
WHERE ativo = true;
```

#### ✅ Full-Text Search (Busca Textual)

```sql
-- Instalar extensão pg_trgm (trigram)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Criar índice GIN para busca textual
CREATE INDEX idx_produtos_nome_trgm 
ON produtos USING gin(nome gin_trgm_ops);

-- Query com busca LIKE passa a usar o índice
SELECT * FROM produtos 
WHERE nome ILIKE '%notebook%' 
AND empresa_id = 1;
```

---

### 3. Vacuum e Analyze

```sql
-- Executar periodicamente (automatizado ou manual)
VACUUM ANALYZE vendas;
VACUUM ANALYZE produtos;

-- Verificar estatísticas
SELECT schemaname, tablename, last_vacuum, last_analyze
FROM pg_stat_user_tables
ORDER BY last_vacuum DESC;
```

---

### 4. Configurações do PostgreSQL

```conf
# postgresql.conf (ajustar conforme recursos da VPS)

# Memória
shared_buffers = 256MB           # 25% da RAM disponível
effective_cache_size = 1GB       # 50-75% da RAM
work_mem = 16MB                  # Por conexão
maintenance_work_mem = 128MB     # Para VACUUM, CREATE INDEX

# Connections
max_connections = 100

# Query Planner
random_page_cost = 1.1           # Para SSD (padrão: 4.0)
effective_io_concurrency = 200   # Para SSD (padrão: 1)
```


---

## 🐳 Performance Docker

### 1. Otimização de Builds

#### Multi-stage Build (Produção)

```dockerfile
# Dockerfile (Backend)
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Resultado**: Imagem reduzida de ~1GB → ~400MB

---

### 2. Volumes em Produção

#### ❌ Desenvolvimento (Volumes Montados)

```yaml
# docker-compose.dev.yml
volumes:
  - ./api-gateway:/app  # Causa overhead de I/O
```

#### ✅ Produção (Sem Volumes)

```yaml
# docker-compose.prod.yml
# Sem volumes montados (código copiado na imagem)
# Resultado: I/O mais rápido, menos CPU
```

---

### 3. Recursos de Containers

```yaml
# docker-compose.prod.yml
services:
  api-gateway:
    deploy:
      resources:
        limits:
          cpus: '1.0'      # Máximo 1 CPU
          memory: 512M     # Máximo 512MB RAM
        reservations:
          cpus: '0.25'     # Mínimo garantido
          memory: 128M
```

---

## 📊 Monitoramento e Profiling

### 1. Backend Profiling

#### py-spy (Profiler Python)

```powershell
# Instalar
pip install py-spy

# Profiling de um processo rodando
py-spy top --pid <PID>

# Gerar flamegraph
py-spy record -o profile.svg --pid <PID>
```


#### FastAPI Middleware de Timing

```python
# middleware/timing.py
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log queries lentas
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url.path} took {process_time:.2f}s")
    
    return response
```

---

### 2. Frontend Profiling

#### React DevTools Profiler

```typescript
// Envolva componentes para profiling
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: "mount" | "update",
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) {
  console.log(`${id} (${phase}) took ${actualDuration}ms`);
}

<Profiler id="ProdutosList" onRender={onRenderCallback}>
  <ProdutosList />
</Profiler>
```

#### Lighthouse (Métricas Web)

```powershell
# Instalar
npm install -g lighthouse

# Rodar auditoria
lighthouse https://www.runaserp.com.br --view

# Métricas analisadas:
# - FCP (First Contentful Paint)
# - LCP (Largest Contentful Paint)
# - TTI (Time to Interactive)
# - CLS (Cumulative Layout Shift)
```

---

### 3. Monitoramento de Produção

#### Prometheus + Grafana (Recomendado)

```yaml
# docker-compose.prod.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```


#### Sentry (Error Tracking)

```python
# Backend
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # 10% das requests
)
```

```typescript
// Frontend
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  integrations: [new Sentry.BrowserTracing()],
  tracesSampleRate: 0.1,
});
```

---

## 🎯 Checklist de Performance

### Backend
- [ ] Uvicorn com múltiplos workers em produção
- [ ] Queries otimizadas (eager loading, paginação)
- [ ] Índices criados em campos frequentes
- [ ] Connection pooling configurado
- [ ] Redis cache implementado para queries pesadas
- [ ] Background tasks para operações lentas
- [ ] Logs de queries lentas habilitados

### Frontend
- [ ] Code splitting (lazy loading de rotas)
- [ ] React.memo em componentes puros
- [ ] useMemo/useCallback para cálculos pesados
- [ ] Debounce em buscas/filtros
- [ ] TanStack Query configurado com cache
- [ ] Imagens com lazy loading
- [ ] Bundle analisado e otimizado (< 500KB inicial)
- [ ] Virtualização em listas grandes (> 500 itens)

### Banco de Dados
- [ ] Índices criados para queries frequentes
- [ ] Full-text search configurado (pg_trgm)
- [ ] Vacuum/Analyze agendado
- [ ] Configurações do PostgreSQL ajustadas
- [ ] Queries lentas identificadas com EXPLAIN ANALYZE

### Docker
- [ ] Multi-stage builds em produção
- [ ] Volumes removidos em produção
- [ ] Limites de recursos configurados
- [ ] Imagens otimizadas (< 500MB)


### Monitoramento
- [ ] Profiling configurado (py-spy, React DevTools)
- [ ] Middleware de timing no backend
- [ ] Lighthouse rodando periodicamente
- [ ] Prometheus + Grafana em produção (opcional)
- [ ] Sentry configurado para error tracking (opcional)

---

## 📚 Recursos Adicionais

### Documentação Interna
- [Performance CPU](./docs/03-arquitetura/performance-cpu.md) - Análise detalhada
- [Infraestrutura](./docs/03-arquitetura/visao-geral.md) - Arquitetura geral
- [Checklist Desenvolvimento](./CHECKLIST_DESENVOLVIMENTO.md) - Boas práticas

### Ferramentas
- **py-spy** - https://github.com/benfred/py-spy
- **Lighthouse** - https://developers.google.com/web/tools/lighthouse
- **React DevTools** - https://react.dev/learn/react-developer-tools
- **Prometheus** - https://prometheus.io
- **Grafana** - https://grafana.com
- **Sentry** - https://sentry.io

### Artigos Úteis
- **FastAPI Performance** - https://fastapi.tiangolo.com/deployment/
- **React Performance** - https://react.dev/learn/render-and-commit
- **PostgreSQL Tuning** - https://wiki.postgresql.org/wiki/Performance_Optimization
- **Vite Optimization** - https://vitejs.dev/guide/build.html

---

## 🚀 Como Aplicar

### 1. Análise Inicial

```powershell
# Backend: Verificar queries lentas
docker logs erp-api-gateway-dev -f | Select-String "took"

# Frontend: Rodar Lighthouse
lighthouse https://www.runaserp.com.br --view

# Banco: Queries lentas
docker exec -it erp-postgres-dev psql -U runas_user -d runas_db
\x
SELECT query, calls, mean_exec_time, total_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```


### 2. Implementar Otimizações

Priorize conforme o impacto:

**Alto Impacto** (fazer primeiro):
1. Uvicorn com múltiplos workers (prod)
2. Criar índices em campos frequentes
3. Code splitting no frontend
4. Paginação em todas as listagens

**Médio Impacto**:
1. Cache Redis para queries pesadas
2. React.memo em componentes puros
3. Eager loading em queries com JOIN
4. Background tasks para emails

**Baixo Impacto** (se houver tempo):
1. Virtualização de listas
2. Prometheus/Grafana
3. Sentry
4. Flamegraphs com py-spy

### 3. Medir Resultados

```powershell
# Antes das otimizações
lighthouse https://www.runaserp.com.br --output json --output-path before.json

# Aplicar otimizações
# ...

# Depois das otimizações
lighthouse https://www.runaserp.com.br --output json --output-path after.json

# Comparar resultados
# Performance Score: 65 → 92 (+27 pontos)
# LCP: 4.2s → 1.8s (-57%)
# TTI: 7.5s → 3.1s (-59%)
```

---

## 📞 Suporte

### Dúvidas sobre Performance

- **Documentação**: [docs/03-arquitetura/](./docs/03-arquitetura/)
- **Issues Conhecidas**: [docs/09-troubleshooting/](./docs/09-troubleshooting/)
- **Checklist**: [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md)

### Problemas Comuns

- **CPU alto em dev**: Usar `--reload-delay 2` no uvicorn
- **Queries lentas**: Criar índices ou usar eager loading
- **Bundle grande**: Analisar com `rollup-plugin-visualizer`
- **Conexões esgotadas**: Aumentar `pool_size` no SQLAlchemy

---

<div align="center">

**Runas ERP** | Performance Optimization Guide  
**Última atualização**: Junho 2026  
**Objetivo**: < 200ms API | < 3s FCP | < 10% CPU

</div>

