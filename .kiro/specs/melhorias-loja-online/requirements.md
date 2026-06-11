# Requirements Document

## Introduction

Este documento especifica os requisitos para tornar a loja online do sistema ERP multi-tenant 100% funcional. O sistema já possui microserviços de Empresas, Clientes, Produtos, Estoque e Vendas, além de uma loja online básica (catálogo de produtos) e venda de balcão implementada.

As melhorias implementarão três funcionalidades principais:
1. Validação de estoque real no carrinho de compras
2. Criação de cliente no checkout com três fluxos distintos (cadastrado, convidado, cadastro no checkout)
3. Integração com gateway de pagamento Mercado Pago

O sistema utiliza Redis para gerenciamento de sessão do carrinho e segue arquitetura de microserviços com FastAPI + SQLAlchemy + PostgreSQL.

## Glossary

- **Sistema_Loja_Online**: Aplicação web pública onde clientes finais navegam produtos e realizam compras
- **Servico_Carrinho**: Componente que gerencia o carrinho de compras usando Redis como storage de sessão
- **Servico_Estoque**: Microsserviço responsável por controlar disponibilidade e movimentação de produtos
- **Servico_Clientes**: Microsserviço responsável por gerenciar cadastros de clientes vinculados às empresas
- **Servico_Vendas**: Microsserviço responsável por criar e gerenciar vendas (pedidos)
- **Gateway_Pagamento**: Componente que integra com a API do Mercado Pago para processar pagamentos
- **Cliente_Cadastrado**: Usuário que possui registro completo no Servico_Clientes com credenciais de acesso
- **Cliente_Convidado**: Usuário que realiza compra fornecendo apenas dados básicos sem criar cadastro permanente
- **Checkout**: Processo de finalização de compra incluindo coleta de dados, validação de estoque e pagamento
- **Item_Carrinho**: Representação de um produto e sua quantidade no carrinho de compras
- **Venda_Balcao**: Venda criada por vendedor interno onde cliente_id pode ser NULL
- **Multi_Tenant**: Arquitetura onde cada empresa possui dados isolados (produtos, clientes, vendas próprios)
- **Sessao_Carrinho**: Dados temporários do carrinho armazenados no Redis identificados por session_id
- **Transacao_Concorrente**: Múltiplas requisições simultâneas tentando modificar o mesmo recurso (ex: estoque)

## Requirements

### Requirement 1: Validação de Estoque em Tempo Real

**User Story:** Como cliente da loja online, eu quero que o sistema valide a disponibilidade real dos produtos no meu carrinho antes de finalizar a compra, para que eu não tente comprar produtos que não estão disponíveis.

#### Acceptance Criteria

1. WHEN um Item_Carrinho é adicionado ao Servico_Carrinho, THE Sistema_Loja_Online SHALL consultar o Servico_Estoque para verificar disponibilidade atual
2. IF a quantidade solicitada excede o estoque disponível, THEN THE Servico_Carrinho SHALL retornar erro com a quantidade máxima disponível
3. WHEN o checkout é iniciado, THE Sistema_Loja_Online SHALL validar o estoque de todos os Item_Carrinho novamente
4. IF qualquer Item_Carrinho possui estoque insuficiente durante checkout, THEN THE Sistema_Loja_Online SHALL atualizar o carrinho com as quantidades disponíveis e notificar o cliente
5. WHEN múltiplas Transacao_Concorrente tentam reduzir o mesmo estoque, THE Servico_Estoque SHALL processar as requisições de forma serializada preservando consistência
6. THE Servico_Estoque SHALL considerar vendas pendentes de pagamento ao calcular estoque disponível

### Requirement 2: Fluxo de Cliente Convidado (Compra Rápida)

**User Story:** Como cliente da loja online, eu quero poder comprar sem criar cadastro, fornecendo apenas dados básicos, para que eu possa finalizar minha compra rapidamente.

#### Acceptance Criteria

1. WHEN um cliente escolhe checkout como convidado, THE Sistema_Loja_Online SHALL solicitar nome, email, telefone e endereço completo
2. THE Sistema_Loja_Online SHALL validar formato de email e telefone antes de prosseguir
3. WHEN a compra de Cliente_Convidado é finalizada, THE Servico_Vendas SHALL criar venda com cliente_id NULL
4. THE Servico_Vendas SHALL armazenar nome, email, telefone e endereço do Cliente_Convidado nos campos da venda
5. WHEN a venda é criada, THE Sistema_Loja_Online SHALL retornar número do pedido para rastreamento
6. THE Sistema_Loja_Online SHALL enviar email de confirmação com número do pedido para o email fornecido
7. THE Sistema_Loja_Online SHALL NOT criar registro no Servico_Clientes para Cliente_Convidado

