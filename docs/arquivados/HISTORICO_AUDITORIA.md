# Histórico e Auditoria - Runas ERP

## 📊 Visão Geral

O sistema implementa duas estratégias de auditoria e histórico:

1. **Histórico de Status** (Vendas) - Rastreabilidade completa de mudanças
2. **Soft Delete** (Clientes) - Exclusão lógica com preservação de dados

---

## 🔄 Histórico de Status de Vendas

### Tabela: `vendas.historico_status_venda`

Registra TODAS as mudanças de status de uma venda para auditoria completa.

### Campos

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | UUID | Identificador único do registro |
| `venda_id` | UUID | Referência à venda |
| `status_anterior` | VARCHAR(20) | Status antes da mudança (NULL para criação) |
| `status_novo` | VARCHAR(20) | Status após a mudança |
| `alterado_por` | UUID | Usuário que fez a alteração |
| `alterado_em` | TIMESTAMP | Data/hora da alteração |
| `observacao` | TEXT | Observações opcionais |

### Uso no Código Python

```python
from models.historico_status import HistoricoStatusVenda

# Registrar mudança de status
async def mudar_status_venda(
    db: AsyncSession,
    venda_id: UUID,
    status_anterior: str,
    status_novo: str,
    usuario_id: UUID,
    observacao: Optional[str] = None
):
    historico = HistoricoStatusVenda(
        venda_id=venda_id,
        status_anterior=status_anterior,
        status_novo=status_novo,
        alterado_por=usuario_id,
        observacao=observacao
    )
    db.add(historico)
    await db.commit()

# Consultar histórico de uma venda
async def obter_historico(db: AsyncSession, venda_id: UUID):
    result = await db.execute(
        select(HistoricoStatusVenda)
        .where(HistoricoStatusVenda.venda_id == venda_id)
        .order_by(HistoricoStatusVenda.alterado_em)
    )
    return result.scalars().all()
```

### Exemplo de Consulta SQL

```sql
-- Ver histórico completo de uma venda
SELECT 
    h.alterado_em,
    h.status_anterior,
    h.status_novo,
    u.nome as alterado_por_nome,
    h.observacao
FROM vendas.historico_status_venda h
LEFT JOIN gateway.usuarios u ON h.alterado_por = u.id
WHERE h.venda_id = 'uuid-da-venda'
ORDER BY h.alterado_em;

-- Tempo médio entre status
SELECT 
    status_novo,
    AVG(EXTRACT(EPOCH FROM (alterado_em - LAG(alterado_em) OVER (PARTITION BY venda_id ORDER BY alterado_em)))) / 3600 as horas_medias
FROM vendas.historico_status_venda
GROUP BY status_novo;
```

---

## 🗑️ Soft Delete em Clientes

### Campos Adicionados

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `deletado_em` | TIMESTAMP | Data/hora da exclusão (NULL = ativo) |
| `deletado_por` | UUID | Usuário que deletou |
| `motivo_exclusao` | TEXT | Motivo da exclusão |

### Uso no Código Python

```python
# Deletar cliente (soft delete)
async def deletar_cliente(
    db: AsyncSession,
    cliente_id: UUID,
    usuario_id: UUID,
    motivo: str
):
    cliente = await db.get(Cliente, cliente_id)
    cliente.deletado_em = datetime.now()
    cliente.deletado_por = usuario_id
    cliente.motivo_exclusao = motivo
    await db.commit()

# Listar apenas clientes ativos
async def listar_clientes_ativos(db: AsyncSession, empresa_id: int):
    result = await db.execute(
        select(Cliente)
        .where(
            Cliente.empresa_id == empresa_id,
            Cliente.deletado_em == None  # Apenas ativos
        )
        .order_by(Cliente.nome)
    )
    return result.scalars().all()

# Restaurar cliente deletado
async def restaurar_cliente(db: AsyncSession, cliente_id: UUID):
    cliente = await db.get(Cliente, cliente_id)
    cliente.deletado_em = None
    cliente.deletado_por = None
    cliente.motivo_exclusao = None
    await db.commit()
```

### Exemplo de Consulta SQL

```sql
-- Listar clientes ativos
SELECT * FROM clientes.clientes 
WHERE empresa_id = 4 
AND deletado_em IS NULL;

-- Listar clientes deletados
SELECT 
    c.nome,
    c.deletado_em,
    u.nome as deletado_por_nome,
    c.motivo_exclusao
FROM clientes.clientes c
LEFT JOIN gateway.usuarios u ON c.deletado_por = u.id
WHERE c.empresa_id = 4 
AND c.deletado_em IS NOT NULL
ORDER BY c.deletado_em DESC;

-- Restaurar cliente
UPDATE clientes.clientes 
SET deletado_em = NULL, 
    deletado_por = NULL, 
    motivo_exclusao = NULL
WHERE id = 'uuid-do-cliente';
```

---

## 🎯 Benefícios

### Histórico de Status
- ✅ Rastreabilidade completa do ciclo de vida da venda
- ✅ Identificação de gargalos no processo
- ✅ Auditoria para compliance
- ✅ Métricas de performance (tempo entre status)

### Soft Delete
- ✅ Dados nunca são perdidos
- ✅ Possibilidade de restauração
- ✅ Manutenção de integridade referencial
- ✅ Relatórios históricos continuam funcionando

---

## 📈 Métricas e Relatórios

### Tempo Médio de Processamento de Vendas

```sql
WITH primeira_mudanca AS (
    SELECT 
        venda_id,
        MIN(alterado_em) as inicio
    FROM vendas.historico_status_venda
    GROUP BY venda_id
),
ultima_mudanca AS (
    SELECT 
        venda_id,
        MAX(alterado_em) as fim
    FROM vendas.historico_status_venda
    WHERE status_novo IN ('FINALIZADA', 'CANCELADA')
    GROUP BY venda_id
)
SELECT 
    AVG(EXTRACT(EPOCH FROM (u.fim - p.inicio))) / 3600 as horas_medias
FROM primeira_mudanca p
JOIN ultima_mudanca u ON p.venda_id = u.venda_id;
```

### Taxa de Cancelamento

```sql
SELECT 
    COUNT(CASE WHEN status_novo = 'CANCELADA' THEN 1 END)::FLOAT / COUNT(DISTINCT venda_id) * 100 as taxa_cancelamento_pct
FROM vendas.historico_status_venda;
```

---

## 🔐 Compliance e LGPD

O soft delete permite:
- Atender requisitos de direito ao esquecimento (hard delete posterior)
- Manter dados para obrigações legais (notas fiscais, etc.)
- Auditar quem deletou e por quê
- Período de retenção configurável

---

## 📝 Próximos Passos Sugeridos

1. **Produtos**: Adicionar soft delete
2. **Auditoria Geral**: Tabela de log de todas as alterações (JSONB)
3. **Retenção Automática**: Job para hard delete após período legal
4. **Dashboard**: Visualização de métricas de histórico
