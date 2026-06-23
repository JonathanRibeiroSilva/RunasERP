# 🚀 Melhorias Prioritárias do Backend

> **Sugestões de melhorias para implementar ANTES de colocar em produção**
> 
> **Última atualização**: 27/05/2026
> **Arquivado em**: 28/05/2026 — Conteúdo absorvido em `CHECKLIST_DESENVOLVIMENTO.md` (seção Qualidade e Segurança do Backend)

---

## 🎯 Por que fazer AGORA?

✅ **Sem dados em produção**: Mudanças estruturais são fáceis  
✅ **Sem usuários**: Pode quebrar e testar à vontade  
✅ **Sem downtime**: Não precisa se preocupar com disponibilidade  
✅ **Arquitetura limpa**: Evita débito técnico futuro  

---

## 🔥 PRIORIDADE MÁXIMA

### 1. Multi-Tenant (Empresa ID)

**Impacto**: 🔴 CRÍTICO — Afeta toda a arquitetura de dados  
**Esforço**: 1-2 semanas

1. Criar tabela `empresas`
2. Adicionar `empresa_id` em TODAS as tabelas
3. Criar middleware de isolamento
4. Atualizar todos os repositories para filtrar por `empresa_id`
5. Atualizar seeds e testes

---

### 2. Banco de Dados Unificado ✅ IMPLEMENTADO

**Impacto**: 🟡 ALTO — Economia de ~228 MB RAM  
**Status**: Concluído em 27/05/2026 — ver `CONSOLIDACAO_POSTGRES.md` (arquivado)

---

### 3. Auditoria e Logs Estruturados

**Impacto**: 🟡 ALTO — Compliance e debugging  
**Esforço**: 1 semana

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[UUID] = ...
    empresa_id: Mapped[UUID] = ...
    usuario_id: Mapped[UUID] = ...
    tabela: Mapped[str] = ...
    registro_id: Mapped[UUID] = ...
    acao: Mapped[str] = ...       # "CREATE", "UPDATE", "DELETE"
    dados_antes: Mapped[dict] = ...
    dados_depois: Mapped[dict] = ...
    ip_address: Mapped[str] = ...
    user_agent: Mapped[str] = ...
    criado_em: Mapped[datetime] = ...
```

---

### 4. Validação de CEP no Backend

**Impacto**: 🟢 MÉDIO — Segurança e integridade  
**Esforço**: 4-6 horas

```python
class ViaCepService:
    async def validar_cep(self, cep: str) -> dict | None:
        cached = await redis.get(f"cep:{cep}")
        if cached:
            return json.loads(cached)
        
        try:
            response = await httpx.get(f"https://viacep.com.br/ws/{cep}/json/")
            data = response.json()
            if "erro" not in data:
                await redis.setex(f"cep:{cep}", 2592000, json.dumps(data))
                return data
        except Exception as e:
            log.warning("viacep_falhou", cep=cep, error=str(e))
            return None
```

---

## 🔥 PRIORIDADE ALTA

### 5. Soft Delete Consistente + Reativação Automática ✅ ESPECIFICADO

Ver `REGRA_SOFT_DELETE_REATIVACAO.md` (arquivado) para especificação completa.

---

### 6. Índices de Banco de Dados

**Esforço**: 1 dia

```sql
-- Clientes
CREATE INDEX idx_clientes_empresa_ativo ON clientes(empresa_id, ativo);
CREATE INDEX idx_clientes_cpf ON clientes(cpf);
CREATE INDEX idx_clientes_nome ON clientes(nome);

-- Produtos
CREATE INDEX idx_produtos_empresa_ativo ON produtos(empresa_id, ativo);
CREATE INDEX idx_produtos_categoria ON produtos(categoria_id);
CREATE INDEX idx_produtos_nome ON produtos(nome);

-- Vendas
CREATE INDEX idx_vendas_empresa_data ON vendas(empresa_id, data_venda);
CREATE INDEX idx_vendas_cliente ON vendas(cliente_id);
CREATE INDEX idx_vendas_status ON vendas(status);
```

---

### 7. Rate Limiting por Usuário/Empresa

**Esforço**: 1 dia

```python
RATE_LIMITS = {
    "default": "100/minute",
    "login": "5/minute",
    "cadastro": "10/minute",
    "consulta": "200/minute",
    "relatorio": "10/minute",
}
```

---

### 8. Error Handlers Padronizados

Ver `ERROR_HANDLING_GUIDE.md` (arquivado) para implementação completa.

---

### 9. Validações de Negócio Centralizadas

**Esforço**: 2-3 dias

```python
class ClienteValidator:
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        pass
    
    @staticmethod
    async def validar_credito_disponivel(cliente: Cliente, valor_compra: Decimal) -> bool:
        if cliente.bloqueado:
            raise ValidationError("Cliente bloqueado")
        if cliente.credito_disponivel < valor_compra:
            raise ValidationError("Crédito insuficiente")
        return True
```

---

## 🟡 PRIORIDADE MÉDIA

### 10. Cache Estratégico com Redis

```python
# Cache de longa duração (1h - 1 dia)
- Categorias de produtos
- Configurações do sistema
- CEPs consultados

# Cache de curta duração (5-15 min)
- Lista de produtos ativos
- Estoque disponível
- Crédito disponível de clientes
```

### 11. Testes Automatizados

- Services: 80%+
- Validators: 90%+
- Endpoints: 70%+

### 12. Documentação Swagger/OpenAPI

### 13. Backup Automatizado

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres -U runas runas_erp | gzip > backup_$DATE.sql.gz
aws s3 cp backup_$DATE.sql.gz s3://runas-backups/
```

---

## 💰 Custo vs Benefício

| Melhoria | Esforço | Impacto | ROI | Prioridade |
|----------|---------|---------|-----|------------|
| Multi-Tenant | 2 semanas | 🔴 Crítico | ⭐⭐⭐⭐⭐ | MÁXIMA |
| Banco Unificado | 6 horas | 🟡 Alto | ⭐⭐⭐⭐⭐ | ✅ FEITO |
| Auditoria | 1 semana | 🟡 Alto | ⭐⭐⭐⭐ | MÁXIMA |
| Validação CEP | 6 horas | 🟢 Médio | ⭐⭐⭐⭐ | MÁXIMA |
| Soft Delete + Reativação | 2 dias | 🟡 Alto | ⭐⭐⭐⭐ | ALTA |
| Índices | 1 dia | 🟡 Alto | ⭐⭐⭐⭐⭐ | ALTA |
| Rate Limiting | 1 dia | 🟢 Médio | ⭐⭐⭐ | ALTA |
| Error Handlers | 2 dias | 🟡 Alto | ⭐⭐⭐⭐ | ALTA |
| Cache | 1 semana | 🟢 Médio | ⭐⭐⭐ | MÉDIA |
| Testes | 3 semanas | 🟡 Alto | ⭐⭐⭐⭐ | MÉDIA |
| Swagger | 1 semana | 🟢 Médio | ⭐⭐⭐ | MÉDIA |
| Backup | 3 dias | 🔴 Crítico | ⭐⭐⭐⭐⭐ | MÉDIA |

---

**Documento criado em**: 27/05/2026  
**Arquivado em**: 28/05/2026
