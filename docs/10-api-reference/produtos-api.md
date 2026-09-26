# API de Produtos - Runas

> **Referência** da API do serviço de Produtos, conferida contra `services/produtos/routers/produtos.py`, `schemas/produtos.py`, `services/produtos.py`, `repositories/produtos.py` e `models/`.

---

## 📋 Visão Geral

**Porta do serviço**: `8002` (`services/produtos/Dockerfile`; no compose de dev fica em `127.0.0.1:8002`)
**Formato**: JSON

### Autenticação e tenant

O serviço **não valida JWT**. O api-gateway autentica e injeta os headers que o serviço trata como identidade:

| Header | Obrigatório | Função |
|--------|-------------|--------|
| `X-Empresa-Id` | Sim, nas rotas administrativas | ID da empresa (tenant). Ausente ou `<= 0`: **400**. |
| `X-Servico-Interno-Token` | Só quando `SERVICO_INTERNO_TOKEN` estiver configurado | Prova de origem interna (`interno.py`). `/health` é isento. |

As rotas **públicas** (`/loja-online/publico/*` e `/catalogo-publico/*`) não usam `X-Empresa-Id`: resolvem o tenant pelo parâmetro `empresaSlug` (a empresa precisa estar `ATIVA` com `catalogo_ativo = true`, senão 404).

Rotas que recebem `empresa_id` no corpo (`POST /categorias`, `/produtos`, `/variantes`, `/fornecedores`) respondem **403** se ele diferir do header.

### O que o gateway expõe

`api-gateway/routers/proxy.py` encaminha, exigindo usuário autenticado (qualquer papel): `/produtos`, `/categorias`, `/variantes`, `/fornecedores` e `/loja-online/*`. Sem autenticação: só `/loja-online/publico/*` (GET). **Não passam pelo gateway**: `/fornecedor-produtos/*` e `/catalogo-publico/*`; só são alcançáveis direto no serviço.

### Convenções

- Listagens retornam `{"total", "skip", "limit", "items"}` paginadas por `skip`/`limit` (padrão `limit=10`, máximo `100`; exceções indicadas). Não existe `page`/`size`/`pages`.
- Valores monetários são `Decimal` no serviço. A CONFIRMAR: se o JSON entrega número ou string (depende do serializador do Pydantic); os exemplos usam número por legibilidade.
- Os campos de data são `criado_em` / `atualizado_em`.

---

## 📍 Endpoints

| Verbo | Caminho | Status | Descrição |
|-------|---------|--------|-----------|
| POST | `/categorias` | 201 | Cria categoria |
| GET | `/categorias` | 200 | Lista categorias |
| GET | `/categorias/{id}` | 200 | Busca categoria |
| PUT | `/categorias/{id}` | 200 | Atualiza categoria |
| DELETE | `/categorias/{id}` | 204 | Exclui categoria |
| POST | `/produtos` | 201 | Cria produto |
| GET | `/produtos` | 200 | Lista produtos |
| GET | `/produtos/{id}` | 200 | Busca produto completo |
| GET | `/produtos/categoria/{categoria_id}` | 200 | Lista por categoria |
| GET | `/produtos/buscar/nome?nome=` | 200 | Busca por nome (mín. 3 caracteres) |
| PUT | `/produtos/{id}` | 200 | Atualiza produto |
| DELETE | `/produtos/{id}` | 204 | Soft delete |
| PATCH | `/produtos/{id}/restaurar` | 204 | Restaura produto deletado |
| POST | `/variantes` | 201 | Cria variante |
| GET | `/variantes/{id}` | 200 | Busca variante |
| GET | `/variantes/produto/{produto_id}` | 200 | Lista variantes do produto |
| PUT | `/variantes/{id}` | 200 | Atualiza variante |
| DELETE | `/variantes/{id}` | 204 | Exclui variante |
| POST | `/loja-online/config` | 201 | Cria config de exibição |
| GET | `/loja-online/config/{produto_id}` | 200 | Config de um produto |
| PUT | `/loja-online/config/{config_id}` | 200 | Atualiza config |
| GET | `/loja-online/produtos` | 200 | Produtos ativos com status de publicação |
| PUT | `/loja-online/produtos/{produto_id}/publicar` | 200 | Publica/despublica (upsert) |
| POST | `/loja-online/fotos` | 201 | Adiciona foto |
| GET | `/loja-online/fotos/{produto_id}` | 200 | Lista fotos |
| PUT | `/loja-online/fotos/{foto_id}` | 200 | Atualiza foto |
| DELETE | `/loja-online/fotos/{foto_id}` | 204 | Exclui foto |
| GET | `/loja-online/publico/produtos` | 200 | Vitrine pública |
| GET | `/loja-online/publico/categorias` | 200 | Categorias públicas |
| GET | `/loja-online/publico/produto/{id}` | 200 | Produto público |
| GET | `/catalogo-publico/produto/{id}` | 200 | Igual ao anterior (só direto no serviço) |
| POST | `/fornecedores` | 201 | Cria fornecedor |
| GET | `/fornecedores` | 200 | Lista fornecedores |
| GET | `/fornecedores/{id}` | 200 | Busca fornecedor |
| PUT | `/fornecedores/{id}` | 200 | Atualiza fornecedor |
| DELETE | `/fornecedores/{id}` | 204 | Exclui fornecedor |
| POST | `/fornecedor-produtos` | 201 | Vincula fornecedor a produto |
| GET | `/fornecedor-produtos/{vinculo_id}` | 200 | Busca vínculo |
| GET | `/fornecedor-produtos/produto/{produto_id}` | 200 | Fornecedores de um produto (array) |
| GET | `/fornecedor-produtos/fornecedor/{fornecedor_id}` | 200 | Produtos de um fornecedor (array) |
| PUT | `/fornecedor-produtos/{vinculo_id}` | 200 | Atualiza vínculo |
| DELETE | `/fornecedor-produtos/{vinculo_id}` | 204 | Exclui vínculo |

