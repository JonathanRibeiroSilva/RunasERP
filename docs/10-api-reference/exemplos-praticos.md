# Exemplos Práticos - Runas API

> Exemplos conferidos contra os schemas e as rotas do código (`api-gateway/routers/proxy.py`, `services/*/routers/`, `services/*/schemas/`). Onde uma rota não existe, o exemplo diz isso em vez de fingir que funciona.

---

## Convenções dos exemplos

- **`BASE_URL`**: o gateway. Em desenvolvimento, `http://localhost:8000` (`docker-compose.dev.yml`, serviço `api-gateway`). O caminho é **sem prefixo `/api`** quando se fala direto com o gateway; o `/api` só existe no nginx do frontend, que o remove antes de repassar (`frontend/nginx.conf`, `rewrite ^/api/(.*)$ /$1`).
- **Autenticação**: `Authorization: Bearer <access_token>`. O login é `POST /auth/login` com corpo **form-urlencoded** (`username` e `password`), não JSON (`api-gateway/routers/auth.py`, `OAuth2PasswordRequestForm`). A resposta traz `access_token`, `refresh_token` e `user`, e `user.empresa_id` é o tenant. Detalhes em [Guia de Autenticação](./guia-autenticacao.md).
- **`X-Empresa-Id`**: **não se envia ao gateway.** O gateway descarta qualquer `x-empresa-id` vindo do cliente e injeta o do token (`api-gateway/proxy/service_proxy.py`, `_inject_context_headers`). Só quem chama um serviço direto (porta 8001-8007, sem passar pelo gateway) precisa mandar o header.
- **`empresa_id` no corpo**: clientes, produtos, categorias, variantes e estoque exigem `empresa_id` no JSON de criação, e ele tem de ser igual ao do token (senão 400 em clientes, 403 em produtos e estoque). Os exemplos abaixo pegam o valor do login.
- **Papéis**: `/estoque/*` exige ADMIN ou OPERADOR (`require_admin_or_operador`); `/contas/*` e `/notificacoes/*` exigem ADMIN.

---

## Cenários Comuns

### 1. Cadastrar Cliente Completo

O limite de crédito e o dia de vencimento **não** entram no `POST /clientes`: `ClienteCreate` não tem esses campos (o Pydantic os ignora em silêncio). Eles são definidos depois, em `PUT /clientes/{id}/credito` (`limite_credito >= 0`, `dia_vencimento` de 1 a 28).

```bash
#!/bin/bash
BASE_URL="http://localhost:8000"
EMAIL="seu_email"
SENHA="sua_senha"

# 0. Login (form-urlencoded)
LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
  --data-urlencode "username=$EMAIL" \
  --data-urlencode "password=$SENHA")
TOKEN=$(echo "$LOGIN" | jq -r '.access_token')
EMPRESA_ID=$(echo "$LOGIN" | jq -r '.user.empresa_id')

# 1. Criar cliente (empresa_id, nome, cpf e telefone são obrigatórios)
CLIENTE_ID=$(curl -s -X POST "$BASE_URL/clientes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"empresa_id\": $EMPRESA_ID,
    \"cpf\": \"12345678909\",
    \"nome\": \"João Silva\",
    \"telefone\": \"+5511999999999\",
    \"email\": \"joao@email.com\"
  }" | jq -r '.id')

echo "Cliente criado: $CLIENTE_ID"

# 2. Definir limite de crédito e dia de vencimento
curl -s -X PUT "$BASE_URL/clientes/$CLIENTE_ID/credito" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"limite_credito": 1000.00, "dia_vencimento": 10}'

# 3. Adicionar endereço (cep com exatamente 8 dígitos, sem hífen)
curl -s -X POST "$BASE_URL/clientes/$CLIENTE_ID/enderecos" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cep": "01310100",
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP",
    "principal": true
  }'

echo "Endereço adicionado!"
```

O CPF precisa ter dígitos verificadores válidos (`validar_cpf`); o telefone é normalizado para E.164 (`+55...`).

---

