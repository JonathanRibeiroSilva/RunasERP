# Requirements Document - Loja Online MVP

## Introduction

Este documento especifica os requisitos funcionais completos para o MVP da Loja Online (E-commerce) do ERP. O sistema permite que clientes realizem compras online com validação avançada de estoque, múltiplas formas de pagamento (online via Mercado Pago e offline), gestão de taxa de entrega por bairro, controle de reservas temporárias, e notificações automáticas via WhatsApp.

O escopo abrange desde a experiência de compra do cliente (adição ao carrinho, checkout, pagamento) até a gestão completa do ciclo de vida da venda (confirmação, separação, entrega, finalização), incluindo integrações com serviços externos (Mercado Pago, ViaCEP, Evolution API) e controle rigoroso de concorrência no estoque.

## Glossary

- **Sistema_Loja**: O sistema completo de e-commerce, incluindo carrinho, checkout e gestão de vendas
- **Carrinho_Service**: Componente responsável pelo gerenciamento do carrinho de compras em Redis
- **Checkout_Service**: Componente responsável pelo processamento do checkout e criação de vendas
- **Estoque_Service**: Serviço externo que gerencia quantidades físicas de produtos
- **Pagamento_Service**: Componente responsável pela integração com Mercado Pago
- **Reserva_Temporaria**: Bloqueio temporário de quantidade de estoque durante o processo de compra
- **Redis_Lock**: Mecanismo de bloqueio distribuído para garantir atomicidade em operações concorrentes
- **Cliente_Logado**: Usuário autenticado com cliente_id válido
- **Cliente_Convidado**: Usuário não autenticado que realiza compra fornecendo apenas dados básicos
- **Webhook**: Notificação assíncrona do Mercado Pago sobre eventos de pagamento
- **Multi_Tenant**: Arquitetura onde cada empresa possui configurações e dados isolados
- **Taxa_Entrega**: Valor cobrado para entrega de produtos no endereço do cliente
- **Fiado**: Modalidade de crédito onde o cliente possui limite disponível para compras
- **Pagamento_Misto**: Combinação de crédito (fiado) e pagamento online na mesma transação
- **ViaCEP**: API externa para consulta de endereços e extração de bairros via CEP
- **Evolution_API**: Serviço externo para envio de notificações via WhatsApp
- **Job_Limpeza**: Processo automatizado que remove reservas temporárias expiradas
- **Estoque_Disponivel**: Quantidade física menos a soma de reservas não expiradas
- **Baixa_Estoque**: Redução definitiva da quantidade física no momento da separação
- **Historico_Status**: Auditoria completa de mudanças de status da venda


## Requirements

### Requirement 1: Adicionar Produtos ao Carrinho com Reserva Temporária

**User Story:** Como um cliente, eu quero adicionar produtos ao carrinho e ter a quantidade reservada temporariamente, para que eu tenha garantia de disponibilidade enquanto navego.

#### Acceptance Criteria

1. WHEN um cliente adiciona um produto ao carrinho, THE Carrinho_Service SHALL consultar o Estoque_Service para verificar disponibilidade antes de adicionar
2. WHEN um produto está disponível em quantidade suficiente, THE Carrinho_Service SHALL criar uma Reserva_Temporaria com duração de 15 minutos
3. WHEN um produto está disponível em quantidade parcial (menor que solicitado), THE Carrinho_Service SHALL adicionar apenas a quantidade disponível e exibir aviso ao cliente
4. WHEN um produto está com estoque zerado, THE Carrinho_Service SHALL retornar erro HTTP 409 e bloquear a adição
5. WHEN uma Reserva_Temporaria é criada, THE Sistema_Loja SHALL usar Redis_Lock para garantir atomicidade da operação
6. WHILE uma Reserva_Temporaria está ativa, THE Estoque_Service SHALL calcular Estoque_Disponivel subtraindo a soma de todas as reservas não expiradas
7. WHEN um cliente adiciona mais unidades de um produto já no carrinho, THE Carrinho_Service SHALL validar disponibilidade considerando apenas as unidades adicionais
8. THE Carrinho_Service SHALL armazenar o carrinho em Redis com TTL de 7 dias
9. THE Carrinho_Service SHALL limitar a adição a 100 unidades por produto
10. THE Carrinho_Service SHALL limitar o carrinho a 50 produtos diferentes

### Requirement 2: Validar Estoque ao Exibir Carrinho

**User Story:** Como um cliente, eu quero que o carrinho sempre exiba quantidades atualizadas, para que eu saiba se posso continuar com a compra.

#### Acceptance Criteria

1. WHEN um cliente acessa o carrinho, THE Carrinho_Service SHALL validar disponibilidade de cada item consultando o Estoque_Service
2. WHEN um produto está com estoque zerado, THE Carrinho_Service SHALL remover o item do carrinho e exibir mensagem explicativa
3. WHEN um produto está disponível em quantidade parcial, THE Carrinho_Service SHALL ajustar automaticamente a quantidade no carrinho para o máximo disponível
4. WHEN um produto está disponível em quantidade suficiente, THE Carrinho_Service SHALL manter a quantidade original
5. WHEN um produto foi desativado, THE Carrinho_Service SHALL remover o item do carrinho
6. WHEN existem itens zerados no carrinho, THE Carrinho_Service SHALL bloquear o botão de checkout
7. THE Carrinho_Service SHALL exibir indicador visual para cada produto informando status de disponibilidade (OK, PARCIAL, ZERADO)

### Requirement 3: Processar Checkout com Reserva Final

**User Story:** Como um cliente, eu quero finalizar minha compra com garantia de que os produtos estão reservados, para que não haja perda de estoque durante o pagamento.

#### Acceptance Criteria

1. WHEN um cliente inicia o checkout, THE Checkout_Service SHALL validar novamente todo o estoque do carrinho
2. WHEN algum produto está zerado no momento do checkout, THE Checkout_Service SHALL retornar erro HTTP 409 e impedir prosseguimento
3. WHEN todos os produtos estão disponíveis, THE Checkout_Service SHALL criar uma nova Reserva_Temporaria com duração de 5 minutos para pagamento
4. WHEN a Reserva_Temporaria de 5 minutos é criada, THE Checkout_Service SHALL liberar a Reserva_Temporaria anterior de 15 minutos
5. THE Checkout_Service SHALL usar Redis_Lock durante a criação da reserva final para evitar race conditions
6. WHEN a Reserva_Temporaria de 5 minutos expira sem pagamento, THE Job_Limpeza SHALL remover a reserva e liberar o estoque


### Requirement 4: Autenticar Cliente no Checkout

**User Story:** Como um lojista, eu quero que o sistema identifique o cliente de forma flexível, para que tanto clientes cadastrados quanto novos clientes possam comprar.

#### Acceptance Criteria

1. WHEN um Cliente_Logado inicia o checkout, THE Checkout_Service SHALL usar o cliente_id da sessão autenticada
2. WHERE um cliente não está autenticado, THE Checkout_Service SHALL oferecer duas opções: comprar como convidado ou criar conta
3. WHEN um Cliente_Convidado escolhe comprar sem cadastro, THE Checkout_Service SHALL exigir Nome e Telefone obrigatoriamente
4. WHERE a compra é como convidado, THE Checkout_Service SHALL aceitar Email e CPF opcionalmente
5. WHEN um cliente escolhe criar conta durante o checkout, THE Checkout_Service SHALL exigir Nome, CPF, Telefone, Email e Senha
6. WHEN uma nova conta é criada durante checkout, THE Sistema_Loja SHALL ativar o cliente imediatamente e prosseguir com a compra usando o cliente_id criado
7. THE Checkout_Service SHALL validar formato de telefone (DDD + 9 dígitos) e normalizar para armazenamento
8. WHERE CPF é fornecido, THE Checkout_Service SHALL validar dígitos verificadores
9. WHEN um CPF fornecido já está cadastrado no sistema, THE Checkout_Service SHALL retornar erro HTTP 409 e sugerir login

### Requirement 5: Selecionar Forma de Pagamento Online

**User Story:** Como um cliente, eu quero pagar online via Mercado Pago, para que eu tenha a compra confirmada automaticamente após o pagamento.

#### Acceptance Criteria

