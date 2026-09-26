# 🛒 Regras de Negócio - Vendas

Regras de negócio do serviço de Vendas (Carrinho, Venda/Pedido e Pagamentos), conferidas contra `services/vendas/` (`main.py`, `models/venda.py`, `schemas/`, `services/`, `routers/`, `jobs/`) e, nos pontos de integração, contra `services/estoque/` e `api-gateway/`.

> **Legenda de status**: **Implementado** = existe e roda no código; **Parcial** = existe com ressalvas; **Não implementado** = aparecia neste documento mas não há código que o faça.

> **Pedido e Venda são a mesma entidade.** Não existe tabela nem modelo `Pedido`: "pedido" é a `Venda` enquanto está em `PEDIDO`/`PENDENTE_PAGAMENTO`. Uma venda não "vira" outra depois do pagamento; o mesmo registro muda de status. O campo `numero_venda` (`V-{ano}-{empresa_id}-{seq com 5 dígitos}`, `utils/numero_venda.py`) é único por empresa.

---

## 0. O que roda em segundo plano

`main.py` sobe **dois** loops `asyncio` no `lifespan` (não há Celery no serviço):

| Loop | Intervalo | Função |
|------|-----------|--------|
| `verificar_pagamentos_pendentes` | 60 s (`PAGAMENTOS_PENDENTES_INTERVALO_SEGUNDOS`) | Cancela venda `PENDENTE_PAGAMENTO` com mais de 5 min |
| `reconciliar_estoque_vendas` | 120 s (`RECONCILIACAO_ESTOQUE_INTERVALO_SEGUNDOS`) | Refaz a baixa de estoque de venda marcada como indeterminada |

Existem outros três arquivos em `services/vendas/jobs/` (`limpar_reservas.py`, `limpar_carrinhos_abandonados.py`, `verificar_timeouts_separacao.py`), mas **nada os agenda**: não são importados pelo `main.py` e não há cron, compose ou script no repositório que os chame. Tratam-se de scripts de execução manual (`python jobs/<arquivo>.py`). O docstring de `jobs/__init__.py` está desatualizado (fala em "cancela pagamentos >5min a cada 5 minutos"; o loop real é de 60 s).

---

## 1. Carrinho

O carrinho é **anônimo e por sessão**, vive no Redis e é acessado por `GET/POST/PUT/DELETE /loja/carrinho...?empresaSlug=<slug>` (`routers/loja.py`, `services/carrinho_service.py`). Não há `token` de carrinho nem `cliente_id` no carrinho.

### 📊 Estrutura de Dados

Valor JSON em `carrinho:{sessao_id}:{empresa_id}` (`CarrinhoResponse`, `schemas/loja.py`).

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `sessao_id` | String (UUID v4) | Identificador, entregue ao cliente no cookie `cart_session_id` |
| `empresa_id` | Integer | Tenant, resolvido a partir de `empresaSlug` |
| `itens` | Array | Cada item: `produto_id`, `variante_id` (opcional), `codigo_produto`, `descricao_produto`, `preco_unitario`, `quantidade`, `subtotal`, `estoque_disponivel` |
| `subtotal` | Decimal | Soma dos subtotais dos itens |
| `quantidade_itens` | Integer | Número de linhas de item |
| `criado_em` / `atualizado_em` | DateTime | Datas do carrinho |

Não há campo `total` nem `expira_em` no carrinho; o prazo é o TTL da chave no Redis.

### ✅ Regras

**RN-CAR-001: Carrinho anônimo por sessão — Implementado**
- Não exige login. O identificador é o cookie `cart_session_id` (HttpOnly, `path=/`, `max_age` de 7 dias, `Secure`/`SameSite=None` só quando `FRONTEND_URL` é HTTPS).
- Se o cookie não veio, o servidor gera um UUID e o define na resposta.
- **Não implementado**: "converter carrinho anônimo em carrinho de cliente". O checkout recebe `cliente_id` ou `cliente_novo` no corpo; o carrinho em si nunca é associado a um cliente.
- A loja precisa estar habilitada: `empresaSlug` sem empresa dá 404, e empresa com `catalogo_ativo` falso dá 404 "Loja indisponível no momento" (`utils/tenant.py`).