### 2. Criar Produto com Variantes

A variante é criada em `POST /variantes` com `produto_id` **no corpo**. Não existe `POST /produtos/{id}/variantes`. O campo é `markup_pct`, e `preco_venda` é calculado pelo servidor a partir de `preco_custo` e `markup_pct` (o que vier no corpo é ignorado).

```python
import requests

BASE_URL = "http://localhost:8000"

# Login (form-urlencoded)
login = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "seu_email", "password": "sua_senha"},
).json()
EMPRESA_ID = login["user"]["empresa_id"]

headers = {"Authorization": f"Bearer {login['access_token']}"}

# 1. Criar categoria
categoria = requests.post(
    f"{BASE_URL}/categorias",
    headers=headers,
    json={"empresa_id": EMPRESA_ID, "nome": "Bebidas", "descricao": "Bebidas em geral"},
).json()

# 2. Criar produto (categoria_id é obrigatório; preco default 0.00)
produto = requests.post(
    f"{BASE_URL}/produtos",
    headers=headers,
    json={
        "empresa_id": EMPRESA_ID,
        "categoria_id": categoria["id"],
        "nome": "Coca-Cola",
        "descricao": "Refrigerante",
    },
).json()

# 3. Adicionar variantes
variantes = [
    {"tamanho": "2L", "preco_custo": 5.00, "markup": 40},
    {"tamanho": "1L", "preco_custo": 3.00, "markup": 45},
    {"tamanho": "600ml", "preco_custo": 2.00, "markup": 50},
]

for v in variantes:
    requests.post(
        f"{BASE_URL}/variantes",
        headers=headers,
        json={
            "empresa_id": EMPRESA_ID,
            "produto_id": produto["id"],
            "sku": f"COCA-{v['tamanho']}",
            "preco_custo": v["preco_custo"],
            "markup_pct": v["markup"],
            "atributos": [{"chave": "tamanho", "valor": v["tamanho"]}],
        },
    )

print("Produto criado com 3 variantes!")
```

---

### 3. Fluxo Completo de Venda (Loja Online)

O carrinho e o checkout públicos vivem em **`/loja/...`**, não em `/carrinho`. O gateway encaminha `/carrinho/*` para o serviço de vendas, mas o serviço não tem nenhum router nesse caminho, então essas chamadas não chegam a um handler. As rotas reais são `GET/DELETE /loja/carrinho`, `POST /loja/carrinho/itens`, `PUT/DELETE /loja/carrinho/itens/{produto_id}` e `POST /loja/checkout` (`services/vendas/routers/loja.py`).

Pontos que o exemplo respeita:

- Toda chamada leva `?empresaSlug=<slug-da-loja>` (o gateway resolve o tenant por ele) e a loja precisa estar com `catalogo_ativo` (senão 404 "Loja indisponível no momento").
- O carrinho é identificado pelo cookie `cart_session_id` (HttpOnly, 7 dias), definido pelo servidor. Por isso o `fetch` usa `credentials: 'include'`. No navegador, chame pelo `/api` do nginx do frontend (mesma origem); o CORS do gateway só libera `FRONTEND_URL`.
- Não existe QR Code na resposta do checkout. Pagamento online (PIX, DEBITO, CREDITO) devolve `mercadopago_init_point`, uma URL do Mercado Pago (Checkout Pro) para onde o cliente é redirecionado.
- `pagamentos` é uma lista, com no mínimo R$ 1,00 por item, e a soma tem de cobrir o total do carrinho mais o frete (senão 400). Só uma forma online é aceita por pedido.
- Endereço usa `estado` (não `uf`) e `cep` com 8 dígitos; é obrigatório para `DELIVERY`.