1. WHERE pagamento online é selecionado, THE Checkout_Service SHALL oferecer três opções: PIX, Cartão de Débito, Cartão de Crédito
2. WHEN uma forma de pagamento online é selecionada, THE Pagamento_Service SHALL criar uma preferência no Mercado Pago usando o access_token da empresa
3. THE Pagamento_Service SHALL recuperar configurações de pagamento da tabela configuracoes_pagamento filtrando por empresa_id
4. THE Pagamento_Service SHALL incluir na preferência: itens do carrinho, valor total, URLs de retorno (sucesso, falha, pendente)
5. WHEN a preferência é criada com sucesso, THE Checkout_Service SHALL criar a venda com status PEDIDO antes do redirecionamento
6. THE Checkout_Service SHALL manter a Reserva_Temporaria de 5 minutos ativa após criação da venda
7. WHEN a preferência é criada, THE Checkout_Service SHALL atualizar a venda para status PENDENTE_PAGAMENTO e armazenar payment_id
8. THE Pagamento_Service SHALL redirecionar o cliente para a URL de pagamento do Mercado Pago
9. WHEN a Reserva_Temporaria de 5 minutos expira sem confirmação de pagamento, THE Sistema_Loja SHALL cancelar automaticamente a venda

### Requirement 6: Selecionar Forma de Pagamento Offline

**User Story:** Como um cliente, eu quero pagar na entrega ou retirada, para que eu não precise usar pagamento online.

#### Acceptance Criteria

1. WHERE pagamento offline é selecionado, THE Checkout_Service SHALL oferecer duas opções: Dinheiro e Fiado
2. WHEN a forma Dinheiro é selecionada, THE Checkout_Service SHALL perguntar se o cliente precisa de troco
3. WHERE o cliente precisa de troco, THE Checkout_Service SHALL solicitar o valor do troco e armazenar na venda
4. WHEN a forma Dinheiro é selecionada, THE Checkout_Service SHALL criar a venda com status PEDIDO e forma_pagamento como DINHEIRO
5. WHEN a forma Fiado é selecionada, THE Checkout_Service SHALL validar se o cliente possui campo permite_fiado_online igual a TRUE
6. WHEN permite_fiado_online é FALSE, THE Checkout_Service SHALL retornar erro HTTP 403 informando que fiado online não está liberado
7. WHEN Fiado é selecionado e permitido, THE Checkout_Service SHALL validar se o cliente está ativo, não bloqueado e possui crédito disponível maior que zero
8. WHEN o crédito disponível é insuficiente para o valor total, THE Checkout_Service SHALL retornar erro HTTP 400 informando saldo insuficiente
9. WHEN todas as validações de Fiado são aprovadas, THE Checkout_Service SHALL bloquear o valor do crédito imediatamente e criar a venda com status PEDIDO
10. WHERE a opção é Cliente_Convidado, THE Checkout_Service SHALL permitir apenas Dinheiro e bloqueair Fiado


### Requirement 7: Processar Pagamento Misto (Fiado + Online)

**User Story:** Como um cliente com crédito disponível, eu quero usar parte do meu crédito e pagar o restante online, para que eu possa aproveitar meu saldo sem precisar pagar tudo com crédito.

#### Acceptance Criteria

1. WHERE pagamento misto é selecionado, THE Checkout_Service SHALL validar que o cliente possui permite_fiado_online igual a TRUE
2. WHEN pagamento misto é escolhido, THE Checkout_Service SHALL solicitar o valor a ser usado do crédito com mínimo de R$ 1,00
3. THE Checkout_Service SHALL aceitar valores com centavos no campo de crédito
4. WHEN o valor de crédito solicitado é maior que o crédito disponível, THE Checkout_Service SHALL retornar erro HTTP 400 informando saldo insuficiente
5. WHEN o valor de crédito é válido, THE Checkout_Service SHALL calcular o valor restante como (valor_total - valor_credito)
6. THE Checkout_Service SHALL bloquear o valor de crédito imediatamente antes de criar a preferência no Mercado Pago
7. THE Pagamento_Service SHALL criar a preferência no Mercado Pago apenas com o valor restante (não com o valor total)
8. WHEN o pagamento online falha ou é cancelado, THE Checkout_Service SHALL liberar o crédito bloqueado de volta ao cliente
9. WHEN o pagamento online é aprovado, THE Checkout_Service SHALL manter o crédito bloqueado e registrar a transação de uso
10. THE Checkout_Service SHALL armazenar na venda os valores: valor_credito_usado, valor_pago_online, valor_total

### Requirement 8: Receber e Processar Webhooks do Mercado Pago

**User Story:** Como um lojista, eu quero que o sistema processe automaticamente as notificações de pagamento, para que as vendas sejam confirmadas sem intervenção manual.

#### Acceptance Criteria

1. WHEN o Mercado Pago envia um webhook, THE Pagamento_Service SHALL validar que a requisição vem do Mercado Pago verificando assinatura
2. THE Sistema_Loja SHALL registrar a URL do webhook como /loja/{empresa_slug}/webhook/mercadopago
3. WHEN um webhook é recebido, THE Pagamento_Service SHALL consultar a tabela webhook_processados usando payment_id como chave única
4. WHEN o payment_id já existe em webhook_processados, THE Pagamento_Service SHALL retornar HTTP 200 sem processar novamente (idempotência)
5. WHEN o webhook é novo, THE Pagamento_Service SHALL inserir o payment_id em webhook_processados antes de processar
6. WHEN o evento é payment.approved, THE Pagamento_Service SHALL atualizar a venda para status CONFIRMADA e manter a Reserva_Temporaria ativa
7. WHEN o evento é payment.rejected ou payment.cancelled, THE Pagamento_Service SHALL atualizar a venda para status CANCELADA e liberar a Reserva_Temporaria
8. WHEN o evento é payment.refunded, THE Pagamento_Service SHALL atualizar a venda para status REEMBOLSADA e processar devolução de estoque e crédito
9. THE Pagamento_Service SHALL criar entrada no Historico_Status para cada mudança de status registrando: status_anterior, status_novo, timestamp, origem (webhook)
10. WHEN o processamento do webhook falha, THE Pagamento_Service SHALL logar o erro com structlog incluindo payment_id, evento, empresa_id e stack trace
11. THE Pagamento_Service SHALL retornar HTTP 200 para o Mercado Pago mesmo em caso de erro interno para evitar reenvios desnecessários

### Requirement 9: Calcular Taxa de Entrega por Bairro

**User Story:** Como um lojista, eu quero cobrar taxa de entrega diferenciada por bairro, para que eu possa refletir custos logísticos variáveis.

#### Acceptance Criteria

1. WHEN o tipo de entrega selecionado é DELIVERY, THE Checkout_Service SHALL exigir endereço completo incluindo CEP
2. WHEN o tipo de entrega selecionado é RETIRADA, THE Checkout_Service SHALL marcar endereço como opcional
3. WHEN um CEP é fornecido, THE Sistema_Loja SHALL consultar a API ViaCEP para obter informações do endereço
4. WHEN a consulta ao ViaCEP retorna sucesso, THE Sistema_Loja SHALL extrair o campo bairro da resposta
5. WHEN o bairro é extraído, THE Sistema_Loja SHALL consultar a tabela faixas_entrega filtrando por bairro e empresa_id
6. WHEN existe uma configuração específica para o bairro, THE Sistema_Loja SHALL usar a taxa da tabela faixas_entrega
7. WHEN não existe configuração específica para o bairro, THE Sistema_Loja SHALL usar a taxa_entrega_padrao da tabela configuracoes_loja
8. WHEN a consulta ao ViaCEP falha ou retorna erro, THE Sistema_Loja SHALL permitir continuar o checkout usando a taxa_entrega_padrao
9. THE Sistema_Loja SHALL exibir a taxa de entrega calculada no resumo do pedido antes da finalização
10. WHERE o tipo de entrega é RETIRADA, THE Sistema_Loja SHALL definir taxa de entrega como R$ 0,00


### Requirement 10: Gerenciar Ciclo de Vida da Venda com Status

**User Story:** Como um lojista, eu quero acompanhar o progresso de cada venda através de status claros, para que eu saiba quais ações preciso tomar.

#### Acceptance Criteria

