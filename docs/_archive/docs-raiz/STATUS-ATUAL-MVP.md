# 📊 Status Atual do MVP - Análise do Terminal

> **Arquivado em**: 28/05/2026 — Snapshot de status de 26/05/2026. Erros descritos já foram corrigidos.

**Data da análise**: 26/05/2026  
**Status geral**: 🟡 85% funcional (na data da análise)

---

## Resumo dos Problemas Encontrados

### ❌ API Gateway — Seed do Admin (CRÍTICO — JÁ CORRIGIDO)

**Erro**:
```
{"error": "password cannot be longer than 72 bytes", "event": "seed.admin_error"}
```

**Causa**: Bcrypt limita senhas a 72 bytes. Código foi corrigido para truncar automaticamente.

**Correção aplicada**:
```python
# usuario_repository.py
def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

# seed.py
admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123")[:72]
```

**Solução**: `docker-compose up -d --build api-gateway`

---

### ❌ Evolution API — Conexão com Banco (NÃO-CRÍTICO)

**Erro**:
```
Error: P1001: Can't reach database server at `db-evolution:5432`
```

**Causa**: Timing — Evolution API inicia antes do banco estar pronto.

**Solução**: `docker-compose restart evolution-api`

---

### ⚠️ Bcrypt Version Warning (INFORMATIVO)

**Erro**:
```
(trapped) error reading bcrypt version
AttributeError: module 'bcrypt' has no attribute '__about__'
```

**Impacto**: Apenas warning, hash de senhas funciona normalmente.

---

## ✅ Correções Já Aplicadas

- PgAdmin: Email alterado de `admin@runas.local` para `admin@runas.com`
- Bcrypt: Código corrigido para truncar senha em 72 bytes

---

## Serviços Essenciais para MVP (na data)

| Serviço | Status |
|---------|--------|
| Redis | ✅ Up |
| RabbitMQ | ✅ Up |
| PostgreSQL (todos) | ✅ Up |
| API Gateway | 🟡 Up (seed falhava) |
| Serviço Clientes | ✅ Up |
| Serviço Produtos | ✅ Up |
| Evolution API | ❌ Exited |

---

**Data**: 26/05/2026  
**Arquivado em**: 28/05/2026
