---
paths:
  - "**/alembic/**"
  - "**/alembic.ini"
  - "**/database.py"
---

# Alembic — comandos e erros comuns

O alerta de crashloop (uma revision ruim derruba o serviço em loop no boot) e o princípio de que rollback volta imagem e nunca DDL estão no `CLAUDE.md`, seção Database Migrations. Releia-os antes de escrever uma revision.

```python
# Todo model SQLAlchemy DEVE declarar o schema
class MyModel(Base):
    __tablename__ = "my_table"
    __table_args__ = {"schema": "service_name"}  # OBRIGATÓRIO
```

`alembic/env.py` precisa de `include_schemas=False` e `version_table_schema="<schema_do_serviço>"`.

`init_db()` também se recusa a subir quando `alembic/versions/` está vazio, então uma imagem montada sem as migrations falha alto em vez de subir "saudável" sobre um schema vazio.

```bash
docker exec -it erp-<serviço>-dev alembic revision --autogenerate -m "descrição"
# Sempre revise o arquivo gerado em alembic/versions/ antes de aplicar
docker exec -it erp-<serviço>-dev alembic upgrade head

# Inspeção
docker exec -it erp-<serviço>-dev alembic current
docker exec -i erp-db-dev psql -U erp -d erp -c "SELECT version_num FROM <schema>.alembic_version;"
```

**Nunca:** `include_schemas=True`, falta de `__table_args__`, migration sem revisão, editar migration já aplicada.

## Troubleshooting

| Erro | Causa | Correção |
|------|-------|----------|
| Detecta tabelas de outros schemas | `include_schemas=True` no env.py | Voltar para `False` |
| Tabela criada em `public` em vez do schema do serviço | Falta `__table_args__` | Adicionar e criar nova migration |
| `type ENUM already exists` | A migration tenta criar um ENUM existente | Criar migration vazia (`pass`) e carimbar |
| Alembic detecta mudanças fantasma | Estado do model ≠ estado do banco | Aplicar as pendentes; último recurso: `alembic stamp head` (cuidado) |