**RN-CAR-002: Expiração do carrinho — Implementado (prazo diferente do documentado)**
- O TTL do carrinho é de **7 dias** (`CARRINHO_TTL = 604800`), renovado a cada leitura do carrinho, e não 2 horas.
- Não há liberação automática de "reservas do carrinho" atrelada a essa expiração (ver RN-CAR-003).
- **Não implementado**: job Celery a cada 15 minutos. Não há Celery. O script `limpar_carrinhos_abandonados.py` (remove carrinho parado há mais de 7 dias) existe, mas não é agendado; como a chave do Redis já expira sozinha, ele é redundante.

**RN-CAR-003: Reserva de estoque no carrinho — Parcial (mecanismo diferente do documentado)**
- Ao adicionar item, `CarrinhoService.adicionar_item` cria uma **reserva temporária** na tabela `vendas.reservas_temporarias` (`ReservaTemporaria`), com validade de **15 minutos** (`RESERVA_TTL_MINUTOS`), sob lock Redis por produto/variante (5 s).
- Ela **não altera** `quantidade_reservada` nem `quantidade_disponivel` no serviço de Estoque. A disponibilidade é calculada no vendas: `física (GET /estoque/disponibilidade) − soma das reservas temporárias não expiradas`, nunca negativa.
- Se o serviço de Estoque não responde, a quantidade física é tratada como 0 (fail-closed): a reserva é recusada.
- A reserva temporária **não é renovada** enquanto o carrinho é usado: passados 15 minutos ela deixa de contar na disponibilidade.
- No checkout as reservas temporárias da sessão são liberadas e refeitas (também com 15 min) antes de criar a venda.
- Os itens já em Redis não são revalidados contra a expiração da reserva; quem decide de verdade é a reserva real no `criar_venda` e a baixa na confirmação (RN-VEN-002).

**RN-CAR-004: Validação de disponibilidade — Implementado**
- Antes de reservar, o sistema confere produto/variante no serviço de Produtos e exige preço de venda > 0 (o preço vem do catálogo, `preco_do_catalogo`, com promoção vigente).
- Estoque insuficiente: HTTP 400 com "Estoque insuficiente. ..." e o item não entra no carrinho.
- **Não implementado**: "cliente é notificado da indisponibilidade" (só a resposta de erro da própria chamada).

**RN-CAR-005: Remoção de item — Parcial**
- `DELETE /loja/carrinho/itens/{produto_id}` (com `variante_id` opcional na query) remove a linha do Redis.
- **Não** libera a reserva temporária: ela só sai do cálculo ao expirar (15 min) ou no checkout. O mesmo vale para `PUT` de quantidade (só recalcula o subtotal, sem tocar a reserva) e para `DELETE /loja/carrinho` (esvazia o Redis).
- Não há "`quantidade_disponivel` restaurada"/"`quantidade_reservada` decrementada" no Estoque, porque essa reserva nunca esteve lá.

**RN-CAR-006: Armazenamento — Implementado (com TTL diferente)**
- Redis (`REDIS_URL`), JSON, chave `carrinho:{sessao_id}:{empresa_id}`, TTL de 7 dias.

---

## 2. Venda (inclui o "Pedido")

### 📊 Estrutura de Dados

Tabela `vendas.vendas` (`models/venda.py`, `Venda`). Campos principais:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `id` | UUID | Sim | Identificador |
| `empresa_id` | Integer | Sim | Tenant |
| `numero_venda` | String(50) | Sim | Único por empresa (`uq_vendas_empresa_numero`) |
| `cliente_id` | UUID | Não | Cliente cadastrado; nulo em venda de balcão ou de visitante |
| `cliente_convidado_nome/telefone/email/cpf` | String | Não | Dados do visitante quando não há `cliente_id` |
| `subtotal`, `desconto_tipo`, `desconto_valor`, `valor_total` | Numeric(10,2) / String | Sim (desconto_tipo não) | Totais; `desconto_tipo` é `PERCENTUAL` ou `VALOR_FIXO` |
| `valor_frete` | Numeric(10,2) | Sim | Taxa de entrega |
| `status` | String(20) | Sim | `StatusVenda` (seção 2.2) |
| `tipo_entrega` | String(20) | Sim | `RETIRADA` (padrão) ou `DELIVERY` |
| `endereco_*` | String | Não | Endereço de entrega **gravado na própria venda** (logradouro, número, complemento, bairro, cidade, estado, cep) |
| `mercadopago_preference_id`, `mercadopago_payment_id` | String(100) | Não | Vínculo com o Mercado Pago |
| `sessao_carrinho_id` | String(100) | Não | Sessão do carrinho, para limpá-lo depois do pagamento |
| `reconciliacao_estoque_pendente`, `reconciliacao_motivo` | Boolean / Text | Sim / Não | Baixa de estoque indeterminada (RN-VEN-002) |
| `data_pedido`, `data_confirmacao`, `data_separacao`, `data_entregue`, `data_finalizada`, `data_cancelada` | DateTime | `data_pedido` sim | Datas do fluxo |
| `motivo_cancelamento`, `cancelada_por` | Text / UUID | Não | Cancelamento |
| `observacao`, `created_at`, `updated_at` | | | |

