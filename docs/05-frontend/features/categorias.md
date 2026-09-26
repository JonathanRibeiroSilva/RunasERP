# Categorias de produto — interface

**Verificado contra o código em:** 2026-09-26
**Frontend:** `frontend/src/pages/Produtos/CategoriasPage.tsx` (255 LOC) + `CategoriasPage.scss`
**Backend:** `services/produtos/routers/produtos.py:50-134` (`router_categorias`)

Categoria é pré-requisito de produto: `Produto.categoria_id` é
`nullable=False` (`services/produtos/models/produto.py:49-54`), então não há
cadastro de produto sem categoria existente.

---

## Acesso

- Rota: `/categorias` (`frontend/src/App.tsx:167`)
- Menu lateral: **Produtos → Categorias** (`Sidebar.tsx:82`)
- Sem `RoleProtectedRoute`: qualquer usuário autenticado que chegue ao
  `MainLayout` alcança a página.

---

## O que a página faz

| Operação | Como | Chamada |
|---|---|---|
| Listar | `useEffect` no mount, sem paginação | `api.get('/categorias?limit=100')` (`:40`) |
| Criar | Modal, campo `nome` obrigatório (`required` HTML5) | `api.post('/categorias', {...payload, empresa_id})` (`:65`) |
| Editar | Mesmo modal, pré-preenchido | `api.put('/categorias/{id}', payload)` (`:62`) |
| Excluir | `confirm()` nativo com o nome da categoria (`:99`) | `api.delete('/categorias/{id}')` (`:104`) |

Detalhes que costumam ser lembrados errado:

- **É um modal, não um formulário inline:** `.modal-overlay` / `.modal-content`
  em `:146-147`. Os botões são **Salvar** e **Cancelar**, iguais em criação e
  edição.
- **Não há badge de status.** O card mostra avatar com a primeira letra do nome
  (`:224`), nome e descrição. Nada de "Ativo/Inativo".
- **Não usa React Query para ler.** A lista vive em `useState` e é recarregada
  chamando `carregarCategorias()` à mão. O `useQueryClient` só serve para
  invalidar a chave `['categorias']` que *outras* páginas consomem
  (`:72`, `:106`).
- Estado vazio: "Nenhuma categoria cadastrada" (`:205`). Loading: spinner
  Bootstrap (`:121-131`).

### A gambiarra da cor

A página tem um campo **Cor** (color picker + hex, `maxLength 7`) que **não
existe no backend**. O valor é concatenado dentro da descrição com um separador
e desmontado na leitura:

```ts
// CategoriasPage.tsx:54-59
const payloadDescricao = formData.cor ? `${formData.descricao}::color::${formData.cor}` : formData.descricao;
const payload = { ...formData, descricao: payloadDescricao };
delete payload.cor;
```

```ts
// CategoriasPage.tsx:212-216 (e :84-88 na edição)
if (desc.includes('::color::')) { const parts = desc.split('::color::'); desc = parts[0]; color = parts[1]; }
```

Consequências reais: a cor consome o orçamento de 500 caracteres de `descricao`;
uma descrição que contenha `::color::` é truncada; e qualquer outro consumidor da
API (storefront, relatório) lê o marcador como texto da descrição.

---

## Contrato do backend (o que realmente volta)

`CategoriaRead` (`services/produtos/schemas/produtos.py:35-39`) expõe **quatro
campos**:

```python
empresa_id: int
nome: str          # max_length=100
descricao: str | None  # max_length=500
id: UUID
```

O modelo (`services/produtos/models/categoria.py`) tem exatamente essas colunas
— **não existe `ativo`, nem `criado_em`, nem `cor`**. A interface `Categoria` do
frontend (`CategoriasPage.tsx:9-16`) declara `cor?`, `ativo` e `criado_em`: os
três chegam sempre `undefined` do servidor. É tipo sem lastro, não contrato.

Unicidade é **por tenant**, não global:
`UniqueConstraint('empresa_id', 'nome')` (`models/categoria.py:16`).

