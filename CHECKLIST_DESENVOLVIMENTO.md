# 📋 Checklist de Desenvolvimento - ERP Runas

> **Última atualização**: 23/06/2026
> 
> Este documento lista o status atual e próximas funcionalidades do sistema ERP.
> **Status**: 🔴 Não iniciado | 🟡 Em progresso | ✅ Concluído

---

## 📊 Visão Geral do Progresso - Junho 2026

### Backend (APIs REST)

| Serviço | Status | Endpoints | Multi-Tenancy | Migrations | Observações |
|---------|--------|-----------|---------------|------------|-------------|
| **API Gateway** | ✅ 100% | 15 | N/A | ✅ | Auth JWT, RBAC, Proxy, Rate Limit |
| **Empresas** | ✅ 100% | 8 | N/A | ✅ | CRUD completo no Gateway |
| **Clientes** | ✅ 100% | 12 | ✅ | ✅ | CRUD, Endereços, Crédito |
| **Produtos** | ✅ 100% | 25 | ✅ | ✅ | CRUD, Variantes, Categorias, Fornecedores |
| **Estoque** | ✅ 100% | 19 | ✅ | ✅ | Movimentações, Lotes, Inventário |
| **Vendas** | ✅ 100% | 14 | ✅ | ✅ | PDV, Workflow 6 estados |
| **Loja Online** | ✅ 100% | 26 | ✅ | ✅ | Catálogo, Carrinho, Checkout |
| **Financeiro** | 🔴 0% | 0 | - | - | Não implementado |
| **Notificações** | 🔴 0% | 0 | - | - | Não implementado |

**Total**: 119 endpoints funcionais | 6 serviços completos

### Frontend (React + TypeScript)

| Módulo | Status | Rotas | Componentes | Observações |
|--------|--------|-------|-------------|-------------|
| **Autenticação** | ✅ 100% | 3 | 5 | Login, Register, OAuth Google |
| **Dashboard** | ✅ 100% | 1 | 8 | Página inicial com cards KPI |
| **Clientes** | ✅ 90% | 6 | 12 | Falta: Histórico de compras |
| **Produtos** | ✅ 100% | 7 | 15 | CRUD completo + Categorias |
| **Loja Online** | ✅ 100% | 6 | 18 | Catálogo → Checkout → Rastreamento |
| **Estoque** | 🔴 0% | 0 | 0 | Backend pronto, frontend pendente |
| **Vendas/PDV** | 🔴 0% | 0 | 0 | Backend pronto, frontend pendente |
| **Financeiro** | 🔴 0% | 0 | 0 | Backend não implementado |

**Total**: 23 rotas | 58 componentes | ~18.000 linhas TS/TSX

### Infraestrutura

- ✅ **Docker Compose**: Dev + Prod configurados
- ✅ **PostgreSQL**: 8 schemas em 1 container (consolidado)
- ✅ **Redis**: Cache e sessões
- ✅ **RabbitMQ**: Mensageria (preparado, não usado ainda)
- ✅ **Nginx**: Reverse proxy com rate limiting
- ✅ **Ngrok**: Tunnel para desenvolvimento (.env.ngrok)
- ✅ **Alembic**: Migrations em 6/8 serviços
- ✅ **Multi-Tenancy**: Row-level isolation (empresa_id)

---

## 🎯 PRIORIDADES - Próximas 4 Semanas

### Semana 1-2: PDV/Vendas Frontend 🔥 URGENTE
**Objetivo**: Vendedor consegue usar o sistema

- [ ] **VendasPage** - Lista de vendas com filtros
- [ ] **PDVPage** - Tela de ponto de venda
  - [ ] Busca de produtos (autocomplete)
  - [ ] Busca de clientes (autocomplete)
  - [ ] Adicionar itens ao carrinho
  - [ ] Aplicar desconto (% ou R$)
  - [ ] Múltiplas formas de pagamento
  - [ ] Calcular troco
  - [ ] Validar crédito FIADO
- [ ] **VendaDetalhesPage** - Ver venda completa
- [ ] **Modais de Ações**
  - [ ] Confirmar venda (PEDIDO → CONFIRMADA)
  - [ ] Separar pedido (CONFIRMADA → SEPARADA)
  - [ ] Entregar pedido (SEPARADA → ENTREGUE)
  - [ ] Cancelar venda

**Entregável**: PDV funcional para vendas presenciais

### Semana 3: Estoque Frontend 🔥 ALTA
**Objetivo**: Controlar movimentações de estoque