Não existem `endereco_entrega_id`, `forma_pagamento`, `payment_id`, `link_pagamento` nem `itens` em JSON na venda: a forma de pagamento fica em `PagamentoVenda`, o link do Mercado Pago não é persistido (só o `preference_id`; a URL volta na resposta do checkout como `mercadopago_init_point`) e os itens ficam em `vendas.itens_venda` (`ItemVenda`, com snapshot de produto, preço e flags `estoque_reservado`/`estoque_baixado`).

Tabelas relacionadas: `itens_venda`, `pagamentos_venda` (`forma_pagamento` em `DINHEIRO`, `PIX`, `DEBITO`, `CREDITO`, `FIADO`; `valor_pago`; troco para `DINHEIRO`; `gera_conta_receber`; `conta_receber_id`), `reservas_estoque_venda` (`RESERVADA`, `BAIXADA`, `LIBERADA`), `reservas_temporarias`, `historico_status_venda` e `webhooks_processados` (idempotência por `payment_id`).

### 2.1. Regras de criação e checkout

**RN-PED-001: Validações no checkout — Parcial**
- Carrinho vazio: 400 "Carrinho está vazio". **Implementado.**
- Cliente cadastrado (`cliente_id`): precisa existir, estar ativo e não estar bloqueado (`verificar_cliente_existe`); senão 400. **Implementado.** Corpo com `cliente_id` **ou** `cliente_novo`, nunca os dois (validador do schema).
- Visitante (`cliente_novo`): nome (mín. 3), telefone com 10 ou 11 dígitos e, se informado, CPF com dígitos verificadores. `criar_conta` opcional cria a conta do comprador. **Implementado.**
- Endereço: **não há** "endereço deve existir" em cadastro. Para `DELIVERY` o corpo traz `endereco_entrega` (obrigatório nesse caso), que é gravado na venda. **Divergente do documento anterior.**
- Pagamentos: `pagamentos` tem no mínimo 1 item, cada um com valor de no mínimo R$ 1,00, no máximo **uma** forma online (`PIX`, `DEBITO` ou `CREDITO`), e a soma tem de cobrir subtotal do carrinho + frete. **Implementado.**
- Frete: em `DELIVERY`, `EntregaService.calcular_taxa_entrega` (taxa padrão da loja ou faixa por bairro).

**RN-PED-002: Conversão carrinho → venda — Parcial**
- O checkout cria a venda em `PEDIDO` (`VendaService.criar_venda`) e, em seguida, ajusta o status: `PENDENTE_PAGAMENTO` se há forma online, senão continua `PEDIDO`. **Não existe** o status `PENDENTE` do documento anterior.
- O preço **não** vem do carrinho: `criar_venda` relê o catálogo (preço de hoje, com promoção vigente).
- Reserva real: `criar_venda` chama `POST /estoque/reservar` para cada item (com `documento = numero_venda`). Falta de estoque (o Estoque respondeu que não tem) recusa a venda e desfaz as reservas já feitas; resposta indeterminada (timeout/5xx) cria a venda marcada para reconciliação (RN-VEN-002).
- O carrinho é removido **só** no pagamento offline (imediatamente) ou, no pagamento online, quando o webhook aprova o pagamento. Se a venda for cancelada por timeout, o carrinho é recriado a partir dos itens (`_restaurar_carrinho_se_necessario`); também há `POST /loja/pedidos/{numero_venda}/recuperar-carrinho` (cliente autenticado, status `PEDIDO` ou `PENDENTE_PAGAMENTO`).

