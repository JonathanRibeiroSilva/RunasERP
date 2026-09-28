# Glossário - Runas

> **Termos técnicos e conceitos** utilizados no projeto Runas. Cada termo aponta para onde ele existe no código; termos de coisas que não estão em uso estão marcados como tal.

---

## A

### API Gateway
Ponto de entrada único do frontend (`api-gateway/`, porta 8000). Autentica (JWT), aplica rate limiting (`api-gateway/middleware/rate_limit.py`), idempotência de escritas e repassa as requisições aos 7 serviços, injetando os headers de contexto (`X-Empresa-Id`, `X-Cliente-Id`, `X-Servico-Interno-Token`) em `api-gateway/proxy/service_proxy.py`.

### Alembic
Ferramenta de migração de banco para SQLAlchemy. Cada serviço e o gateway têm seu próprio diretório `alembic/versions/`.

### Async/Await
Padrão de programação assíncrona em Python usado nos serviços FastAPI (SQLAlchemy async, `httpx` async).

---

## B

### Backoff
Espera crescente entre tentativas. No frontend, `frontend/src/services/api/axios.ts` repete GET/HEAD/OPTIONS que recebem 502/503/504 até 3 vezes, esperando 1s, 2s e 3s (janela de deploy).

### Badge
Elemento visual que exibe status ou categorias. Não há um `Badge` genérico em `frontend/src/components/`; existem badges por módulo, como `EstoqueStatusBadge` e `MovimentacaoBadge` em `frontend/src/pages/Estoque/components/`.