- [ ] **EstoquePage** - Lista de produtos em estoque
- [ ] **MovimentacoesPage** - Histórico de movimentações
- [ ] **EntradaEstoquePage** - Registrar entrada
- [ ] **SaidaEstoquePage** - Registrar saída
- [ ] **AjusteInventarioPage** - Corrigir divergências
- [ ] **AlertasPage** - Estoque baixo + Lotes vencendo

**Entregável**: Gestão básica de estoque funcional

### Semana 4: Testes Automatizados 🟡 MÉDIA
**Objetivo**: 80% cobertura nos serviços principais

- [ ] **Clientes**: 37 testes (15 unit + 10 repos + 12 integr)
- [ ] **Produtos**: 50 testes (25 unit + 25 integr)
- [ ] **Vendas**: 39 testes (20 unit + 14 integr + 5 E2E)
- [ ] **Loja Online**: 66 testes (30 unit + 26 integr + 10 E2E)

**Entregável**: ~180 testes | Cobertura 80%+ | CI/CD configurado

---

## ✅ FUNCIONALIDADES IMPLEMENTADAS

### 1. API GATEWAY ✅

#### Autenticação ✅
- ✅ Login com email/senha
- ✅ OAuth2 Google
- ✅ JWT access + refresh tokens
- ✅ Logout com blacklist (Redis)
- ✅ Renovação de token
- ✅ Validação de token expirado

#### RBAC (Controle de Acesso) ✅
- ✅ Roles: ADMIN, GERENTE, VENDEDOR, OPERADOR
- ✅ Middleware de autenticação
- ✅ Middleware de autorização por role
- ✅ Verificação X-Empresa-Id

#### Proxy ✅
- ✅ Roteamento para microsserviços
- ✅ Rate limiting (100 req/min)
- ✅ Health checks
- ✅ Logging estruturado

#### Email Service ✅
- ✅ Envio de emails transacionais
- ✅ Templates HTML
- ✅ Verificação de email
- ✅ Recuperação de senha

### 2. CLIENTES ✅

#### CRUD ✅
- ✅ Criar cliente (PF/PJ)
- ✅ Listar com paginação
- ✅ Buscar por ID
- ✅ Atualizar dados
- ✅ Soft delete (desativar)
- ✅ Bloquear/desbloquear

#### Validações ✅
- ✅ CPF com dígitos verificadores
- ✅ CNPJ com dígitos verificadores
- ✅ Email válido
- ✅ Telefone DDD + 9 dígitos
- ✅ CEP 8 dígitos

#### Endereços ✅
- ✅ Múltiplos endereços por cliente
- ✅ Endereço principal
- ✅ Tipos: residencial, comercial, cobrança, entrega

#### Crédito ✅
- ✅ Definir limite de crédito
- ✅ Calcular crédito disponível
- ✅ Dia de vencimento (1-28)
- ✅ Histórico de alterações

#### Multi-Tenancy ✅
- ✅ Isolamento por empresa_id
- ✅ CPF único por empresa
- ✅ Validação header X-Empresa-Id

### 3. PRODUTOS ✅

#### CRUD ✅
- ✅ Criar produto
- ✅ Listar com filtros (nome, categoria, ativo)
- ✅ Buscar por ID
- ✅ Atualizar dados
- ✅ Soft delete

#### Categorias ✅
- ✅ CRUD completo
- ✅ Hierarquia (categoria pai)
- ✅ Ícone e cor
- ✅ Ordenação

#### Variantes ✅
- ✅ CRUD de variantes
- ✅ SKU único por empresa
- ✅ Atributos (cor, tamanho, etc)
- ✅ Preço e markup individual
- ✅ Cálculo automático preço venda

#### Fornecedores ✅
- ✅ CRUD completo
- ✅ CNPJ validado
- ✅ Associação produto-fornecedor
- ✅ Preço de custo por fornecedor
- ✅ Tempo de entrega

#### Loja Online ✅
- ✅ Configuração (visível, destaque, ordem)
- ✅ Upload de fotos
- ✅ Catálogo público
- ✅ SEO (slug, meta)

#### Multi-Tenancy ✅
- ✅ Isolamento por empresa_id
- ✅ SKU único por empresa
- ✅ Categorias isoladas

### 4. ESTOQUE ✅

#### Controle ✅
- ✅ Quantidade disponível
- ✅ Quantidade reservada
- ✅ Estoque mínimo/máximo
- ✅ Localização física
- ✅ Custo médio