**RN-PED-003: Formas de pagamento — Parcial**
- Formas aceitas no schema: `DINHEIRO`, `PIX`, `DEBITO`, `CREDITO`, `FIADO`. Pagamento misto é aceito (uma online + offline).
- **Online** (`PIX`/`DEBITO`/`CREDITO`): a venda fica `PENDENTE_PAGAMENTO` (não existe `AGUARDANDO_PAGAMENTO`) e é criada uma **preferência do Mercado Pago (Checkout Pro)**.
- **Offline** (`DINHEIRO`/`FIADO`): a venda fica `PEDIDO` até alguém confirmá-la em `POST /vendas/{id}/confirmar`.
- `FIADO` **não** valida crédito, **não** cria conta a receber e **não** debita crédito (ver RN-PED-005).

**RN-PED-004: Pagamento online (Mercado Pago) — Parcial**
- **Não há QR Code na resposta.** O checkout devolve `mercadopago_init_point`, a URL do Checkout Pro, para onde o cliente é redirecionado; PIX é um dos meios oferecidos lá.
- A integração usa `POST /checkout/preferences` (não `POST /v1/payments`), com `external_reference = venda.id` e `notification_url` apontando para o webhook da loja. A preferência expira em **5 minutos** (`TIMEOUT_PAGAMENTO`, `services/mercadopago_service.py`), não 30.
- Se a criação da preferência falha, o checkout **não falha**: a venda fica `PENDENTE_PAGAMENTO` sem `preference_id` e o cliente usa `POST /loja/pedidos/{numero_venda}/retry-payment` (cliente autenticado; status `PEDIDO` ou `PENDENTE_PAGAMENTO`; gera nova preferência).
- Credenciais do Mercado Pago são por tenant (`ConfiguracaoPagamento`, rotas `/pagamentos/admin/...`); `MP_ENVIRONMENT` (padrão `sandbox`) escolhe o ambiente.

**RN-PED-005: Pagamento fiado — Não implementado**
- **Não** valida crédito, **não** cria conta a receber no Financeiro, **não** debita crédito e **não** leva a venda direto para `CONFIRMADO` (esse status nem existe).
- O único código de fiado é: `PagamentoVenda.gera_conta_receber = True` quando a forma é `FIADO`; exigir `cliente_id` para confirmar/adicionar pagamento fiado (`Venda fiada requer cliente identificado`); e, no checkout de cliente cadastrado, exigir `permite_fiado_online` na resposta do serviço de Clientes. **Esse campo não existe no serviço de Clientes** (nenhum outro arquivo do repositório o define), então, para cliente cadastrado, o fiado no checkout é sempre recusado com "Cliente não autorizado para compras fiadas online".
- O serviço Financeiro só expõe `GET /health` (ver [README](./README.md)). `finalizar_venda` tem um `TODO` no lugar da criação da conta a receber, e `conta_receber_id` nunca é preenchido.
- Nota: para visitante (`cliente_novo`) essa checagem de fiado no checkout não roda; ele só esbarra na confirmação, que exige `cliente_id` para fiado.

**RN-PED-006: Confirmação de pagamento — Implementado**
- O webhook (`POST /loja/{empresa_slug}/webhook/mercadopago`) lê o pagamento na API do Mercado Pago, e `decidir_acao_webhook` (`services/webhook_politica.py`) decide: aprovado em venda ainda não confirmada → `confirmar_venda`; venda já `CONFIRMADA` ou além, `CANCELADA` ou `REEMBOLSADA` → ignora (aprovado depois de cancelar gera log crítico de revisão manual; segundo pagamento aprovado gera log crítico e nota no histórico de "cobrança em duplicidade, reembolso manual necessário").
- O status resultante é **`CONFIRMADA`** (não existe `PAGO`). A confirmação também roda pelo job de timeout quando ele encontra pagamento aprovado.
- Idempotência: `webhooks_processados` (por `payment_id`) e trava de linha (`FOR UPDATE`) na venda.
- Assinatura `x-signature` (HMAC-SHA256 do manifesto `id;request-id;ts`) é verificada **quando** o lojista gravou o segredo e o cabeçalho veio; sem segredo, ou sem cabeçalho (IPN legado), a notificação passa com aviso no log. Assinatura presente e errada: 401.
- Não há "converter pedido em venda" nem "baixa física" separada: a baixa acontece dentro de `confirmar_venda` (RN-VEN-002).

