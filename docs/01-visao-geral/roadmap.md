# Roadmap - Runas

> **Planejamento de desenvolvimento** e evolução do Runas

---

## 🎯 Visão Geral

Este documento apresenta o roadmap de desenvolvimento do Runas, organizado em fases com objetivos claros e prazos estimados.

---

## ✅ Fase 0: Fundação (Concluída - Maio 2026)

### Objetivos
- Definir arquitetura e stack tecnológica
- Criar documentação base
- Configurar infraestrutura de desenvolvimento

### Entregas
- ✅ Arquitetura de microsserviços definida
- ✅ Stack tecnológica escolhida
- ✅ Docker Compose configurado
- ✅ Estrutura de pastas criada
- ✅ Documentação inicial

---

## 🚧 Fase 1: MVP Backend (Em Progresso - Junho 2026)

### Objetivos
- Implementar todos os microsserviços
- Configurar autenticação e autorização
- Integrar serviços externos

### Entregas

#### API Gateway (85% completo)
- ✅ Autenticação JWT
- ✅ OAuth2 (Google, Microsoft)
- ✅ Roteamento básico
- ✅ Rate limiting
- ✅ Proxy para microsserviços
- ✅ Email Service
- ✅ Password Recovery Flow
- 🚧 Testes de integração
- 🚧 Documentação Swagger

#### Serviço de Clientes (90% completo)
- ✅ CRUD de clientes
- ✅ Validação de CPF
- ✅ Gestão de endereços
- ✅ Controle de crédito
- ✅ Bloqueio/desbloqueio
- ✅ Soft delete
- ✅ Transações ACID
- 🟡 Integração com ViaCEP (frontend implementado, backend pendente)
- 🚧 Histórico de alterações
- 🚧 Testes unitários

#### Serviço de Produtos (85% completo)
- ✅ CRUD de produtos
- ✅ CRUD de categorias
- ✅ Sistema de variantes
- ✅ Atributos de variantes
- ✅ Cálculo de markup
- ✅ Soft delete
- ✅ Transações ACID
- 🚧 Catálogo público
- 🚧 Gestão de fornecedores
- 🚧 Upload de fotos
- 🚧 Testes unitários

#### Serviço de Estoque (90% completo)
- ✅ Controle de estoque
- ✅ Movimentações (entrada, saída, ajuste, devolução, perda)
- ✅ Gestão de lotes
- ✅ Inventário físico
- ✅ Estoque mínimo/máximo
- ✅ Reserva de estoque
- ✅ Localização física
- ✅ Transações ACID
- 🚧 Alertas de estoque mínimo
- 🚧 Alertas de validade
- 🚧 FIFO/FEFO
- 🚧 Testes unitários

#### Serviço de Vendas (5% completo)
- 🚧 Carrinho de compras
- 🚧 Checkout
- 🚧 Gestão de pedidos
- 🚧 Validação de crédito
- 🚧 Reserva de estoque
- 🚧 Integração Mercado Pago
- 🚧 Testes unitários

#### Serviço Financeiro (5% completo)
- 🚧 Contas a receber
- 🚧 Contas a pagar
- 🚧 Pagamentos
- 🚧 Jobs de cobrança
- 🚧 Cálculo de juros/multa
- 🚧 Testes unitários

#### Serviço de Notificações (75% completo)
- ✅ Email Service implementado
- ✅ Estrutura base de notificações
- 🚧 Integração Evolution API (WhatsApp)
- 🚧 Consumidor de eventos
- 🚧 Retry automático
- 🚧 Templates de mensagens
- 🚧 Testes unitários

**Prazo**: 30 de Junho de 2026  
**Progresso Geral**: 62% completo

---

## 📅 Fase 2: MVP Frontend (Julho 2026)

### Objetivos
- Implementar interface completa
- Integrar com backend
- Garantir responsividade

### Entregas

#### Infraestrutura (90% completo)
- ✅ Setup Vite + React + TypeScript
- ✅ Configuração de rotas
- ✅ Design system base
- ✅ Autenticação (Login, Register, OAuth)
- ✅ Password Recovery
- ✅ Interceptors HTTP
- ✅ Configuração Nginx + Docker
- ✅ Integração Ngrok para desenvolvimento
- 🚧 Testes E2E

