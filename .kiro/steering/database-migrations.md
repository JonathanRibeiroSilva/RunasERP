---
inclusion: auto
---

# Database Migrations - Regras Obrigatórias

## Princípio Fundamental

**SEMPRE use Alembic migrations para qualquer alteração no banco de dados.**

**NUNCA use `Base.metadata.create_all()` ou `Base.metadata.drop_all()` em código de produção.**

---

## Arquitetura Multi-Schema

O projeto usa **um único banco PostgreSQL** com **schemas separados por serviço**:

- `gateway` → Autenticação e proxy
- `empresas` → Multi-tenancy
- `clientes` → Gestão de clientes
- `produtos` → Catálogo de produtos
- `estoque` → Controle de estoque
- `vendas` → Pedidos e vendas (inclui loja online)
- `financeiro` → Contas a pagar/receber
- `notificacoes` → Notificações e alertas

**Cada serviço gerencia APENAS seu próprio schema.**

---

## Configuração do Alembic (env.py)

Todo `alembic/env.py` deve seguir este padrão:

```python
# Configurar schema específico do serviço
def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        version_table_schema="<NOME_DO_SCHEMA>",  # ← Schema do serviço
        include_schemas=False,  # ← NUNCA True
    )

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema="<NOME_DO_SCHEMA>",  # ← Schema do serviço
        include_schemas=False,  # ← NUNCA True
    )
```

**Regras:**
- `version_table_schema`: DEVE ser o schema do serviço (ex: `"clientes"`, `"produtos"`)
- `include_schemas`: DEVE ser `False` (nunca `True`)
- Isso garante que cada serviço vê apenas suas próprias tabelas

---

## Models SQLAlchemy

Todos os models devem especificar explicitamente o schema:

```python
from database import Base

class MeuModel(Base):
    __tablename__ = "minha_tabela"
    __table_args__ = {"schema": "nome_do_schema"}  # ← OBRIGATÓRIO
    
    id: Mapped[int] = mapped_column(primary_key=True)
    # ... outros campos
```

**Sem `__table_args__`**, a tabela será criada no schema `public` (ERRADO).

---

## Workflow de Migrations

### 1. Criar nova migration

```bash
# Dentro do container do serviço
docker exec -it erp-<servico>-dev alembic revision --autogenerate -m "descrição da mudança"
```

Exemplo:
```bash
docker exec -it erp-produtos-dev alembic revision --autogenerate -m "add campo codigo_barras"
```

### 2. Revisar a migration gerada

Abra o arquivo em `alembic/versions/` e verifique:
- ✅ Está criando/alterando apenas tabelas do schema correto
- ✅ Não está tentando criar tabelas de outros serviços
- ✅ Os tipos de dados estão corretos
- ✅ Índices e constraints necessários estão presentes

### 3. Aplicar a migration

```bash
docker exec -it erp-<servico>-dev alembic upgrade head
```

### 4. Verificar no banco

```bash
docker exec -i erp-db-dev psql -U erp -d erp -c "SELECT version_num FROM <schema>.alembic_version;"
```

---

## Checklist ao Criar Nova Funcionalidade

Sempre que adicionar/modificar models:

- [ ] Model tem `__table_args__ = {"schema": "<nome_schema>"}`
- [ ] Criou migration com `alembic revision --autogenerate`
- [ ] Revisou a migration gerada (schema correto, sem tabelas extras)
- [ ] Aplicou a migration com `alembic upgrade head`
- [ ] Verificou a tabela `<schema>.alembic_version` no banco
- [ ] **NUNCA** usou `Base.metadata.create_all()` no código

---

## Troubleshooting

### "Migration detecta tabelas de outros schemas"

**Causa**: `include_schemas=True` no `env.py`

**Solução**: Alterar para `include_schemas=False`

### "Tabela criada no schema public em vez do schema correto"

**Causa**: Falta `__table_args__ = {"schema": "..."}` no model

**Solução**: Adicionar `__table_args__` e criar nova migration

### "type ENUM already exists"

**Causa**: Migration tentando criar ENUM que já existe

**Solução**: 
1. Se é migration inicial de um serviço antigo, criar migration vazia (`pass`) e marcar como aplicada
2. Para novas migrations, Alembic deve detectar ENUMs existentes automaticamente

### "Alembic detecta mudanças quando não deveria"

**Causa**: Diferença entre estado do banco e models

