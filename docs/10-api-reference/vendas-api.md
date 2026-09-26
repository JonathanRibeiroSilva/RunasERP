# API de Vendas - Runas

> Referência do serviço `services/vendas`, escrita a partir do código dos routers (`services/vendas/routers/`) e dos schemas (`services/vendas/schemas/`). O que não foi possível confirmar no código está marcado como **A CONFIRMAR**.

---

## Visão geral

| Item | Valor | Fonte |
|------|-------|-------|
| Porta do serviço | `8004` | `services/vendas/Dockerfile:18,22` |
| Formato | JSON | - |
| Health check | `GET /health` (isento da prova de origem interna) | `main.py`, `interno.py:31` |
| Docs interativas | `/docs` (FastAPI padrão) | `main.py` |

O serviço **não valida JWT**. Quem autentica é o API Gateway, que injeta os headers de identidade (ver [Identidade e tenant](#identidade-e-tenant)).

### O que o gateway expõe

O gateway (`api-gateway/routers/proxy.py`, `api-gateway/proxy/service_proxy.py:28-43`) só encaminha para o serviço de vendas os prefixos `/loja`, `/carrinho`, `/pagamentos` e `/integracoes`. Consequências, todas verificadas no código:

| Grupo de rotas do serviço | Alcançável pelo gateway? |
|---------------------------|--------------------------|
| `/loja/*` (carrinho, checkout, rastreio, meus pedidos, webhook) | Sim, catch-all `/loja/{path:path}` (`proxy.py:209`) e três rotas autenticadas de cliente (`proxy.py:116-203`) |
| `/pagamentos/admin/*` | Parcial: o gateway aceita só `GET`, `POST` e `PATCH` em `/pagamentos/{path:path}` (`proxy.py:452-455`). `PUT` e `DELETE` de `/pagamentos/admin/configuracao` **não passam** pelo gateway |
| `/integracoes` | Sim, `GET`/`PUT`/`DELETE`, só admin (`proxy.py:507-519`) |
| `/vendas/*` | **Não.** Não existe rota `/vendas` no gateway. O serviço só recebe essas chamadas de dentro da malha (ex.: exportação do tenant em `api-gateway/routers/plataforma.py:332`, que lê `GET /vendas`) |
| `/admin/entrega/*` | **Não.** Não há prefixo `/admin` em `SERVICE_URLS` nem rota equivalente no gateway |
| `/carrinho/*` | O gateway encaminha `/carrinho/{path}` para o serviço (`proxy.py:47`), mas o serviço **não tem** rota `/carrinho`: o carrinho vive em `/loja/carrinho`. Chamar `/carrinho/...` pelo gateway resulta em 404 vindo do serviço |

Em produção o frontend chama o gateway com o prefixo `/api`, que o nginx remove (`frontend/nginx.conf:24-36`). Ex.: `/api/loja/carrinho?empresaSlug=x` chega ao gateway como `/loja/carrinho?empresaSlug=x`.

### Identidade e tenant

Dois esquemas, conforme o router (`services/vendas/utils/tenant.py`):

- **Rotas administrativas** (`/vendas`, `/admin/entrega`, `/pagamentos/admin`, `/integracoes`): dependem do header `X-Empresa-Id` (inteiro > 0, senão 400). O gateway injeta o header a partir do usuário autenticado.
- **Rotas da loja** (`/loja/*`): dependem do query param `empresaSlug`. O serviço resolve o slug chamando `GET {EMPRESAS_URL}/empresas/publico/{slug}`; sem o param, 400; slug inexistente, 404; loja com `catalogo_ativo` falso, 404 `Loja indisponível no momento`.
- **Rotas de cliente logado** (`meus-pedidos`, `retry-payment`, `recuperar-carrinho`): além do slug, exigem `X-Cliente-Id`, injetado pelo gateway a partir do JWT do cliente. Sem o header, 401.
- **Prova de origem interna:** todo pedido (menos `/health`) deve trazer `X-Servico-Interno-Token`. O gateway o carimba. Enquanto `SERVICO_INTERNO_TOKEN` não estiver configurado, o serviço deixa passar e só registra warning (`interno.py:58-72`); token presente e errado devolve 403.

O gateway remove `x-empresa-id`, `x-cliente-id` e `x-servico-interno-token` enviados pelo cliente antes de injetar os seus (`api-gateway/proxy/service_proxy.py`, lista `for interno in (...)` em `proxy_request`).

---

## Loja online (público)

Prefixo `/loja`, tag `loja-online`. Todas as rotas exigem `?empresaSlug=<slug>`.

O carrinho fica no Redis, identificado pelo cookie `cart_session_id` (HttpOnly, `Path=/`, `Max-Age=604800` = 7 dias; `Secure` e `SameSite=None` quando `FRONTEND_URL` é `https://`, senão `SameSite=Lax`) (`routers/loja.py:30-44`). O TTL do carrinho no Redis também é de 7 dias e é renovado ao ler (`services/carrinho_service.py:38,87-88`).

### GET /loja/carrinho

Obtém o carrinho da sessão ou cria um novo. Se não houver cookie, gera uma sessão e devolve `Set-Cookie`. Se a sessão já virou venda e o carrinho foi limpo pelo webhook, gera uma sessão nova.

Resposta 200 (`CarrinhoResponse`):

```json
{
  "sessao_id": "string",
  "empresa_id": 1,
  "itens": [
    {
      "produto_id": "uuid",
      "variante_id": "uuid ou null",
      "quantidade": 2,
      "codigo_produto": "string ou null",
      "descricao_produto": "string",
      "preco_unitario": 49.90,
      "subtotal": 99.80,
      "estoque_disponivel": true
    }
  ],
  "subtotal": 99.80,
  "quantidade_itens": 1,
  "criado_em": "datetime",
  "atualizado_em": "datetime"
}
```

Erros: 400 (slug ausente), 404 (slug inexistente ou loja indisponível), 500.

### POST /loja/carrinho/itens

Adiciona item; se já existir, incrementa a quantidade. Devolve o carrinho completo (`CarrinhoResponse`), status 200.

```json
{ "produto_id": "uuid", "variante_id": "uuid (opcional)", "quantidade": 2 }
```

`quantidade` é `Decimal` maior que 0. Erros: 400 (`ValueError` do serviço, por exemplo estoque insuficiente), 422, 500.

### PUT /loja/carrinho/itens/{produto_id}

Atualiza a quantidade. O item é identificado por `produto_id` na URL e, opcionalmente, `?variante_id=<uuid>`. Exige o cookie `cart_session_id`. Devolve `CarrinhoResponse`.

```json
{ "quantidade": 5 }
```

Erros: 404 (`ValueError` do serviço), 422 (cookie ausente ou body inválido), 500.

### DELETE /loja/carrinho/itens/{produto_id}

Remove o item (`?variante_id=<uuid>` opcional). Exige o cookie. Resposta 200 com `CarrinhoResponse` (não é 204).

### DELETE /loja/carrinho

Limpa o carrinho. Exige o cookie. Resposta 200: `{"message": "Carrinho limpo com sucesso"}`.

### POST /loja/checkout

Converte o carrinho em venda com status `PEDIDO`, reserva estoque e limpa o carrinho (docstring de `processar_checkout`). Exige o cookie `cart_session_id`. Resposta com status 200 (o decorator não define `status_code`).

Request (`CheckoutRequest`):

```json
{
  "cliente_id": "uuid (ou cliente_novo, nunca os dois)",
  "cliente_novo": {
    "nome": "string (3-200)",
    "email": "string (opcional)",
    "telefone": "10 ou 11 digitos, com ou sem mascara",
    "cpf": "opcional, valida digitos verificadores"
  },
  "criar_conta": false,
  "tipo_entrega": "RETIRADA | DELIVERY",
  "endereco_entrega": {
    "logradouro": "string (3-200)",
    "numero": "string (max 20)",
    "complemento": "opcional",
    "bairro": "string (2-100)",
    "cidade": "string (2-100)",
    "estado": "UF de 2 letras",
    "cep": "8 digitos, sem mascara"
  },
  "pagamentos": [
    { "forma_pagamento": "PIX", "valor": 114.80 }
  ],
  "observacao": "string (max 500, opcional)"
}
```

Regras de validação (`schemas/loja.py`):

- Informar `cliente_id` **ou** `cliente_novo`; nenhum ou ambos dá 422.
- `endereco_entrega` é obrigatório quando `tipo_entrega=DELIVERY`.
- `pagamentos` tem ao menos 1 item, cada `valor >= 1.00`.
- No máximo **uma** forma online entre `PIX`, `DEBITO` e `CREDITO` por pedido. `DINHEIRO` e `FIADO` não entram nessa contagem.
- Formas válidas: `DINHEIRO`, `PIX`, `DEBITO`, `CREDITO`, `FIADO` (`models/venda.py:38-44`).

Resposta (`CheckoutResponse`):

```json
{
  "venda_id": "uuid",
  "numero_venda": "string",
  "status": "string",
  "valor_total": 114.80,
  "mercadopago_init_point": "url ou null",
  "mensagem": "Pedido criado com sucesso! Aguarde confirmação do pagamento.",
  "access_token": "string ou null (só se a conta foi criada)",
  "cliente_id": "uuid ou null",
  "conta_criada": false
}
```

Erros: 400 (`ValueError` do serviço), 422, 500.

**A CONFIRMAR:** formato de `numero_venda` (o exemplo do gateway usa `V-2024-001`, `proxy.py:161`, mas o gerador não foi conferido) e quais status podem voltar em `status` (`PEDIDO` ou `PENDENTE_PAGAMENTO`, conforme o fluxo de pagamento online); a regra de FIADO e o cálculo do frete no checkout ficam em `services/loja_service.py`, não conferido.

### GET /loja/rastrear/{numero_venda}

Público, sem autenticação de cliente. Resposta 200 (`RastreamentoPedido`): `numero_venda`, `status_atual`, `data_pedido`, `data_confirmacao`, `data_separacao`, `data_entregue`, `data_finalizada`, `data_cancelada`, `tipo_entrega`, `valor_total`, `historico` (lista de objetos livres), `proxima_etapa`, `previsao_entrega`. Erros: 404 (`Pedido {numero} não encontrado`), 500.

### GET /loja/meus-pedidos

Cliente autenticado (`X-Cliente-Id`). Query: `skip` (padrão 0), `limit` (padrão 20). Resposta 200: lista de `PedidoClienteResumido` (`id`, `numero_venda`, `data_pedido`, `status`, `valor_total`, `quantidade_itens`). Erros: 401 (sem `X-Cliente-Id`), 400 (id inválido), 500. No gateway exige `get_current_active_cliente`.

### POST /loja/pedidos/{numero_venda}/retry-payment

Cliente autenticado. Gera nova preferência do Mercado Pago para pedido com pagamento pendente. Só funciona se o pedido for do cliente e estiver em `PEDIDO` ou `PENDENTE_PAGAMENTO`; grava o novo `mercadopago_preference_id` e força o status `PENDENTE_PAGAMENTO`.

Resposta 200:

```json
{
  "success": true,
  "venda_id": "uuid",
  "numero_venda": "string",
  "mercadopago_url": "string",
  "mensagem": "Novo link de pagamento gerado com sucesso"
}
```

Erros: 404 (pedido), 403 (pedido de outro cliente), 400 (status não permite), 502 (não resolveu o slug da loja), 500 (falha do Mercado Pago ou sem link).

### POST /loja/pedidos/{numero_venda}/recuperar-carrinho

Cliente autenticado. Reconstrói o carrinho a partir dos itens de um pedido em `PEDIDO` ou `PENDENTE_PAGAMENTO`, numa **sessão nova** (novo cookie `cart_session_id`), e grava a nova sessão na venda. Itens sem estoque são omitidos e listados.

Resposta 200:

```json
{
  "success": true,
  "venda_id": "uuid",
  "numero_venda": "string",
  "nova_sessao_id": "string",
  "carrinho": { "...": "CarrinhoResponse" },
  "itens_adicionados": 2,
  "itens_sem_estoque": [
    { "descricao": "string", "quantidade_pedido": 1.0, "erro": "string" }
  ],
  "mensagem": "string"
}
```

Erros: 404, 403 (pedido de outro cliente), 400 (status não permite, ou nenhum item disponível em estoque), 500.

### Webhook do Mercado Pago

```http
POST /loja/{empresa_slug}/webhook/mercadopago
GET  /loja/{empresa_slug}/webhook/mercadopago/test
```

O slug vem **no caminho** (não usa `empresaSlug`). Pelo gateway cai no catch-all público `/loja/{path:path}`. Não existe `/pagamentos/webhook/mercadopago` no serviço de vendas, embora o gateway declare essa rota (`proxy.py:498`).

Comportamento (`routers/webhook.py`):

- Aceita Webhooks v2 (`type`/`action`/`data.id` no body) e IPN (`?topic=&id=`). Só processa `topic` igual a `payment` ou `merchant_order`; outro valor devolve 200 `{"status": "ignored", "reason": "Tipo não suportado"}`.
- Sem identificador de recurso: 400. Slug que não resolve empresa: 404.
- Assinatura: se o lojista gravou `mercadopago_webhook_secret` e a notificação traz `x-signature`, valida; inválida devolve 401. **Sem segredo gravado ou sem `x-signature`, a notificação é aceita** (só warning). Ou seja, hoje a rota aceita notificação não assinada.
- Para `merchant_order`, busca os pagamentos vinculados. Sem pagamentos: 200 `{"status": "ok", "reason": "Sem pagamentos para processar"}`.
- Sucesso: 200 `{"status": "ok", "payment_ids": ["..."]}`. Falha ao processar um pagamento: 500.
- O `/test` devolve 200 `{"status": "ok", "message": "Webhook do Mercado Pago está acessível", "empresa_slug": "..."}`.

**A CONFIRMAR:** a garantia de idempotência citada na docstring do webhook (implementada em `MercadoPagoService.processar_webhook_payment`, não conferida aqui).

---

## Vendas (administrativo, interno ao serviço)

Prefixo `/vendas`, tag `Vendas`. Exige `X-Empresa-Id`. **Não exposto pelo gateway** (ver a tabela acima); documentado porque existe no serviço e é usado dentro da malha.

### Ciclo de vida

Enum `StatusVenda` (`models/venda.py:13-23`): `PEDIDO`, `PENDENTE_PAGAMENTO`, `CONFIRMADA`, `SEPARADA`, `EM_ENTREGA`, `ENTREGUE`, `FINALIZADA`, `CANCELADA`, `REEMBOLSADA`.

Transições que os endpoints implementam (docstrings de `routers/vendas.py`):

```
PEDIDO --confirmar--> CONFIRMADA --separar--> SEPARADA --entregar--> ENTREGUE --finalizar--> FINALIZADA
PEDIDO / CONFIRMADA / SEPARADA --cancelar--> CANCELADA
```

Nenhuma rota de `routers/vendas.py` leva a `EM_ENTREGA`, `PENDENTE_PAGAMENTO` ou `REEMBOLSADA` (`PENDENTE_PAGAMENTO` é gravado pelo `retry-payment` em `loja.py`). `REEMBOLSADA` é atribuída pelo fluxo de reembolso (`VendaService.reembolsar_venda` e `MercadoPagoService.processar_webhook_payment`), sem rota própria no router de vendas. **A CONFIRMAR:** quem atribui `EM_ENTREGA` (só aparece no enum e no texto de rastreio de `loja_service.py`).

### POST /vendas

Cria venda com status `PEDIDO` e reserva estoque. Resposta **201** (`VendaDetalhada`). `empresa_id` do body precisa ser igual ao header `X-Empresa-Id`, senão 403. Erros: 400 (`ValueError`, ex.: produto ou cliente inválido), 422.

```json
{
  "empresa_id": 1,
  "cliente_id": "uuid (opcional, venda balcão)",
  "tipo_entrega": "RETIRADA",
  "observacao": "string",
  "itens": [
    { "produto_id": "uuid", "variante_id": "uuid (opcional)", "quantidade": 2,
      "codigo_produto": "opcional", "descricao_produto": "opcional" }
  ],
  "desconto_tipo": "PERCENTUAL | VALOR_FIXO",
  "desconto_valor": 0
}
```

- `itens` tem ao menos 1 item. O item **não aceita `preco_unitario`**: o preço vem do catálogo, e o campo enviado dá 422 (`extra="forbid"`, `schemas/venda.py:23-35`).
- `desconto_valor > 0` exige `desconto_tipo`; `PERCENTUAL` não passa de 100.
- `tipo_entrega` padrão: `RETIRADA`; outro valor: `DELIVERY`.

### GET /vendas

Query: `skip` (padrão 0, min 0), `limit` (padrão 100, 1 a 1000), `status_filtro` (enum `StatusVenda`), `cliente_id` (uuid), `data_inicio` e `data_fim` (datetime). Note que o parâmetro se chama **`status_filtro`**, não `status`. Resposta 200: `{"total": n, "skip": n, "limit": n, "items": [...]}` (sem `page`/`size`/`pages`; `response_model=dict`, sem schema tipado dos itens).

### GET /vendas/{venda_id}

Resposta 200 (`VendaDetalhada`): campos de `VendaResponse` (`id`, `empresa_id`, `cliente_id`, `tipo_entrega`, `observacao`, `numero_venda`, `subtotal`, `desconto_tipo`, `desconto_valor`, `valor_total`, `status`, `data_pedido`, `data_confirmacao`, `data_separacao`, `data_entregue`, `data_finalizada`, `data_cancelada`, `motivo_cancelamento`, `cancelada_por`, `created_at`, `updated_at`) mais `itens` e `pagamentos`. Cada item traz `id`, `venda_id`, `produto_id`, `variante_id`, `codigo_produto`, `descricao_produto`, `quantidade`, `preco_unitario`, `subtotal`, `estoque_reservado`, `estoque_baixado`, `created_at`. 404 se não existir.

### PUT /vendas/{venda_id}

Atualiza a venda **somente em `PEDIDO`**. Todos os campos são opcionais: `cliente_id`, `tipo_entrega`, `observacao`, `desconto_tipo`, `desconto_valor`. Erros: 404, 400.

### POST /vendas/{venda_id}/confirmar

`PEDIDO` para `CONFIRMADA`, registrando os pagamentos. Body:

```json
{
  "pagamentos": [
    { "forma_pagamento": "DINHEIRO", "valor_pago": 120.00, "valor_recebido": 150.00, "comprovante": "opcional" }
  ]
}
```

`pagamentos` com ao menos 1 item; `valor_pago > 0`; `valor_recebido` só é aceito para `DINHEIRO` (senão 422). Regras da docstring: soma dos pagamentos maior ou igual ao total; `FIADO` exige cliente identificado; troco calculado para `DINHEIRO`. Erro de regra: 400.

### POST /vendas/{venda_id}/separar

`CONFIRMADA` para `SEPARADA`. Sem body. Erro de regra: 400.

### POST /vendas/{venda_id}/entregar

`SEPARADA` para `ENTREGUE`; baixa o estoque no serviço de Estoque e marca os itens com `estoque_baixado`. Sem body. Erro de regra: 400.

### POST /vendas/{venda_id}/finalizar

`ENTREGUE` para `FINALIZADA`. Sem body. A docstring diz que a criação de conta a receber para `FIADO` no Financeiro é "futuro" (não implementada). Erro de regra: 400.

### POST /vendas/{venda_id}/cancelar

Permitido em `PEDIDO`, `CONFIRMADA` e `SEPARADA`; libera as reservas de estoque. Body:

```json
{ "motivo": "string (10 a 500 caracteres)", "usuario_id": "uuid (opcional)" }
```

Erros: 400 (regra de negócio, ex.: status não permite), 503 quando o serviço de estoque não respondeu (`EstoqueIndeterminadoError`): nada foi cancelado e é seguro repetir. Para venda `ENTREGUE` ou `FINALIZADA` a docstring manda usar devolução.

### GET /vendas/{venda_id}/pagamentos

Lista de `PagamentoVendaResponse` (`id`, `venda_id`, `forma_pagamento`, `valor_pago`, `valor_recebido`, `valor_troco`, `gera_conta_receber`, `conta_receber_id`, `comprovante`, `data_pagamento`, `created_at`). 404 se a venda não existir.

### POST /vendas/{venda_id}/pagamentos

Adiciona pagamento adicional. Resposta **201** (`PagamentoVendaResponse`). Body: `forma_pagamento`, `valor_pago` (> 0), `valor_recebido` (opcional), `comprovante` (opcional, máx 200). Recusa venda `CANCELADA` ou `FINALIZADA` (400) e `FIADO` sem cliente (400). `gera_conta_receber` fica `true` para `FIADO`.

### GET /vendas/relatorios/resumo

Query obrigatória: `data_inicio` e `data_fim` (datetime). Resposta 200:

```json
{
  "periodo_inicio": "datetime",
  "periodo_fim": "datetime",
  "total_vendas": 0,
  "valor_total": 0.0,
  "ticket_medio": 0.0,
  "por_status": { "PEDIDO": { "count": 1, "valor": 10.0 } }
}
```

Considera no máximo 10000 vendas no período (`limit=10000`, `vendas.py:344`).

---

## Configuração de pagamento (Mercado Pago)

Prefixo `/pagamentos/admin`, exige `X-Empresa-Id`. Pelo gateway: só admin/operador logado (`get_current_active_user`) e só `GET`/`POST`/`PATCH`.

| Verbo e caminho | Função | Resposta |
|-----------------|--------|----------|
| `GET /pagamentos/admin/status` | Diz se há configuração, sem expor credenciais | 200 `{configurado, ativo, webhook_assinatura_configurada, ultima_atualizacao}` |
| `GET /pagamentos/admin/configuracao` | Lê a configuração | 200 `ConfiguracaoPagamentoResponse`; 404 se não houver |
| `POST /pagamentos/admin/configuracao` | Cria | **201**; 409 se já existir |
| `PUT /pagamentos/admin/configuracao` | Atualiza | 200; 404 se não existir. **Não passa pelo gateway** |
| `PATCH /pagamentos/admin/configuracao/ativar` | Ativa | 200; 404 se não existir |
| `PATCH /pagamentos/admin/configuracao/desativar` | Desativa | 200; 404 se não existir |
| `DELETE /pagamentos/admin/configuracao` | Remove (irreversível) | 200 `{"message": "Configuração de pagamento deletada com sucesso"}`; 404. **Não passa pelo gateway** |

Body de `POST` e `PUT` (mesmos campos): `mercadopago_access_token` (string, mín. 20), `mercadopago_public_key` (string, mín. 20), `mercadopago_webhook_secret` (opcional, mín. 1; vazio mantém o gravado), `ativo` (padrão `true`).

`ConfiguracaoPagamentoResponse`: `id`, `empresa_id`, `mercadopago_public_key`, `ativo`, `created_at`, `updated_at`. O `access_token` e o segredo do webhook nunca são devolvidos.

---

## Configuração de entrega

Prefixo `/admin/entrega`, exige `X-Empresa-Id`. **Não exposto pelo gateway.**

| Verbo e caminho | Função | Resposta |
|-----------------|--------|----------|
| `GET /admin/entrega/configuracao` | Lê taxa padrão; cria com padrão (taxa 0,00 e cobrar `true`) se não existir | 200 `{id, empresa_id, taxa_entrega_padrao, cobrar_taxa_entrega}` |
| `PUT /admin/entrega/configuracao` | Atualiza. Body: `taxa_entrega_padrao` (>= 0, obrigatório), `cobrar_taxa_entrega` (padrão `true`) | 200 |
| `GET /admin/entrega/faixas` | Lista exceções por bairro; `?apenas_ativas=true` filtra | 200, lista de `{id, empresa_id, bairro, taxa, ativo}` |
| `POST /admin/entrega/faixas` | Cria. Body: `bairro` (2-100), `taxa` (>= 0), `ativo` (padrão `true`) | **201**; 409 se o bairro já tiver faixa |
| `GET /admin/entrega/faixas/{faixa_id}` | Detalhe | 200; 404 |
| `PUT /admin/entrega/faixas/{faixa_id}` | Atualiza. Body: `taxa` (obrigatório), `ativo` (padrão `true`) | 200; 404 |
| `DELETE /admin/entrega/faixas/{faixa_id}` | Remove | 200 `{"message": "Faixa de entrega deletada com sucesso"}`; 404 |
| `GET /admin/entrega/simular/{cep}` | Simula a taxa para um CEP (consulta ViaCEP) | 200 `{cep, logradouro, bairro, cidade, estado, taxa_calculada, tipo}` com `tipo` `excecao` ou `padrao`; 400 se CEP inválido |

---

## Integrações do tenant (WhatsApp e SMTP)

Prefixo `/integracoes`, exige `X-Empresa-Id`. No gateway: `GET`/`PUT`/`DELETE`, só `require_admin` (`proxy.py:507-519`).

| Verbo | Função | Resposta |
|-------|--------|----------|
| `GET /integracoes` | Estado atual; sem registro devolve o estado vazio | 200 `IntegracaoResponse` |
| `PUT /integracoes` | Cria ou atualiza (upsert) | 200 `IntegracaoResponse` |
| `DELETE /integracoes` | Remove; o tenant volta a usar SMTP/Evolution globais | **204**; 404 se não houver configuração |

Body do `PUT` (todos opcionais; segredo vazio ou ausente mantém o atual): `evolution_url`, `evolution_api_key`, `evolution_instance`, `whatsapp_ativo`, `smtp_host`, `smtp_port` (1 a 65535), `smtp_user`, `smtp_password`, `smtp_from_name`, `email_ativo`.

`IntegracaoResponse` nunca devolve segredo: traz `evolution_api_key_configurado` e `smtp_password_configurado` (booleanos), além de `id`, `empresa_id`, `evolution_url`, `evolution_instance`, `whatsapp_ativo`, `smtp_host`, `smtp_port`, `smtp_user`, `smtp_from_name`, `email_ativo`, `updated_at`.

---

## Jobs em segundo plano

Iniciados no `lifespan` de `main.py`:

- `verificar_pagamentos_pendentes`: a cada 60 s.
- `reconciliar_estoque_vendas`: a cada 120 s.

Não há Celery no serviço; são tarefas `asyncio` com loop próprio (`main.py`, `_loop_periodico`).

---

## Códigos de erro

Padrões observados nos routers:

| Código | Quando |
|--------|--------|
| 400 | `ValueError` de regra de negócio; `X-Empresa-Id` inválido; `empresaSlug` ausente; `X-Cliente-Id` malformado |
| 401 | `X-Cliente-Id` ausente em rota de cliente; assinatura de webhook inválida |
| 403 | `empresa_id` do body diferente do header (`POST /vendas`); pedido de outro cliente; token interno inválido |
| 404 | Recurso não encontrado; slug inexistente ou loja indisponível |
| 409 | Configuração de pagamento ou faixa de entrega já existente |
| 422 | Validação do Pydantic (inclui cookie `cart_session_id` ausente nas rotas que o exigem) |
| 502 | Não resolveu a loja no `retry-payment` |
| 503 | Estoque não respondeu ao cancelar venda |
| 500 | Erro interno; várias rotas devolvem `str(e)` no `detail` |

O código **410 (carrinho expirado)** não existe no serviço.

---

## Documentação relacionada

- [Regras de Negócio - Vendas](../11-regras-negocio/vendas.md)
- [Mapeamento de rotas do gateway](./mapeamento-rotas.md)
- [API de Estoque](./estoque-api.md)
- [API Financeiro](./financeiro-api.md)
- [Guia de Autenticação](./guia-autenticacao.md)
- [Exemplos Práticos](./exemplos-praticos.md)

O documento de regras de negócio ainda descreve conceitos que este código não tem (carrinho por `token` com expiração de 2 h, job Celery de limpeza); não foi revisado nesta passada.