```typescript
// Frontend - Fluxo de compra no catálogo
const API = '/api';            // nginx do frontend remove o /api
const SLUG = 'minha-loja';     // slug da empresa

const q = `empresaSlug=${SLUG}`;
const opts = { credentials: 'include' as const };

class CheckoutFlow {
  // 1. Obter (ou criar) o carrinho: o servidor define o cookie cart_session_id
  async criarCarrinho() {
    const response = await fetch(`${API}/loja/carrinho?${q}`, opts);
    return response.json(); // { sessao_id, itens, subtotal, ... }
  }

  // 2. Adicionar produtos (variante_id é opcional)
  async adicionarProduto(produtoId: string, varianteId: string | null, quantidade: number) {
    const response = await fetch(`${API}/loja/carrinho/itens?${q}`, {
      ...opts,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        produto_id: produtoId,
        variante_id: varianteId,
        quantidade,
      }),
    });
    return response.json(); // carrinho atualizado
  }

  // 3. Finalizar compra (visitante: cliente_novo; cadastrado: cliente_id, nunca os dois)
  async finalizarCompra(total: number) {
    const response = await fetch(`${API}/loja/checkout?${q}`, {
      ...opts,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cliente_novo: {
          nome: 'João Silva',
          telefone: '11999999999',
        },
        tipo_entrega: 'RETIRADA',
        pagamentos: [{ forma_pagamento: 'PIX', valor: total }],
      }),
    });

    const pedido = await response.json();
    // { venda_id, numero_venda, status: 'PENDENTE_PAGAMENTO', valor_total, mercadopago_init_point, ... }

    // Pagamento online: redirecionar para o Mercado Pago
    if (pedido.mercadopago_init_point) {
      window.location.href = pedido.mercadopago_init_point;
    }
    return pedido;
  }
}

// Uso
const checkout = new CheckoutFlow();
const carrinho = await checkout.criarCarrinho();
await checkout.adicionarProduto('uuid-produto', 'uuid-variante', 2);
await checkout.finalizarCompra(/* subtotal do carrinho, mais o frete se DELIVERY */ 20.0);
```

Para `DELIVERY`, acrescente `endereco_entrega: { logradouro, numero, bairro, cidade, estado: 'SP', cep: '01310100' }` e some o frete ao `valor`. Depois do checkout, o pedido pode ser acompanhado em `GET /loja/rastrear/{numero_venda}?empresaSlug=...` (público). Regras do ciclo de vida da venda em [Regras de Negócio - Vendas](../11-regras-negocio/vendas.md).

---

### 4. Gestão de Estoque

A entrada é `POST /estoque/entrada` (201), com `produto_id`/`variante_id` **no corpo**. Não existe `POST /estoque/{id}/entrada`. `referencia_id` não é um campo; o número do documento vai em `documento` (máx. 100 caracteres). Se ainda não há registro de estoque para o produto/variante, a entrada o cria.

```python
# Script para receber mercadoria do fornecedor
import requests
from typing import List, Dict

BASE_URL = "http://localhost:8000"

login = requests.post(
    f"{BASE_URL}/auth/login",
    data={"username": "seu_email", "password": "sua_senha"},
).json()
EMPRESA_ID = login["user"]["empresa_id"]
HEADERS = {"Authorization": f"Bearer {login['access_token']}"}  # papel ADMIN ou OPERADOR


def receber_mercadoria(nota_fiscal: str, itens: List[Dict]):
    """
    Registra entrada de mercadoria no estoque

    Args:
        nota_fiscal: Número da nota fiscal
        itens: Lista de dicts com produto_id, variante_id, sku e quantidade
    """
    for item in itens:
        response = requests.post(
            f"{BASE_URL}/estoque/entrada",
            headers=HEADERS,
            json={
                "empresa_id": EMPRESA_ID,
                "produto_id": item["produto_id"],
                "variante_id": item["variante_id"],
                "quantidade": item["quantidade"],
                "motivo": f"NF {nota_fiscal}",
                "documento": nota_fiscal,
            },
        )

        if response.status_code == 201:
            print(f"OK {item['sku']}: +{item['quantidade']} unidades")
        else:
            print(f"Erro ao registrar {item['sku']}: {response.text}")


# Uso
receber_mercadoria("NF-12345", [
    {"produto_id": "uuid-produto", "variante_id": "uuid-1", "sku": "COCA-2L", "quantidade": 100},
    {"produto_id": "uuid-produto", "variante_id": "uuid-2", "sku": "COCA-1L", "quantidade": 150},
    {"produto_id": "uuid-produto", "variante_id": "uuid-3", "sku": "COCA-600ml", "quantidade": 200},
])
```