**Solução**:
1. Verificar se todas as migrations anteriores foram aplicadas
2. Verificar se os models têm `__table_args__` corretos
3. Usar `alembic stamp head` para sincronizar estado (CUIDADO!)

---

## Exemplo Completo: Adicionar Campo em Produto

### 1. Modificar o model

```python
# services/produtos/models/produto.py
class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = {"schema": "produtos"}
    
    # ... campos existentes ...
    
    # Novo campo
    codigo_barras: Mapped[Optional[str]] = mapped_column(
        String(13),
        index=True,
        comment="Código de barras EAN-13"
    )
```

### 2. Gerar migration

```bash
docker exec -it erp-produtos-dev alembic revision --autogenerate -m "add codigo_barras to produtos"
```

### 3. Revisar arquivo gerado

```python
# alembic/versions/XXXXX_add_codigo_barras_to_produtos.py
def upgrade() -> None:
    op.add_column('produtos', 
        sa.Column('codigo_barras', sa.String(13), nullable=True),
        schema='produtos'  # ← Verificar que está no schema correto
    )
    op.create_index(
        'ix_produtos_produtos_codigo_barras',
        'produtos',
        ['codigo_barras'],
        schema='produtos'
    )
```

### 4. Aplicar

```bash
docker exec -it erp-produtos-dev alembic upgrade head
```

### 5. Verificar

```bash
docker exec -i erp-db-dev psql -U erp -d erp -c "\d produtos.produtos"
```

---

## Comandos Úteis

```bash
# Ver migrations pendentes
docker exec -it erp-<servico>-dev alembic current
docker exec -it erp-<servico>-dev alembic history

# Aplicar migrations
docker exec -it erp-<servico>-dev alembic upgrade head

# Rollback (CUIDADO!)
docker exec -it erp-<servico>-dev alembic downgrade -1

# Ver estado no banco
docker exec -i erp-db-dev psql -U erp -d erp -c "
  SELECT schemaname, tablename, tableowner 
  FROM pg_tables 
  WHERE schemaname = '<nome_schema>' 
  ORDER BY tablename;
"

# Ver todas as versões de migration
docker exec -i erp-db-dev psql -U erp -d erp -c "
  SELECT 'gateway' as schema, version_num FROM gateway.alembic_version
  UNION ALL SELECT 'empresas', version_num FROM empresas.alembic_version
  UNION ALL SELECT 'clientes', version_num FROM clientes.alembic_version
  UNION ALL SELECT 'produtos', version_num FROM produtos.alembic_version
  UNION ALL SELECT 'estoque', version_num FROM estoque.alembic_version
  UNION ALL SELECT 'vendas', version_num FROM vendas.alembic_version
  ORDER BY schema;
"
```

---

## Status Atual das Migrations (2026-06-11)

| Serviço | Schema | Versão Atual | Observações |
|---------|--------|--------------|-------------|
| gateway | `gateway` | `20260611_gateway` | ✅ Migrado para Alembic |
| empresas | `empresas` | `20260611_empresas` | ✅ Migrado para Alembic |
| clientes | `clientes` | `001_multitenancy` | ✅ Multi-tenancy implementado |
| produtos | `produtos` | `20260609_multitenancy` | ✅ Multi-tenancy implementado |
| estoque | `estoque` | `20260609_multitenancy` + `001_migrate_to_uuid` | ✅ UUIDs + multi-tenancy |
| vendas | `vendas` | `20260611_loja_mvp` | ✅ Loja online MVP completa |
| financeiro | `financeiro` | (nenhuma) | ⚠️ Serviço vazio ainda |
| notificacoes | `notificacoes` | (nenhuma) | ⚠️ Serviço vazio ainda |

---

## Resumo: O Que NUNCA Fazer

❌ **NUNCA** usar `Base.metadata.create_all()` em produção  
❌ **NUNCA** usar `include_schemas=True` no Alembic  
❌ **NUNCA** esquecer `__table_args__ = {"schema": "..."}` nos models  
❌ **NUNCA** aplicar migration sem revisar o arquivo gerado  
❌ **NUNCA** modificar migration depois de aplicada (criar nova em vez disso)  
❌ **NUNCA** fazer queries diretas em schema de outro serviço  

✅ **SEMPRE** usar Alembic para mudanças no banco  
✅ **SEMPRE** especificar schema nos models  
✅ **SEMPRE** revisar migrations geradas automaticamente  
✅ **SEMPRE** testar migrations em desenvolvimento antes de produção  
✅ **SEMPRE** manter cada serviço isolado no seu schema  