#### Módulos
- ✅ Dashboard (página inicial)
- ✅ Autenticação completa
- 🟡 Clientes (85% - falta histórico)
  - ✅ Lista com filtros
  - ✅ Cadastro
  - ✅ Edição
  - ✅ Gestão de endereços
  - ✅ Gestão de crédito
  - 🚧 Histórico de compras
- ✅ Produtos (80% - falta fotos e fornecedores)
  - ✅ Lista com filtros
  - ✅ Cadastro
  - ✅ Edição
  - ✅ Detalhes
  - ✅ Gestão de variantes
  - ✅ Gestão de categorias
  - 🚧 Upload de fotos
  - 🚧 Gestão de fornecedores
- 🔴 Estoque (0%)
  - 🚧 Visão geral
  - 🚧 Movimentações
  - 🚧 Lotes
  - 🚧 Inventário
  - 🚧 Alertas
- 🔴 Vendas (0%)
  - 🚧 PDV
  - 🚧 Lista de vendas
  - 🚧 Detalhes
  - 🚧 Devolução
- 🔴 Financeiro (0%)
  - 🚧 Dashboard
  - 🚧 Contas a receber
  - 🚧 Contas a pagar
  - 🚧 Fluxo de caixa

#### Componentes
- ✅ Componentes comuns (Button, Input, Card, etc.)
- ✅ Formulários reutilizáveis
- ✅ Tabelas com paginação
- ✅ Modais
- 🚧 Gráficos e dashboards
- 🚧 Upload de arquivos

**Prazo**: 31 de Julho de 2026  
**Progresso Geral**: 44% completo

---

## 🧪 Fase 3: Testes e Qualidade (Agosto 2026)

### Objetivos
- Atingir 80% de cobertura de testes
- Corrigir bugs identificados
- Otimizar performance

### Entregas
- 🔴 Testes unitários (backend)
- 🔴 Testes de integração (backend)
- 🔴 Testes E2E (frontend)
- 🔴 Testes de carga
- 🔴 Correção de bugs
- 🔴 Otimizações de performance

**Prazo**: 31 de Agosto de 2026

---

## 🚀 Fase 4: Deploy e Lançamento (Setembro 2026)

### Objetivos
- Preparar ambiente de produção
- Realizar deploy inicial
- Monitorar estabilidade

### Entregas
- 🔴 Configuração de servidor
- 🔴 CI/CD pipeline
- 🔴 Monitoramento (logs, métricas)
- 🔴 Backup automático
- 🔴 Documentação de deploy
- 🔴 Treinamento de usuários
- 🔴 Lançamento beta

**Prazo**: 30 de Setembro de 2026

---

## 📈 Fase 5: Pós-MVP - Melhorias (Outubro-Dezembro 2026)

### Objetivos
- Coletar feedback de usuários
- Implementar melhorias prioritárias
- Adicionar funcionalidades complementares

### Entregas Planejadas

#### Melhorias de UX
- 🔴 Onboarding interativo
- 🔴 Tutoriais in-app
- 🔴 Atalhos de teclado
- 🔴 Modo offline (PWA)
- 🔴 Tema escuro/claro

#### Funcionalidades Novas
- 🔴 Relatórios avançados
- 🔴 Exportação de dados (PDF, Excel)
- 🔴 Importação em lote
- 🔴 Etiquetas e tags personalizadas
- 🔴 Notas e anexos
- 🔴 Histórico de alterações completo
- 🔴 Auditoria de ações

#### Integrações
- 🔴 Nota Fiscal Eletrônica (NF-e)
- 🔴 Integração com marketplaces
- 🔴 API pública para terceiros
- 🟡 ViaCEP para validação de endereços (frontend ✅, backend 🚧)
- 🔴 WhatsApp Business (Evolution API)
- 🔴 Mercado Pago
- 🔴 Correios (cálculo de frete)

