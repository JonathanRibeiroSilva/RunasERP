# Changelog - Fix: Nome Fantasia no Catálogo Público

## Data: 12/06/2026

---

## 🐛 Bug Fix: Endpoint Público Bloqueado

### Problema
- **Sintoma**: Catálogo público mostra "Catálogo de Produtos" em vez do nome fantasia da empresa
- **Erro**: Endpoint `/api/empresas/publico/distribuidora-central` retorna 401 (Unauthorized)
- **Impacto**: Nome fantasia configurado no seed não aparece no catálogo

### Causa Raiz
O API Gateway proxy tinha a rota `/empresas/*` configurada apenas para acesso de ADMIN:

```python
@router.api_route(
    "/empresas/{path:path}",
    methods=["GET", "PUT", "DELETE"],
    tags=["Empresas"],
)
async def proxy_empresas_path(
    request: Request,
    path: str,
    current_user: Annotated[Usuario, Depends(require_admin)]  # ← Bloqueio aqui
):
    """Proxy para serviço de empresas (apenas admin)."""
    full_path = f"/empresas/{path}"
    return await ServiceProxy.proxy_request(request, full_path, current_user)
```

Quando o catálogo público tentava acessar `/empresas/publico/distribuidora-central`, caía nessa rota protegida e retornava 401.

---

## ✅ Solução Implementada

Adicionada rota pública **ANTES** da rota protegida no `api-gateway/routers/proxy.py`:

```python
# NOVA ROTA PÚBLICA (deve vir ANTES da rota protegida)
@router.api_route(
    "/empresas/publico/{path:path}",
    methods=["GET"],
    tags=["Empresas Público"]
)
async def proxy_empresas_publico(request: Request, path: str):
    """Proxy para informações públicas de empresas (sem autenticação)."""
    full_path = f"/empresas/publico/{path}" if path else "/empresas/publico"
    return await ServiceProxy.proxy_request(request, full_path)  # ← SEM autenticação
```

### Por que funciona?
O FastAPI processa rotas na ordem em que são definidas. A rota mais específica (`/empresas/publico/*`) agora é verificada **antes** da rota genérica (`/empresas/*`).

---

## 🧪 Teste Manual

### Antes do Fix:
```bash
curl http://localhost/api/empresas/publico/distribuidora-central
# Retorno: 401 Unauthorized
```

### Depois do Fix:
```bash
curl http://localhost/api/empresas/publico/distribuidora-central
# Retorno: 200 OK
{
  "slug": "distribuidora-central",
  "nome_fantasia": "Distribuidora Central",
  "catalogo_titulo": "Catálogo Online - Distribuidora Central",
  "catalogo_descricao": "Alimentos e bebidas com os melhores preços da região!",
  ...
}
```

---

## 📋 Arquivos Modificados

```
api-gateway/routers/proxy.py
```

---

## 🚀 Como Testar

1. **Reiniciar o API Gateway**:
   ```bash
   docker-compose restart api-gateway
   ```

2. **Acessar o catálogo público** (sem login):
   ```
   http://localhost/c/distribuidora-central
   ```

3. **Verificar o título da página**:
   - ✅ Deve mostrar: `"🏪 Catálogo Online - Distribuidora Central"`
   - ✅ Descrição: `"Alimentos e bebidas com os melhores preços da região!"`

4. **Abrir console do navegador** (F12):
   - ✅ Request para `/api/empresas/publico/distribuidora-central` deve retornar 200
   - ✅ Não deve ter erros de autenticação

---

## 🎯 Resultado Esperado

### Catálogo Público:
```
┌────────────────────────────────────────────────┐
│ 🏪 Catálogo Online - Distribuidora Central    │
│ Alimentos e bebidas com os melhores preços!   │
│                                                 │
│ [Compartilhar] [WhatsApp]                      │
└────────────────────────────────────────────────┘
```

---

## 📝 Notas Técnicas

### Ordem das Rotas no FastAPI
FastAPI processa rotas na ordem de definição:
1. ✅ `/empresas/publico/{path}` (mais específica) → sem auth
2. ✅ `/empresas/{path}` (genérica) → com auth de ADMIN

Se a ordem fosse invertida, a rota genérica capturaria todas as requests, incluindo as públicas.

### Rotas Públicas no Gateway
Outras rotas públicas já implementadas:
- `/catalogo/*` - Catálogo público
- `/carrinho/*` - Carrinho de compras
- `/empresas/publico/*` - Informações públicas de empresas (NOVA)

---

## 🔗 Relacionado

- `CHANGELOG_LOJA_ONLINE_UX_IMPROVEMENTS.md` - Botão "Ver Minha Loja"
- `services/empresas/seed.py` - Seed com nomes fantasia
- `frontend/src/pages/CatalogoPublico/CatalogoPage.tsx` - Frontend do catálogo

---

## ✅ Status

- [x] Bug identificado
- [x] Causa raiz encontrada
- [x] Fix implementado
- [x] Changelog documentado
- [ ] Teste manual pelo usuário (AGUARDANDO)
- [ ] Commit: `fix(gateway): allow public access to /empresas/publico/* endpoint`

---

**Autor**: Kiro AI  
**Data**: 12/06/2026  
**Prioridade**: 🔴 Alta (bloqueava MVP do catálogo)
