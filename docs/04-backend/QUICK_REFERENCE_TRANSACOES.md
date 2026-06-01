# Guia Rápido - Transações de Banco de Dados

> **Referência rápida** para implementar transações atômicas no Runas ERP

---

## 🚀 Template Básico

### Service com Transação Simples

```python
async def criar_recurso(self, dados: CreateSchema):
    """Cria um novo recurso com transação atômica."""
    try:
        async with self.session.begin_nested():
            # Validações
            if await self.repo.existe(dados.nome):
                raise ValueError("Recurso já existe")
            
            # Operação
            recurso = await self.repo.criar(**dados.model_dump())
        
        # Commit
        await self.session.commit()
        return recurso
        
    except ValueError:
        await self.session.rollback()
        raise
    except Exception as e:
        await self.session.rollback()
        log.error("erro_criar_recurso", error=str(e))
        raise
```

### Service com Transação Complexa

```python
async def operacao_complexa(db: AsyncSession, dados: Schema):
    """Operação com múltiplas ações atômicas."""
    try:
        async with db.begin_nested():
            # 1. Primeira operação
            obj1 = await Repo1.criar(db, ...)
            
            # 2. Segunda operação (depende da primeira)
            obj2 = await Repo2.criar(db, obj1_id=obj1.id, ...)
            
            # 3. Terceira operação
            obj3 = await Repo3.atualizar(db, ...)
        
        # Commit de tudo
        await db.commit()
        
        log.info("operacao_sucesso", obj1_id=obj1.id)
        return obj1, obj2, obj3
        
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        log.error("operacao_falhou", error=str(e))
        raise
```

### Router Simplificado

```python
@router.post("/recurso", response_model=Schema, status_code=201)
async def criar_recurso(
    dados: CreateSchema,
    db: AsyncSession = Depends(get_db)
):
    """Cria um novo recurso."""
    try:
        return await Service.criar(db, dados)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## ✅ Checklist de Implementação

### Antes de Começar
- [ ] Identificar todas as operações de banco na função
- [ ] Verificar se há operações que devem ser atômicas
- [ ] Planejar ordem das operações

### Durante a Implementação
- [ ] Usar `async with db.begin_nested():`
- [ ] Colocar todas as operações dentro do bloco
- [ ] Fazer `await db.commit()` após o bloco
- [ ] Adicionar `try/except` com rollback
- [ ] Adicionar logs de sucesso e erro

### Após Implementação
- [ ] Remover commits/rollbacks do router
- [ ] Testar cenário de sucesso
- [ ] Testar cenário de falha (rollback)
- [ ] Verificar logs
- [ ] Atualizar documentação

---

## 🎯 Padrões por Tipo de Operação

### CREATE (Criar)

```python
async def criar(self, dados):
    try:
        async with self.session.begin_nested():
            # Validar duplicidade
            if await self.repo.existe(dados.chave):
                raise ValueError("Já existe")
            
            # Criar
            obj = await self.repo.criar(**dados.model_dump())
        
        await self.session.commit()
        return obj
    except ValueError:
        await self.session.rollback()
        raise
    except Exception:
        await self.session.rollback()
        raise
```

### UPDATE (Atualizar)

```python
async def atualizar(self, id, dados):
    try:
        async with self.session.begin_nested():
            # Buscar
            obj = await self.repo.buscar(id)
            if not obj:
                raise ValueError("Não encontrado")
            
            # Validar mudanças
            if dados.campo and dados.campo != obj.campo:
                if await self.repo.existe_campo(dados.campo):
                    raise ValueError("Campo já existe")
            
            # Atualizar
            obj = await self.repo.atualizar(id, **dados.model_dump())
        
        await self.session.commit()
        return obj
    except ValueError:
        await self.session.rollback()
        raise
    except Exception:
        await self.session.rollback()
        raise
```

### DELETE (Deletar)

```python
async def deletar(self, id):
    try:
        async with self.session.begin_nested():
            # Buscar
            obj = await self.repo.buscar(id)
            if not obj:
                raise ValueError("Não encontrado")
            
            # Validar se pode deletar
            if await self.repo.tem_dependencias(id):
                raise ValueError("Possui dependências")
            
            # Deletar
            await self.repo.deletar(id)
        
        await self.session.commit()
    except ValueError:
        await self.session.rollback()
        raise
    except Exception:
        await self.session.rollback()
        raise