#### Performance
- 🔴 Cache avançado
- 🔴 Otimização de queries
- 🔴 Lazy loading
- 🔴 Compressão de imagens

**Prazo**: 31 de Dezembro de 2026

---

## 🎯 Fase 6: Expansão (2027)

### Objetivos
- Expandir funcionalidades
- Suportar novos tipos de negócio
- Internacionalização

### Entregas Planejadas

#### Novos Módulos
- 🔴 Compras e Fornecedores
- 🔴 Produção e Manufatura
- 🔴 Recursos Humanos
- 🔴 CRM Avançado
- 🔴 Marketing e Campanhas

#### Multi-tenant
- 🔴 Suporte a múltiplas empresas
- 🔴 Isolamento de dados
- 🔴 Planos e assinaturas

#### Internacionalização
- 🔴 Suporte a múltiplos idiomas
- 🔴 Múltiplas moedas
- 🔴 Fusos horários
- 🔴 Localização de datas e números

#### Mobile
- 🔴 App iOS nativo
- 🔴 App Android nativo
- 🔴 Sincronização offline

**Prazo**: Dezembro de 2027

---

## 🔮 Futuro (2028+)

### Visão de Longo Prazo

#### Inteligência Artificial
- Previsão de demanda
- Sugestão de preços
- Detecção de fraudes
- Chatbot de atendimento

#### Analytics Avançado
- Business Intelligence
- Dashboards personalizáveis
- Análise preditiva
- Benchmarking

#### Ecossistema
- Marketplace de plugins
- API pública robusta
- Webhooks customizáveis
- Integrações com ERPs legados

#### Escalabilidade
- Kubernetes
- Microserviços adicionais
- Event sourcing
- CQRS

---

## 📊 Métricas de Sucesso

### MVP (Fase 1-4)
- 🟡 62% das funcionalidades backend core implementadas
- 🟡 44% das funcionalidades frontend implementadas
- 🎯 80% de cobertura de testes
- 🎯 < 2s tempo de resposta médio
- 🎯 99% uptime
- 🎯 10 clientes beta ativos

### Progresso Atual (Maio 2026)
- ✅ API Gateway: 85% completo
- ✅ Clientes Backend: 90% completo
- ✅ Produtos Backend: 85% completo
- ✅ Estoque Backend: 90% completo
- ✅ Notificações: 75% completo
- 🔴 Vendas Backend: 5% completo
- 🔴 Financeiro Backend: 5% completo
- ✅ Frontend Infraestrutura: 90% completo
- ✅ Frontend Clientes: 85% completo
- ✅ Frontend Produtos: 80% completo
- 🔴 Frontend Estoque: 0% completo
- 🔴 Frontend Vendas: 0% completo
- 🔴 Frontend Financeiro: 0% completo

### Pós-MVP (Fase 5-6)
- 🎯 100 clientes ativos
- 🎯 NPS > 50
- 🎯 < 5% churn mensal
- 🎯 > 80% satisfação de usuários
- 🎯 < 1% taxa de bugs críticos

### Longo Prazo (2028+)
- 🎯 1.000+ clientes ativos
- 🎯 NPS > 70
- 🎯 < 2% churn mensal
- 🎯 > 90% satisfação de usuários
- 🎯 Líder de mercado no segmento

---

## 🔄 Processo de Atualização

Este roadmap é revisado e atualizado:
- **Mensalmente**: Ajustes de prioridades e prazos
- **Trimestralmente**: Revisão de fases e objetivos
- **Anualmente**: Planejamento estratégico de longo prazo

---

## 💡 Como Contribuir

Tem sugestões para o roadmap? 

1. Abra uma issue no GitHub com a tag `roadmap`
2. Descreva a funcionalidade ou melhoria
3. Explique o valor para os usuários
4. A equipe avaliará e priorizará

---

## 📞 Contato

Dúvidas sobre o roadmap?
- **Email**: product@denebcorp.com
- **Discord**: [Link do servidor]

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.1.0  
**Última Atualização**: 27 de Maio de 2026  
**Progresso Geral**: Backend 62% | Frontend 44% | Sistema 53%
