# Glossário - Runas

> **Termos técnicos e conceitos** utilizados no projeto Runas

---

## A

### API Gateway
Ponto de entrada único para todas as requisições do frontend. Responsável por autenticação, roteamento e rate limiting.

### Alembic
Ferramenta de migração de banco de dados para SQLAlchemy. Gerencia versões do schema do banco.

### Async/Await
Padrão de programação assíncrona em Python que permite operações não-bloqueantes.

---

## B

### Badge
Componente visual que exibe status ou categorias (ex: "Confirmado", "VIP", "Pendente").

### Backoff
Estratégia de retry que aumenta progressivamente o tempo de espera entre tentativas.

### Broker
Intermediário de mensagens (RabbitMQ) que gerencia filas e eventos entre microsserviços.

---

## C

### Carrinho
Coleção temporária de produtos selecionados antes da finalização da compra. Expira em 24h.

### Celery
Framework Python para execução de tarefas assíncronas e agendadas (jobs).

### Checkout
Processo de finalização de compra, convertendo carrinho em pedido.

### CNPJ
Cadastro Nacional da Pessoa Jurídica. Identificador único de empresas no Brasil.

### CPF
Cadastro de Pessoas Físicas. Identificador único de cidadãos brasileiros.

### CRUD
Create, Read, Update, Delete - operações básicas de manipulação de dados.

### Crédito Disponível
Valor que o cliente ainda pode utilizar em compras fiadas, calculado como: `limite_credito - saldo_devedor`.

---

## D

### Dark Mode
Tema visual com fundo escuro e texto claro, padrão do Runas.

### Deduplicação
Técnica para evitar processamento duplicado de eventos/notificações usando Redis.

### Docker Compose
Ferramenta para orquestração de múltiplos containers Docker.

### Domain Event
Evento que representa algo significativo que aconteceu no domínio de negócio (ex: `pedido.confirmado`).

---

## E

### Endpoint
URL específica de uma API que executa uma operação (ex: `POST /clientes`).

### Evolution API
Serviço self-hosted para envio de mensagens WhatsApp.

### Exchange
Componente do RabbitMQ que roteia mensagens para filas baseado em routing keys.

---

## F

### FastAPI
Framework web Python moderno e de alta performance, usado em todos os microsserviços.

### Fiado
Modalidade de pagamento onde o cliente compra a crédito e paga posteriormente.

### Fila (Queue)
Estrutura de dados FIFO (First In, First Out) usada para processar mensagens assíncronas.

### Fornecedor
Empresa que fornece produtos para revenda.

---

## G

### Glassmorphism
Efeito visual de vidro fosco com blur e transparência, usado sutilmente no design.

### Glow Effect
Efeito de brilho/sombra colorida ao redor de elementos, usado com moderação.

---

## H

### Health Check
Endpoint que verifica se um serviço está funcionando corretamente (`GET /health`).

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
- **500**: Erro interno

---

## I

### Idempotência
Propriedade de uma operação que pode ser executada múltiplas vezes sem alterar o resultado.

### Inventário
Processo de contagem física do estoque para ajustar divergências.

---

## J

### JWT (JSON Web Token)
Padrão de token para autenticação. Contém informações do usuário codificadas.

---

## L

### Limite de Crédito
Valor máximo que um cliente pode dever em compras fiadas.

### Lote
Conjunto de produtos recebidos de uma vez, com data de validade e rastreabilidade.

---

## M

### Markup
Percentual adicionado ao preço de custo para calcular o preço de venda.

### Mercado Pago
Plataforma de pagamentos online, usada para PIX automático.

### Microsserviço
Serviço independente que implementa uma funcionalidade específica do sistema.

### Migration
Script que altera a estrutura do banco de dados de forma controlada e versionada.

### Modalidade de Entrega
Forma como o pedido será entregue: **RETIRADA** (cliente busca) ou **ENTREGA** (enviado ao cliente).

### Modalidade de Pagamento
Forma de pagamento do pedido: **A_VISTA** (pago imediatamente) ou **FIADO** (pago depois).

### Movimentação
Registro de entrada, saída ou ajuste de estoque. Imutável após criação.

---

## O

### OAuth2
Protocolo de autorização usado para login seguro.

### ORM (Object-Relational Mapping)
Técnica que mapeia objetos Python para tabelas de banco de dados (SQLAlchemy).

---

## P

### Pedido
Ordem de compra confirmada, gerada a partir de um carrinho finalizado.

### PIX
Sistema de pagamento instantâneo brasileiro, integrado via Mercado Pago.

### PostgreSQL
Sistema de gerenciamento de banco de dados relacional usado no Runas.

### Produto
Item comercializado, pode ter múltiplas variantes (tamanhos, cores, etc).

### Pydantic
Biblioteca Python para validação de dados usando type hints.

---

## Q

### Query Parameter
Parâmetro passado na URL após `?` (ex: `?page=1&size=20`).

---

## R

### RabbitMQ
Sistema de mensageria usado para comunicação assíncrona entre microsserviços.

### Rate Limiting
Limitação de número de requisições por período para prevenir abuso.

### Redis
Banco de dados em memória usado para cache, sessões e filas.

### Refresh Token
Token de longa duração usado para renovar o access token sem novo login.

### Repository Pattern
Padrão de projeto que abstrai o acesso a dados em uma camada separada.

### Retry
Tentativa automática de reexecutar uma operação que falhou.

### Role
Papel/função de um usuário no sistema: **ADMIN** (acesso total) ou **OPERADOR** (acesso limitado).

### Routing Key
Chave usada pelo RabbitMQ para rotear mensagens para filas específicas.

---

## S

### Saldo Devedor
Valor total que um cliente deve em compras fiadas.

### Schema
Estrutura de dados definida com Pydantic para validação de entrada/saída da API.

### Seed
Processo de popular o banco de dados com dados iniciais (admin, categorias).

### SKU (Stock Keeping Unit)
Código único que identifica uma variante de produto.

### Snapshot
Cópia dos dados em um momento específico (ex: preço do produto no momento da compra).

### Soft Delete
Desativação lógica de um registro sem deletá-lo fisicamente (campo `ativo=False`).

### SQLAlchemy
ORM Python usado para interagir com o banco de dados.

### Status de Pedido
Estado atual do pedido: PENDENTE, CONFIRMADO, SEPARANDO, ENVIADO, ENTREGUE, CANCELADO.

---

## T

### Toast
Notificação temporária que aparece na tela (geralmente 3 segundos).

### Token
Credencial de autenticação gerada após login bem-sucedido.

### Transação
Conjunto de operações de banco que devem ser executadas atomicamente (tudo ou nada).

### TypeScript
Superset do JavaScript que adiciona tipagem estática.

---

## U

### UUID (Universally Unique Identifier)
Identificador único de 128 bits usado como chave primária no banco.

---

## V

### Variante
Versão específica de um produto (ex: Coca-Cola 2L, Coca-Cola 600ml).

### Vencimento
Data limite para pagamento de uma conta a receber.

### Vite
Build tool moderno e rápido para projetos frontend.

---

## W

### Webhook
Endpoint HTTP que recebe notificações automáticas de serviços externos (ex: Mercado Pago).

### WhatsApp
Aplicativo de mensagens usado para notificações via Evolution API.

---

## Z

### Zod
Biblioteca TypeScript para validação de schemas e dados.

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
