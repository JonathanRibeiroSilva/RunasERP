# Changelog - Implementação de Soft Delete em Produtos

## Resumo das Mudanças

Implementação de soft delete para produtos com ajuste nos filtros da interface.

### Comportamento Anterior
- **Todos**: mostrava todos os produtos (não funcionava corretamente)
- **Ativos**: mostrava apenas produtos ativos
- **Inativos**: mostrava apenas produtos inativos
- DELETE fazia hard delete (remoção permanente do banco)

### Comportamento Novo
- **Todos**: mostra todos os produtos não deletados (ativos e inativos)
- **Excluídos**: mostra apenas produtos com soft delete
- DELETE agora faz soft delete (marca `deletado_em` com timestamp)
- Novo endpoint PATCH `/produtos/{id}/restaurar` para restaurar produtos deletados

---

## Mudanças no Backend

### 1. Model (`models/produto.py`)
```python
# Adicionado campo para soft delete
deletado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
```

### 2. Repository (`repositories/produtos.py`)

#### Método `listar_todos` refatorado:
```python
async def listar_todos(
    self, 
    skip: int = 0, 
    limit: int = 10, 
    apenas_ativos: bool | None = None,
    apenas_deletados: bool = False
) -> tuple[list[Produto], int]:
```

**Lógica:**
- `apenas_deletados=False`: retorna produtos com `deletado_em IS NULL`
- `apenas_deletados=True`: retorna produtos com `deletado_em IS NOT NULL`
- `apenas_ativos=None`: não filtra por status ativo/inativo
- `apenas_ativos=True/False`: filtra por status (só quando `apenas_deletados=False`)

#### Método `deletar` alterado para soft delete:
```python
async def deletar(self, produto_id: UUID) -> bool:
    """Soft delete de um produto (marca como deletado)."""
    produto.deletado_em = datetime.utcnow()
```

#### Novo método `restaurar`:
```python
async def restaurar(self, produto_id: UUID) -> bool:
    """Restaura um produto deletado."""
    produto.deletado_em = None
```

### 3. Service (`services/produtos.py`)

#### Método `listar_produtos` simplificado:
```python
async def listar_produtos(
    self, 
    skip: int = 0, 
    limit: int = 10, 
    apenas_deletados: bool = False
):
    return await self.produto_repo.listar_todos(
        skip=skip, 
        limit=limit, 
        apenas_ativos=None,  # Não filtra por ativo/inativo
        apenas_deletados=apenas_deletados
    )
```

#### Novo método `restaurar_produto`:
```python
async def restaurar_produto(self, produto_id: UUID):
    """Restaura um produto deletado."""
```

### 4. Router (`routers/produtos.py`)

#### Endpoint GET `/produtos` alterado:
```python
@router_produtos.get("", response_model=dict)
async def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    apenas_deletados: bool = Query(False),  # Novo parâmetro
    session: AsyncSession = Depends(get_db),
):
```

#### Novo endpoint PATCH `/produtos/{id}/restaurar`:
```python
@router_produtos.patch("/{produto_id}/restaurar", status_code=204)
async def restaurar_produto(produto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Restaura um produto deletado."""
```

---

## Mudanças no Frontend

### 1. State (`ProdutosPage.tsx`)
```typescript
// Antes
const [statusFilter, setStatusFilter] = useState<'todos' | 'ativos' | 'inativos'>('ativos');

// Depois
const [statusFilter, setStatusFilter] = useState<'todos' | 'excluidos'>('todos');
```

### 2. Parâmetros da API
```typescript
// Antes
if (statusFilter === 'ativos') {
  params.apenas_ativos = true;
} else if (statusFilter === 'inativos') {
  params.apenas_ativos = false;
}

// Depois
params.apenas_deletados = statusFilter === 'excluidos';
```

### 3. Botões de Filtro
```tsx
{/* Antes */}
<button>Todos</button>
<button>Ativos</button>
<button>Inativos</button>

{/* Depois */}
<button>Todos</button>
<button>Excluídos</button>
```

### 4. Ações na Tabela
- **Filtro "Todos"**: mostra botões Ver, Editar e Excluir
- **Filtro "Excluídos"**: mostra apenas botão Restaurar

### 5. Função `handleRestore` (nova)
```typescript
const handleRestore = async (id: string, nome: string) => {
  await api.patch(`/produtos/${id}/restaurar`);
  toast.success('Produto restaurado com sucesso');
};
```

---

## Migration

### Arquivo: `alembic/versions/add_deletado_em_to_produtos.py`

```python
def upgrade() -> None:
    """Adiciona campo deletado_em para soft delete."""
    op.add_column(
        'produtos',
        sa.Column('deletado_em', sa.DateTime(), nullable=True),
        schema='produtos'
    )
    
    op.create_index(
        'ix_produtos_deletado_em',
        'produtos',
        ['deletado_em'],
        schema='produtos'
    )
```

---

## Como Aplicar as Mudanças

### 1. Rodar a migration
```bash
cd services/produtos
alembic upgrade head
```

### 2. Reiniciar o backend
```bash
docker-compose restart produtos
```

### 3. Rebuild do frontend (se necessário)
```bash
cd frontend
npm run build
```

---

## Testes Recomendados

1. **Listar produtos (filtro "Todos")**
   - GET `/produtos?apenas_deletados=false`
   - Deve retornar produtos ativos e inativos (não deletados)

2. **Listar produtos excluídos**
   - GET `/produtos?apenas_deletados=true`
   - Deve retornar apenas produtos com `deletado_em IS NOT NULL`

3. **Excluir produto**
   - DELETE `/produtos/{id}`
   - Deve marcar `deletado_em` com timestamp atual
   - Produto deve aparecer no filtro "Excluídos"

4. **Restaurar produto**
   - PATCH `/produtos/{id}/restaurar`
   - Deve limpar `deletado_em` (NULL)
   - Produto deve voltar para o filtro "Todos"

5. **Validações**
   - Tentar deletar produto já deletado → erro 400
   - Tentar restaurar produto não deletado → erro 400

---

## Impacto em Outros Módulos

### ⚠️ Atenção
Se outros serviços consultam produtos diretamente no banco, eles precisam adicionar o filtro:
```sql
WHERE deletado_em IS NULL
```

### Módulos que podem ser afetados:
- **Vendas**: ao buscar produtos disponíveis
- **Estoque**: ao listar produtos para movimentação
- **Catálogo Público**: já filtra por `ativo=True`, mas deve adicionar filtro de `deletado_em IS NULL`

---

## Próximos Passos (Opcional)

1. Implementar hard delete permanente (admin only)
2. Adicionar campo `deletado_por` (UUID do usuário)
3. Criar job para limpar produtos deletados há mais de X dias
4. Adicionar auditoria de restaurações