#### Movimentações ✅
- ✅ Entrada (compra, devolução)
- ✅ Saída (venda, perda)
- ✅ Ajuste (inventário)
- ✅ Transferência entre locais
- ✅ Histórico completo

#### Lotes ✅
- ✅ Controle por lote
- ✅ Código único
- ✅ Data validade
- ✅ Fornecedor origem
- ✅ Alertas de vencimento

#### Inventário ✅
- ✅ Inventário físico
- ✅ Divergências (falta/sobra)
- ✅ Ajustes automáticos
- ✅ Observações

#### Relatórios ✅
- ✅ Estoque geral
- ✅ Movimentações por período
- ✅ Produtos estoque baixo
- ✅ Produtos sem estoque
- ✅ Lotes vencendo

#### Multi-Tenancy ✅
- ✅ Isolamento por empresa_id
- ✅ Código lote único por empresa

### 5. VENDAS ✅

#### CRUD ✅
- ✅ Criar venda
- ✅ Listar com filtros
- ✅ Buscar por ID/número
- ✅ Atualizar (se PEDIDO)
- ✅ Cancelar venda

#### Workflow ✅
- ✅ **PEDIDO** - Venda criada
- ✅ **CONFIRMADA** - Pagamento confirmado
- ✅ **SEPARADA** - Itens separados
- ✅ **ENTREGUE** - Pedido entregue
- ✅ **FINALIZADA** - Venda finalizada
- ✅ **CANCELADA** - Venda cancelada

#### Itens ✅
- ✅ Múltiplos itens por venda
- ✅ Produto + variante
- ✅ Quantidade e preço unitário
- ✅ Subtotal calculado

#### Pagamentos ✅
- ✅ Múltiplas formas (PIX, Débito, Crédito, Dinheiro, FIADO)
- ✅ Pagamento misto (ex: R$ 50 PIX + R$ 50 Dinheiro)
- ✅ Troco calculado
- ✅ Parcelas (Crédito)

#### Descontos ✅
- ✅ Desconto percentual
- ✅ Desconto valor fixo
- ✅ Aplicado no total

#### Integração Estoque ✅
- ✅ Reservar estoque (CONFIRMADA)
- ✅ Baixar estoque (ENTREGUE)
- ✅ Liberar estoque (CANCELADA)
- ✅ Validar disponibilidade

#### Validações ✅
- ✅ Cliente ativo e não bloqueado
- ✅ Crédito disponível (FIADO)
- ✅ Estoque disponível
- ✅ Valores positivos

#### Relatórios ✅
- ✅ Resumo de vendas
- ✅ Vendas por período
- ✅ Produtos mais vendidos
- ✅ Vendas por cliente

#### Multi-Tenancy ✅
- ✅ Isolamento por empresa_id
- ✅ Número venda único por empresa

### 6. LOJA ONLINE ✅

#### Catálogo Público ✅
- ✅ Listar produtos visíveis
- ✅ Filtrar por categoria
- ✅ Buscar por nome
- ✅ Ordenar (preço, nome, destaque)
- ✅ Paginação

#### Produto Detalhes ✅
- ✅ Informações completas
- ✅ Galeria de fotos
- ✅ Seletor de variantes
- ✅ Verificar estoque
- ✅ Adicionar ao carrinho
- ✅ Produtos relacionados
- ✅ Compartilhar (link, WhatsApp)

#### Carrinho ✅
- ✅ Sessão por cookie HttpOnly
- ✅ Adicionar item
- ✅ Atualizar quantidade
- ✅ Remover item
- ✅ Limpar carrinho
- ✅ Calcular subtotal
- ✅ Persistência entre sessões

#### Checkout ✅
- ✅ **Step 1: Dados do Cliente**
  - ✅ Nome, telefone, email, CPF
  - ✅ Cliente convidado ou cadastrado
  - ✅ Formatação automática
  - ✅ Validação em tempo real
- ✅ **Step 2: Entrega**
  - ✅ Retirada no local (grátis)
  - ✅ Delivery com endereço
  - ✅ Busca CEP via ViaCEP
  - ✅ Cálculo de frete
- ✅ **Step 3: Pagamento**
  - ✅ PIX, Débito, Crédito (Mercado Pago)
  - ✅ Dinheiro (calcular troco)
  - ✅ FIADO (validar crédito)
  - ✅ Pagamento misto

#### Rastreamento ✅
- ✅ Buscar por número pedido
- ✅ Timeline visual de status
- ✅ Histórico de alterações
- ✅ Previsão de entrega
- ✅ Dados da loja

