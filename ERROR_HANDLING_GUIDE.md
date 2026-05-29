# 🚨 Guia de Error Handling - Runas ERP

> **Como funciona e boas práticas de tratamento de erros**
> 
> **Última atualização**: 27/05/2026

---

## 📋 Estado Atual

### ✅ O que já existe:

1. **Exceções customizadas** (`shared/exceptions.py`):
   - `RunasBaseException` - Base para todas as exceções
   - `ValidationError` - Erros de validação
   - `NotFoundError` - Recurso não encontrado
   - `ConflictError` - Conflitos (duplicação, etc)
   - `UnauthorizedError` - Não autenticado
   - `ForbiddenError` - Sem permissão
   - Exceções específicas de negócio (estoque, crédito, etc)

2. **Global Exception Handler** (em todos os `main.py`):
   ```python
   @app.exception_handler(Exception)
   async def global_exception_handler(request: Request, exc: Exception):
       log.error("unhandled_exception", error=str(exc), path=request.url.path)
       return JSONResponse(
           status_code=500,
           content={"detail": "Erro interno do servidor"}
       )
   ```

### ❌ O que falta:

1. **Handlers específicos** para cada tipo de exceção customizada
2. **Respostas padronizadas** com códigos HTTP corretos
3. **Detalhes úteis** nos erros (sem expor informações sensíveis)
4. **Rastreamento** com request_id
5. **Tratamento de HTTPException** do FastAPI

---

## 🎯 Como Funciona (Teoria)

### Fluxo de Erro no FastAPI

```
1. Requisição chega no endpoint
2. Código executa e lança exceção
3. FastAPI procura handler específico para aquela exceção
4. Se não encontrar, usa o handler genérico (Exception)
5. Retorna resposta JSON com erro
```


### Hierarquia de Handlers

```python
# Mais específico (procura primeiro)
@app.exception_handler(ValidationError)
async def validation_error_handler(...):
    return JSONResponse(status_code=400, ...)

@app.exception_handler(NotFoundError)
async def not_found_error_handler(...):
    return JSONResponse(status_code=404, ...)

# Menos específico (fallback)
@app.exception_handler(Exception)
async def global_exception_handler(...):
    return JSONResponse(status_code=500, ...)
```

---

## ✅ Boas Práticas (Recomendado)

### 1. Handler para Cada Tipo de Exceção

**Por quê?**: Retornar código HTTP correto e mensagem apropriada.

```python
# main.py
from shared.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
)

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Erros de validação de negócio (400 Bad Request)."""
    log.warning(
        "validation_error",
        error=exc.message,
        details=exc.details,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "validation_error",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Recurso não encontrado (404 Not Found)."""
    log.info(
        "not_found",
        error=exc.message,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "not_found",
            "message": exc.message
        }
    )

@app.exception_handler(ConflictError)
async def conflict_error_handler(request: Request, exc: ConflictError):
    """Conflito de dados (409 Conflict)."""
    log.warning(
        "conflict_error",
        error=exc.message,
        details=exc.details,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "conflict",
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(UnauthorizedError)
async def unauthorized_error_handler(request: Request, exc: UnauthorizedError):
    """Não autenticado (401 Unauthorized)."""
    log.warning(
        "unauthorized",
        error=exc.message,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "unauthorized",
            "message": exc.message
        }
    )

@app.exception_handler(ForbiddenError)
async def forbidden_error_handler(request: Request, exc: ForbiddenError):
    """Sem permissão (403 Forbidden)."""
    log.warning(
        "forbidden",
        error=exc.message,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "forbidden",
            "message": exc.message
        }
    )
```


### 2. Handler para HTTPException do FastAPI

**Por quê?**: FastAPI usa HTTPException internamente. Precisamos padronizar a resposta.

```python
from fastapi import HTTPException

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para HTTPException do FastAPI."""
    log.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail
        }
    )
```

### 3. Handler Global com Request ID

**Por quê?**: Rastrear erros entre microsserviços.