### Requirement 3: Fluxo de Cliente Cadastrado

**User Story:** Como cliente cadastrado no sistema, eu quero fazer login e ter minhas compras vinculadas ao meu cadastro, para que eu possa acessar histórico e dados salvos.

#### Acceptance Criteria

1. WHEN um Cliente_Cadastrado acessa o checkout, THE Sistema_Loja_Online SHALL identificar o cliente através da sessão autenticada
2. THE Sistema_Loja_Online SHALL recuperar dados cadastrais do Servico_Clientes automaticamente
3. WHEN a compra é finalizada, THE Servico_Vendas SHALL vincular a venda ao cliente_id do Cliente_Cadastrado
4. THE Sistema_Loja_Online SHALL permitir que Cliente_Cadastrado visualize histórico de pedidos
5. WHEN Cliente_Cadastrado acessa "Meus Pedidos", THE Sistema_Loja_Online SHALL listar todas as vendas vinculadas ao seu cliente_id
6. THE Sistema_Loja_Online SHALL exibir endereços salvos do Cliente_Cadastrado durante checkout

### Requirement 4: Fluxo de Cadastro no Checkout

**User Story:** Como novo cliente da loja online, eu quero criar minha conta durante o checkout, para que eu possa finalizar a compra e ter acesso a recursos de cliente cadastrado posteriormente.

#### Acceptance Criteria

1. WHEN um cliente escolhe criar cadastro no checkout, THE Sistema_Loja_Online SHALL solicitar nome, email, telefone, CPF, endereço completo e senha
2. THE Sistema_Loja_Online SHALL validar unicidade de email e CPF antes de criar cadastro
3. THE Sistema_Loja_Online SHALL validar formato de CPF usando validador apropriado
4. THE Sistema_Loja_Online SHALL validar força de senha (mínimo 8 caracteres, letra maiúscula, minúscula, número)
5. WHEN dados são válidos, THE Sistema_Loja_Online SHALL criar registro no Servico_Clientes vinculado à empresa Multi_Tenant
6. WHEN o cadastro é criado com sucesso, THE Servico_Clientes SHALL retornar o cliente_id gerado
7. THE Servico_Vendas SHALL vincular a venda ao cliente_id retornado pelo Servico_Clientes
8. WHEN a compra é finalizada, THE Sistema_Loja_Online SHALL autenticar o cliente automaticamente
9. THE Sistema_Loja_Online SHALL enviar email de boas-vindas com instruções de acesso

### Requirement 5: Gerenciamento de Sessão do Carrinho

**User Story:** Como administrador do sistema, eu quero que o carrinho de compras utilize Redis para armazenamento de sessão, para garantir performance e escalabilidade.

#### Acceptance Criteria

1. THE Servico_Carrinho SHALL armazenar todos os Item_Carrinho no Redis usando session_id como chave
2. WHEN um Item_Carrinho é adicionado, THE Servico_Carrinho SHALL definir TTL (Time To Live) de 24 horas para a Sessao_Carrinho
3. WHEN o cliente interage com o carrinho, THE Servico_Carrinho SHALL renovar o TTL da Sessao_Carrinho
4. WHEN o checkout é concluído com sucesso, THE Servico_Carrinho SHALL remover a Sessao_Carrinho do Redis
5. WHEN a Sessao_Carrinho expira, THE Redis SHALL remover automaticamente os dados
6. THE Servico_Carrinho SHALL serializar Item_Carrinho como JSON antes de armazenar no Redis
7. WHEN o carrinho é recuperado, THE Servico_Carrinho SHALL deserializar JSON e validar integridade dos dados

### Requirement 6: Integração com Mercado Pago

**User Story:** Como cliente da loja online, eu quero pagar minhas compras usando Mercado Pago, para ter acesso a diversos métodos de pagamento de forma segura.

#### Acceptance Criteria

