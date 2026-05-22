# Correção de Erro de Serialização nos Endpoints de Listagem

**Data**: 22 de maio de 2026  
**Problema**: Erro 500 (PydanticSerializationError) ao listar registros  
**Causa**: Endpoints retornando objetos SQLAlchemy ao invés de schemas Pydantic

---

## 🔍 Problema Identificado

Os endpoints de listagem estavam retornando objetos SQLAlchemy diretamente, causando erro ao tentar serializar para JSON:

```
PydanticSerializationError: Unable to serialize unknown type: <class 'models.cliente.Cliente'>
```

### Causa Raiz

FastAPI espera que os endpoints retornem:
- Schemas Pydantic (que são serializáveis)
- Dicionários Python
- Tipos primitivos

Mas os endpoints estavam retornando:
- Objetos SQLAlchemy Model diretamente do banco de dados

---

## ✅ Serviços Corrigidos

### 1. **Serviço de Clientes** ✅

**Arquivo**: `services/clientes/routers/clientes.py`

**Endpoint corrigido**: `GET /clientes`

**Correção aplicada**:
```python
# ANTES (ERRADO)
clientes, total = await service.listar_clientes(skip, limit, nome, cpf, bloqueado)
return {
    "items": clientes,  # ❌ Objetos SQLAlchemy
    "total": total,
    "skip": skip,
    "limit": limit
}

# DEPOIS (CORRETO)
clientes, total = await service.listar_clientes(skip, limit, nome, cpf, bloqueado)
# Converter modelos SQLAlchemy para schemas Pydantic
clientes_response = [ClienteResponse.model_validate(cliente) for cliente in clientes]
return {
    "items": clientes_response,  # ✅ Schemas Pydantic
    "total": total,
    "skip": skip,
    "limit": limit
}
```

---

### 2. **Serviço de Produtos** ✅

**Arquivo**: `services/produtos/routers/produtos.py`

**Endpoints corrigidos**:

#### 2.1. `GET /categorias`
```python
categorias_response = [CategoriaRead.model_validate(cat) for cat in categorias]
return {"total": total, "skip": skip, "limit": limit, "items": categorias_response}
```

#### 2.2. `GET /produtos`
```python
produtos_response = [ProdutoRead.model_validate(prod) for prod in produtos]
return {"total": total, "skip": skip, "limit": limit, "items": produtos_response}
```

#### 2.3. `GET /produtos/categoria/{categoria_id}`
```python
produtos_response = [ProdutoRead.model_validate(prod) for prod in produtos]
return {"total": total, "skip": skip, "limit": limit, "items": produtos_response}
```

#### 2.4. `GET /produtos/buscar/nome`
```python
return [ProdutoReadSimples.model_validate(prod) for prod in produtos]
```

#### 2.5. `GET /variantes/produto/{produto_id}`
```python
return [VarianteRead.model_validate(var) for var in variantes]
```

#### 2.6. `GET /catalogo/fotos/{produto_id}`
```python
return [CatalogoFotoRead.model_validate(foto) for foto in fotos]
```

#### 2.7. `GET /fornecedores`
```python
fornecedores_response = [FornecedorRead.model_validate(forn) for forn in fornecedores]
return {"total": total, "skip": skip, "limit": limit, "items": fornecedores_response}
```

#### 2.8. `GET /fornecedor-produtos/produto/{produto_id}`
```python
return [FornecedorProdutoRead.model_validate(vinc) for vinc in vinculos]
```

#### 2.9. `GET /fornecedor-produtos/fornecedor/{fornecedor_id}`
```python
return [FornecedorProdutoRead.model_validate(vinc) for vinc in vinculos]
```

---

### 3. **Serviço de Estoque** ✅

**Status**: Já estava correto!

O serviço de estoque já fazia a conversão corretamente no service layer:

```python
# services/estoque/services/estoque_service.py
async def listar_estoques(...) -> List[EstoqueComAlerta]:
    estoques = await EstoqueRepository.listar(...)
    
    result = []
    for estoque in estoques:
        response = EstoqueComAlerta.model_validate(estoque)  # ✅ Já convertia
        response.alerta_estoque_baixo = ...
        response.alerta_estoque_zerado = ...
        result.append(response)
    
    return result
```

---

## 🔧 Padrão de Correção Aplicado

Para todos os endpoints de listagem, aplicamos o seguinte padrão:

```python
# 1. Buscar dados do repositório/service (retorna SQLAlchemy models)
items = await service.listar_items(...)

# 2. Converter para schemas Pydantic usando model_validate
items_response = [ItemSchema.model_validate(item) for item in items]

# 3. Retornar schemas Pydantic (serializáveis)
return items_response
# ou
return {"items": items_response, "total": total, ...}
```

---

## 📦 Rebuild e Deploy

### Containers Atualizados

```bash
# 1. Clientes
docker-compose build clientes
docker-compose up -d clientes

# 2. Produtos
docker-compose build produtos
docker-compose up -d produtos

# 3. Estoque (não precisou rebuild - já estava correto)
```

### Verificação

Após o deploy, todos os endpoints de listagem devem retornar JSON válido:

```bash
# Testar clientes
curl http://localhost:8001/clientes?skip=0&limit=10

# Testar produtos
curl http://localhost:8002/produtos?skip=0&limit=10

# Testar categorias
curl http://localhost:8002/categorias?skip=0&limit=10

# Testar estoque
curl http://localhost:8003/estoque?skip=0&limit=10
```

---

## 📚 Lições Aprendidas

### ✅ Boas Práticas

1. **Sempre converter SQLAlchemy → Pydantic nos endpoints**
   - Usar `Schema.model_validate(model)` para conversão
   - Nunca retornar objetos SQLAlchemy diretamente

2. **Duas abordagens válidas**:
   - **Service Layer**: Converter no service (como Estoque faz)
   - **Router Layer**: Converter no router (como Clientes e Produtos fazem agora)

3. **Preferência**: Converter no service layer
   - Mantém routers mais limpos
   - Reutilizável em múltiplos endpoints
   - Mais fácil de testar

### ⚠️ Armadilhas Comuns

1. **Não confiar apenas no `response_model`**
   - `response_model` valida a saída, mas não converte SQLAlchemy automaticamente
   - Precisa converter explicitamente antes de retornar

2. **Cuidado com relacionamentos**
   - SQLAlchemy lazy loading pode causar problemas
   - Use `selectinload()` ou `joinedload()` para carregar relacionamentos
   - Ou configure `from_attributes=True` nos schemas Pydantic

3. **List comprehension é seu amigo**
   ```python
   # ✅ Correto
   [Schema.model_validate(item) for item in items]
   
   # ❌ Errado
   items  # Retornar lista de SQLAlchemy models
   ```

---

## 🎯 Resultado Final

### Status dos Serviços

| Serviço | Status | Endpoints Corrigidos |
|---------|--------|---------------------|
| **Clientes** | ✅ Corrigido | 1 endpoint |
| **Produtos** | ✅ Corrigido | 9 endpoints |
| **Estoque** | ✅ Já estava OK | 0 (já correto) |
| **Vendas** | ⏳ Não verificado | - |
| **Financeiro** | ⏳ Não verificado | - |
| **Notificações** | ⏳ Não verificado | - |

### Próximos Passos

1. ✅ Testar todos os endpoints corrigidos
2. ⏳ Verificar serviços de Vendas, Financeiro e Notificações
3. ⏳ Aplicar mesma correção se necessário
4. ⏳ Adicionar testes automatizados para prevenir regressão

---

## 📝 Referências

- [Pydantic model_validate](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_validate)
- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