Atualizações usam **PUT** (não PATCH), exceto `restaurar`. Não existe `PATCH /produtos/{id}/variantes/...`, `POST /produtos/{id}/variantes`, `PATCH /produtos/{id}/catalogo`, `POST /produtos/{id}/catalogo/fotos`, `GET /catalogo` nem `POST /fornecedores/{id}/produtos`.

---

## 📂 Categorias

```http
POST /categorias
```
```json
{ "empresa_id": 1, "nome": "Bebidas", "descricao": "Bebidas em geral" }
```
`nome` 1 a 100 caracteres (obrigatório); `descricao` até 500.

**Response 201** (`CategoriaRead`): `id`, `empresa_id`, `nome`, `descricao`.

`GET /categorias` devolve `{"total","skip","limit","items":[...]}` (padrão `limit=10`). Nome duplicado na mesma empresa: **400** `Categoria 'X' já existe`; a comparação é **exata**, diferencia maiúsculas de minúsculas (e o banco tem `UNIQUE (empresa_id, nome)`). Atualizar categoria inexistente também dá **400**.

`DELETE /categorias/{id}`: 404 se não existir. Categoria com produtos vinculados é barrada pelo banco (`ON DELETE RESTRICT`), mas o router não trata essa exceção: a resposta é **500** `Erro ao deletar categoria`, não 409.

---

## 📦 Produtos

### Criar
```http
POST /produtos
```
```json
{
  "empresa_id": 1,
  "categoria_id": "uuid",
  "nome": "Coca-Cola",
  "descricao": "Refrigerante",
  "preco": 7.00,
  "custo": 5.00,
  "preco_promocional": 6.50,
  "promocao_fim": "2026-12-31",
  "unidade_medida": "UN",
  "ativo": true
}
```

Obrigatórios: `empresa_id`, `nome` (1 a 255) e `categoria_id`. `preco` e `custo` têm padrão `0.00` (`>= 0`). `unidade_medida` aceita `UN, KG, G, LT, ML, CX, PCT, FD, SC, PAR, M, CM` (padrão `UN`).

Validações (todas **400**): categoria inexistente na empresa; `preco < custo`; `preco_promocional > preco`; `preco_promocional` sem `promocao_fim`. `promocao_fim` é o último dia da promoção, inclusive, no fuso -03:00 (data no passado é aceita e encerra a promoção).

**Response 201** (`ProdutoRead`, mesmo formato do `GET /produtos/{id}` abaixo).