1. WHEN o checkout é finalizado, THE Gateway_Pagamento SHALL criar preferência de pagamento na API do Mercado Pago
2. THE Gateway_Pagamento SHALL incluir itens do carrinho, valores totais e dados do comprador na preferência
3. THE Gateway_Pagamento SHALL armazenar preference_id retornado pela API vinculado à venda pendente
4. WHEN a preferência é criada, THE Sistema_Loja_Online SHALL redirecionar cliente para página de pagamento do Mercado Pago
5. THE Gateway_Pagamento SHALL configurar webhook para receber notificações de pagamento
6. WHEN o Mercado Pago envia notificação de pagamento aprovado, THE Gateway_Pagamento SHALL consultar status do pagamento via API
7. IF o pagamento é confirmado como aprovado, THEN THE Servico_Vendas SHALL marcar venda como paga e confirmar pedido
8. IF o pagamento é rejeitado, THEN THE Servico_Vendas SHALL manter venda como pendente e notificar cliente
9. THE Gateway_Pagamento SHALL armazenar payment_id do Mercado Pago vinculado à venda
10. THE Gateway_Pagamento SHALL implementar idempotência para evitar processar a mesma notificação múltiplas vezes

### Requirement 7: Reserva Temporária de Estoque

**User Story:** Como administrador do sistema, eu quero que o estoque seja reservado temporariamente durante o processo de pagamento, para evitar overselling em vendas concorrentes.

#### Acceptance Criteria

1. WHEN o checkout é iniciado, THE Servico_Estoque SHALL criar reserva temporária para todos os Item_Carrinho
2. THE Servico_Estoque SHALL definir TTL de 15 minutos para cada reserva temporária
3. THE Servico_Estoque SHALL subtrair quantidades reservadas do estoque disponível para novas consultas
4. WHEN o pagamento é confirmado, THE Servico_Estoque SHALL converter reserva temporária em movimentação definitiva de saída
5. WHEN a reserva expira sem confirmação de pagamento, THE Servico_Estoque SHALL liberar automaticamente o estoque reservado
6. IF o pagamento é rejeitado, THEN THE Servico_Estoque SHALL liberar imediatamente a reserva temporária
7. THE Servico_Estoque SHALL armazenar identificador da venda associado a cada reserva temporária

### Requirement 8: Consistência Multi-Tenant

**User Story:** Como administrador do sistema, eu quero garantir isolamento de dados entre empresas, para que cada empresa acesse apenas seus próprios produtos, clientes e vendas.

#### Acceptance Criteria

1. WHEN o Sistema_Loja_Online é acessado, THE sistema SHALL identificar a empresa através do domínio ou subdomínio
2. THE Servico_Carrinho SHALL armazenar empresa_id junto com cada Sessao_Carrinho
3. THE Sistema_Loja_Online SHALL exibir apenas produtos da empresa correspondente no catálogo
4. WHEN o Servico_Estoque valida disponibilidade, THE serviço SHALL considerar apenas estoque da empresa_id correspondente
5. WHEN o Servico_Clientes cria cadastro, THE serviço SHALL vincular cliente à empresa_id identificada
6. THE Servico_Vendas SHALL vincular cada venda à empresa_id correspondente
7. THE Sistema_Loja_Online SHALL prevenir acesso cross-tenant em todas as operações

### Requirement 9: Tratamento de Erros e Resiliência

**User Story:** Como desenvolvedor do sistema, eu quero que o sistema trate falhas de integração de forma resiliente, para garantir boa experiência do usuário mesmo em caso de problemas temporários.

#### Acceptance Criteria

1. WHEN o Servico_Estoque está indisponível durante validação, THE Sistema_Loja_Online SHALL retornar erro claro e sugerir tentativa posterior
2. WHEN o Servico_Clientes está indisponível durante cadastro, THE Sistema_Loja_Online SHALL permitir checkout como Cliente_Convidado temporariamente
3. WHEN o Gateway_Pagamento falha ao criar preferência, THE Sistema_Loja_Online SHALL manter carrinho salvo e permitir retry
4. WHEN a comunicação com API do Mercado Pago falha, THE Gateway_Pagamento SHALL implementar retry com backoff exponencial (3 tentativas)
5. IF todas as tentativas de comunicação com Mercado Pago falham, THEN THE Sistema_Loja_Online SHALL notificar administrador e cliente
6. THE Gateway_Pagamento SHALL logar todas as requisições e respostas da API do Mercado Pago para auditoria
7. WHEN o webhook do Mercado Pago recebe notificação duplicada, THE Gateway_Pagamento SHALL processar idempotentemente sem erro

### Requirement 10: Validações de Dados de Checkout

**User Story:** Como administrador do sistema, eu quero que todos os dados fornecidos no checkout sejam validados rigorosamente, para garantir qualidade dos dados e prevenir erros.