**RN-PED-007: Falha no pagamento — Parcial**
- Pagamento `rejected`/`cancelled` em venda `PEDIDO` ou `PENDENTE_PAGAMENTO`: a venda **volta/permanece em `PENDENTE_PAGAMENTO`** (não existe `PAGAMENTO_RECUSADO`), guardando o `payment_id`, para nova tentativa. As reservas **não** são liberadas nesse momento.
- A venda só é cancelada quando o prazo de 5 minutos vence sem pagamento aprovado (RN-PED-009). Esse evento negado em venda já confirmada ou terminal é ignorado (anti-downgrade).
- Status de pagamento não final (`pending`, `in_process`, `in_mediation`, `authorized`): aguarda, sem marcar o webhook como processado.

**RN-PED-008: Cancelamento — Parcial**
- `POST /vendas/{id}/cancelar`, corpo `{motivo, usuario_id?}`, com `motivo` **obrigatório, de 10 a 500 caracteres**. **Implementado.**
- Só é permitido em `PEDIDO`, `CONFIRMADA` e `SEPARADA`. **`PENDENTE_PAGAMENTO` não pode ser cancelada manualmente** (só o timeout a cancela), e `ENTREGUE`/`FINALIZADA` recebem a mensagem "Use devolução", mas **não existe rota de devolução**: a única saída é o reembolso via webhook do Mercado Pago (RN-VEN-004).
- Efeito: estorna no Estoque o que já foi baixado (`POST /estoque/estornar-venda`, idempotente por `numero_venda`); se o Estoque não confirmar, responde **503** e nada é cancelado. Depois libera as reservas dos itens não baixados (`POST /estoque/liberar-reserva`), marca as reservas como `LIBERADA` e a venda como `CANCELADA`.
- Venda com `mercadopago_payment_id` (paga online): o sistema **não** chama a API de reembolso do Mercado Pago; registra log crítico e nota no histórico "reembolso manual necessário".
- **Não implementado**: "se fiado, crédito é estornado" (não há débito para estornar).
- Não há a regra "apenas pedidos não finalizados": o critério é a lista de status acima.

**RN-PED-009: Timeout de pagamento — Implementado**
- O loop de 60 s cancela vendas `PENDENTE_PAGAMENTO` com `data_pedido` mais antiga que 5 minutos **e com `mercadopago_preference_id` preenchido**. Uma venda sem preferência (falha ao criar no Mercado Pago) **não** é candidata e não é cancelada por esse loop, ao contrário do que o comentário do checkout sugere.
- Antes de cancelar, o job procura pagamento aprovado no Mercado Pago (`/v1/payments/search`); se achar, confirma a venda; se o Mercado Pago estiver indisponível, adia o cancelamento.
- Cancelando: libera reservas, marca `CANCELADA` ("Cancelamento automático: timeout de pagamento (5min)"), recria o carrinho e avisa o cliente por WhatsApp (se tiver telefone).
- Trava por linha com `SKIP LOCKED`, seguro para várias instâncias.

### 2.2. Status da venda (`StatusVenda`, 9 estados)

| Status | Como se chega | Próximos estados no código |
|--------|---------------|----------------------------|
| `PEDIDO` | Criação (`POST /vendas` ou checkout sem forma online) | `CONFIRMADA`, `CANCELADA`, `PENDENTE_PAGAMENTO` (checkout online, retry-payment, pagamento negado), `REEMBOLSADA` (webhook) |
| `PENDENTE_PAGAMENTO` | Checkout com forma online | `CONFIRMADA` (pagamento aprovado), `CANCELADA` (só pelo timeout), `REEMBOLSADA` (webhook) |
| `CONFIRMADA` | `POST /vendas/{id}/confirmar` ou webhook | `SEPARADA`, `CANCELADA`, `REEMBOLSADA` |
| `SEPARADA` | `POST /vendas/{id}/separar` (exige `CONFIRMADA`) | `ENTREGUE`, `CANCELADA`, `REEMBOLSADA` |
| `EM_ENTREGA` | **Nenhum código a define** | Declarado no enum e tratado como "já confirmado" no webhook e no rastreio, mas inalcançável: `entregar` exige `SEPARADA` e vai direto a `ENTREGUE` |
| `ENTREGUE` | `POST /vendas/{id}/entregar` (exige `SEPARADA`) | `FINALIZADA`, `REEMBOLSADA` |
| `FINALIZADA` | `POST /vendas/{id}/finalizar` (exige `ENTREGUE`) | `REEMBOLSADA` |
| `CANCELADA` | Cancelamento manual, timeout de pagamento ou falta de estoque na confirmação | Terminal |
| `REEMBOLSADA` | Webhook `refunded`/`charged_back` | Terminal |