```python
import uuid

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções não tratadas."""
    request_id = str(uuid.uuid4())
    
    log.error(
        "unhandled_exception",
        request_id=request_id,
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True  # Inclui stack trace no log
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "Erro interno do servidor",
            "request_id": request_id  # Cliente pode reportar esse ID
        }
    )
```

---

## 🎨 Formato de Resposta Padronizado

### Sucesso (2xx)

```json
{
  "id": "uuid",
  "nome": "João Silva",
  "cpf": "12345678900"
}
```

### Erro (4xx, 5xx)

```json
{
  "error": "validation_error",
  "message": "CPF inválido",
  "details": {
    "field": "cpf",
    "value": "123",
    "reason": "CPF deve ter 11 dígitos"
  },
  "request_id": "uuid"  // Apenas em erros 500
}
```

---

## 📊 Mapeamento de Exceções → HTTP Status

| Exceção | HTTP Status | Quando Usar |
|---------|-------------|-------------|
| `ValidationError` | 400 Bad Request | Dados inválidos (CPF, email, etc) |
| `UnauthorizedError` | 401 Unauthorized | Não autenticado (sem token) |
| `ForbiddenError` | 403 Forbidden | Sem permissão (token válido mas sem acesso) |
| `NotFoundError` | 404 Not Found | Recurso não existe |
| `ConflictError` | 409 Conflict | Duplicação, estado inválido |
| `HTTPException` | Variável | Erros do FastAPI |
| `Exception` | 500 Internal Server Error | Erro não tratado |


---

## 💡 Exemplos de Uso

### No Service Layer

```python
# services/cliente_service.py
from shared.exceptions import ValidationError, NotFoundError, ConflictError

class ClienteService:
    async def criar_cliente(self, data: ClienteCreate) -> Cliente:
        # Verificar duplicação
        cliente_existente = await self.repo.buscar_por_cpf(data.cpf)
        if cliente_existente and cliente_existente.ativo:
            raise ConflictError(
                message="CPF já cadastrado",
                details={"cpf": data.cpf}
            )
        
        # Validar crédito
        if data.limite_credito < 0:
            raise ValidationError(
                message="Limite de crédito não pode ser negativo",
                details={"limite_credito": data.limite_credito}
            )
        
        return await self.repo.criar(data)
    
    async def buscar_cliente(self, cliente_id: UUID) -> Cliente:
        cliente = await self.repo.buscar_por_id(cliente_id)
        if not cliente:
            raise NotFoundError(
                message="Cliente não encontrado",
                details={"cliente_id": str(cliente_id)}
            )
        return cliente
```

### No Router

```python
# routers/clientes.py
@router.post("/", response_model=ClienteRead, status_code=201)
async def criar_cliente(
    data: ClienteCreate,
    session: AsyncSession = Depends(get_db)
):
    """
    Cria um novo cliente.
    
    Raises:
        ConflictError: CPF já cadastrado
        ValidationError: Dados inválidos
    """
    service = ClienteService(session)
    
    # Não precisa try/except aqui!
    # Os handlers globais vão pegar as exceções
    cliente = await service.criar_cliente(data)
    
    return cliente
```

---

## 🔍 Debugging e Logs

### Níveis de Log por Tipo de Erro

```python
# 400-499: WARNING (erro do cliente)
log.warning("validation_error", ...)
log.warning("conflict_error", ...)

# 404: INFO (recurso não encontrado é comum)
log.info("not_found", ...)

# 500: ERROR (erro do servidor)
log.error("unhandled_exception", exc_info=True, ...)
```

### Informações Úteis no Log

```python
log.error(
    "unhandled_exception",
    request_id=request_id,
    error=str(exc),
    error_type=type(exc).__name__,
    path=request.url.path,
    method=request.method,
    user_id=current_user.id if current_user else None,
    empresa_id=current_empresa.id if current_empresa else None,
    exc_info=True  # Stack trace completo
)
```

---