---

### 5. Relatório de Vendas

**O gateway não expõe a API administrativa de vendas.** `SERVICE_URLS` e `routers/proxy.py` só encaminham `/loja`, `/carrinho`, `/pagamentos` e `/integracoes` para o serviço de vendas; não há rota `/vendas` nem `/pedidos` no gateway. A listagem `GET /vendas` existe no serviço (`services/vendas/routers/vendas.py`), mas só se alcança direto na porta 8004, o que é possível em desenvolvimento (`127.0.0.1:8004`, `docker-compose.dev.yml`); em produção a porta não é publicada (`docker-compose.prod.yml`). **A CONFIRMAR:** se o frontend ou algum cliente precisa dessa listagem por meio do gateway; hoje não há caminho.

Chamando o serviço direto, o header `X-Empresa-Id` é obrigatório e, quando `SERVICO_INTERNO_TOKEN` está configurado no ambiente, também `X-Servico-Interno-Token` (vazio = o serviço deixa passar, `services/vendas/interno.py`). A paginação é `skip`/`limit` (`limit` até 1000), o filtro de período é `data_inicio`/`data_fim`, e a resposta é `{total, skip, limit, items}`, cada item com `valor_total` e `status`.

```python
# Gerar relatório de vendas do mês (chamando o serviço de vendas direto, só em dev)
import requests
from datetime import datetime
import pandas as pd

VENDAS_URL = "http://127.0.0.1:8004"
HEADERS = {"X-Empresa-Id": "1"}
# HEADERS["X-Servico-Interno-Token"] = "<SERVICO_INTERNO_TOKEN>"  # se estiver definido


def relatorio_vendas_mes():
    hoje = datetime.now()
    primeiro_dia = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    vendas = []
    skip = 0
    limit = 500

    while True:
        response = requests.get(
            f"{VENDAS_URL}/vendas",
            headers=HEADERS,
            params={
                "skip": skip,
                "limit": limit,
                "data_inicio": primeiro_dia.isoformat(),
                "data_fim": hoje.isoformat(),
            },
        )
        response.raise_for_status()
        data = response.json()
        vendas.extend(data["items"])

        skip += limit
        if skip >= data["total"]:
            break

    df = pd.DataFrame(vendas)
    df["valor_total"] = df["valor_total"].astype(float)  # garante tipo numérico

    print(f"Relatório de Vendas - {hoje.strftime('%m/%Y')}")
    print(f"Total de vendas: {len(df)}")
    print(f"Valor total: R$ {df['valor_total'].sum():.2f}")
    print(f"Ticket médio: R$ {df['valor_total'].mean():.2f}")
    print("\nPor status:")
    print(df.groupby('status')['valor_total'].agg(['count', 'sum']))

    df.to_excel(f"vendas_{hoje.strftime('%Y%m')}.xlsx", index=False)


relatorio_vendas_mes()
```

O serviço também tem `GET /vendas/relatorios/resumo` (`data_inicio` e `data_fim` obrigatórios), que devolve `total_vendas`, `valor_total`, `ticket_medio` e `por_status`.

---

### 6. Cobrança Automática

**Não há o que exemplificar.** O gateway encaminha `/contas/*` para o serviço financeiro, mas `services/financeiro/main.py` só expõe `GET /health` e não monta nenhum router. Não existe `GET /contas/vencer`, nem contas a receber, nem envio automático de lembrete por evento. O único WhatsApp que o sistema envia hoje é o do serviço de vendas, nas mudanças de status do pedido (`services/vendas/services/notificacao_service.py`). Ver o aviso em [Regras de Negócio - Índice](../11-regras-negocio/README.md).

---

