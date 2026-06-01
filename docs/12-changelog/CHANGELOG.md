# Changelog - Runas

> **Histórico de versões** e mudanças do projeto Runas

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### 🚧 Em Desenvolvimento

- Implementação completa dos microsserviços
- Interface frontend completa
- Testes automatizados
- Documentação de API

### ✨ Adicionado

**Backend - Transações de Banco de Dados** (2026-05-26)
- Implementação de transações atômicas ACID em todos os serviços implementados
- Uso de `begin_nested()` para operações complexas
- Tratamento robusto de exceções com rollback automático
- Logging estruturado de operações e erros
- Documentação completa sobre transações

**Serviços Atualizados:**
- ✅ **Estoque**: Todas as operações (entrada, saída, ajuste, reserva) com transações atômicas
- ✅ **Produtos**: CRUD de produtos, categorias e variantes com transações atômicas
- ✅ **Clientes**: CRUD de clientes, crédito, endereços com transações atômicas
- ⚪ **Vendas**: Serviço ainda não implementado
- ⚪ **Financeiro**: Serviço ainda não implementado

**Melhorias de Arquitetura:**
- Separação clara de responsabilidades (Router → Service → Repository)
- Commits gerenciados exclusivamente na camada de serviço
- Routers simplificados sem lógica de transação
- Padrões consistentes em todos os serviços

### 📚 Documentação

- Novo documento: `docs/04-backend/transacoes-banco-dados.md`
  - Conceitos ACID explicados
  - Padrões de implementação
  - Exemplos práticos completos
  - Boas práticas e anti-padrões
  - Guia de troubleshooting
- Novo documento: `docs/04-backend/QUICK_REFERENCE_TRANSACOES.md`
  - Templates prontos para uso
  - Checklist de implementação
  - Padrões por tipo de operação
- Novo documento: `docs/04-backend/README.md`
  - Visão geral do backend
  - Stack tecnológica
  - Arquitetura em camadas
- Novo documento: `TRANSACOES_IMPLEMENTADAS.md`
  - Resumo executivo
  - Status de implementação
  - Exemplos práticos

---

## [1.0.0] - 2026-05-26

### 🎉 Lançamento Inicial (MVP)

#### ✨ Adicionado

**Infraestrutura**
- Arquitetura de microsserviços com Docker Compose
- API Gateway com autenticação JWT
- PostgreSQL (1 banco por serviço)
- Redis para cache e sessões
- RabbitMQ para mensageria
- pgAdmin pré-configurado
- Migrations automáticas via Alembic
- Health checks em todos os serviços

**Backend - API Gateway**
- Autenticação OAuth2 + JWT
- Rate limiting (100 req/min anônimo, 500 req/min autenticado)
- Roteamento para microsserviços
- Middleware de logging estruturado
- Gestão de usuários (ADMIN, OPERADOR)

**Backend - Serviço de Clientes**
- CRUD completo de clientes
- Validação de CPF
- Gestão de endereços
- Controle de crédito e limite
- Bloqueio automático por inadimplência
- Histórico de movimentações

**Backend - Serviço de Produtos**
- CRUD de produtos e categorias
- Sistema de variantes (SKU, preço, markup)
- Catálogo público
- Gestão de fornecedores
- Upload de fotos
- Cálculo automático de preço de venda

**Backend - Serviço de Estoque**
- Controle de estoque por variante
- Movimentações (entrada, saída, ajuste)
- Alertas de estoque mínimo
- Histórico imutável de movimentações
- Eventos para estoque baixo

**Backend - Serviço de Vendas**
- Carrinho de compras (expira em 24h)
- Checkout com validações
- Gestão de pedidos
- Integração Mercado Pago (PIX)
- Pagamento em dinheiro com troco
- Pagamento fiado com validação de crédito
- Webhook para confirmação de pagamento
- Gestão de frete manual

**Backend - Serviço Financeiro**
- Contas a receber
- Pagamentos parciais e totais
- Cálculo automático de vencimento
- Jobs automáticos de cobrança
- Alertas de contas vencidas
- Histórico de pagamentos

**Backend - Serviço de Notificações**
- WhatsApp via Evolution API
- Consumidor de eventos RabbitMQ
- Retry automático (5 tentativas)
- Deduplicação de mensagens
- Histórico de notificações

**Frontend**
- Interface React + TypeScript
- Design system completo (dark mode)
- Autenticação com refresh token
- Dashboard com métricas
- Módulo de Clientes
- Módulo de Produtos
- Módulo de Estoque
- Módulo de Vendas
- Módulo Financeiro
- Responsivo (mobile-first)

**Documentação**
- README completo
- Guia de setup
- Arquitetura detalhada
- Diagramas de sequência
- Mapeamento de rotas
- Design system
- Guia de contribuição
- Glossário
- FAQ

#### 🔧 Configuração

- Docker Compose com 7 serviços + infraestrutura
- Variáveis de ambiente via .env
- Makefile com comandos úteis
- Seed automático de dados iniciais
- pgAdmin com conexões pré-configuradas

#### 📚 Documentação

- Estrutura organizada em 12 seções
- Diagramas de arquitetura
- Diagramas de sequência por domínio
- Regras de negócio documentadas
- Guias de setup e deployment

---

## [0.2.0] - 2026-05-15

### 🏗️ Fase de Planejamento

#### ✨ Adicionado

- Definição da arquitetura de microsserviços
- Especificação de modelos de dados
- Definição de endpoints de API
- Regras de negócio documentadas
- Stack tecnológica definida

#### 📚 Documentação

- Documento de arquitetura inicial
- Especificação de requisitos
- Diagramas de fluxo

---

## [0.1.0] - 2026-05-01

### 🌱 Concepção do Projeto

#### ✨ Adicionado

- Definição do escopo do MVP
- Pesquisa de mercado
- Análise de concorrentes
- Definição de personas
- Roadmap inicial

#### 📚 Documentação

- Documento de visão do produto
- Análise de viabilidade
- Proposta de valor

---

## Tipos de Mudanças

- **✨ Adicionado** - Novas funcionalidades
- **🔧 Modificado** - Mudanças em funcionalidades existentes
- **🗑️ Removido** - Funcionalidades removidas
- **🐛 Corrigido** - Correções de bugs
- **🔒 Segurança** - Correções de vulnerabilidades
- **📚 Documentação** - Mudanças na documentação
- **⚡ Performance** - Melhorias de performance
- **♻️ Refatoração** - Mudanças de código sem alterar funcionalidade

---

## Links de Comparação

- [Unreleased]: https://github.com/denebcorp/runas/compare/v1.0.0...HEAD
- [1.0.0]: https://github.com/denebcorp/runas/releases/tag/v1.0.0
- [0.2.0]: https://github.com/denebcorp/runas/releases/tag/v0.2.0
- [0.1.0]: https://github.com/denebcorp/runas/releases/tag/v0.1.0

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