1. WHEN uma venda é criada no checkout, THE Sistema_Loja SHALL definir status inicial como PEDIDO
2. WHEN o cliente é redirecionado para pagamento online, THE Sistema_Loja SHALL atualizar status para PENDENTE_PAGAMENTO
3. WHEN o pagamento é aprovado via webhook, THE Sistema_Loja SHALL atualizar status para CONFIRMADA
4. WHEN o lojista marca produtos como separados, THE Sistema_Loja SHALL atualizar status para SEPARADA
5. WHERE o tipo de entrega é DELIVERY e produtos foram separados, THE Sistema_Loja SHALL permitir atualização para status EM_ENTREGA
6. WHEN o cliente recebe os produtos, THE Sistema_Loja SHALL atualizar status para ENTREGUE
7. WHEN todos os processos pós-venda são concluídos, THE Sistema_Loja SHALL atualizar status para FINALIZADA
8. WHEN uma venda é cancelada por timeout, rejeição de pagamento ou manualmente, THE Sistema_Loja SHALL atualizar status para CANCELADA
9. WHEN um reembolso é processado, THE Sistema_Loja SHALL atualizar status para REEMBOLSADA
10. THE Sistema_Loja SHALL criar entrada no Historico_Status para cada mudança de status incluindo: status_anterior, status_novo, timestamp, usuario_id (se aplicável), observacao

### Requirement 11: Implementar Timeouts e Cancelamentos Automáticos

**User Story:** Como um lojista, eu quero que vendas abandonadas sejam canceladas automaticamente, para que o estoque não fique bloqueado indefinidamente.

#### Acceptance Criteria

1. WHEN uma Reserva_Temporaria de 15 minutos (carrinho) expira, THE Job_Limpeza SHALL remover a reserva da tabela reservas_temporarias
2. WHEN uma Reserva_Temporaria de 5 minutos (checkout) expira sem confirmação de pagamento, THE Sistema_Loja SHALL cancelar a venda automaticamente
3. WHEN uma venda permanece no status CONFIRMADA por mais de 48 horas, THE Sistema_Loja SHALL cancelar automaticamente e criar entrada no Historico_Status
4. WHEN uma venda está no status CONFIRMADA por 12 horas, THE Sistema_Loja SHALL enviar notificação de aviso ao lojista
5. WHEN uma venda está no status CONFIRMADA por 24 horas, THE Sistema_Loja SHALL enviar notificação urgente ao lojista
6. WHERE o status é PEDIDO ou PENDENTE_PAGAMENTO, THE Sistema_Loja SHALL permitir que o cliente cancele a venda
7. WHERE o status é diferente de FINALIZADA, THE Sistema_Loja SHALL permitir que o lojista cancele a venda manualmente
8. WHEN o webhook retorna evento payment.rejected, THE Sistema_Loja SHALL cancelar a venda automaticamente
9. THE Job_Limpeza SHALL executar a cada 1 minuto para processar reservas expiradas
10. WHEN uma venda é cancelada automaticamente por timeout, THE Sistema_Loja SHALL liberar Reserva_Temporaria e crédito bloqueado (se aplicável)

### Requirement 12: Realizar Baixa de Estoque no Momento Correto

**User Story:** Como um lojista, eu quero que o estoque seja baixado apenas quando eu separo os produtos, para que o inventário reflita a realidade física.

#### Acceptance Criteria

1. WHILE a venda está no status PEDIDO, THE Sistema_Loja SHALL manter apenas a Reserva_Temporaria sem baixar o estoque físico
2. WHILE a venda está no status PENDENTE_PAGAMENTO, THE Sistema_Loja SHALL manter apenas a Reserva_Temporaria sem baixar o estoque físico
3. WHILE a venda está no status CONFIRMADA, THE Sistema_Loja SHALL manter apenas a Reserva_Temporaria sem baixar o estoque físico
4. WHEN a venda é atualizada para status SEPARADA, THE Sistema_Loja SHALL realizar a Baixa_Estoque chamando o Estoque_Service
5. WHEN a Baixa_Estoque é realizada com sucesso, THE Sistema_Loja SHALL remover a Reserva_Temporaria correspondente
6. WHEN a Baixa_Estoque falha por indisponibilidade, THE Sistema_Loja SHALL retornar erro HTTP 409 e impedir a mudança de status
7. WHILE a venda está no status ENTREGUE, THE Sistema_Loja SHALL manter o estoque já baixado sem alterações
8. WHEN uma venda é cancelada antes do status SEPARADA, THE Sistema_Loja SHALL apenas liberar a Reserva_Temporaria sem alterar estoque físico
9. WHEN uma venda é cancelada após o status SEPARADA, THE Sistema_Loja SHALL devolver a quantidade ao estoque físico chamando o Estoque_Service
10. THE Sistema_Loja SHALL logar todas as operações de Baixa_Estoque com structlog incluindo: venda_id, produto_id, quantidade, timestamp, resultado


### Requirement 13: Enviar Notificações via WhatsApp

**User Story:** Como um cliente, eu quero receber atualizações sobre minha compra via WhatsApp, para que eu saiba o status do pedido sem precisar acessar o site.

#### Acceptance Criteria

1. WHEN uma venda é criada com status PEDIDO, THE Sistema_Loja SHALL enviar mensagem WhatsApp genérica: "Pedido #XXX recebido! Aguardando pagamento"
2. WHEN o pagamento é aprovado e status muda para CONFIRMADA, THE Sistema_Loja SHALL enviar mensagem: "✅ Pagamento aprovado! Preparando pedido"
3. WHEN o status muda para SEPARADA, THE Sistema_Loja SHALL enviar mensagem: "📦 Pedido pronto!"
4. WHEN o status muda para ENTREGUE, THE Sistema_Loja SHALL enviar mensagem: "🎉 Pedido entregue! Obrigado"
5. THE Sistema_Loja SHALL enviar notificações usando a Evolution_API configurada para a empresa
6. WHEN uma notificação falha ao ser enviada, THE Sistema_Loja SHALL logar o erro mas não bloquear o fluxo da venda
7. THE Sistema_Loja SHALL enviar notificações para o telefone fornecido no checkout (normalizado)
8. THE Sistema_Loja SHALL incluir no log de notificação: venda_id, telefone_destino, mensagem, timestamp, resultado
9. WHERE o cliente é Cliente_Convidado sem telefone, THE Sistema_Loja SHALL pular notificações via WhatsApp sem gerar erro
10. THE Sistema_Loja SHALL formatar o número de telefone para o padrão brasileiro (55 + DDD + número) antes de enviar

### Requirement 14: Gerenciar Sessão de Carrinho com Cookie

**User Story:** Como um cliente, eu quero que meu carrinho seja mantido entre sessões, para que eu possa continuar comprando depois.

#### Acceptance Criteria

1. WHEN um cliente acessa a loja pela primeira vez, THE Sistema_Loja SHALL gerar um sessao_id único (UUID v4)
2. THE Sistema_Loja SHALL armazenar o sessao_id em cookie HttpOnly com duração de 7 dias
3. THE Sistema_Loja SHALL usar o sessao_id como chave para armazenar o carrinho no Redis
4. WHEN um cliente retorna ao site, THE Sistema_Loja SHALL recuperar o sessao_id do cookie e carregar o carrinho do Redis
5. WHEN o cookie expira após 7 dias, THE Redis SHALL remover automaticamente o carrinho usando TTL
6. WHEN um cliente finaliza uma compra, THE Sistema_Loja SHALL limpar o carrinho do Redis mas manter o cookie para novas compras
7. THE Sistema_Loja SHALL configurar o cookie com flags: HttpOnly, Secure (em produção), SameSite=Lax
8. WHEN múltiplos checkouts são iniciados com o mesmo sessao_id, THE Sistema_Loja SHALL permitir apenas um checkout ativo por vez
9. THE Sistema_Loja SHALL associar a Reserva_Temporaria ao sessao_id para controle de expiração
10. WHEN um cliente faz logout ou limpa cookies, THE Sistema_Loja SHALL manter o carrinho no Redis até o TTL expirar

### Requirement 15: Implementar Cache de Produtos da Loja

**User Story:** Como um cliente, eu quero que a listagem de produtos carregue rapidamente, para que eu tenha uma experiência fluida na navegação.

#### Acceptance Criteria