### Listar
```http
GET /produtos?skip=0&limit=10&busca=coca&categoria_id=<uuid>&apenas_deletados=false
```
- `busca` (mín. 1 caractere): nome, parcial e sem diferenciar maiúsculas.
- `categoria_id`: filtra por categoria.
- `apenas_deletados`: `false` (padrão) = produtos não deletados, **ativos e inativos**; `true` = só os deletados.
- Não existem `page`, `size`, `nome` nem `ativo` como parâmetros.

Cada item é `ProdutoReadSimples`: `id`, `empresa_id`, `categoria_id`, `nome`, `descricao`, `ativo`, `criado_em`, `preco`, `preco_promocional`, `promocao_fim`, `preco_efetivo`. **Sem `variantes`.**

`GET /produtos/categoria/{categoria_id}` (404 se a categoria não existir) devolve itens com o formato completo `ProdutoRead` e **inclui deletados**. `GET /produtos/buscar/nome?nome=` devolve um array simples (não o envelope) de `ProdutoReadSimples`.

### Buscar
```http
GET /produtos/{id}
```
**Response 200** (`ProdutoRead`):
```json
{
  "id": "uuid",
  "empresa_id": 1,
  "categoria_id": "uuid",
  "categoria": { "id": "uuid", "empresa_id": 1, "nome": "Bebidas", "descricao": null },
  "nome": "Coca-Cola",
  "descricao": "Refrigerante",
  "ativo": true,
  "criado_em": "2026-05-26T10:00:00",
  "preco": 7.00,
  "custo": 5.00,
  "preco_promocional": 6.50,
  "promocao_fim": "2026-12-31",
  "preco_efetivo": 6.50,
  "codigo_barras": null,
  "sku": null,
  "unidade_medida": "UN",
  "variantes": [],
  "loja_online_config": null,
  "loja_online_fotos": [],
  "fornecedores": []
}
```
`preco_efetivo` é o preço que vale hoje: o promocional enquanto `promocao_fim >= hoje` (fuso -03:00), senão `preco`. 404 se não existir; **produtos deletados também são retornados** (não há filtro de `deletado_em` neste GET).

### Atualizar, excluir, restaurar
- `PUT /produtos/{id}`: campos parciais (`nome`, `categoria_id`, `descricao`, `ativo`, `preco`, `custo`, `preco_promocional`, `promocao_fim`, `unidade_medida`). Só o que foi enviado é gravado, e `null` limpa campos anuláveis (descrição, promoção). As mesmas regras de preço/promoção valem sobre o **resultado** do PUT, e mudar `preco` também é recusado (**400**) se ficar abaixo do `preco_fornecedor` de algum vínculo. Produto inexistente aqui dá **400**, não 404.
- `DELETE /produtos/{id}`: **soft delete** (preenche `deletado_em`); nenhuma checagem de estoque, vendas ou variantes. 404 se não existir ou já estiver deletado. Variantes, fotos, config e vínculos permanecem.
- `PATCH /produtos/{id}/restaurar`: 204; 404 se não existir ou não estiver deletado.

---

## 🏷️ Variantes

### Criar
```http
POST /variantes
```
```json
{
  "empresa_id": 1,
  "produto_id": "uuid",
  "sku": "COCA-2L",
  "preco_custo": 5.00,
  "markup_pct": 40.0,
  "atributos": [ {"chave": "tamanho", "valor": "2L"} ]
}
```
`sku` 1 a 100; `preco_custo > 0`; `markup_pct >= 0`. **`preco_venda` é sempre calculado pelo servidor; se vier no corpo, é ignorado.**

```
preco_venda = preco_custo * (1 + markup_pct / 100)     # arredondado a 2 casas, ROUND_HALF_UP
5.00 * (1 + 40 / 100) = 7.00
```

**Response 201** (`VarianteRead`): `id`, `empresa_id`, `produto_id`, `sku`, `preco_custo`, `markup_pct`, `preco_venda`, `ativo`, `atributos` (`[{id, variante_id, chave, valor}]`). Produto inexistente ou SKU repetido na empresa: **400** (`SKU 'X' já existe`), não 409.

