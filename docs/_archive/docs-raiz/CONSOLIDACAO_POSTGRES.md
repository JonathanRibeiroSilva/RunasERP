# Consolidação PostgreSQL - 8 Containers → 1 Container

> **Arquivado em**: 28/05/2026 — Migração concluída. Documentação histórica do processo.

---

## 📊 Resumo das Mudanças

### Antes:
- **8 containers PostgreSQL** separados (um por serviço)
- **~268 MB de RAM** consumidos
- **8 healthchecks** rodando simultaneamente
- **8 volumes** Docker separados

### Depois:
- **1 container PostgreSQL** consolidado
- **~35-40 MB de RAM** (economia de ~228 MB = 85%)
- **1 healthcheck** único
- **1 volume** Docker
- **8 schemas** separados dentro do mesmo database

---

## 🔧 Arquivos Modificados

- `.env` — URLs de conexão com `search_path` por schema
- `docker-compose.yml` — Container único `erp-db`
- `docker-compose.dev.yml` — Container único `erp-db-dev`
- `postgres/init-schemas.sql` — Script de criação dos 8 schemas
- `pgadmin/servers.json` — 1 servidor ao invés de 8
- `pgadmin/pgpass` — Credenciais simplificadas

---

## 🚀 Como Verificar

```bash
# Conectar ao PostgreSQL
docker exec -it erp-db-dev psql -U erp -d erp

# Listar schemas
\dn
# Deve mostrar: gateway, clientes, produtos, estoque, vendas, financeiro, notificacoes, evolution

# Ver consumo de memória
docker stats --no-stream
```

---

## 🔄 Migração de Dados (Se Necessário)

```bash
# Backup de cada database antiga
docker exec erp-db-gateway-dev pg_dump -U erp gateway > backup_gateway.sql

# Restaurar no novo container com schema correto
docker exec -i erp-db-dev psql -U erp -d erp -c "SET search_path TO gateway;" < backup_gateway.sql
```

---

## 🐛 Troubleshooting

```bash
# Erro: "schema does not exist"
docker exec -i erp-db-dev psql -U erp -d erp < postgres/init-schemas.sql

# Erro: "permission denied for schema"
docker exec -it erp-db-dev psql -U erp -d erp -c "GRANT ALL ON SCHEMA gateway TO erp;"

# Container não inicia
docker logs erp-db-dev
docker volume rm runaserp_db_data
docker-compose up -d db
```

---

## 🔄 Rollback

```bash
# Restaurar arquivos do git
git checkout .env docker-compose.yml docker-compose.dev.yml
docker-compose down -v
docker-compose up -d
```

---

**Migração realizada em**: 27/05/2026  
**Arquivado em**: 28/05/2026