### Broker
Intermediário de mensagens. Há um container RabbitMQ em `docker-compose.prod.yml` e cada serviço tem `events/publisher.py`, mas **nenhum código chama `publish`**: não há comunicação por eventos entre serviços hoje. Ver [RabbitMQ](#rabbitmq).

---

## C

### Carrinho
Coleção temporária de itens da loja online, guardada no Redis pelo serviço de vendas (`services/vendas/services/carrinho_service.py`) com TTL de 7 dias. Identificado pelo cookie `cart_session_id`.

### Celery
**Não é usado.** Aparece em alguns `requirements.txt`, mas nenhum código importa Celery. As tarefas periódicas são dois loops `asyncio` em `services/vendas/main.py` (`verificar_pagamentos_pendentes` a cada 60s e `reconciliar_estoque_vendas` a cada 120s) e um endpoint `POST /plataforma/jobs/regua` no gateway (`api-gateway/routers/plataforma.py`), chamado pelo cron do host.

### Checkout
Finalização de compra na loja online (`processar_checkout` em `services/vendas/routers/loja.py`): valida o carrinho, reserva estoque e cria a venda com status `PENDENTE_PAGAMENTO` quando há pagamento online (PIX, débito ou crédito) ou `PEDIDO` quando não há (`services/vendas/services/loja_service.py`).

### CNPJ
Cadastro Nacional da Pessoa Jurídica. No serviço de empresas é validado com dígito verificador e guardado **com** máscara (`XX.XXX.XXX/XXXX-XX`). Ver [Guia de máscaras e validações](../02-desenvolvimento/GUIA_MASCARAS_VALIDACOES.md).

### CPF
Cadastro de Pessoas Físicas. Validado com dígito verificador nos serviços de clientes e vendas e guardado sem máscara.

### CRUD
Create, Read, Update, Delete - operações básicas de manipulação de dados.

### Crédito Disponível
Campo `credito_disponivel` do cliente (`services/clientes/models/cliente.py`). Muda por `PUT /clientes/{id}/credito` (redefine o limite) e `POST /clientes/{id}/credito/ajustar` (soma um delta). A regra documentada é `limite_credito - saldo_devedor`, mas não existe `saldo_devedor`: ao redefinir o limite, o código assume saldo devedor zero (`TODO` em `services/clientes/services/cliente_service.py`). O serviço de vendas não consulta nem debita esse crédito numa venda fiado.

---

## D

### Dark Mode
Tema escuro, padrão do Runas ("Dark Mode First" em `frontend/src/styles/variables.scss`, fundo `#080A0F`, primária `#0EA5E9`).

### Deduplicação
Evitar processar duas vezes o mesmo evento. Existe em três lugares: `Idempotency-Key` no gateway (reserva no Redis, `api-gateway/proxy/idempotency.py`), tabela `webhooks_processados` no serviço de vendas (`WebhookProcessado`) e tabelas `baixas_venda_processadas` / `estornos_venda_processados` no serviço de estoque.

### Docker Compose
Orquestração dos containers. Arquivos: `docker-compose.dev.yml` (local) e `docker-compose.prod.yml` (produção, via Coolify). Use `docker compose` (v2).

---

## E

### Empresa (tenant)
Loja cliente do SaaS. Cada registro dos serviços carrega `empresa_id`; o gateway resolve o tenant pelo usuário autenticado ou pelo `slug` da loja pública e injeta `X-Empresa-Id`. Modelo em `services/empresas/models/empresa.py` (`TipoEmpresa`: MATRIZ/FILIAL; `StatusEmpresa`: ATIVA/INATIVA/SUSPENSA).

### Endpoint
URL específica de uma API que executa uma operação (ex: `POST /clientes`).

### Evolution API
Serviço self-hosted para WhatsApp. As variáveis `EVOLUTION_*` estão no serviço de notificações e a integração é configurável em `Configuracoes/IntegracoesPage.tsx`, mas o container `evolution-api` **não é implantado** em produção (comentário em `docker-compose.prod.yml`): as chamadas de WhatsApp falham fechadas.

---

## F

### FastAPI
Framework web Python usado no gateway e em todos os 7 microsserviços.

### Fiado
Forma de pagamento `FIADO` (`FormaPagamento` em `services/vendas/models/venda.py`): o cliente compra a crédito e paga depois. Exige cliente identificado (`services/vendas/routers/vendas.py`). A geração de conta a receber no financeiro está marcada como "futuro" no código.

### Forma de Pagamento
Enum `FormaPagamento`: `DINHEIRO`, `PIX`, `DEBITO`, `CREDITO`, `FIADO`. Uma venda pode ter mais de um pagamento (pagamento misto).

### Fornecedor
Empresa que fornece produtos. Modelos `Fornecedor` e `FornecedorProduto` no serviço de produtos; o lote de estoque também tem um campo texto `fornecedor`.

---

## G

### Glassmorphism
Efeito de vidro fosco (`backdrop-filter`), disponível no mixin `glass-panel` de `frontend/src/styles/mixins.scss`.

### Glow Effect
Brilho colorido ao redor de elementos (tokens `*-glow` em `frontend/src/styles/variables.scss`).

---

## H

### Headers internos
Headers que só o gateway pode definir (ele descarta os que vierem do navegador):
- **`X-Empresa-Id`**: tenant da requisição; os serviços confiam nele como identidade.
- **`X-Cliente-Id`**: comprador autenticado na loja online.
- **`X-Servico-Interno-Token`**: prova de que a chamada veio de dentro da malha (`SERVICO_INTERNO_TOKEN`, o mesmo valor nos 8 containers; `api-gateway/interno.py`).
- **`X-Plataforma`** + **`X-Plataforma-Token`**: marcam rotas de administração da plataforma no serviço de empresas, injetados só pelo router `/plataforma` do gateway depois de `require_super_admin`.

### Health Check
Todos os serviços e o gateway expõem `GET /health`. O gateway tem também `GET /health/ready`, que verifica banco, Redis e os 7 serviços.

### HTTP Status Codes
Códigos numéricos que indicam o resultado de uma requisição HTTP:
- **200**: Sucesso
- **201**: Criado
- **400**: Requisição inválida
- **401**: Não autenticado
- **403**: Sem permissão
- **404**: Não encontrado
- **409**: Conflito
- **422**: Validação falhou
- **429**: Rate limit excedido
- **500**: Erro interno

---

## I

### Idempotência
Propriedade de uma operação que pode ser executada múltiplas vezes sem alterar o resultado. No gateway, escritas com o header `Idempotency-Key` devolvem a resposta já salva por até `IDEMPOTENCY_TTL_SECONDS` (padrão 86400).

### Inventário
Contagem física do estoque para ajustar divergências. Modelos `Inventario` e `ItemInventario` no serviço de estoque.

---

## J

### JWT (JSON Web Token)
Token de autenticação emitido pelo gateway (algoritmo padrão `HS256`, access token de 30 minutos, refresh token de 7 dias; `api-gateway/config.py`).

---

## L

### Limite de Crédito
Campo `limite_credito` do cliente: valor máximo em compras fiado.

### Lote
Conjunto de unidades recebidas de uma vez, com `data_validade` e `fornecedor` (`Lote` em `services/estoque/models/estoque.py`). Status: `ATIVO`, `VENCIDO`, `BLOQUEADO`.

---

## M

### Markup
Percentual sobre o custo para formar o preço de venda. Campo `markup_pct` da variante; `preco_venda = preco_custo * (1 + markup_pct / 100)` (`services/produtos/models/variante.py`).

### Mercado Pago
Plataforma de pagamentos usada em dois papéis: checkout da loja online de cada lojista (`services/vendas/services/mercadopago_service.py`, inclui PIX) e cobrança da mensalidade dos lojistas pela plataforma (`api-gateway/services/preapproval_service.py`).

### Microsserviço
Serviço independente. São 7: clientes (8001), produtos (8002), estoque (8003), vendas (8004), financeiro (8005), notificacoes (8006) e empresas (8007). Financeiro e notificações ainda não têm modelos nem routers de negócio.

### Migration
Script Alembic que altera a estrutura do banco de forma controlada e versionada.

### Movimentação
Registro de estoque (`Movimentacao`). Tipos (`TipoMovimentacao`): `ENTRADA`, `SAIDA`, `AJUSTE`, `DEVOLUCAO`, `PERDA`, `TRANSFERENCIA`.

---

## O

### OAuth2
Protocolo de autorização usado no login do comprador da loja online com Google e Microsoft (rotas `/auth/cliente/oauth/google/*` e `/auth/cliente/oauth/microsoft/*` em `api-gateway/routers/auth_cliente.py`). `api-gateway/auth/oauth2.py` é outra coisa: extrai e valida o Bearer token (`OAuth2PasswordBearer`).

### ORM (Object-Relational Mapping)
Técnica que mapeia objetos Python para tabelas de banco de dados (SQLAlchemy).

---

## P

### Papel (Role)
Enum `RoleEnum` do usuário administrativo (`api-gateway/models/usuario.py`):
- **SUPER_ADMIN**: administra a plataforma; sem tenant (`empresa_id` nulo).
- **ADMIN**: administrador de uma empresa.
- **OPERADOR**: acesso limitado dentro da empresa (padrão).

### Pedido
Venda criada pela loja online; nasce com status `PEDIDO`, ou `PENDENTE_PAGAMENTO` se o pagamento é online (modelo `Venda` em `services/vendas/models/venda.py`).

### PIX
Pagamento instantâneo brasileiro. Na loja online é processado pelo Mercado Pago; também é uma `FormaPagamento`.

### PostgreSQL
Banco de dados relacional usado pelo gateway e pelos serviços.

### Produto
Item comercializado (`services/produtos/models/produto.py`); pode ter múltiplas variantes.

### Pydantic
Biblioteca Python de validação de dados; define os schemas de entrada e saída dos serviços.

---

## Q

### Query Parameter
Parâmetro passado na URL após `?` (ex: `?skip=0&limit=100` na listagem de clientes).

---

## R

### RabbitMQ
Sistema de mensageria. Está provisionado no `docker-compose.prod.yml` e os serviços têm `events/publisher.py` com `aio_pika`, mas **nenhum código publica eventos**: é infraestrutura sem uso.

### Rate Limiting
Limite de requisições por período, via `slowapi` no gateway: 300/minuto por IP por padrão, mais apertado nas rotas de login, registro e reset de senha.

### Redis
Banco em memória usado para o carrinho da loja (serviço de vendas), as reservas de `Idempotency-Key`, a blacklist de tokens (`api-gateway/auth/oauth2.py`) e o cache de inadimplência (`api-gateway/middleware/inadimplencia_middleware.py`) no gateway.

### Refresh Token
Token de longa duração (7 dias), gravado pelo gateway no cookie HTTP-only `refresh_token` e trocado por um novo access token em `POST /auth/refresh` (`api-gateway/routers/auth.py`). O frontend não chama essa rota: ao receber 401, `frontend/src/services/api/axios.ts` limpa os tokens e redireciona para `/login`.

### Repository Pattern
Camada de acesso a dados separada. Existe em `repositories/` do gateway e de clientes, empresas, estoque, produtos e vendas (em financeiro e notificações o diretório só tem `__init__.py`).

### Retry
Reexecução automática de uma operação que falhou. Ver [Backoff](#backoff).

---

## S

### Schema
Estrutura de dados definida com Pydantic para validação de entrada/saída da API.

### Seed
Popular o banco com dados iniciais. Há um `seed.py` no gateway e em cada serviço. Ver [SEED_DATA_COMPLETO.md](../06-operacao/SEED_DATA_COMPLETO.md).

### SKU (Stock Keeping Unit)
Código da variante, único por empresa (`uq_variantes_empresa_sku`). O produto também tem um `sku` opcional.

### Slug
Endereço público da loja da empresa (`/c/{slug}`), só letras minúsculas, números e hífen (`services/empresas/schemas/empresa.py`).

### Snapshot
Cópia dos dados em um momento específico. O item de venda guarda `descricao_produto`, `codigo_produto` e `preco_unitario` do momento da compra (`ItemVenda`).

### Soft Delete
Desativação lógica sem apagar o registro (campo `ativo=False`), usado em clientes e empresas, entre outros.

### SQLAlchemy
ORM Python usado para interagir com o banco de dados (modo async).

### Status de Venda
Enum `StatusVenda` (`services/vendas/models/venda.py`), 9 estados: `PEDIDO`, `PENDENTE_PAGAMENTO`, `CONFIRMADA`, `SEPARADA`, `EM_ENTREGA` (só DELIVERY), `ENTREGUE`, `FINALIZADA`, `CANCELADA`, `REEMBOLSADA`.

---

## T

### Tipo de Entrega
Enum `TipoEntrega`: **RETIRADA** (cliente busca) ou **DELIVERY** (enviado ao cliente).

### Toast
Notificação temporária (react-toastify, wrapper em `frontend/src/utils/toast.ts`): 4s por padrão, 5s para erro.

### Token
Credencial de autenticação gerada após login bem-sucedido.

### Transação
Conjunto de operações de banco que devem ser executadas atomicamente (tudo ou nada).

### TypeScript
Superset do JavaScript com tipagem estática, usado no frontend.

---

## U

### UUID (Universally Unique Identifier)
Identificador de 128 bits usado como chave primária na maioria das tabelas. Exceção: `empresas` usa inteiro autoincremento (por isso `empresa_id` é `int`).

---

## V

### Variante
Versão específica de um produto (ex: Coca-Cola 2L, Coca-Cola 600ml), com SKU, custo, markup e preço próprios (`services/produtos/models/variante.py`).

### Vencimento
Data limite de pagamento. Existe como `dia_vencimento` do fiado no cliente e `vence_em` da assinatura do lojista na plataforma. Não há contas a receber: o serviço financeiro ainda não tem modelos.

### Vite
Build tool do frontend (Vite 8, servidor de desenvolvimento na porta 3000).

---

## W

### Webhook
Endpoint HTTP que recebe notificações de serviços externos. O Mercado Pago notifica o serviço de vendas (`services/vendas/routers/webhook.py`, assinatura verificada) e o gateway (`POST /plataforma/webhook/mercadopago` em `api-gateway/routers/plataforma.py`, assinaturas dos lojistas).

### WhatsApp
Canal de notificação previsto via Evolution API. Ver [Evolution API](#evolution-api): não está em produção.

---

## Z

### Zod
Biblioteca TypeScript de validação de schemas, usada nos formulários com react-hook-form (ex: `frontend/src/pages/Configuracoes/empresaSchema.ts`).
