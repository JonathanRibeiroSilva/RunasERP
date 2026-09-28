# API de Clientes - Runas

> **Referência** da API do microsserviço de Clientes.
> Todos os endpoints abaixo foram lidos de `services/clientes/routers/clientes.py`,
> `services/clientes/routers/enderecos.py` e `services/clientes/schemas/cliente.py`.

---

## 📋 Visão Geral

**Porta do serviço**: `8001` (`docker-compose.dev.yml`, `CLIENTES_URL: http://clientes:8001`)
**Acesso direto em dev**: `http://127.0.0.1:8001` — o mapeamento é `"127.0.0.1:8001:8001"`, ou seja, só de localhost.
**Acesso pelo frontend**: `/api/clientes/...`; o nginx do frontend remove o prefixo `/api`
(`rewrite ^/api/(.*)$ /$1 break` em `frontend/nginx.conf`) e o api-gateway atende em `/clientes/...`.
**Formato**: JSON

---

## 🔐 Autenticação

**O serviço de clientes não valida JWT.** Ele exige apenas o header de tenant:

```http
X-Empresa-Id: 1
```

Sem esse header, qualquer rota responde **400** (`services/clientes/utils/tenant.py`).

Quem valida o JWT é o **api-gateway**: `/clientes` e `/clientes/{path}` dependem de
`get_current_active_user` (`api-gateway/routers/proxy.py:229` e `:250`), e o proxy
injeta `X-Empresa-Id` (e `X-Cliente-Id`, quando o portador é um cliente) a partir do
token — ver `_inject_context_headers` em `api-gateway/proxy/service_proxy.py`.

Portanto, pelo gateway:

```http
Authorization: Bearer <access_token>
```

Existe também um header de prova de origem interna, `X-Servico-Interno-Token`
(`services/clientes/interno.py`). Ele está **fail-open**: se o serviço não tiver
`SERVICO_INTERNO_TOKEN` configurado, ou se a requisição não trouxer o header,
a requisição passa. Só um valor *presente e diferente* resulta em **403**.

---

## 📍 Endpoints

Prefixo do router de clientes: `/clientes`.
Prefixo do router de endereços: `/clientes/{cliente_id}/enderecos`.

### Clientes

#### Listar Clientes
```http
GET /clientes
```

**Query Parameters:**
- `skip` (int, opcional): registros a pular (padrão: 0, mínimo 0)
- `limit` (int, opcional): máximo de registros (padrão: 100, entre 1 e 100)
- `nome` (string, opcional): busca parcial por nome **ou** CPF
- `cpf` (string, opcional): CPF exato
- `bloqueado` (boolean, opcional): filtra por status de bloqueio
- `ativo` (boolean, opcional): filtra por ativo/inativo

**Response 200:** a chave da lista é `clientes` (não `items`), e a paginação é por `skip`/`limit` (não `page`/`size`):
```json
{
  "clientes": [
    {
      "id": "3f2a...",
      "empresa_id": 1,
      "nome": "João Silva",
      "cpf": "12345678909",
      "telefone": "+5511999999999",
      "email": "joao@email.com",
      "data_nasc": "1990-01-15",
      "limite_credito": "1000.00",
      "credito_disponivel": "800.00",
      "dia_vencimento": 10,
      "bloqueado": false,
      "ativo": true,
      "criado_em": "2026-05-26T10:00:00Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 100
}
```

---

#### Buscar Cliente por ID
```http
GET /clientes/{cliente_id}
```

`cliente_id` é UUID. **Response 200:** um objeto no mesmo formato dos itens acima.

---

#### Buscar Cliente com Endereços
```http
GET /clientes/{cliente_id}/completo
```

**Response 200:** o cliente com o campo adicional `enderecos` (lista de endereços):
```json
{
  "id": "3f2a...",
  "nome": "João Silva",
  "enderecos": [
    {
      "id": "9b1c...",
      "cliente_id": "3f2a...",
      "cep": "01310100",
      "logradouro": "Av. Paulista",
      "numero": "1000",
      "complemento": "Apto 101",
      "bairro": "Bela Vista",
      "cidade": "São Paulo",
      "uf": "SP",
      "principal": true
    }
  ]
}
```

---

#### Buscar Cliente por CPF
```http
GET /clientes/cpf/{cpf}
```

**Response 200:** mesmo formato de `GET /clientes/{cliente_id}`.

---

#### Criar Cliente
```http
POST /clientes
```

**Request Body:** `empresa_id`, `nome`, `cpf` e `telefone` são **obrigatórios**;
`email` e `data_nasc` são opcionais. O `empresa_id` do body precisa ser igual ao
header `X-Empresa-Id`, senão a resposta é **400**.
```json
{
  "empresa_id": 1,
  "nome": "João Silva",
  "cpf": "12345678909",
  "telefone": "+5511999999999",
  "email": "joao@email.com",
  "data_nasc": "1990-01-15"
}
```

**Response 201:** cliente criado.
**409:** CPF já cadastrado para a empresa.

> `limite_credito` e `dia_vencimento` **não** fazem parte do corpo de criação
> (`ClienteCreate` herda só de `ClienteBase`). Use `PUT /clientes/{cliente_id}/credito`.

---

#### Criar Cliente via OAuth
```http
POST /clientes/oauth
```

Para cadastro vindo de login social (Google/Microsoft). `email` é obrigatório;
`cpf` e `telefone` são opcionais e podem ser preenchidos depois.

**Request Body:**
```json
{
  "empresa_id": 1,
  "nome": "João Silva",
  "email": "joao@email.com"
}
```