```

### OPERAÇÃO COMPLEXA (Múltiplas Ações)

```python
async def operacao_complexa(db, dados):
    try:
        async with db.begin_nested():
            # 1. Buscar/criar recurso principal
            principal = await Repo1.buscar_ou_criar(db, dados.id)
            
            # 2. Calcular valores
            valor_anterior = principal.valor
            valor_novo = valor_anterior + dados.incremento
            
            # 3. Registrar histórico
            historico = await Repo2.criar(db,
                recurso_id=principal.id,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
                tipo="INCREMENTO"
            )
            
            # 4. Atualizar recurso
            principal = await Repo1.atualizar(db, 
                principal.id, 
                valor=valor_novo
            )
            
            # 5. Criar registros relacionados
            for item in dados.itens:
                await Repo3.criar(db,
                    principal_id=principal.id,
                    historico_id=historico.id,
                    **item.model_dump()
                )
        
        await db.commit()
        log.info("operacao_sucesso", id=principal.id)
        return principal
        
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        log.error("operacao_falhou", error=str(e))
        raise
```

---

## ⚠️ Erros Comuns

### ❌ Commit no Repository

```python
# ERRADO
async def criar(self, **kwargs):
    obj = Model(**kwargs)
    self.session.add(obj)
    await self.session.commit()  # ❌ NÃO!
    return obj
```

```python
# CORRETO
async def criar(self, **kwargs):
    obj = Model(**kwargs)
    self.session.add(obj)
    await self.session.flush()  # ✅ Apenas flush
    return obj
```

### ❌ Commit no Router

```python
# ERRADO
@router.post("/recurso")
async def criar(dados, db):
    obj = await service.criar(db, dados)
    await db.commit()  # ❌ NÃO!
    return obj
```

```python
# CORRETO
@router.post("/recurso")
async def criar(dados, db):
    return await service.criar(db, dados)  # ✅ Service gerencia
```

### ❌ Sem Rollback

```python
# ERRADO
async def criar(self, dados):
    async with self.session.begin_nested():
        obj = await self.repo.criar(dados)
    await self.session.commit()
    return obj  # ❌ E se der erro?
```

```python
# CORRETO
async def criar(self, dados):
    try:
        async with self.session.begin_nested():
            obj = await self.repo.criar(dados)
        await self.session.commit()
        return obj
    except Exception:
        await self.session.rollback()  # ✅ Rollback!
        raise
```

### ❌ Operações Fora da Transação

```python
# ERRADO
async def operacao(db, dados):
    obj1 = await Repo1.criar(db, dados)  # ❌ Fora da transação
    
    async with db.begin_nested():
        obj2 = await Repo2.criar(db, obj1.id)
    
    await db.commit()
```

```python
# CORRETO
async def operacao(db, dados):
    try:
        async with db.begin_nested():
            obj1 = await Repo1.criar(db, dados)  # ✅ Dentro
            obj2 = await Repo2.criar(db, obj1.id)  # ✅ Dentro
        
        await db.commit()
    except Exception:
        await db.rollback()
        raise
```

---

## 📊 Fluxo de Execução

```
┌─────────────────────────────────────────┐
│         1. Router recebe request        │
│    - Valida dados (Pydantic)           │
│    - Injeta sessão DB                   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         2. Service inicia transação     │
│    async with db.begin_nested():        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      3. Validações de negócio           │
│    - Verifica duplicidade               │
│    - Valida regras                      │
│    - Lança ValueError se inválido       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      4. Operações de banco              │
│    - Repository.criar()                 │
│    - Repository.atualizar()             │
│    - Repository.criar_relacionado()     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         5. Commit ou Rollback           │
│    ✅ Sucesso: await db.commit()        │
│    ❌ Erro: await db.rollback()         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         6. Retorna ao Router            │
│    - Sucesso: retorna objeto            │
│    - Erro: lança exceção                │
└─────────────────────────────────────────┘
```

---

## 🔍 Debugging

### Ver Queries SQL

```python
# Ativar echo no engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True  # ✅ Mostra todas as queries
)
```

### Logs Estruturados

```python
import structlog

log = structlog.get_logger()

# Início da operação
log.info("operacao_iniciada", 
    usuario_id=usuario_id,
    dados=dados.model_dump()
)

# Sucesso
log.info("operacao_sucesso",
    recurso_id=recurso.id,
    tempo_ms=tempo
)

# Erro
log.error("operacao_falhou",
    error=str(e),
    stack_trace=traceback.format_exc()
)
```

### Verificar Estado da Transação

```python
# Dentro do service
print(f"In transaction: {db.in_transaction()}")
print(f"Is active: {db.is_active}")
```

---

## 📚 Documentação Completa

Para mais detalhes, consulte:

- **[Guia Completo de Transações](./transacoes-banco-dados.md)**
- **[README Backend](./README.md)**
- **[Changelog](../12-changelog/CHANGELOG.md)**

---

**Última atualização:** 2026-05-26  
**Versão:** 1.0.0