#### Acceptance Criteria

1. THE Sistema_Loja_Online SHALL validar formato de email usando regex padrão RFC 5322
2. THE Sistema_Loja_Online SHALL validar formato de telefone brasileiro (celular e fixo)
3. THE Sistema_Loja_Online SHALL validar CPF usando algoritmo de dígitos verificadores
4. THE Sistema_Loja_Online SHALL validar CEP usando formato brasileiro (XXXXX-XXX)
5. THE Sistema_Loja_Online SHALL validar que endereço completo contenha: logradouro, número, bairro, cidade, estado, CEP
6. WHEN validação de campo falha, THE Sistema_Loja_Online SHALL retornar mensagem de erro específica indicando o problema
7. THE Sistema_Loja_Online SHALL sanitizar inputs para prevenir XSS e SQL injection
8. THE Sistema_Loja_Online SHALL validar que quantidade de Item_Carrinho seja número inteiro positivo maior que zero

### Requirement 11: Auditoria e Rastreabilidade

**User Story:** Como administrador do sistema, eu quero que todas as operações críticas sejam auditadas, para permitir rastreamento e resolução de problemas.

#### Acceptance Criteria

1. THE Servico_Vendas SHALL registrar timestamp de criação, atualização e conclusão de cada venda
2. THE Servico_Vendas SHALL registrar tipo de cliente (cadastrado, convidado, novo) em cada venda
3. THE Gateway_Pagamento SHALL registrar todos os eventos de pagamento com timestamps
4. THE Servico_Estoque SHALL registrar cada reserva temporária com timestamp e venda_id
5. WHEN reserva temporária expira, THE Servico_Estoque SHALL registrar evento de liberação automática
6. THE Sistema_Loja_Online SHALL logar tentativas de checkout com validação de estoque
7. WHEN erro ocorre em qualquer serviço, THE sistema SHALL gerar request_id único e incluir em logs para correlação

### Requirement 12: Parser e Serialização de Dados do Carrinho

**User Story:** Como desenvolvedor do sistema, eu quero parsers robustos para serialização de dados do carrinho no Redis, para garantir integridade dos dados em todas as operações.

#### Acceptance Criteria

1. WHEN Item_Carrinho é salvo no Redis, THE Parser_Carrinho SHALL serializar objeto para JSON incluindo produto_id, quantidade, preco_unitario, empresa_id
2. THE Parser_Carrinho SHALL validar que todos os campos obrigatórios estão presentes antes de serializar
3. WHEN Sessao_Carrinho é recuperada do Redis, THE Parser_Carrinho SHALL deserializar JSON para objetos Item_Carrinho
4. THE Parser_Carrinho SHALL validar tipos de dados durante deserialização (números são numéricos, IDs são inteiros positivos)
5. IF deserialização falha devido a dados corrompidos, THEN THE Servico_Carrinho SHALL retornar erro e sugerir limpeza do carrinho
6. THE Pretty_Printer_Carrinho SHALL formatar Sessao_Carrinho em JSON estruturado para debug e logs
7. FOR ALL Sessao_Carrinho válidas, serializar com Parser_Carrinho, deserializar e serializar novamente SHALL produzir JSON equivalente (round-trip property)

## Out of Scope

As seguintes funcionalidades NÃO fazem parte deste escopo e serão implementadas futuramente:

- **Cálculo de frete**: O sistema opera para comércio local e não vende para fora da região
- **Sistema de cupons de desconto**: Será implementado em fase posterior
- **Notificações por email/WhatsApp**: Confirmações serão implementadas posteriormente
- **Sistema completo de autenticação/login**: Apenas o cadastro básico será implementado; login completo com recuperação de senha, 2FA, etc. será feito futuramente
- **Programa de fidelidade/cashback**: Fora do escopo inicial
- **Múltiplos endereços de entrega**: Cliente terá apenas um endereço inicialmente

## Notes

- O sistema de Venda de Balcão já implementado permite cliente_id NULL, demonstrando que o modelo de dados suporta vendas sem cliente cadastrado
- A integração com Mercado Pago requer credenciais (Public Key e Access Token) configuradas nas variáveis de ambiente
- O Redis será usado exclusivamente para sessão do carrinho; dados de vendas finalizadas vão para PostgreSQL
- Transações concorrentes de estoque devem usar locks otimistas (versioning) ou pessimistas (SELECT FOR UPDATE) para garantir consistência
- Parsers de serialização do carrinho são críticos para integridade - round-trip testing é obrigatório