**Response 200** (e não 201): a operação é idempotente por email — pode retornar
um cliente já existente.

---

#### Atualizar Cliente
```http
PATCH /clientes/{cliente_id}
```

**Request Body:** só `nome`, `telefone`, `email` e `data_nasc` são atualizáveis
(`ClienteUpdate`); todos opcionais. CPF e `empresa_id` não são editáveis por aqui.
```json
{
  "nome": "João Silva Santos",
  "telefone": "+5511988888888",
  "email": "joao.novo@email.com"
}
```

**Response 200:** cliente atualizado.

---

#### Desativar Cliente (Soft Delete)
```http
DELETE /clientes/{cliente_id}
```

**Response 204:** cliente marcado como inativo; o registro permanece no banco.

---

#### Reativar Cliente
```http
POST /clientes/{cliente_id}/ativar
```

**Response 200:** cliente reativado.

---

### Endereços

#### Listar Endereços do Cliente
```http
GET /clientes/{cliente_id}/enderecos
```

**Response 200:** lista de endereços (array puro, sem envelope de paginação).
`cep` tem exatamente **8 dígitos, sem pontuação** (`min_length=8, max_length=8`).
```json
[
  {
    "id": "9b1c...",
    "cliente_id": "3f2a...",
    "cep": "01310100",
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "complemento": "Apto 101",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP",
    "principal": true
  }
]
```

---

#### Adicionar Endereço
```http
POST /clientes/{cliente_id}/enderecos
```

**Request Body:** `cep`, `logradouro`, `numero`, `bairro`, `cidade` e `uf` são
obrigatórios; `complemento` é opcional e `principal` tem padrão `false`.
```json
{
  "cep": "01310100",
  "logradouro": "Av. Paulista",
  "numero": "1000",
  "complemento": "Apto 101",
  "bairro": "Bela Vista",
  "cidade": "São Paulo",
  "uf": "SP",
  "principal": false
}
```

**Response 201:** endereço criado.

---

#### Atualizar Endereço
```http
PATCH /clientes/{cliente_id}/enderecos/{endereco_id}
```

**Request Body:** todos os campos de endereço, opcionais (`EnderecoUpdate`).

**Response 200:** endereço atualizado.

---

#### Remover Endereço
```http
DELETE /clientes/{cliente_id}/enderecos/{endereco_id}
```

**Response 204:** endereço removido.

---

### Gestão de Crédito

> Estas rotas passam pelo mesmo `/clientes/{path}` do gateway, que exige apenas
> usuário autenticado (`get_current_active_user`) — **não** há checagem de role
> ADMIN no gateway nem no serviço de clientes.

#### Definir Limite de Crédito
```http
PUT /clientes/{cliente_id}/credito
```

Atenção: é `PUT`, não `PATCH` (`@router.put` em `routers/clientes.py`).

**Request Body:** `limite_credito` obrigatório (`>= 0`); `dia_vencimento` opcional (1 a 28).
```json
{
  "limite_credito": 2000.00,
  "dia_vencimento": 15
}
```

**Response 200:** cliente com o crédito atualizado.

---

#### Ajustar Crédito Disponível
```http
POST /clientes/{cliente_id}/credito/ajustar
```

Aplica um delta ao `credito_disponivel`. Usado internamente pelos serviços de
Vendas e Financeiro.

**Request Body:**
```json
{
  "delta": -200.00
}
```

Positivo devolve crédito, negativo consome.

**Response 200:** cliente com o crédito ajustado.
**400:** o ajuste é inválido (o repositório recusa com `ValueError`, que o serviço traduz em 400).

---

#### Bloquear Cliente
```http
POST /clientes/{cliente_id}/bloquear
```

É `POST`, não `PATCH`. Cliente bloqueado não pode fazer compras fiadas.

**Response 200:** cliente bloqueado.

---

#### Desbloquear Cliente
```http
POST /clientes/{cliente_id}/desbloquear
```

É `POST`, não `PATCH`.

**Response 200:** cliente desbloqueado.

---

### Rotas do cliente logado (só no gateway)

Estas duas não existem no serviço de clientes — são atalhos do api-gateway
(`api-gateway/routers/proxy.py:68` e `:92`), que trocam o `me` pelo `cliente_id`
do JWT antes de repassar:

```http
GET   /clientes/me
PATCH /clientes/me
```

---

## 🚨 Códigos de Erro

O serviço de clientes levanta **400, 404, 409 e 500**; o 422 vem da validação do
Pydantic/FastAPI. **401 e 403 nascem no gateway** — o único 403 do próprio serviço
vem do `X-Servico-Interno-Token` inválido.

| Código | Descrição |
|--------|-----------|
| 400 | `X-Empresa-Id` ausente ou `<= 0`; `empresa_id` do body diferente do header; ajuste de crédito recusado |
| 401 | Não autenticado (gateway) |
| 403 | Bloqueio no gateway ou `X-Servico-Interno-Token` inválido |
| 404 | Cliente ou endereço não encontrado |
| 409 | CPF já cadastrado para a empresa |
| 422 | Validação de schema falhou (CPF inválido, telefone fora do E.164, CEP diferente de 8 dígitos, `uf` diferente de 2 letras) |
| 500 | Erro interno do servidor |

---

## 📚 Documentação Relacionada

- [Regras de Negócio - Clientes](../11-regras-negocio/clientes.md)
- [Mapeamento Completo de Rotas](./mapeamento-rotas.md)
- [Guia de Autenticação](./guia-autenticacao.md)

---

**Projeto:** Runas
**Serviço:** `services/clientes` (porta 8001)