1. WHEN um cliente acessa a listagem de produtos, THE Sistema_Loja SHALL consultar o cache Redis primeiro
2. WHEN o cache contém os produtos, THE Sistema_Loja SHALL retornar os dados do cache sem consultar o banco
3. WHEN o cache não contém os produtos, THE Sistema_Loja SHALL consultar o banco e armazenar no cache com TTL de 5 minutos
4. WHEN um produto é atualizado no painel admin, THE Sistema_Loja SHALL invalidar o cache de produtos da empresa
5. THE Sistema_Loja SHALL usar como chave do cache: produtos:{empresa_id}
6. THE Sistema_Loja SHALL armazenar no cache apenas produtos com ativo=TRUE
7. WHEN o TTL de 5 minutos expira, THE Redis SHALL remover automaticamente o cache
8. THE Sistema_Loja SHALL incluir no cache: id, nome, descricao, preco, imagem_url, estoque_disponivel (calculado), categoria
9. WHEN a consulta ao cache falha por erro de conexão, THE Sistema_Loja SHALL consultar o banco diretamente e logar o erro
10. THE Sistema_Loja SHALL logar operações de cache (hit, miss, invalidação) com structlog para monitoramento de performance


### Requirement 16: Validar CPF de Cliente

**User Story:** Como um lojista, eu quero que CPFs sejam validados antes de criar cadastros, para que eu tenha dados confiáveis e evite duplicação.

#### Acceptance Criteria

1. WHERE CPF é fornecido no checkout, THE Sistema_Loja SHALL validar o formato (11 dígitos numéricos)
2. WHEN o CPF possui formato válido, THE Sistema_Loja SHALL validar os dígitos verificadores usando o algoritmo oficial
3. WHEN os dígitos verificadores são inválidos, THE Sistema_Loja SHALL retornar erro HTTP 400 com mensagem "CPF inválido"
4. WHEN o CPF é válido, THE Sistema_Loja SHALL consultar a tabela clientes para verificar se já existe cadastro com o mesmo CPF e empresa_id
5. WHEN já existe um cliente com o CPF fornecido, THE Sistema_Loja SHALL retornar erro HTTP 409 com mensagem "CPF já cadastrado. Faça login para continuar"
6. THE Sistema_Loja SHALL armazenar o CPF sem formatação (apenas dígitos)
7. THE Sistema_Loja SHALL aceitar CPF com formatação (XXX.XXX.XXX-XX) e remover pontos e hífens antes de validar
8. WHERE o cliente é Cliente_Convidado e fornece CPF, THE Sistema_Loja SHALL validar mas não criar cadastro permanente
9. WHEN um Cliente_Convidado fornece CPF já cadastrado, THE Sistema_Loja SHALL permitir a compra mas sugerir login
10. THE Sistema_Loja SHALL logar tentativas de cadastro com CPF duplicado para auditoria

### Requirement 17: Rastrear Pedido com Número e CPF

**User Story:** Como um cliente, eu quero rastrear meu pedido usando apenas o número e meu CPF, para que eu possa consultar o status sem login.

#### Acceptance Criteria

1. WHEN um cliente acessa a página de rastreamento, THE Sistema_Loja SHALL solicitar número do pedido e CPF
2. WHEN os dados são fornecidos, THE Sistema_Loja SHALL consultar a tabela vendas filtrando por numero_pedido, CPF (se fornecido no checkout) e empresa_id
3. WHEN a venda é encontrada, THE Sistema_Loja SHALL exibir: status atual, histórico de status, itens comprados, valor total, tipo de entrega
4. WHEN a venda não é encontrada, THE Sistema_Loja SHALL retornar mensagem "Pedido não encontrado. Verifique os dados"
5. THE Sistema_Loja SHALL gerar número do pedido no formato: {ano}{mes}{sequencial} (exemplo: 202401001)
6. THE Sistema_Loja SHALL exibir o status atual com descrição amigável ao cliente
7. THE Sistema_Loja SHALL exibir o Historico_Status ordenado por timestamp decrescente
8. WHERE o cliente é Cliente_Convidado sem CPF, THE Sistema_Loja SHALL permitir rastreamento apenas com número do pedido e telefone
9. THE Sistema_Loja SHALL aplicar rate limit de 10 consultas por minuto por IP na rota de rastreamento
10. THE Sistema_Loja SHALL logar todas as consultas de rastreamento com: numero_pedido, ip_origem, timestamp, resultado

### Requirement 18: Armazenar Configurações Multi-Tenant de Pagamento

**User Story:** Como um lojista, eu quero configurar minhas credenciais do Mercado Pago de forma isolada, para que cada empresa use sua própria conta.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL armazenar credenciais do Mercado Pago na tabela configuracoes_pagamento com campos: empresa_id, access_token, public_key
2. WHEN o Pagamento_Service cria uma preferência, THE Sistema_Loja SHALL consultar configuracoes_pagamento filtrando por empresa_id
3. WHEN não existem configurações de pagamento para a empresa, THE Sistema_Loja SHALL retornar erro HTTP 500 e logar "Mercado Pago não configurado"
4. THE Sistema_Loja SHALL criptografar o access_token antes de armazenar no banco usando criptografia AES-256
5. THE Sistema_Loja SHALL descriptografar o access_token apenas no momento de uso para chamadas à API do Mercado Pago
6. WHEN as configurações são atualizadas no painel admin, THE Sistema_Loja SHALL validar as credenciais fazendo uma chamada de teste à API do Mercado Pago
7. WHEN a validação das credenciais falha, THE Sistema_Loja SHALL retornar erro HTTP 400 com mensagem "Credenciais inválidas"
8. THE Sistema_Loja SHALL armazenar timestamp de criação e última atualização nas configurações
9. THE Sistema_Loja SHALL logar acesso às configurações de pagamento com: empresa_id, timestamp, usuario_id (admin)
10. WHERE múltiplas empresas usam o sistema, THE Sistema_Loja SHALL garantir isolamento total de credenciais via empresa_id

### Requirement 19: Implementar Job de Limpeza de Reservas

**User Story:** Como um desenvolvedor do sistema, eu quero um processo automatizado que limpe reservas expiradas, para que o estoque não fique bloqueado por reservas antigas.

#### Acceptance Criteria

1. THE Job_Limpeza SHALL executar a cada 1 minuto verificando reservas expiradas
2. WHEN o Job_Limpeza é executado, THE Sistema_Loja SHALL consultar a tabela reservas_temporarias filtrando por expira_em menor que timestamp atual
3. WHEN reservas expiradas são encontradas, THE Job_Limpeza SHALL remover os registros da tabela em lote
4. THE Job_Limpeza SHALL logar cada execução com: timestamp, quantidade_removida, tempo_execucao
5. WHEN a remoção de reservas falha, THE Job_Limpeza SHALL logar o erro e continuar nas próximas execuções
6. THE Job_Limpeza SHALL usar transação de banco para garantir atomicidade na remoção
7. THE Job_Limpeza SHALL processar no máximo 1000 reservas por execução para evitar sobrecarga
8. WHEN existem mais de 1000 reservas expiradas, THE Job_Limpeza SHALL processar o restante na próxima execução
9. THE Sistema_Loja SHALL implementar o Job_Limpeza usando scheduler (APScheduler ou Celery)
10. THE Job_Limpeza SHALL incluir no log: job_id, empresa_id (se aplicável), quantidade_reservas_removidas, timestamp_inicio, timestamp_fim


### Requirement 20: Controlar Concorrência com Redis Lock

**User Story:** Como um desenvolvedor do sistema, eu quero evitar race conditions em operações de estoque, para que não ocorram reservas duplicadas ou vendas de produtos sem estoque.

#### Acceptance Criteria

1. WHEN uma operação de reserva de estoque é iniciada, THE Sistema_Loja SHALL adquirir um Redis_Lock usando chave: lock:estoque:{produto_id}:{variante_id}
2. THE Redis_Lock SHALL ter timeout de 5 segundos para evitar deadlocks
3. WHEN o Redis_Lock não pode ser adquirido após 3 tentativas, THE Sistema_Loja SHALL retornar erro HTTP 503 com mensagem "Sistema temporariamente indisponível. Tente novamente"
4. WHEN o Redis_Lock é adquirido com sucesso, THE Sistema_Loja SHALL executar a operação de reserva e liberar o lock imediatamente após
5. THE Sistema_Loja SHALL garantir que o Redis_Lock seja liberado mesmo em caso de exceção usando bloco try-finally
6. WHEN múltiplas requisições tentam reservar o mesmo produto simultaneamente, THE Redis_Lock SHALL garantir processamento sequencial
7. THE Sistema_Loja SHALL usar Redis_Lock apenas para operações críticas: criar reserva, baixar estoque, cancelar reserva
8. THE Sistema_Loja SHALL logar tentativas de aquisição de lock com: produto_id, variante_id, timestamp, resultado, tempo_espera
9. WHEN o Redis está indisponível, THE Sistema_Loja SHALL retornar erro HTTP 503 e logar a falha de infraestrutura
10. THE Sistema_Loja SHALL implementar Redis_Lock usando biblioteca redis-py com método setnx (set if not exists)