O `REEMBOLSO` do webhook vale para qualquer status diferente de `REEMBOLSADA` (`decidir_acao_webhook`). O status é `varchar(20)` sem transição validada no banco; as regras acima estão nos métodos de `VendaService`. Cada mudança grava uma linha em `historico_status_venda`.

**Edição**: `PUT /vendas/{id}` só é aceito em `PEDIDO` (cliente, tipo de entrega, observação, desconto); mexer no desconto recalcula `subtotal` e `valor_total`.

---

## 3. Confirmação, estoque e finalização

**RN-VEN-001: Criação e status inicial — Divergente do documento anterior**
- Não existe "venda criada após a confirmação de pagamento com status `FINALIZADA`". A venda nasce em `PEDIDO` (ou `PENDENTE_PAGAMENTO` no checkout online), e `FINALIZADA` é o penúltimo estágio, depois de `CONFIRMADA → SEPARADA → ENTREGUE`.
- `POST /vendas` (administrativo) cria a venda direto, com `cliente_id` opcional (balcão), `itens` (o preço é sempre o do catálogo; o cliente não informa), desconto opcional e `empresa_id` no corpo igual ao header `X-Empresa-Id` (senão 403).

**RN-VEN-002: Baixa de estoque na confirmação — Implementado (endpoint diferente)**
- `confirmar_venda` (`PEDIDO`/`PENDENTE_PAGAMENTO` → `CONFIRMADA`) exige soma dos pagamentos ≥ `valor_total`, registra os `PagamentoVenda` (troco em `DINHEIRO`) e chama **uma** vez `POST /estoque/baixar-venda` com todos os itens e `documento = numero_venda`. **Não** é `POST /estoque/confirmar-reserva` (essa rota não existe no serviço de Estoque; só aparece no docstring do gateway).
- No Estoque a baixa é atômica e idempotente por `numero_venda` (ledger `BaixaVendaProcessada`): decrementa `quantidade`, converte a reserva (decrementa `quantidade_reservada`) e registra movimentação `SAIDA` com motivo "Venda confirmada". Falta de estoque: 409.
- Três resultados no vendas: **sucesso** → confirma; **sem estoque** (definitivo) → cancela a venda, libera reservas e, se já havia pagamento online aprovado, loga "reembolso necessário" (o reembolso é manual); **indeterminado** (timeout, erro de rede, 5xx) → **não cancela** venda paga: grava `reconciliacao_estoque_pendente = true` e a chamada falha com `EstoqueIndeterminadoError`.
- **Reconciliação**: o loop de 120 s reprocessa vendas com a marca e `mercadopago_payment_id` preenchido. Uma venda marcada sem `payment_id` (por exemplo, reserva indeterminada na criação de venda de balcão) **não** entra nessa varredura.
- `entregar_venda` é só logística: marca as reservas como `BAIXADA` e **não** mexe em estoque (o docstring do router `POST /vendas/{id}/entregar` ainda diz que baixa estoque; o serviço diz e faz o contrário).

**RN-VEN-003: Eventos publicados — Não implementado**
- Existe `events/publisher.py` (exchange `erp.events`, tipo topic, RabbitMQ), mas **nada o chama**: nenhum arquivo de vendas importa `get_publisher`. Os eventos `venda.finalizada`, `pedido.pago`, `estoque.confirmado`, `venda.fiada_criada` e `pedido.cancelado` **não são publicados**.
- O que existe no lugar: mensagens de WhatsApp (RN-VEN-005) e o histórico de status.