### Atualizar
```http
PUT /variantes/{id}
```
Campos opcionais: `sku`, `preco_custo`, `markup_pct`, `ativo`. Ao mudar custo ou markup, `preco_venda` é recalculado sobre o valor gravado (ex.: custo 5.50 e markup 45 dão 7.98). **Atributos não são editáveis por este endpoint.** Variante inexistente: **400**.

`GET /variantes/produto/{produto_id}` retorna array de `VarianteRead` (404 se o produto não existir). `DELETE /variantes/{id}` apaga de fato (sem checar estoque ou vendas).

---

## 🛒 Loja Online (catálogo público)

Não existe "catálogo" separado: a exibição é a `LojaOnlineConfig` (1:1 com o produto) e as `LojaOnlineFoto`.

### Publicar ou despublicar (rota usada pelo admin)
```http
PUT /loja-online/produtos/{produto_id}/publicar
```
```json
{ "visivel": true, "destaque": false }
```
Faz upsert da config (cria se não existir). 404 se o produto não existir. Retorna `LojaOnlineConfigRead`: `id`, `produto_id`, `visivel`, `destaque`, `ordem_exibicao`, `descricao_publica`, `atualizado_em`.

### Config completa
- `POST /loja-online/config`: `produto_id` + `visivel` (padrão `false`), `destaque` (padrão `false`), `ordem_exibicao` (`>= 0`, padrão 0), `descricao_publica`. **400** se o produto não existir ou já houver config.
- `PUT /loja-online/config/{config_id}`: atualiza pelo **ID da config**, não do produto. Inexistente: 400.
- `GET /loja-online/produtos?skip=0&limit=20`: produtos **ativos** da empresa com `visivel`, `destaque`, `ordem_exibicao`, `preco` (ordenados por nome).

### Fotos
```http
POST /loja-online/fotos
```
```json
{ "produto_id": "uuid", "url": "https://example.com/coca.jpg", "ordem": 0 }
```
`url` 1 a 500 caracteres (não é validada como URL); `ordem >= 0`. Resposta 201: `id`, `produto_id`, `url`, `ordem`. `GET /loja-online/fotos/{produto_id}` lista ordenado por `ordem`.

### Rotas públicas (sem autenticação)
```http
GET /loja-online/publico/produtos?empresaSlug=<slug>&categoria_id=&busca=&ordenar=nome&skip=0&limit=20
GET /loja-online/publico/categorias?empresaSlug=<slug>&skip=0&limit=100
GET /loja-online/publico/produto/{id}?empresaSlug=<slug>
```
- `empresaSlug` é obrigatório. Empresa inexistente, não `ATIVA` ou com catálogo desligado: 404.
- `produtos` lista só produtos **ativos, não deletados e com config `visivel = true`** (sem config = não publicado). `ordenar`: `nome` (padrão), `preco_asc`, `preco_desc`, `recentes`; `busca` mín. 2 caracteres; `limit` até 100. Itens no formato `ProdutoReadSimples`. `destaque` e `ordem_exibicao` **não** influenciam a ordenação.
- `categorias`: `limit` até 200; devolve todas as categorias da empresa, com ou sem produtos publicados.
- `produto/{id}` devolve `ProdutoLojaOnlineRead` (sem custo, markup nem fornecedores; variantes só com `id`, `preco_venda`, `ativo`, `atributos`). 404 se o produto estiver inativo. **Não verifica `visivel` nem `deletado_em`**, e não filtra variantes inativas.

**Exemplo:**
```bash
curl "http://localhost:8002/loja-online/publico/produtos?empresaSlug=distribuidora-central&limit=20"
```
Não há campo de estoque nessas respostas.

---

## 🏭 Fornecedores

```http
POST /fornecedores
```
```json
{
  "empresa_id": 1,
  "nome": "Distribuidora ABC Ltda",
  "cnpj": "12.345.678/0001-90",
  "email": "contato@abc.com",
  "telefone": "+5511999999999",
  "endereco": "Rua X, 100",
  "cidade": "São Paulo",
  "uf": "SP"
}
```
Só `empresa_id` e `nome` (1 a 255) são obrigatórios. `cnpj` até 18 caracteres, **sem validação de dígitos**; CNPJ repetido na empresa: **400**. O fornecedor não tem `razao_social`, `nome_fantasia` nem `prazo_entrega_dias` (o prazo é do vínculo). `ativo` no corpo do POST é ignorado (nasce ativo).