### Requirement 21: Registrar Logs Estruturados

**User Story:** Como um desenvolvedor e lojista, eu quero logs estruturados de todas as operações críticas, para que eu possa debugar problemas e auditar transações.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL usar structlog para todos os logs com formato JSON
2. WHEN uma operação de carrinho é executada, THE Sistema_Loja SHALL logar: acao, sessao_id, produto_id, quantidade, timestamp, resultado
3. WHEN uma operação de checkout é iniciada, THE Sistema_Loja SHALL logar: checkout_iniciado, sessao_id, cliente_id, valor_total, tipo_entrega, forma_pagamento, timestamp
4. WHEN um pagamento é processado, THE Sistema_Loja SHALL logar: payment_id, venda_id, valor, status, timestamp, empresa_id
5. WHEN um webhook é recebido, THE Sistema_Loja SHALL logar: evento, payment_id, venda_id, timestamp, processado (boolean), erro (se aplicável)
6. WHEN uma mudança de status ocorre, THE Sistema_Loja SHALL logar: venda_id, status_anterior, status_novo, usuario_id, timestamp, origem
7. WHEN uma operação de estoque falha, THE Sistema_Loja SHALL logar: operacao, produto_id, quantidade_solicitada, estoque_disponivel, erro, timestamp
8. THE Sistema_Loja SHALL incluir em todos os logs: request_id, empresa_id, timestamp_utc
9. WHEN um erro HTTP 500 ocorre, THE Sistema_Loja SHALL logar stack trace completo com contexto da requisição
10. THE Sistema_Loja SHALL configurar níveis de log: DEBUG (desenvolvimento), INFO (produção), ERROR (sempre)

### Requirement 22: Validar Limites de Quantidade no Carrinho

**User Story:** Como um desenvolvedor do sistema, eu quero limites de quantidade para proteger a performance, para que carrinho excessivamente grandes não sobrecarreguem o sistema.

#### Acceptance Criteria

1. WHEN um cliente adiciona um produto ao carrinho, THE Carrinho_Service SHALL validar que a quantidade solicitada não excede 100 unidades
2. WHEN a quantidade excede 100 unidades, THE Carrinho_Service SHALL retornar erro HTTP 400 com mensagem "Quantidade máxima por produto: 100 unidades"
3. WHEN um cliente tenta adicionar mais produtos ao carrinho, THE Carrinho_Service SHALL validar que o total de produtos diferentes não excede 50
4. WHEN o limite de 50 produtos diferentes é atingido, THE Carrinho_Service SHALL retornar erro HTTP 400 com mensagem "Limite de 50 produtos diferentes atingido"
5. THE Carrinho_Service SHALL calcular o total de produtos diferentes somando as chaves do hash Redis do carrinho
6. WHEN um cliente atualiza a quantidade de um item no carrinho, THE Carrinho_Service SHALL aplicar a mesma validação de 100 unidades
7. THE Sistema_Loja SHALL permitir configurar esses limites na tabela configuracoes_loja: max_unidades_por_produto, max_produtos_diferentes
8. WHEN os limites não estão configurados, THE Sistema_Loja SHALL usar valores padrão: 100 unidades e 50 produtos
9. THE Sistema_Loja SHALL logar tentativas de exceder limites com: sessao_id, produto_id, quantidade_solicitada, limite, timestamp
10. THE Carrinho_Service SHALL validar limites antes de consultar estoque para otimizar performance

### Requirement 23: Configurar Taxa de Entrega Global e por Bairro

**User Story:** Como um lojista, eu quero configurar taxa de entrega padrão e exceções por bairro, para que eu possa gerenciar custos logísticos de forma flexível.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL armazenar taxa_entrega_padrao na tabela configuracoes_loja com tipo DECIMAL(10,2)
2. THE Sistema_Loja SHALL armazenar exceções na tabela faixas_entrega com campos: empresa_id, bairro (VARCHAR), taxa (DECIMAL)
3. WHEN um bairro possui configuração específica, THE Sistema_Loja SHALL usar a taxa da tabela faixas_entrega com prioridade sobre a padrão
4. WHEN o lojista cadastra uma exceção de bairro, THE Sistema_Loja SHALL normalizar o nome do bairro removendo acentos e convertendo para maiúsculas
5. THE Sistema_Loja SHALL comparar bairros de forma case-insensitive durante consultas
6. WHEN o lojista atualiza a taxa_entrega_padrao, THE Sistema_Loja SHALL aplicar imediatamente para novos checkouts
7. WHEN uma exceção de bairro é removida, THE Sistema_Loja SHALL usar a taxa_entrega_padrao automaticamente para aquele bairro
8. THE Sistema_Loja SHALL permitir taxa zero para bairros específicos (frete grátis pontual)
9. THE Sistema_Loja SHALL validar que taxas sejam valores positivos ou zero durante cadastro
10. WHEN o lojista tenta cadastrar exceção duplicada para o mesmo bairro, THE Sistema_Loja SHALL retornar erro HTTP 409


### Requirement 24: Permitir Troca de Forma de Pagamento

**User Story:** Como um cliente, eu quero poder trocar a forma de pagamento antes de pagar, para que eu possa escolher a melhor opção para mim.

#### Acceptance Criteria

1. WHILE a venda está no status PEDIDO, THE Sistema_Loja SHALL permitir que o cliente troque a forma de pagamento ilimitadamente
2. WHILE a venda está no status PENDENTE_PAGAMENTO, THE Sistema_Loja SHALL permitir que o cliente troque a forma de pagamento ilimitadamente
3. WHEN a forma de pagamento é trocada de online para offline, THE Sistema_Loja SHALL cancelar a preferência do Mercado Pago
4. WHEN a forma de pagamento é trocada de offline para online, THE Sistema_Loja SHALL criar uma nova preferência no Mercado Pago
5. WHEN a forma de pagamento é trocada de Fiado para outra, THE Sistema_Loja SHALL liberar o crédito bloqueado
6. WHEN a forma de pagamento é trocada para Fiado, THE Sistema_Loja SHALL validar novamente permite_fiado_online e crédito disponível
7. WHEN a forma de pagamento é trocada em pagamento misto, THE Sistema_Loja SHALL recalcular valor de crédito e valor online
8. THE Sistema_Loja SHALL registrar cada troca de forma de pagamento no Historico_Status com observação incluindo forma anterior e nova
9. WHEN o status muda para CONFIRMADA, THE Sistema_Loja SHALL bloquear qualquer troca de forma de pagamento
10. THE Sistema_Loja SHALL manter a Reserva_Temporaria ativa durante todas as trocas de forma de pagamento

### Requirement 25: Consultar API ViaCEP para Endereços

**User Story:** Como um cliente, eu quero que meu endereço seja preenchido automaticamente ao digitar o CEP, para que eu tenha uma experiência rápida no checkout.

#### Acceptance Criteria

1. WHEN um cliente fornece um CEP, THE Sistema_Loja SHALL consultar a API pública ViaCEP no endpoint https://viacep.com.br/ws/{cep}/json/
2. WHEN a consulta ao ViaCEP retorna sucesso (HTTP 200), THE Sistema_Loja SHALL extrair os campos: logradouro, bairro, localidade, uf
3. WHEN o ViaCEP retorna o campo "erro": true, THE Sistema_Loja SHALL retornar mensagem "CEP não encontrado"
4. WHEN a consulta ao ViaCEP falha por timeout (mais de 5 segundos), THE Sistema_Loja SHALL permitir que o cliente prossiga informando endereço manualmente
5. WHEN a consulta ao ViaCEP falha por erro de rede, THE Sistema_Loja SHALL logar o erro e usar taxa_entrega_padrao
6. THE Sistema_Loja SHALL validar formato do CEP (8 dígitos) antes de consultar o ViaCEP
7. THE Sistema_Loja SHALL aceitar CEP com formatação (XXXXX-XXX) e remover o hífen antes de consultar
8. WHEN o ViaCEP está indisponível, THE Sistema_Loja SHALL exibir mensagem "Serviço de CEP temporariamente indisponível. Preencha o endereço manualmente"
9. THE Sistema_Loja SHALL armazenar o bairro retornado pelo ViaCEP para cálculo da taxa de entrega
10. THE Sistema_Loja SHALL implementar retry de até 2 tentativas com intervalo de 1 segundo em caso de falha de rede

