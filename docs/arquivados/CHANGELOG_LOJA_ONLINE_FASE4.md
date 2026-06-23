# Changelog - Loja Online MVP - FASE 4: Complete Checkout

## Data: 2026-06-11

## 📋 Resumo
Implementação completa do checkout da loja online com todas as regras de negócio definidas, incluindo:
- Validação de clientes convidados
- Cálculo de taxa de entrega
- Pagamento misto (fiado + online)
- Integração com Mercado Pago
- Notificações WhatsApp
- Histórico de status
- Cache de produtos
- Reservas de estoque no checkout (5min)

---

## 🆕 Novos Serviços Criados

### 1. `services/historico_status_service.py`
**Propósito**: Gerenciar histórico de mudanças de status de vendas para auditoria e rastreamento.

**Métodos**:
- `registrar_mudanca()`: Registra mudança de status no banco
- `listar_por_venda()`: Lista histórico de uma venda (ordenado por data)
- `obter_ultimo_status()`: Obtém último registro de status

**Uso**: Chamado toda vez que o status de uma venda muda (checkout, pagamento confirmado, separada, etc).

---

### 2. `services/cache_service.py`
**Propósito**: Cache de produtos em Redis com TTL de 5 minutos para melhorar performance.

**Métodos**:
- `obter_produto()`: Obtém produto do cache ou busca no serviço
- `invalidar_produto()`: Remove produto do cache
- `limpar_cache_empresa()`: Limpa todo cache de uma empresa

**Características**:
- TTL: 5 minutos
- Cache key pattern: `loja:produto:{produto_id}` ou `loja:produto:{produto_id}:variante:{variante_id}`
- Fallback: Se Redis falhar, busca direto no serviço

---

### 3. `services/notificacao_service.py`
**Propósito**: Envio de notificações via WhatsApp usando Evolution API.

**Métodos**:
- `enviar_confirmacao_pedido()`: Notifica criação do pedido
- `enviar_pagamento_confirmado()`: Notifica aprovação do pagamento
- `enviar_pedido_separado()`: Notifica que pedido está pronto
- `enviar_pedido_entregue()`: Notifica entrega/retirada
- `enviar_pedido_cancelado()`: Notifica cancelamento

**Características**:
- Integração com Evolution API (opcional)
- Formatação automática de telefone (55 + DDD + número)
- Mensagens personalizadas por tipo de evento
- Não bloqueia checkout se Evolution API estiver indisponível

---

## ♻️ Serviços Atualizados

### 4. `services/loja_service.py` - **REESCRITO COMPLETO**
**Mudanças**: Implementação completa do checkout com todas as regras de negócio.

**Novo fluxo do `processar_checkout()`**:

1. **Validação do Carrinho**
   - Obtém carrinho do Redis
   - Valida que não está vazio

2. **Validação do Cliente**
   - **Cliente convidado**: Valida nome, telefone (DDD + 9 dígitos), email (regex), CPF (dígitos verificadores)
   - **Cliente cadastrado**: Busca no serviço de clientes, valida ativo/não bloqueado
   - **Cliente cadastrado com FIADO**: Verifica campo `permite_fiado_online`

3. **Cálculo de Taxa de Entrega**
   - Se DELIVERY: chama `EntregaService.calcular_taxa_entrega()`
   - Usa cálculo híbrido (taxa padrão + exceções por bairro)
   - Busca dados via ViaCEP

4. **Validação de Estoque e Reservas**
   - Libera reservas temporárias do carrinho (15min)
   - Cria novas reservas de checkout (5min)
   - Valida estoque disponível para todos os itens
   - Usa Redis Lock para prevenir race conditions

5. **Validação de Pagamentos**
   - Valida valor mínimo de R$ 1,00 por forma de pagamento
   - Valida que total dos pagamentos >= total do pedido
   - Valida que apenas uma forma de pagamento online é permitida
   - Se tem FIADO, valida que cliente autoriza fiado online

6. **Criação da Venda**
   - Status inicial: `PENDENTE_PAGAMENTO` (se pagamento online) ou `PEDIDO` (se offline)
   - Salva dados do cliente convidado (se aplicável)
   - Salva endereço de entrega (se DELIVERY)
   - Salva valor do frete

7. **Integração Mercado Pago**
   - Se pagamento online: cria preferência
   - Salva `preference_id` e `init_point` na venda
   - Timeout: 5 minutos
   - Webhook: `/loja/{empresa_slug}/webhook/mercadopago`

8. **Registro de Histórico**
   - Registra status inicial no `historico_status_venda`
   - Observação: "Pedido criado via loja online"

9. **Notificação WhatsApp**
   - Envia notificação de confirmação do pedido
   - Não bloqueia checkout se falhar

10. **Limpeza**
    - Limpa carrinho do Redis
    - Commit no banco