**Response 201** (`FornecedorRead`): os campos acima mais `id`, `ativo`, `criado_em`, `atualizado_em`.

`GET /fornecedores?skip=0&limit=10&apenas_ativos=true` devolve o envelope `{total, skip, limit, items}` (por padrão só ativos). `DELETE` apaga de fato (204) e leva junto os vínculos (cascade).

### Vincular fornecedor a produto
```http
POST /fornecedor-produtos
```
```json
{
  "fornecedor_id": "uuid",
  "produto_id": "uuid",
  "codigo_fornecedor": "ABC-COCA-2L",
  "preco_fornecedor": 5.00,
  "prazo_entrega_dias": 3,
  "quantidade_minima": 1
}
```
`preco_fornecedor > 0`; `prazo_entrega_dias >= 0` (padrão 0); `quantidade_minima >= 1` (padrão 1). **Response 201** (`FornecedorProdutoRead`): esses campos mais `id`, `ativo`, `criado_em`. **400** se fornecedor ou produto não existirem na empresa, ou se `preco_fornecedor` for maior que o `preco` de venda do produto. Não existe campo `principal`, `cod_fornecedor` nem `preco_custo` no vínculo.

---

## 🚨 Códigos de Erro

| Código | Quando |
|--------|--------|
| 400 | `ValueError` do serviço: dados inválidos, duplicidade (nome de categoria, SKU, CNPJ), regra de preço, referência inexistente em criação, **e também "não encontrado" em PUT/POST de atualização**; também `X-Empresa-Id` ausente ou `<= 0` |
| 403 | `empresa_id` do corpo diferente do header |
| 404 | "Não encontrado" em GET por ID, DELETE, `restaurar` e listagens por produto/categoria/fornecedor; slug inválido nas rotas públicas |
| 422 | Validação do Pydantic (campo faltando, tamanho, `preco_custo <= 0`, UUID inválido) |
| 500 | Erro interno, incluindo excluir categoria com produtos |

401/403 de permissão vêm do gateway.

---

## 💡 Casos de Uso

### Cadastrar produto completo

```bash
# 1. Categoria
curl -X POST http://localhost:8002/categorias   -H "X-Empresa-Id: 1" -H "Content-Type: application/json"   -d '{"empresa_id":1,"nome":"Bebidas"}'

# 2. Produto (usa o id da categoria)
curl -X POST http://localhost:8002/produtos   -H "X-Empresa-Id: 1" -H "Content-Type: application/json"   -d '{"empresa_id":1,"categoria_id":"<categoria_id>","nome":"Coca-Cola","preco":7.00,"custo":5.00}'

# 3. Variante
curl -X POST http://localhost:8002/variantes   -H "X-Empresa-Id: 1" -H "Content-Type: application/json"   -d '{"empresa_id":1,"produto_id":"<produto_id>","sku":"COCA-2L","preco_custo":5.00,"markup_pct":40,"atributos":[{"chave":"tamanho","valor":"2L"}]}'

# 4. Publicar na loja online
curl -X PUT http://localhost:8002/loja-online/produtos/<produto_id>/publicar   -H "X-Empresa-Id: 1" -H "Content-Type: application/json"   -d '{"visivel":true,"destaque":false}'
```

### Ajustar markup de todas as variantes

```python
import requests

BASE_URL = "http://localhost:8002"
H = {"X-Empresa-Id": "1"}

produtos = requests.get(f"{BASE_URL}/produtos", headers=H, params={"limit": 100}).json()["items"]
for p in produtos:
    # a listagem não traz variantes: busque-as por produto
    variantes = requests.get(f"{BASE_URL}/variantes/produto/{p['id']}", headers=H).json()
    for v in variantes:
        requests.put(
            f"{BASE_URL}/variantes/{v['id']}",
            headers=H,
            json={"markup_pct": float(v["markup_pct"]) + 10},
        )
```

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Produtos](../11-regras-negocio/produtos.md)
- [Mapeamento Completo de Rotas](./mapeamento-rotas.md)
- [OpenAPI Specification](./openapi.yaml)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Última revisão de conteúdo:** contra o código em 2026-09-26