### Requirement 26: Integrar com Evolution API para WhatsApp

**User Story:** Como um lojista, eu quero usar minha instância do Evolution API para enviar notificações, para que eu possa me comunicar com clientes via WhatsApp.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL armazenar configurações do Evolution API na tabela configuracoes_whatsapp com campos: empresa_id, api_url, api_key, instancia
2. WHEN uma notificação precisa ser enviada, THE Sistema_Loja SHALL consultar configuracoes_whatsapp filtrando por empresa_id
3. WHEN não existem configurações de WhatsApp, THE Sistema_Loja SHALL logar aviso e pular o envio de notificação sem gerar erro
4. WHEN as configurações existem, THE Sistema_Loja SHALL fazer POST para {api_url}/message/sendText com headers: apikey: {api_key}
5. THE Sistema_Loja SHALL enviar no body: number (telefone), textMessage (mensagem), instance (instância)
6. WHEN o Evolution API retorna sucesso (HTTP 200 ou 201), THE Sistema_Loja SHALL logar o envio com message_id retornado
7. WHEN o Evolution API retorna erro (4xx ou 5xx), THE Sistema_Loja SHALL logar o erro mas não bloquear o fluxo da venda
8. THE Sistema_Loja SHALL implementar timeout de 10 segundos para chamadas ao Evolution API
9. THE Sistema_Loja SHALL formatar o número de telefone no padrão brasileiro: 55 + DDD (2 dígitos) + número (8 ou 9 dígitos) sem espaços ou caracteres especiais
10. THE Sistema_Loja SHALL logar todas as tentativas de envio com: venda_id, telefone_destino, mensagem, timestamp, http_status, erro (se aplicável)

### Requirement 27: Implementar Histórico Completo de Status

**User Story:** Como um lojista, eu quero visualizar todo o histórico de mudanças de status de uma venda, para que eu possa auditar o processo e identificar problemas.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL armazenar histórico na tabela historico_status_venda com campos: venda_id, status_anterior, status_novo, timestamp, usuario_id, origem, observacao
2. WHEN qualquer mudança de status ocorre, THE Sistema_Loja SHALL criar uma entrada no histórico ANTES de atualizar o status da venda
3. THE Sistema_Loja SHALL registrar a origem da mudança de status usando enum: WEBHOOK, MANUAL_LOJISTA, MANUAL_CLIENTE, SISTEMA_TIMEOUT
4. WHERE a mudança é manual, THE Sistema_Loja SHALL armazenar o usuario_id do responsável
5. WHERE a mudança é via webhook, THE Sistema_Loja SHALL armazenar payment_id na observação
6. WHERE a mudança é por timeout, THE Sistema_Loja SHALL armazenar o motivo específico na observação (ex: "Timeout 48h sem separação")
7. WHEN o lojista visualiza uma venda, THE Sistema_Loja SHALL exibir o histórico ordenado por timestamp decrescente
8. THE Sistema_Loja SHALL exibir no histórico: timestamp formatado, status anterior → status novo, origem, responsável (se aplicável), observação
9. THE Sistema_Loja SHALL usar transação de banco para garantir que histórico e status sejam atualizados atomicamente
10. THE Sistema_Loja SHALL permitir filtrar histórico por: venda_id, período, status, origem


### Requirement 28: Processar Reembolsos e Devoluções de Estoque

**User Story:** Como um lojista, eu quero que reembolsos devolvam automaticamente estoque e crédito, para que o inventário e saldo do cliente sejam corrigidos.

#### Acceptance Criteria

1. WHEN o webhook recebe evento payment.refunded, THE Sistema_Loja SHALL atualizar a venda para status REEMBOLSADA
2. WHEN o status muda para REEMBOLSADA após status SEPARADA, THE Sistema_Loja SHALL devolver as quantidades ao estoque físico chamando o Estoque_Service
3. WHEN o status muda para REEMBOLSADA antes de status SEPARADA, THE Sistema_Loja SHALL apenas liberar a Reserva_Temporaria sem alterar estoque físico
4. WHERE a venda usou crédito (fiado ou misto), THE Sistema_Loja SHALL devolver o valor de crédito usado ao saldo do cliente
5. WHEN a devolução de crédito é processada, THE Sistema_Loja SHALL criar transação de crédito com tipo DEVOLUCAO_REEMBOLSO
6. THE Sistema_Loja SHALL registrar no Historico_Status a mudança para REEMBOLSADA com origem WEBHOOK e observação incluindo payment_id
7. WHEN a devolução de estoque falha, THE Sistema_Loja SHALL logar erro crítico com detalhes mas não bloquear a mudança de status
8. WHEN a devolução de crédito falha, THE Sistema_Loja SHALL logar erro crítico e criar alerta para processamento manual
9. THE Sistema_Loja SHALL enviar notificação via WhatsApp: "Reembolso processado para o pedido #XXX"
10. THE Sistema_Loja SHALL logar operação de reembolso com: venda_id, valor_reembolsado, estoque_devolvido, credito_devolvido, timestamp

### Requirement 29: Validar Bloqueio de Cliente para Fiado

**User Story:** Como um lojista, eu quero que clientes bloqueados não possam usar crédito online, para que eu tenha controle sobre inadimplência.

#### Acceptance Criteria

1. WHEN a forma de pagamento Fiado é selecionada, THE Checkout_Service SHALL validar que o campo cliente.bloqueado é FALSE
2. WHEN cliente.bloqueado é TRUE, THE Checkout_Service SHALL retornar erro HTTP 403 com mensagem "Cliente bloqueado. Entre em contato com a loja"
3. WHEN a forma de pagamento Fiado é selecionada, THE Checkout_Service SHALL validar que o campo cliente.ativo é TRUE
4. WHEN cliente.ativo é FALSE, THE Checkout_Service SHALL retornar erro HTTP 403 com mensagem "Cliente inativo"
5. WHEN pagamento misto é selecionado, THE Checkout_Service SHALL aplicar as mesmas validações de bloqueio e ativo
6. WHERE o pagamento é 100% online (sem uso de crédito), THE Checkout_Service SHALL permitir compra mesmo com cliente bloqueado
7. THE Checkout_Service SHALL validar bloqueio e status antes de validar crédito disponível
8. WHEN o cliente é bloqueado durante uma compra em andamento (status PEDIDO), THE Sistema_Loja SHALL permitir concluir apenas se pagamento for 100% online
9. THE Sistema_Loja SHALL logar tentativas de uso de crédito por clientes bloqueados com: cliente_id, venda_id, valor_tentado, timestamp
10. THE Checkout_Service SHALL exibir mensagem amigável ao cliente bloqueado sugerindo contato com a loja

### Requirement 30: Implementar Isolamento Multi-Tenant Completo

**User Story:** Como um provedor do sistema, eu quero garantir isolamento total entre empresas, para que dados e configurações não vazem entre tenants.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL incluir filtro por empresa_id em TODAS as consultas ao banco de dados
2. THE Sistema_Loja SHALL validar que o empresa_id da requisição corresponde ao empresa_id extraído do token JWT ou slug da URL
3. WHEN uma requisição tenta acessar dados de outra empresa, THE Sistema_Loja SHALL retornar erro HTTP 403 Forbidden
4. THE Sistema_Loja SHALL usar o empresa_slug na URL para identificar o tenant: /loja/{empresa_slug}/produtos
5. WHEN o empresa_slug na URL não corresponde a nenhuma empresa ativa, THE Sistema_Loja SHALL retornar erro HTTP 404
6. THE Sistema_Loja SHALL armazenar empresa_id em todas as tabelas: vendas, reservas_temporarias, configuracoes_loja, configuracoes_pagamento, faixas_entrega
7. THE Sistema_Loja SHALL criar índices compostos incluindo empresa_id para otimizar queries multi-tenant
8. WHEN cache é usado, THE Sistema_Loja SHALL incluir empresa_id na chave do cache para evitar vazamento entre tenants
9. WHEN webhooks do Mercado Pago chegam, THE Sistema_Loja SHALL validar que o payment_id corresponde a uma venda do tenant correto
10. THE Sistema_Loja SHALL logar tentativas de acesso cross-tenant com: ip_origem, usuario_id, empresa_id_solicitado, empresa_id_autorizado, timestamp

### Requirement 31: Gerenciar Produto com Variantes no Carrinho