### Endpoints

| Método | Rota | Status | Observação |
|---|---|---|---|
| POST | `/categorias` | 201 | `empresa_id` é **obrigatório no body** (`CategoriaBase`, `schemas/produtos.py:19`). Se divergir do header `X-Empresa-Id`, retorna **403** (`routers/produtos.py:61-62`) |
| GET | `/categorias` | 200 | Retorna `{total, skip, limit, items}`. Default do serviço é `limit=10` (`services/produtos.py:117`) — a página pede 100 |
| GET | `/categorias/{id}` | 200 | |
| PUT | `/categorias/{id}` | 200 | `CategoriaUpdate`: `nome` e `descricao`, ambos opcionais |
| DELETE | `/categorias/{id}` | 204 | |

### Exclusão é definitiva, não soft delete

`CategoriaRepository.deletar` chama `session.delete(categoria)`
(`repositories/produtos.py:106`). Não há coluna de soft delete na categoria — o
soft delete (`deletado_em`) existe em **Produto**, não em Categoria.

Não há verificação de produtos vinculados no serviço. A proteção vem do banco:
`ForeignKey("produtos.categorias.id", ondelete="RESTRICT")`
(`models/produto.py:51`). O `IntegrityError` resultante cai no
`except Exception` genérico do router (`routers/produtos.py:133-134`), então o
cliente recebe **500 "Erro ao deletar categoria"** — não um 400 explicativo.
Isso é um defeito, não o comportamento desejado.

---

## Erros por status

| Status | Corpo | Quando |
|---|---|---|
| 400 | `Categoria '<nome>' já existe` | Nome duplicado no mesmo tenant, em POST ou PUT (`services/produtos.py:107` e `:130`) |
| 400 | `Categoria com ID <id> não encontrada` | **PUT** de id inexistente: o router converte qualquer `ValueError` em 400 (`routers/produtos.py:115-116`), não em 404 |
| 403 | `empresa_id do body não corresponde ao header X-Empresa-Id` | Só no POST |
| 404 | `Categoria com ID <id> não encontrada` | GET e DELETE de id inexistente (`services/produtos.py:114`, `:138`) |
| 422 | erro de validação do FastAPI | POST sem `empresa_id`, ou `nome` acima de 100 / `descricao` acima de 500 caracteres |
| 500 | `Erro ao deletar categoria` | Exclusão de categoria com produtos vinculados (ver acima) |
| 500 | `Erro ao criar categoria` / `Erro ao atualizar categoria` | Qualquer exceção que não seja `ValueError` em POST / PUT (`routers/produtos.py:70-71`, `:117-118`) |

A página exibe essas mensagens via `getErrorMessage(error, ...)` em um toast
(`CategoriasPage.tsx:75`, `:109`).

---

## Dívidas conhecidas nesta tela

- Cor guardada dentro de `descricao` com separador `::color::` (ver acima).
- Exclusão bloqueada pelo banco devolve 500 em vez de 400.
- `ativo` / `criado_em` / `cor` tipados no frontend sem existirem na API.
- Sem paginação, busca ou ordenação: carrega até 100 registros e filtra nada.
- Leitura fora do React Query, ao contrário do resto do módulo de Produtos
  (ver `docs/05-frontend/frontend-architectural-debt-log.md`, H2 e C2).
- Sem `aria-label` nos botões de ícone (só `title`).

A CONFIRMAR: números de latência e cobertura de teste desta tela. Não há
benchmark nem teste automatizado de `CategoriasPage` no repositório — os nove
arquivos em `frontend/src/**/__tests__/` não cobrem esta página.

---

## Relacionados

- [API de Produtos e Categorias](../../10-api-reference/produtos-api.md)
- [Checklist de Desenvolvimento](../../02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md)
- [Design System — componentes](../design/componentes.md)
- [Regras de negócio — produtos](../../11-regras-negocio/produtos.md)