## ⚠️ O que NÃO fazer

### ❌ Expor Detalhes Internos

```python
# RUIM
return JSONResponse(
    status_code=500,
    content={"detail": str(exc)}  # Pode expor stack trace!
)

# BOM
return JSONResponse(
    status_code=500,
    content={
        "error": "internal_server_error",
        "message": "Erro interno do servidor",
        "request_id": request_id
    }
)
```

### ❌ Usar try/except em Todo Lugar

```python
# RUIM - Poluído
@router.post("/")
async def criar_cliente(data: ClienteCreate):
    try:
        service = ClienteService()
        try:
            cliente = await service.criar_cliente(data)
            return cliente
        except ValidationError as e:
            raise HTTPException(400, str(e))
        except ConflictError as e:
            raise HTTPException(409, str(e))
    except Exception as e:
        raise HTTPException(500, "Erro interno")

# BOM - Limpo
@router.post("/")
async def criar_cliente(data: ClienteCreate):
    service = ClienteService()
    cliente = await service.criar_cliente(data)
    return cliente
    # Handlers globais cuidam dos erros!
```

### ❌ Retornar Códigos HTTP Errados

```python
# RUIM
raise HTTPException(500, "Cliente não encontrado")  # 500 é erro do servidor!

# BOM
raise NotFoundError("Cliente não encontrado")  # Handler retorna 404
```

---

## 📋 Checklist de Implementação

### Para Cada Microsserviço:

- [ ] Adicionar handlers específicos para cada exceção customizada
- [ ] Adicionar handler para HTTPException
- [ ] Melhorar handler global com request_id
- [ ] Padronizar formato de resposta de erro
- [ ] Adicionar logs estruturados
- [ ] Testar cada tipo de erro
- [ ] Documentar erros no Swagger

### Exemplo de main.py Completo:

```python
# main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
import uuid
import structlog

from shared.exceptions import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
)

log = structlog.get_logger()
app = FastAPI()

# Handlers específicos
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    log.warning("validation_error", error=exc.message, details=exc.details)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "validation_error", "message": exc.message, "details": exc.details}
    )

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    log.info("not_found", error=exc.message)
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "not_found", "message": exc.message}
    )

@app.exception_handler(ConflictError)
async def conflict_error_handler(request: Request, exc: ConflictError):
    log.warning("conflict_error", error=exc.message, details=exc.details)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "conflict", "message": exc.message, "details": exc.details}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    log.warning("http_exception", status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())
    log.error("unhandled_exception", request_id=request_id, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "internal_server_error", "message": "Erro interno", "request_id": request_id}
    )
```

---

## 🎯 Benefícios

### ✅ Com Error Handlers Adequados:

1. **Códigos HTTP corretos**: 400, 404, 409, 500, etc.
2. **Mensagens claras**: Cliente sabe o que aconteceu
3. **Código limpo**: Sem try/except em todo lugar
4. **Rastreabilidade**: request_id para debugging
5. **Segurança**: Não expõe detalhes internos
6. **Logs estruturados**: Fácil de analisar
7. **Consistência**: Todas as APIs retornam o mesmo formato

### ❌ Sem Error Handlers:

1. Stack traces expostos ao cliente
2. Sempre retorna 500 (mesmo para erros do cliente)
3. Mensagens genéricas e inúteis
4. Difícil de debugar
5. Código poluído com try/except

---

## 🚀 Recomendação

**SIM, é uma EXCELENTE prática implementar!**

**Prioridade**: 🟡 ALTA

**Esforço**: 1-2 dias (implementar em todos os microsserviços)

**Benefícios**: 
- Melhor experiência do desenvolvedor frontend
- Debugging mais fácil
- Código mais limpo
- Produção mais estável

**Adicionar em**: `MELHORIAS_BACKEND_PRIORITARIAS.md` na seção de Prioridade Alta

---

**Documento criado em**: 27/05/2026  
**Responsável**: Equipe de Backend  
**Status**: Recomendação para implementação