**RN-VEN-004: Cancelamento e devolução — Parcial**
- Cancelamento: ver RN-PED-008. **Não** há cancelamento de venda `ENTREGUE`/`FINALIZADA`.
- Reembolso: o webhook com pagamento `refunded`/`charged_back` chama `reembolsar_venda`, que devolve o estoque baixado (`POST /estoque/estornar-venda`, movimentação **`DEVOLUCAO`**, não `ENTRADA`) e marca a venda `REEMBOLSADA`. É idempotente (status `REEMBOLSADA` + ledger de estorno no Estoque); se o estorno for indeterminado, responde erro e o Mercado Pago reenvia o webhook.
- **Não implementado**: motivo obrigatório no reembolso (o motivo só é exigido no cancelamento) e estorno de crédito fiado.

**RN-VEN-005: Notificações por WhatsApp — Implementado (melhor esforço)**
- Via Evolution API, configurada por tenant (`/integracoes`), em: criação do pedido, pagamento confirmado, pedido separado, entregue e cancelado por timeout (`services/notificacao_service.py`). Falha no envio é registrada e nunca derruba a operação. A confirmação de pagamento e as de separado/entregue só saem quando a venda tem `cliente_convidado_telefone`.
- `verificar_timeouts_separacao.py` (alertas de 12 h/24 h e cancelamento em 48 h de venda `CONFIRMADA`) **não está agendado**, portanto essa regra não roda.

### 3.1. Status da reserva de estoque da venda (`StatusReserva`)

| Status | Significado |
|--------|-------------|
| `RESERVADA` | Reserva criada na venda (`reservas_estoque_venda`) |
| `BAIXADA` | Marcada em `entregar_venda` (o estoque já saíra na confirmação) |
| `LIBERADA` | Cancelamento, timeout ou falta de estoque |

---

## 4. Fluxos (como o código roda)

### 4.1. Loja online, pagamento online (PIX/cartão)

```
1. Cliente adiciona itens (POST /loja/carrinho/itens?empresaSlug=...)
   → valida produto e preço, reserva temporária de 15 min (banco do vendas)
   → carrinho no Redis (TTL 7 dias)

2. POST /loja/checkout
   → valida carrinho, cliente e pagamentos; calcula frete
   → cria venda PEDIDO, reserva no Estoque (POST /estoque/reservar por item)
   → status PENDENTE_PAGAMENTO, cria preferência no Mercado Pago
   → responde mercadopago_init_point; o carrinho continua no Redis

3. Cliente paga no Mercado Pago; o MP chama o webhook
   → CONFIRMADA: baixa no Estoque (POST /estoque/baixar-venda), registra o pagamento,
     limpa o carrinho, avisa por WhatsApp

4. Operação: separar → entregar → finalizar
   CONFIRMADA → SEPARADA → ENTREGUE → FINALIZADA

Sem pagamento em 5 min: o loop cancela (CANCELADA), libera reservas e recria o carrinho.
```

### 4.2. Loja online, pagamento offline (`DINHEIRO`/`FIADO`)

```
POST /loja/checkout → venda PEDIDO, reserva no Estoque, carrinho limpo
→ alguém confirma em POST /vendas/{id}/confirmar (com os pagamentos)
→ baixa de estoque, CONFIRMADA, e segue o fluxo operacional
```

Não há conta a receber nem débito de crédito no caso `FIADO`. Além disso, `POST /vendas/...` **não é roteado pelo gateway** (ver seção 5.3); a confirmação manual só é alcançável chamando o serviço direto.

### 4.3. Cancelamento

```
POST /vendas/{id}/cancelar {motivo (10-500 caracteres)}
→ só PEDIDO, CONFIRMADA ou SEPARADA
→ estorna no Estoque o que já foi baixado; libera reservas dos itens não baixados
→ CANCELADA; se havia pagamento online, log crítico de reembolso manual
```

---

## 5. Integrações

### 5.1. Mercado Pago

| Uso | Chamada | Onde |
|-----|---------|------|
| Criar link de pagamento | `POST https://api.mercadopago.com/checkout/preferences` | `criar_preferencia` |
| Consultar pagamento | `GET /v1/payments/{id}` | `obter_detalhes_pagamento` |
| Achar pagamento aprovado da venda | `GET /v1/payments/search` (`external_reference`, `status=approved`) | job de timeout |
| Ordem de compra (cartão 3DS/IPN) | `GET /merchant_orders/{id}` | webhook |

Webhook: `POST /loja/{empresa_slug}/webhook/mercadopago` (público); `GET /loja/{empresa_slug}/webhook/mercadopago/test` só confirma que está acessível. **Não** existe `POST /webhooks/mercadopago`. O tenant vem do slug (serviço de Empresas). Aceita `type`/`topic` = `payment` ou `merchant_order`; outros tipos são ignorados com 200.