11. **Resposta**
    - Retorna dados da venda
    - Se pagamento online: retorna `mercadopago_init_point` para redirecionamento

**Integrations**:
- `CarrinhoService`: Gerenciar carrinho
- `ClienteValidacaoService`: Validar cliente convidado
- `VendaService`: Criar venda e verificar cliente
- `EntregaService`: Calcular taxa de entrega
- `ReservaTemporariaService`: Gerenciar reservas de estoque
- `MercadoPagoService`: Criar preferência de pagamento
- `HistoricoStatusService`: Registrar mudanças de status
- `NotificacaoService`: Enviar WhatsApp
- `CacheService`: Cache de produtos

---

### 5. `schemas/loja.py`
**Mudanças**: Adicionado suporte para pagamento misto.

**Novos schemas**:
```python
class PagamentoCheckout(BaseModel):
    forma_pagamento: FormaPagamento
    valor: Decimal  # Valor a ser pago nesta forma

class CheckoutRequest(BaseModel):
    # ... campos existentes ...
    pagamentos: List[PagamentoCheckout]  # NOVO: permite múltiplos pagamentos
```

**Validações adicionadas**:
- Valor mínimo de R$ 1,00 por pagamento
- Apenas uma forma de pagamento online permitida (PIX, DEBITO ou CREDITO)
- Total dos pagamentos >= total do pedido

**Schema de resposta atualizado**:
```python
class CheckoutResponse(BaseModel):
    # ... campos existentes ...
    mercadopago_init_point: Optional[str]  # NOVO: URL para pagamento
```

---

### 6. `config.py`
**Mudanças**: Adicionadas variáveis da Evolution API.

**Novas variáveis**:
```python
EVOLUTION_API_URL: str = ""  # URL da Evolution API
EVOLUTION_API_KEY: str = ""  # API Key
EVOLUTION_INSTANCE: str = ""  # Nome da instância
```

---

## 🔄 Integrações Implementadas

### Mercado Pago
- Criação de preferência de pagamento
- Timeout de 5 minutos
- Webhook por empresa: `/loja/{empresa_slug}/webhook/mercadopago`
- Multi-tenant: cada empresa tem suas credenciais

### Evolution API (WhatsApp)
- Notificações assíncronas (não bloqueia checkout)
- Formatação automática de telefone
- Mensagens personalizadas por tipo de evento
- Opcional: continua funcionando se API não estiver configurada

### Serviço de Clientes
- Verificação de cliente ativo/bloqueado
- Verificação de `permite_fiado_online`
- Busca de dados do cliente (nome, telefone, email)

### Serviço de Produtos
- Cache de 5 minutos em Redis
- Fallback para busca direta se cache falhar
- Busca de dados do produto (nome, preço, estoque)

### ViaCEP
- Busca de dados do CEP (bairro, cidade, estado)
- Usado para cálculo de taxa de entrega
- Permite continuar se API falhar (não bloqueia checkout)

---

## 🔒 Regras de Negócio Implementadas

### Cliente Convidado
- ✅ Nome + Telefone obrigatórios
- ✅ Email + CPF opcionais
- ✅ Telefone: DDD + 9 dígitos para celular
- ✅ Email: validação por regex
- ✅ CPF: validação de dígitos verificadores
- ✅ Normalização automática (remove caracteres especiais)

### Cliente Cadastrado com Fiado Online
- ✅ Verifica campo `permite_fiado_online` no serviço de clientes
- ✅ Bloqueia checkout se não autorizado
- ✅ Mensagem clara: "Cliente não autorizado para compras fiadas online"

### Pagamento Misto
- ✅ Suporta múltiplas formas de pagamento
- ✅ Valor mínimo R$ 1,00 por forma
- ✅ Aceita centavos
- ✅ Apenas uma forma online permitida (PIX, DEBITO ou CREDITO)
- ✅ Pode combinar FIADO + online
- ✅ Total dos pagamentos deve ser >= total do pedido

### Taxa de Entrega
- ✅ Cálculo híbrido: taxa padrão + exceções por bairro
- ✅ Busca dados via ViaCEP
- ✅ Permite continuar se ViaCEP falhar
- ✅ Apenas para tipo_entrega=DELIVERY

### Reservas de Estoque
- ✅ Carrinho: 15 minutos
- ✅ Checkout: 5 minutos
- ✅ Redis Lock para prevenir race conditions
- ✅ Validação de estoque antes de criar venda
- ✅ Liberação automática ao expirar

### Status Flow
- ✅ Pagamento online: `PEDIDO` → `PENDENTE_PAGAMENTO` (aguardando aprovação)
- ✅ Pagamento offline: `PEDIDO` (confirmação manual)
- ✅ Histórico completo de mudanças registrado

---

## 📊 Banco de Dados