**User Story:** Como um cliente, eu quero adicionar variantes específicas de produtos ao carrinho, para que eu possa escolher tamanho, cor ou outras opções.

#### Acceptance Criteria

1. WHEN um produto possui variantes, THE Carrinho_Service SHALL exigir que o cliente selecione uma variante antes de adicionar ao carrinho
2. THE Carrinho_Service SHALL armazenar no carrinho: produto_id, variante_id (se aplicável), quantidade
3. WHEN uma Reserva_Temporaria é criada para produto com variante, THE Sistema_Loja SHALL reservar estoque filtrando por produto_id E variante_id
4. WHEN o estoque é consultado, THE Estoque_Service SHALL calcular Estoque_Disponivel considerando variante_id
5. WHEN uma variante específica está sem estoque mas outras variantes têm estoque, THE Carrinho_Service SHALL informar isso ao cliente
6. THE Carrinho_Service SHALL exibir no carrinho: nome do produto, atributos da variante (ex: Tamanho M, Cor Azul), preço, quantidade
7. WHEN o checkout é processado, THE Sistema_Loja SHALL baixar estoque da variante específica selecionada
8. THE Redis_Lock SHALL usar chave incluindo variante: lock:estoque:{produto_id}:{variante_id}
9. WHERE o produto não possui variantes, THE Sistema_Loja SHALL usar variante_id como NULL em todas as operações
10. THE Sistema_Loja SHALL permitir que o mesmo produto com variantes diferentes sejam itens separados no carrinho


### Requirement 32: Implementar Idempotência em Webhooks

**User Story:** Como um desenvolvedor do sistema, eu quero garantir que webhooks duplicados não processem a mesma transação duas vezes, para que não ocorram inconsistências financeiras ou de estoque.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL armazenar payment_id processados na tabela webhook_processados com constraint UNIQUE
2. WHEN um webhook chega, THE Pagamento_Service SHALL tentar inserir o payment_id na tabela webhook_processados
3. WHEN a inserção falha por violação de constraint UNIQUE, THE Pagamento_Service SHALL retornar HTTP 200 imediatamente sem processar
4. WHEN a inserção é bem-sucedida, THE Pagamento_Service SHALL prosseguir com o processamento do evento
5. THE Pagamento_Service SHALL usar transação de banco para garantir atomicidade entre inserção em webhook_processados e atualização da venda
6. THE Sistema_Loja SHALL armazenar na tabela webhook_processados: payment_id, evento, venda_id, timestamp, empresa_id
7. WHEN o Mercado Pago reenvia o mesmo webhook múltiplas vezes, THE Sistema_Loja SHALL processar apenas a primeira ocorrência
8. THE Sistema_Loja SHALL logar webhooks duplicados com nível INFO: "Webhook já processado: {payment_id}"
9. THE Sistema_Loja SHALL manter registros em webhook_processados por 90 dias para auditoria
10. THE Sistema_Loja SHALL implementar job de limpeza que remove registros de webhook_processados com mais de 90 dias

### Requirement 33: Cancelar Venda Manualmente

**User Story:** Como um lojista, eu quero cancelar vendas manualmente quando necessário, para que eu possa lidar com situações excepcionais.

#### Acceptance Criteria

1. WHERE o status da venda é diferente de FINALIZADA, THE Sistema_Loja SHALL permitir que o lojista cancele manualmente
2. WHEN o lojista cancela uma venda, THE Sistema_Loja SHALL solicitar motivo do cancelamento (obrigatório)
3. WHEN a venda é cancelada manualmente, THE Sistema_Loja SHALL atualizar status para CANCELADA e registrar no Historico_Status com origem MANUAL_LOJISTA
4. WHEN a venda cancelada estava no status SEPARADA ou posterior, THE Sistema_Loja SHALL devolver as quantidades ao estoque físico
5. WHEN a venda cancelada usou crédito, THE Sistema_Loja SHALL devolver o valor de crédito ao saldo do cliente
6. WHEN a venda cancelada tinha pagamento online aprovado, THE Sistema_Loja SHALL criar alerta para o lojista processar reembolso manual no Mercado Pago
7. WHEN a venda é cancelada antes do status SEPARADA, THE Sistema_Loja SHALL apenas liberar a Reserva_Temporaria
8. THE Sistema_Loja SHALL enviar notificação via WhatsApp: "Pedido #XXX cancelado. Motivo: {motivo}"
9. THE Sistema_Loja SHALL logar cancelamentos manuais com: venda_id, usuario_id, motivo, status_anterior, timestamp
10. THE Sistema_Loja SHALL armazenar o motivo do cancelamento no campo observacao do Historico_Status

### Requirement 34: Cancelar Venda pelo Cliente

**User Story:** Como um cliente, eu quero cancelar minha compra se ainda não foi paga, para que eu possa desistir da compra sem precisar entrar em contato.

#### Acceptance Criteria

1. WHERE o status da venda é PEDIDO, THE Sistema_Loja SHALL exibir botão "Cancelar Pedido" para o cliente
2. WHERE o status da venda é PENDENTE_PAGAMENTO, THE Sistema_Loja SHALL exibir botão "Cancelar Pedido" para o cliente
3. WHEN o cliente clica em cancelar, THE Sistema_Loja SHALL solicitar confirmação: "Tem certeza que deseja cancelar este pedido?"
4. WHEN o cliente confirma o cancelamento, THE Sistema_Loja SHALL atualizar status para CANCELADA e registrar no Historico_Status com origem MANUAL_CLIENTE
5. WHEN a venda é cancelada pelo cliente, THE Sistema_Loja SHALL liberar a Reserva_Temporaria imediatamente
6. WHEN a venda usou crédito (fiado ou misto), THE Sistema_Loja SHALL devolver o valor de crédito ao saldo do cliente
7. WHERE o status é CONFIRMADA ou posterior, THE Sistema_Loja SHALL ocultar o botão de cancelamento e exibir mensagem "Entre em contato com a loja"
8. THE Sistema_Loja SHALL enviar notificação via WhatsApp: "Seu pedido #XXX foi cancelado"
9. THE Sistema_Loja SHALL logar cancelamentos pelo cliente com: venda_id, cliente_id, sessao_id, status_anterior, timestamp
10. THE Sistema_Loja SHALL aplicar rate limit de 5 cancelamentos por cliente por hora para evitar abuso

### Requirement 35: Exibir Resumo do Pedido antes da Finalização

**User Story:** Como um cliente, eu quero ver um resumo completo do meu pedido antes de finalizar, para que eu possa conferir todos os detalhes.

#### Acceptance Criteria

1. WHEN o cliente acessa a página de resumo, THE Sistema_Loja SHALL exibir todos os itens do carrinho com: imagem, nome, variante (se aplicável), quantidade, preço unitário, subtotal
2. THE Sistema_Loja SHALL calcular e exibir: subtotal dos produtos, taxa de entrega, valor de crédito usado (se misto), valor total
3. THE Sistema_Loja SHALL exibir a forma de pagamento selecionada com descrição clara
4. THE Sistema_Loja SHALL exibir o tipo de entrega (RETIRADA ou DELIVERY) e endereço completo (se DELIVERY)
5. WHERE a forma de pagamento é Dinheiro com troco, THE Sistema_Loja SHALL exibir: "Troco para R$ {valor}"
6. WHERE a forma de pagamento é mista, THE Sistema_Loja SHALL exibir breakdown: "Crédito: R$ {valor_credito} + Online: R$ {valor_online} = Total: R$ {valor_total}"
7. THE Sistema_Loja SHALL exibir estimativa de entrega ou mensagem de disponibilidade para retirada
8. THE Sistema_Loja SHALL exibir botão "Confirmar Pedido" destacado e botão "Voltar e Editar" secundário
9. WHEN o cliente clica em "Confirmar Pedido", THE Sistema_Loja SHALL validar estoque novamente antes de prosseguir
10. THE Sistema_Loja SHALL exibir número de telefone da loja para dúvidas no rodapé do resumo


### Requirement 36: Implementar Normalização de Dados de Entrada

**User Story:** Como um desenvolvedor do sistema, eu quero normalizar dados de entrada automaticamente, para que o sistema aceite diferentes formatos e armazene de forma consistente.

#### Acceptance Criteria