### 7. Integração com Sistema Externo (Mercado Pago)

Não é preciso escrever um servidor intermediário: o serviço de vendas **já recebe** as notificações do Mercado Pago em `POST /loja/{empresa_slug}/webhook/mercadopago` (público, pelo catch-all `/loja/{path}` do gateway). Ele lê o pagamento na API do Mercado Pago pelo id, confirma a venda e dá baixa no estoque; não existe `PATCH /pagamentos/{id}/confirmar`.

A assinatura é conferida no próprio serviço (`services/vendas/services/webhook_assinatura.py`): o cabeçalho `x-signature` tem a forma `ts=<...>,v1=<hmac>`, e o `v1` é o HMAC-SHA256 hexadecimal do manifesto `id:<data.id>;request-id:<x-request-id>;ts:<ts>;`, calculado com o segredo de webhook gravado pelo lojista. Não é o HMAC do corpo JSON. Se o lojista não gravou o segredo, ou a notificação chega sem `x-signature` (IPN legado), o serviço só registra um aviso e processa (`routers/webhook.py`, `_conferir_assinatura`).

Para conferir se a URL está acessível:

```bash
curl "$BASE_URL/loja/minha-loja/webhook/mercadopago/test"
# {"status":"ok","message":"Webhook do Mercado Pago está acessível","empresa_slug":"minha-loja"}
```

A URL a cadastrar no painel do Mercado Pago é `https://<seu-dominio>/api/loja/<slug>/webhook/mercadopago` quando a entrada é o nginx do frontend, ou sem o `/api` quando a entrada é o gateway direto. **A CONFIRMAR:** qual URL está cadastrada no painel em produção.

---

## Coleções Postman

### Variáveis de Ambiente

```json
{
  "base_url": "http://localhost:8000",
  "access_token": "",
  "refresh_token": "",
  "empresa_id": "",
  "empresa_slug": ""
}
```

`empresa_id` e `empresa_slug` saem de `user.empresa_id` e `user.empresa_slug` na resposta do login.

---

## Scripts Úteis

### Backup de Dados

As listagens paginam por `skip` e `limit` (máximo 100 em clientes e em produtos; não existe `size`). A chave da lista é `clientes` em `/clientes` e `items` em `/produtos`.

```bash
#!/bin/bash
# backup.sh - Exportar dados via API

BASE_URL="http://localhost:8000"
DATA=$(date +%Y%m%d)

LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
  --data-urlencode "username=$EMAIL" \
  --data-urlencode "password=$SENHA")
TOKEN=$(echo "$LOGIN" | jq -r '.access_token')

# Pagina uma listagem: $1 = caminho, $2 = chave da lista, $3 = arquivo de saída
exportar() {
  local skip=0 total=1
  echo "[]" > "$3"
  while [ "$skip" -lt "$total" ]; do
    resp=$(curl -s "$BASE_URL/$1?skip=$skip&limit=100" -H "Authorization: Bearer $TOKEN")
    total=$(echo "$resp" | jq '.total')
    jq -s ".[0] + .[1].$2" "$3" <(echo "$resp") > "$3.tmp" && mv "$3.tmp" "$3"
    skip=$((skip + 100))
  done
}

exportar clientes clientes "backup_clientes_$DATA.json"
exportar produtos items "backup_produtos_$DATA.json"

echo "Backup concluído: $DATA"
```

---

## Documentação Relacionada

- [Guia de Autenticação](./guia-autenticacao.md)
- [Mapeamento de rotas do gateway](./mapeamento-rotas.md)
- [API de Clientes](./clientes-api.md)
- [API de Produtos](./produtos-api.md)
- [API de Estoque](./estoque-api.md)
- [API de Vendas](./vendas-api.md)
- [OpenAPI Specification](./openapi.yaml)

---

**Projeto:** Runas
**Equipe:** Equipe DenebCorp
**Data e versão:** A CONFIRMAR (o rodapé anterior dizia "26 de Maio de 2026, versão 1.0.0"; nenhuma fonte no repositório corrobora)