### Tabelas Utilizadas
- `vendas`: Pedidos (com campos de cliente convidado e endereço)
- `historico_status_venda`: Auditoria de mudanças de status
- `reservas_temporarias`: Reservas de estoque (carrinho e checkout)
- `configuracoes_pagamento`: Credenciais Mercado Pago por empresa
- `configuracoes_loja`: Taxa de entrega padrão
- `faixas_entrega`: Exceções de taxa por bairro

### Novos Campos em `vendas`
- `valor_frete`: Taxa de entrega (DELIVERY)
- `cliente_convidado_nome`: Nome do cliente convidado
- `cliente_convidado_telefone`: Telefone do cliente convidado
- `cliente_convidado_email`: Email do cliente convidado (opcional)
- `cliente_convidado_cpf`: CPF do cliente convidado (opcional)
- `endereco_*`: Campos de endereço de entrega
- `mercadopago_preference_id`: ID da preferência do Mercado Pago
- `mercadopago_payment_id`: ID do pagamento aprovado

---

## 🧪 Testes Pendentes

**Testes a serem executados após subir containers**:

### Checkout - Cliente Convidado
- [ ] Criar pedido com nome + telefone (mínimo)
- [ ] Criar pedido com todos os campos (nome, telefone, email, CPF)
- [ ] Validar erro com telefone inválido
- [ ] Validar erro com email inválido
- [ ] Validar erro com CPF inválido

### Checkout - Cliente Cadastrado
- [ ] Criar pedido com cliente existente
- [ ] Validar erro com cliente inativo
- [ ] Validar erro com cliente bloqueado
- [ ] Validar erro FIADO sem `permite_fiado_online`

### Checkout - Pagamento Misto
- [ ] Pagamento só DINHEIRO
- [ ] Pagamento só PIX
- [ ] Pagamento FIADO + PIX (50%/50%)
- [ ] Validar erro com valor < R$ 1,00
- [ ] Validar erro com múltiplas formas online

### Checkout - Taxa de Entrega
- [ ] RETIRADA (taxa zero)
- [ ] DELIVERY com taxa padrão
- [ ] DELIVERY com exceção de bairro
- [ ] DELIVERY com CEP inválido (deve permitir continuar)

### Checkout - Estoque
- [ ] Validar erro com estoque insuficiente
- [ ] Validar reserva de 5min no checkout
- [ ] Validar liberação de reserva do carrinho
- [ ] Validar race condition (concorrência)

### Mercado Pago
- [ ] Criar preferência de pagamento
- [ ] Validar webhook payment.approved
- [ ] Validar webhook payment.rejected
- [ ] Validar idempotência (webhook duplicado)

### Notificações WhatsApp
- [ ] Enviar notificação de confirmação do pedido
- [ ] Enviar notificação de pagamento aprovado
- [ ] Enviar notificação de pedido separado
- [ ] Enviar notificação de pedido entregue
- [ ] Validar que checkout continua se WhatsApp falhar

---

## 📝 Variáveis de Ambiente Necessárias

**Adicionar no `.env` do serviço vendas**:

```env
# URLs Públicas (para Mercado Pago)
API_BASE_URL=https://api.seudominio.com
FRONTEND_URL=https://loja.seudominio.com

# Evolution API (WhatsApp) - OPCIONAL
EVOLUTION_API_URL=https://evolution-api.seudominio.com
EVOLUTION_API_KEY=sua-api-key-aqui
EVOLUTION_INSTANCE=nome-da-instancia
```

---

## 🚀 Próximos Passos (FASE 5)

1. **Jobs de Timeout**:
   - Alertas de separação (12h, 24h)
   - Auto-cancelamento (48h)
   - Limpeza de reservas expiradas

2. **Endpoints Administrativos**:
   - Configurar taxa de entrega
   - Configurar exceções de bairro
   - Configurar credenciais Mercado Pago
   - Gerenciar clientes (permite_fiado_online)

3. **Relatórios**:
   - Vendas por período
   - Produtos mais vendidos
   - Taxa de conversão (carrinho → pedido)
   - Tempo médio de separação

4. **Melhorias de UX**:
   - Estimativa de entrega
   - Rastreamento com mapa
   - Avaliação de pedido
   - Programa de fidelidade

---

## 📚 Documentação de Referência

- **Requirements**: `.kiro/specs/loja-online-mvp/requirements.md`
- **Migration**: `services/vendas/alembic/versions/20260611_add_loja_online_mvp.py`
- **Models**: `services/vendas/models/venda.py`

---

## ✅ Status

**FASE 4: COMPLETA** ✅

Todas as regras de negócio do checkout foram implementadas conforme requirements. O sistema está pronto para testes de integração.

**Próximo**: Aplicar migrations e testar fluxo completo com containers rodando.