1. WHEN um CPF é fornecido, THE Sistema_Loja SHALL remover pontos, hífens e espaços antes de armazenar
2. WHEN um telefone é fornecido, THE Sistema_Loja SHALL remover parênteses, hífens, espaços e caracteres especiais
3. THE Sistema_Loja SHALL aceitar telefone nos formatos: (11) 98888-7777, 11988887777, 11 98888-7777, +55 11 98888-7777
4. THE Sistema_Loja SHALL normalizar telefone para o formato: 11988887777 (apenas dígitos)
5. WHEN um CEP é fornecido, THE Sistema_Loja SHALL aceitar com ou sem hífen: 12345-678 ou 12345678
6. THE Sistema_Loja SHALL normalizar CEP para 8 dígitos sem hífen antes de armazenar
7. WHEN um nome de bairro é armazenado, THE Sistema_Loja SHALL converter para maiúsculas e remover acentos
8. THE Sistema_Loja SHALL comparar bairros usando versão normalizada (maiúsculas, sem acentos)
9. WHEN um email é fornecido, THE Sistema_Loja SHALL converter para minúsculas antes de armazenar
10. THE Sistema_Loja SHALL aplicar trim (remover espaços início/fim) em todos os campos de texto antes de validar

### Requirement 37: Validar Segurança do Cookie de Sessão

**User Story:** Como um desenvolvedor do sistema, eu quero que cookies de sessão sejam seguros, para que sessões não sejam roubadas ou manipuladas.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL configurar cookie de sessão com flag HttpOnly para prevenir acesso via JavaScript
2. WHERE o ambiente é produção (HTTPS), THE Sistema_Loja SHALL configurar cookie com flag Secure
3. THE Sistema_Loja SHALL configurar cookie com SameSite=Lax para prevenir CSRF
4. THE Sistema_Loja SHALL gerar sessao_id usando UUID v4 (128 bits de entropia)
5. THE Sistema_Loja SHALL definir Max-Age do cookie como 604800 segundos (7 dias)
6. THE Sistema_Loja SHALL nomear o cookie como "loja_session" ou similar (não usar "session" genérico)
7. THE Sistema_Loja SHALL configurar Path do cookie como /loja/{empresa_slug} para isolamento entre tenants
8. WHEN um cookie com sessao_id inválido é recebido, THE Sistema_Loja SHALL gerar novo sessao_id
9. THE Sistema_Loja SHALL validar que sessao_id é UUID válido antes de usar como chave Redis
10. THE Sistema_Loja SHALL logar tentativas de acesso com sessao_id malformado com nível WARNING

### Requirement 38: Implementar Rate Limiting em Endpoints Públicos

**User Story:** Como um desenvolvedor do sistema, eu quero limitar taxa de requisições em endpoints públicos, para que o sistema não sofra abuso ou ataques de força bruta.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL aplicar rate limit de 60 requisições por minuto por IP na rota de listagem de produtos
2. THE Sistema_Loja SHALL aplicar rate limit de 30 requisições por minuto por IP nas rotas de carrinho
3. THE Sistema_Loja SHALL aplicar rate limit de 10 requisições por minuto por IP na rota de checkout
4. THE Sistema_Loja SHALL aplicar rate limit de 10 requisições por minuto por IP na rota de rastreamento
5. THE Sistema_Loja SHALL aplicar rate limit de 5 requisições por minuto por IP na rota de criação de conta
6. WHEN o rate limit é excedido, THE Sistema_Loja SHALL retornar HTTP 429 Too Many Requests com header Retry-After
7. THE Sistema_Loja SHALL usar Redis para armazenar contadores de rate limit com TTL de 1 minuto
8. THE Sistema_Loja SHALL incluir headers em todas as respostas: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
9. THE Sistema_Loja SHALL logar violações de rate limit com: ip_origem, endpoint, timestamp, quantidade_requisicoes
10. THE Sistema_Loja SHALL permitir configurar limites por tenant na tabela configuracoes_loja

### Requirement 39: Validar Transações de Banco de Dados

**User Story:** Como um desenvolvedor do sistema, eu quero que operações críticas usem transações, para que dados permaneçam consistentes mesmo em caso de falhas.

#### Acceptance Criteria

1. WHEN uma venda é criada, THE Sistema_Loja SHALL usar transação incluindo: inserção da venda, criação de itens, criação de reserva, bloqueio de crédito (se aplicável)
2. WHEN a Baixa_Estoque é realizada, THE Sistema_Loja SHALL usar transação incluindo: atualização de status para SEPARADA, baixa de estoque, remoção de reserva
3. WHEN um webhook é processado, THE Sistema_Loja SHALL usar transação incluindo: inserção em webhook_processados, atualização de status, criação de histórico
4. WHEN uma venda é cancelada, THE Sistema_Loja SHALL usar transação incluindo: atualização de status, devolução de estoque (se aplicável), devolução de crédito (se aplicável), criação de histórico
5. WHEN qualquer operação da transação falha, THE Sistema_Loja SHALL fazer rollback completo e retornar erro ao cliente
6. THE Sistema_Loja SHALL usar isolation level READ_COMMITTED para evitar dirty reads
7. THE Sistema_Loja SHALL logar início e fim de transações críticas com: transacao_id, operacao, timestamp, resultado
8. WHEN ocorre deadlock em transação, THE Sistema_Loja SHALL fazer retry automático até 3 vezes com backoff exponencial
9. WHEN transação falha após 3 retries, THE Sistema_Loja SHALL logar erro crítico e retornar HTTP 500
10. THE Sistema_Loja SHALL garantir que transações não durem mais de 5 segundos para evitar lock de tabelas


### Requirement 40: Implementar Monitoramento de Saúde do Sistema

**User Story:** Como um DevOps, eu quero endpoints de health check, para que eu possa monitorar a disponibilidade dos serviços críticos.

#### Acceptance Criteria

1. THE Sistema_Loja SHALL expor endpoint GET /health que retorna status de saúde do serviço
2. THE Sistema_Loja SHALL verificar conexão com PostgreSQL e retornar status (healthy/unhealthy)
3. THE Sistema_Loja SHALL verificar conexão com Redis e retornar status (healthy/unhealthy)
4. THE Sistema_Loja SHALL verificar disponibilidade do Estoque_Service e retornar status (healthy/unhealthy/degraded)
5. WHEN todos os componentes estão saudáveis, THE Sistema_Loja SHALL retornar HTTP 200 com JSON: {"status": "healthy", "components": {...}}
6. WHEN algum componente crítico falha, THE Sistema_Loja SHALL retornar HTTP 503 com JSON: {"status": "unhealthy", "components": {...}}
7. THE Sistema_Loja SHALL incluir tempo de resposta de cada componente no health check
8. THE Sistema_Loja SHALL implementar timeout de 2 segundos para cada verificação de componente
9. THE Sistema_Loja SHALL expor endpoint GET /ready que retorna 200 apenas quando sistema está pronto para receber tráfego
10. THE Sistema_Loja SHALL incluir versão do serviço e timestamp no response do health check

---

## Summary

Este documento especifica 40 requisitos funcionais para o MVP da Loja Online, cobrindo:

- **Gestão de Carrinho**: Adição de produtos, validação de estoque, reservas temporárias (Req 1-2)
- **Processo de Checkout**: Validação final, autenticação flexível (Req 3-4)
- **Pagamentos**: Online (Mercado Pago), offline (Dinheiro, Fiado), misto (Req 5-8)
- **Logística**: Taxa de entrega por bairro, integração ViaCEP (Req 9, 25)
- **Ciclo de Vida da Venda**: Status completos, timeouts automáticos, histórico de auditoria (Req 10-11, 27)
- **Estoque**: Baixa no momento correto, controle de concorrência, reservas (Req 12, 20, 31)
- **Notificações**: WhatsApp via Evolution API (Req 13, 26)
- **Experiência do Cliente**: Sessão persistente, rastreamento, resumo de pedido (Req 14, 17, 35)
- **Segurança**: Validação de CPF, multi-tenant, cookies seguros, rate limiting (Req 16, 30, 37-38)
- **Configurações**: Pagamento, entrega, limites (Req 18, 22-23)
- **Confiabilidade**: Idempotência de webhooks, transações de banco, logs estruturados (Req 21, 32, 39)
- **Operações**: Cancelamentos, reembolsos, normalização de dados (Req 28, 33-34, 36)
- **Infraestrutura**: Cache, job de limpeza, health checks (Req 15, 19, 40)

Todos os requisitos seguem padrões EARS e INCOSE, garantindo clareza, testabilidade e rastreabilidade para a implementação do MVP.
