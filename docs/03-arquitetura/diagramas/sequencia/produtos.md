# 📦 Diagramas de Sequência - Produtos

**Data**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Domínio**: Produtos

---

## 📑 Índice

1. [Criar Produto](#21-criar-produto)
2. [Criar Variante](#22-criar-variante)
3. [Listar Produtos com Filtros](#23-listar-produtos-com-filtros)
4. [Vincular Fornecedor ao Produto](#24-vincular-fornecedor-ao-produto)
5. [Atualizar Configuração de Catálogo](#25-atualizar-configuração-de-catálogo)

---

## 2.1. Criar Produto (POST /api/produtos)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant P as Produtos Service
    participant DB as PostgreSQL (Produtos)
    
    U->>G: POST /api/produtos<br/>{nome, categoria_id, descricao}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>P: POST /produtos
    
    Note over P: Validações
    P->>P: Validar nome (min 1, max 255)
    
    P->>DB: SELECT * FROM categorias<br/>WHERE id = {categoria_id}
    DB->>P: Categoria encontrada
    
    alt Categoria não existe
        P->>G: 400 Bad Request<br/>"Categoria não encontrada"
        G->>U: 400 Bad Request
    else Categoria existe
        P->>DB: INSERT INTO produtos<br/>(id, nome, categoria_id, ...)
        DB->>P: Produto criado (UUID)
        
        P->>DB: INSERT INTO catalogo_config<br/>(id, produto_id, visivel=false)
        DB->>P: Config criada
        
        P->>G: 201 Created<br/>{id, nome, categoria_id, ...}
        G->>U: 201 Created
    end
```

### Campos do Produto

```json
{
  "nome": "Coca-Cola 2L",
  "categoria_id": "uuid",
  "descricao": "Refrigerante Coca-Cola 2 litros",
  "marca": "Coca-Cola",
  "codigo_barras": "7894900011517",
  "unidade_medida": "UN",
  "ativo": true
}
```

### Regras de Negócio

- Nome é obrigatório (1-255 caracteres)
- Categoria deve existir no sistema
- Produto criado com `ativo = true` por padrão
- Configuração de catálogo criada automaticamente com `visivel = false`
- Código de barras é opcional mas deve ser único se fornecido

---

## 2.2. Criar Variante (POST /api/produtos/{id}/variantes)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant P as Produtos Service
    participant DB as PostgreSQL (Produtos)
    
    U->>G: POST /api/produtos/{uuid}/variantes<br/>{sku, preco_custo, markup_pct, atributos}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>P: POST /produtos/{uuid}/variantes
    
    P->>DB: SELECT * FROM produtos<br/>WHERE id = {uuid}
    DB->>P: Produto encontrado
    
    P->>DB: SELECT * FROM variantes<br/>WHERE sku = ?
    DB->>P: Verificar SKU único
    
    alt SKU já existe
        P->>G: 400 Bad Request<br/>"SKU já cadastrado"
        G->>U: 400 Bad Request
    else SKU disponível
        Note over P: Calcular preço de venda
        P->>P: preco_venda = preco_custo * (1 + markup_pct/100)
        
        P->>DB: INSERT INTO variantes<br/>(id, produto_id, sku, ...)
        DB->>P: Variante criada (UUID)
        
        loop Para cada atributo
            P->>DB: INSERT INTO atributos_variante<br/>(id, variante_id, chave, valor)
            DB->>P: Atributo criado
        end
        
        P->>G: 201 Created<br/>{id, sku, preco_venda, atributos: [...]}
        G->>U: 201 Created
    end
```

### O que são Variantes?

Variantes representam diferentes versões de um mesmo produto. Exemplos:

**Produto**: Camiseta Básica
- **Variante 1**: Tamanho P, Cor Branca (SKU: CAM-P-BCO)
- **Variante 2**: Tamanho M, Cor Preta (SKU: CAM-M-PTO)
- **Variante 3**: Tamanho G, Cor Azul (SKU: CAM-G-AZL)

**Produto**: Refrigerante Coca-Cola
- **Variante 1**: 350ml Lata (SKU: COCA-350-LT)
- **Variante 2**: 600ml PET (SKU: COCA-600-PT)
- **Variante 3**: 2L PET (SKU: COCA-2L-PT)

### Campos da Variante

```json
{
  "sku": "COCA-2L-PT",
  "preco_custo": 5.50,
  "markup_pct": 45.45,
  "preco_venda": 8.00,
  "codigo_barras": "7894900011517",
  "atributos": [
    {
      "chave": "tamanho",
      "valor": "2L"
    },
    {
      "chave": "embalagem",
      "valor": "PET"
    }
  ],
  "ativo": true
}
```

### Cálculo de Preço

```
preco_venda = preco_custo * (1 + markup_pct / 100)

Exemplo:
preco_custo = R$ 5,50
markup_pct = 45,45%
preco_venda = 5,50 * (1 + 45,45/100)
preco_venda = 5,50 * 1,4545
preco_venda = R$ 8,00
```

### Regras de Negócio

- SKU deve ser único no sistema
- Preço de venda é calculado automaticamente baseado no markup
- Atributos são flexíveis (chave-valor)
- Código de barras é opcional mas deve ser único se fornecido
- Variante criada com `ativo = true` por padrão

---

## 2.3. Listar Produtos com Filtros (GET /api/produtos)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant P as Produtos Service
    participant DB as PostgreSQL (Produtos)
    
    U->>G: GET /api/produtos?categoria_id={uuid}<br/>&ativo=true&page=1&limit=20
    G->>A: Validar Token JWT
    A->>G: Token válido
    
    G->>P: GET /produtos?categoria_id={uuid}<br/>&ativo=true&page=1&limit=20
    
    P->>DB: SELECT p.*, c.nome as categoria_nome<br/>FROM produtos p<br/>JOIN categorias c ON p.categoria_id = c.id<br/>WHERE p.categoria_id = {uuid}<br/>AND p.ativo = true<br/>LIMIT 20 OFFSET 0
    DB->>P: Lista de produtos
    
    loop Para cada produto
        P->>DB: SELECT * FROM variantes<br/>WHERE produto_id = {produto_id}<br/>AND ativo = true
        DB->>P: Variantes do produto
        
        P->>DB: SELECT * FROM catalogo_config<br/>WHERE produto_id = {produto_id}
        DB->>P: Config do catálogo
    end
    
    P->>DB: SELECT COUNT(*) FROM produtos<br/>WHERE categoria_id = {uuid}<br/>AND p.ativo = true
    DB->>P: Total de registros
    
    P->>G: 200 OK<br/>{items: [...], total: 100, page: 1}
    G->>U: 200 OK
```

### Filtros Disponíveis

- `nome` - Busca parcial (case-insensitive)
- `categoria_id` - Filtrar por categoria
- `marca` - Busca parcial
- `codigo_barras` - Busca exata
- `ativo` - true/false
- `visivel_catalogo` - Produtos visíveis no catálogo online
- `page` - Número da página (padrão: 1)
- `limit` - Itens por página (padrão: 20, máx: 100)

### Resposta Paginada

```json
{
  "items": [
    {
      "id": "uuid",
      "nome": "Coca-Cola",
      "categoria_id": "uuid",
      "categoria_nome": "Refrigerantes",
      "descricao": "Refrigerante Coca-Cola",
      "marca": "Coca-Cola",
      "ativo": true,
      "variantes": [
        {
          "id": "uuid",
          "sku": "COCA-2L-PT",
          "preco_venda": 8.00,
          "atributos": [
            {"chave": "tamanho", "valor": "2L"}
          ]
        }
      ],
      "catalogo": {
        "visivel": true,
        "destaque": false,
        "ordem": 1
      }
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

---

## 2.4. Vincular Fornecedor ao Produto (POST /api/fornecedores-produtos)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant P as Produtos Service
    participant DB as PostgreSQL (Produtos)
    
    U->>G: POST /api/fornecedores-produtos<br/>{fornecedor_id, produto_id, preco_fornecedor}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>P: POST /fornecedores-produtos
    
    P->>DB: SELECT * FROM fornecedores<br/>WHERE id = {fornecedor_id}
    DB->>P: Fornecedor encontrado
    
    P->>DB: SELECT * FROM produtos<br/>WHERE id = {produto_id}
    DB->>P: Produto encontrado
    
    alt Fornecedor ou Produto não existe
        P->>G: 404 Not Found
        G->>U: 404 Not Found
    else Ambos existem
        P->>DB: INSERT INTO fornecedor_produtos<br/>(id, fornecedor_id, produto_id, ...)
        DB->>P: Vínculo criado
        
        P->>G: 201 Created<br/>{id, fornecedor_id, produto_id, ...}
        G->>U: 201 Created
    end
```

### Gestão de Fornecedores

Um produto pode ter múltiplos fornecedores com preços diferentes.

**Exemplo**:
```json
{
  "produto_id": "uuid-coca-2l",
  "fornecedores": [
    {
      "fornecedor_id": "uuid-distribuidora-a",
      "fornecedor_nome": "Distribuidora A",
      "preco_fornecedor": 5.50,
      "prazo_entrega_dias": 2,
      "principal": true
    },
    {
      "fornecedor_id": "uuid-distribuidora-b",
      "fornecedor_nome": "Distribuidora B",
      "preco_fornecedor": 5.80,
      "prazo_entrega_dias": 1,
      "principal": false
    }
  ]
}
```

### Campos do Vínculo

```json
{
  "fornecedor_id": "uuid",
  "produto_id": "uuid",
  "preco_fornecedor": 5.50,
  "prazo_entrega_dias": 2,
  "quantidade_minima": 10,
  "principal": true,
  "ativo": true
}
```

### Regras de Negócio

- Produto pode ter múltiplos fornecedores
- Apenas um fornecedor pode ser marcado como `principal`
- Preço do fornecedor é usado como referência para cálculo de markup
- Prazo de entrega ajuda no planejamento de reposição

---

## 2.5. Atualizar Configuração de Catálogo (PUT /api/produtos/{id}/catalogo)

```mermaid
sequenceDiagram
    participant U as Usuário
    participant G as API Gateway
    participant A as Auth Service
    participant P as Produtos Service
    participant DB as PostgreSQL (Produtos)
    
    U->>G: PUT /api/produtos/{uuid}/catalogo<br/>{visivel: true, destaque: true}
    G->>A: Validar Token JWT
    A->>G: Token válido (role: ADMIN/GERENTE)
    
    G->>P: PUT /produtos/{uuid}/catalogo
    
    P->>DB: SELECT * FROM produtos<br/>WHERE id = {uuid}
    DB->>P: Produto encontrado
    
    P->>DB: SELECT * FROM catalogo_config<br/>WHERE produto_id = {uuid}
    DB->>P: Config encontrada
    
    P->>DB: UPDATE catalogo_config<br/>SET visivel=true, destaque=true<br/>WHERE produto_id = {uuid}
    DB->>P: Config atualizada
    
    P->>G: 200 OK<br/>{id, produto_id, visivel, destaque, ...}
    G->>U: 200 OK
```

### Configuração de Catálogo

Controla como o produto aparece no catálogo online/app.

**Campos**:
```json
{
  "produto_id": "uuid",
  "visivel": true,
  "destaque": true,
  "ordem": 1,
  "imagem_url": "https://cdn.runas.com/produtos/coca-2l.jpg",
  "descricao_curta": "Refrigerante Coca-Cola 2L",
  "tags": ["refrigerante", "coca-cola", "bebida"]
}
```

### Regras de Exibição

- `visivel = false`: Produto não aparece no catálogo (padrão ao criar)
- `visivel = true`: Produto aparece no catálogo
- `destaque = true`: Produto aparece em seção de destaques
- `ordem`: Define ordem de exibição (menor número = maior prioridade)

### Casos de Uso

1. **Lançamento de Produto**:
   - Criar produto com `visivel = false`
   - Configurar estoque, preços, imagens
   - Quando pronto: `visivel = true`

2. **Promoção**:
   - Marcar produto como `destaque = true`
   - Ajustar `ordem` para aparecer primeiro
   - Após promoção: `destaque = false`

3. **Produto Descontinuado**:
   - `visivel = false` (não aparece mais no catálogo)
   - `ativo = true` (ainda pode vender estoque restante)

---

## 📊 Resumo de Endpoints

| Método | Endpoint | Descrição | Permissão |
|--------|----------|-----------|-----------|
| POST | `/api/produtos` | Criar produto | ADMIN/GERENTE |
| GET | `/api/produtos` | Listar produtos | Todos |
| GET | `/api/produtos/{id}` | Buscar por ID | Todos |
| PUT | `/api/produtos/{id}` | Atualizar produto | ADMIN/GERENTE |
| DELETE | `/api/produtos/{id}` | Desativar produto | ADMIN |
| POST | `/api/produtos/{id}/variantes` | Criar variante | ADMIN/GERENTE |
| PUT | `/api/produtos/{id}/variantes/{variante_id}` | Atualizar variante | ADMIN/GERENTE |
| POST | `/api/fornecedores-produtos` | Vincular fornecedor | ADMIN/GERENTE |
| PUT | `/api/produtos/{id}/catalogo` | Config catálogo | ADMIN/GERENTE |

---

## 🔐 Permissões por Role

| Operação | ADMIN | GERENTE | VENDEDOR | OPERADOR |
|----------|-------|---------|----------|----------|
| Criar produto | ✅ | ✅ | ❌ | ❌ |
| Listar produtos | ✅ | ✅ | ✅ | ✅ |
| Buscar produto | ✅ | ✅ | ✅ | ✅ |
| Atualizar produto | ✅ | ✅ | ❌ | ❌ |
| Desativar produto | ✅ | ❌ | ❌ | ❌ |
| Gerenciar variantes | ✅ | ✅ | ❌ | ❌ |
| Gerenciar fornecedores | ✅ | ✅ | ❌ | ❌ |
| Config catálogo | ✅ | ✅ | ❌ | ❌ |

---

## 📚 Documentação Relacionada

- **[Regras de Negócio - Produtos](../../../11-regras-negocio/produtos.md)** - Regras detalhadas
- **[API Reference - Produtos](../../../10-api-reference/mapeamento-rotas.md#produtos)** - Referência completa
- **[Estoque](./estoque.md)** - Gestão de estoque de produtos
- **[Índice Geral](./README.md)** - Voltar ao índice

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Mantido por**: Equipe DenebCorp

---

<div align="center">

**[⬆ Voltar ao topo](#-diagramas-de-sequência---produtos)**

</div>