#### Meus Pedidos ✅
- ✅ Listar pedidos do cliente
- ✅ Filtrar por status
- ✅ Ordenar por data
- ✅ Link para rastreamento

#### Features UX ✅
- ✅ Feedback visual (loading, success, error)
- ✅ Empty states amigáveis
- ✅ Formatação automática (tel, CPF, CEP)
- ✅ Validações em tempo real
- ✅ Totalmente responsivo
- ✅ Steps indicator
- ✅ Badge status colorido

---

## 🔴 FUNCIONALIDADES PENDENTES

### 1. VENDAS/PDV - Frontend 🔥

#### Páginas
- [ ] `/vendas` - Lista de vendas
- [ ] `/vendas/nova` - PDV completo
- [ ] `/vendas/:id` - Detalhes venda
- [ ] `/vendas/:id/editar` - Editar (se PEDIDO)
- [ ] `/vendas/relatorios` - Relatórios

#### Componentes
- [ ] `PDV` - Tela principal de vendas
- [ ] `BuscaProduto` - Autocomplete produtos
- [ ] `BuscaCliente` - Autocomplete clientes
- [ ] `ItemVenda` - Card de item no carrinho
- [ ] `ModalPagamento` - Múltiplos pagamentos
- [ ] `DescontoCalculator` - Aplicar desconto
- [ ] `ResumoVenda` - Totais da venda
- [ ] Modais de workflow (confirmar, separar, entregar, cancelar)

#### Features
- [ ] Busca rápida (código barras futuro)
- [ ] Atalhos teclado (F2, F3, F9)
- [ ] Impressão cupom (futuro)
- [ ] Histórico de vendas
- [ ] Gráficos e KPIs

### 2. ESTOQUE - Frontend 🔥

#### Páginas
- [ ] `/estoque` - Dashboard estoque
- [ ] `/estoque/produtos` - Lista produtos
- [ ] `/estoque/movimentacoes` - Histórico
- [ ] `/estoque/entrada` - Registrar entrada
- [ ] `/estoque/saida` - Registrar saída
- [ ] `/estoque/ajuste` - Ajuste inventário
- [ ] `/estoque/alertas` - Estoque baixo + vencimento

#### Componentes
- [ ] `EstoqueCard` - Card de produto
- [ ] `MovimentacaoForm` - Form movimentação
- [ ] `FiltrosEstoque` - Filtros avançados
- [ ] `AlertasWidget` - Widget de alertas
- [ ] `HistoricoTimeline` - Timeline movimentações

#### Features
- [ ] Alertas automáticos (estoque baixo)
- [ ] Notificações (lotes vencendo)
- [ ] Relatórios PDF
- [ ] Gráficos de consumo

### 3. FINANCEIRO - Backend + Frontend 🟡

#### Backend APIs
- [ ] Contas a Receber (CRUD)
- [ ] Contas a Pagar (CRUD)
- [ ] Recebimentos (baixa)
- [ ] Pagamentos (baixa)
- [ ] Fluxo de caixa
- [ ] Conciliação bancária
- [ ] Centros de custo
- [ ] Relatórios

#### Frontend
- [ ] Dashboard financeiro
- [ ] Lista contas receber/pagar
- [ ] Baixa de contas
- [ ] Fluxo de caixa
- [ ] Relatórios financeiros

#### Integrações
- [ ] Gerar conta receber ao confirmar venda FIADO
- [ ] Baixar conta receber ao registrar pagamento
- [ ] Integração Mercado Pago (webhook)

### 4. NOTIFICAÇÕES - Backend + Frontend 🟡

#### Backend APIs
- [ ] WhatsApp (Evolution API)
- [ ] Email transacional
- [ ] SMS (Twilio/similar)
- [ ] Push notifications
- [ ] Templates de mensagens
- [ ] Histórico de envios

#### Frontend
- [ ] Central de notificações
- [ ] Configurações de notificação
- [ ] Templates personalizados

#### Triggers Automáticos
- [ ] Venda confirmada → WhatsApp
- [ ] Venda entregue → WhatsApp
- [ ] Conta vencendo → WhatsApp/Email
- [ ] Estoque baixo → Email
- [ ] Lote vencendo → Email

### 5. RELATÓRIOS E DASHBOARDS 🟡

#### Dashboards
- [ ] Dashboard Executivo (KPIs principais)
- [ ] Dashboard Vendas
- [ ] Dashboard Estoque
- [ ] Dashboard Financeiro