### 5.2. Estoque

Chamadas do vendas ao serviço de Estoque (`services/venda_service.py`, `reserva_temporaria_service.py`), todas com `X-Empresa-Id` e o carimbo `X-Servico-Interno-Token`:

| Rota do Estoque | Quando | Efeito |
|-----------------|--------|--------|
| `GET /estoque/disponibilidade` | Reserva temporária do carrinho | Lê a quantidade física |
| `POST /estoque/reservar` | `criar_venda`, por item | Aumenta `quantidade_reservada`, diminui `quantidade_disponivel` |
| `POST /estoque/liberar-reserva` | Cancelamento, timeout, falta de estoque | Devolve a reserva |
| `POST /estoque/baixar-venda` | `confirmar_venda` | Baixa atômica e idempotente, converte reserva em saída (`SAIDA`) |
| `POST /estoque/estornar-venda` | Cancelamento de venda confirmada e reembolso | Devolve o baixado (`DEVOLUCAO`), idempotente |

`POST /estoque/confirmar-reserva` **não existe** no serviço de Estoque, e `POST /estoque/saida` (`baixar_estoque` em `VendaService`) não é usado no fluxo atual.

### 5.3. Rotas de `/vendas` e o gateway

`api-gateway/proxy/service_proxy.py` só encaminha ao serviço de vendas os prefixos `/loja`, `/carrinho`, `/pagamentos` e `/integracoes`. **Não há `/vendas` no gateway.** As rotas `/vendas/...` (criar, listar, confirmar, separar, entregar, finalizar, cancelar, pagamentos, relatórios) existem no serviço, mas só são alcançáveis direto na porta 8004 (em dev, `127.0.0.1:8004`; em produção o compose não publica essa porta). O prefixo `/carrinho` também não tem router correspondente no vendas (o carrinho é `/loja/carrinho`). **A CONFIRMAR:** como o operador deve confirmar/separar/entregar pedidos em produção, dado que o gateway não roteia essas rotas; o frontend (`frontend/src`) não referencia `/vendas`.

### 5.4. Financeiro

**Não implementado.** O vendas não chama o Financeiro: não há `POST /contas-receber`, `POST /contas-receber/{id}/pagar`, vencimento por `dia_vencimento` nem crédito devolvido ao cliente. `FINANCEIRO_URL` está em `config.py`, mas nenhum código a usa. O serviço Financeiro só expõe `GET /health`.

---

## 6. Outras regras existentes no código

- **Multi-tenancy**: rotas de `/vendas` exigem o header `X-Empresa-Id`; rotas de `/loja` resolvem o tenant por `empresaSlug`; toda consulta filtra por `empresa_id`.
- **Origem interna**: `X-Servico-Interno-Token` é validado por middleware; enquanto `SERVICO_INTERNO_TOKEN` estiver vazio, o serviço deixa passar (fail-open) com log; `/health` é isento.
- **Área do cliente**: `GET /loja/meus-pedidos`, `POST /loja/pedidos/{numero_venda}/retry-payment` e `.../recuperar-carrinho` exigem cliente autenticado (o gateway injeta `X-Cliente-Id`); o pedido tem de pertencer ao cliente (403 caso contrário). `GET /loja/rastrear/{numero_venda}` é público e devolve status, datas e histórico.
- **Configurações por tenant**: `/admin/entrega/...` (taxa de entrega e faixas por bairro), `/pagamentos/admin/...` (credenciais do Mercado Pago) e `/integracoes` (WhatsApp/SMTP), com segredos cifrados (`INTEGRACOES_SECRET_KEY`).
- **Relatório**: `GET /vendas/relatorios/resumo` (período obrigatório) devolve total de vendas, valor total, ticket médio e contagem/valor por status.

---

## 📚 Referências

- [API de Vendas](../10-api-reference/vendas-api.md)
- [Regras de Negócio - Índice](./README.md)
- [Regras de Negócio - Estoque](./estoque.md)

---

**Última atualização**: A CONFIRMAR (o rodapé anterior dizia "26 de Maio de 2026, versão 1.0.0"; nenhuma fonte no repositório corrobora)
**Autor**: Equipe DenebCorp