#### Relatórios
- [ ] Vendas por período
- [ ] Produtos mais vendidos
- [ ] Clientes top 10
- [ ] Análise de margem
- [ ] Curva ABC
- [ ] DRE simplificado
- [ ] Fluxo de caixa projetado

#### Exportação
- [ ] PDF
- [ ] Excel
- [ ] CSV

### 6. MELHORIAS UX/UI 🟡

#### Mobile
- [ ] PWA (instalar como app)
- [ ] Offline mode básico
- [ ] Push notifications
- [ ] Gestures (swipe, pull-to-refresh)

#### Acessibilidade
- [ ] Testes com screen reader
- [ ] Contraste WCAG AAA
- [ ] Navegação completa por teclado
- [ ] Skip links

#### Performance
- [ ] Lazy loading imagens
- [ ] Infinite scroll
- [ ] Service Worker
- [ ] Cache estratégico

---

## 🧪 TESTES

### Status Atual
- 🔴 **Testes Unitários**: 0%
- 🔴 **Testes Integração**: 0%
- 🔴 **Testes E2E**: 0%
- 🔴 **Coverage**: 0%

### Plano (4 semanas)
- [ ] **Clientes**: 37 testes | 80% coverage
- [ ] **Produtos**: 50 testes | 80% coverage
- [ ] **Vendas**: 39 testes | 80% coverage
- [ ] **Loja Online**: 66 testes | 80% coverage
- [ ] **CI/CD**: GitHub Actions com testes automáticos

**Documento**: Ver `GUIA_TESTES_AUTOMATIZADOS.md` na raiz

---

## 🚀 INTEGRAÇÕES

### Implementadas ✅
- ✅ OAuth2 Google (login social)
- ✅ ViaCEP (busca endereço por CEP)
- ✅ Ngrok (tunnel para desenvolvimento)

### Preparadas (não ativas) 🟡
- 🟡 Mercado Pago (pagamentos PIX)
- 🟡 Evolution API (WhatsApp)

### Planejadas 🔴
- 🔴 Twilio (SMS)
- 🔴 AWS S3 (storage de imagens)
- 🔴 Correios (cálculo frete)

---

## 📚 DOCUMENTAÇÃO

### Documentos Principais
- ✅ `README.md` - Overview do projeto
- ✅ `O SISTEMA.md` - Descrição completa
- ✅ `QUICK-START.md` - Início rápido
- ✅ `GUIA_TESTES_AUTOMATIZADOS.md` - Guia de testes
- ✅ `CHECKLIST_DESENVOLVIMENTO.md` - Este documento
- ✅ `FRONTEND_IMPLEMENTACAO.md` - Guia frontend

### Docs Técnicos
- ✅ Swagger/OpenAPI em cada serviço (`/docs`)
- ✅ Alembic migrations em cada serviço
- ✅ Steering rules no `.kiro/steering/`

---

## 📊 MÉTRICAS DO PROJETO

### Backend
- **Linhas de código**: ~25.000 Python
- **Arquivos**: ~250
- **Endpoints REST**: 119
- **Models**: 35+
- **Migrations**: 15+

### Frontend
- **Linhas de código**: ~18.000 TS/TSX/SCSS
- **Arquivos**: ~180
- **Rotas**: 23
- **Componentes**: 58
- **Páginas**: 18

### Infraestrutura
- **Containers Docker**: 5 (nginx, db, redis, rabbitmq, pgadmin)
- **Schemas PostgreSQL**: 8
- **RAM utilizada**: ~800 MB (otimizado)
- **Build time**: ~3 min

---

## 🎯 ROADMAP 2026

### Q2 2026 (Atual)
- [x] MVP Backend completo (Clientes, Produtos, Vendas, Loja)
- [x] Frontend Loja Online
- [x] Multi-tenancy implementado
- [x] Infraestrutura consolidada
- [ ] Frontend PDV/Vendas
- [ ] Frontend Estoque
- [ ] Testes automatizados (80%)

### Q3 2026
- [ ] Serviço Financeiro completo
- [ ] Serviço Notificações completo
- [ ] Integração Mercado Pago ativa
- [ ] Integração WhatsApp ativa
- [ ] Dashboards e relatórios
- [ ] PWA mobile

### Q4 2026
- [ ] App móvel nativo (React Native)
- [ ] BI e analytics avançado
- [ ] Módulo de compras
- [ ] Módulo de estoque avançado (FIFO/FEFO)
- [ ] Sistema de permissões granular

---

**Versão**: 2.1.0  
**Última atualização**: 23/06/2026  
**Próxima revisão**: 30/06/2026
