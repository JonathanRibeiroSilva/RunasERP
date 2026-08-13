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

#### Serviço de Produtos (95% completo)
- ✅ CRUD de produtos
- ✅ CRUD de categorias
- ✅ Sistema de variantes
- ✅ Atributos de variantes
- ✅ Cálculo de markup
- ✅ Soft delete
- ✅ Transações ACID
- ✅ Multi-tenancy 100%
- ✅ Loja online (API pública)
- ✅ Gestão de fornecedores
- ✅ Upload de fotos
- 🚧 Histórico de preços
- 🚧 Produtos compostos (kits)
- 🚧 Testes unitários

#### Serviço de Estoque (95% completo)
- ✅ Controle de estoque
- ✅ Movimentações (entrada, saída, ajuste, devolução, perda)
- ✅ Gestão de lotes
- ✅ Inventário físico
- ✅ Estoque mínimo/máximo
- ✅ Reserva de estoque
- ✅ Localização física
- ✅ Transações ACID
- ✅ Multi-tenancy 100%
- ✅ Integração com Vendas (reserva/baixa automática)
- ✅ Relatórios (geral, movimentações, baixo, zerado)
- 🚧 Notificações automáticas (estoque baixo, lotes vencendo)
- 🚧 Bloqueio de lotes vencidos
- 🚧 FIFO/FEFO
- 🚧 Testes unitários

#### Serviço de Vendas (90% completo)
- ✅ Modelos completos (Venda, ItemVenda, PagamentoVenda, ReservaEstoqueVenda)
- ✅ CRUD de vendas completo
- ✅ Workflow completo (6 estados)
- ✅ Múltiplas formas de pagamento
- ✅ Validação de crédito
- ✅ Reserva/liberação/baixa de estoque (integração HTTP)
- ✅ Multi-tenancy 100% nativo
- ✅ Cliente opcional (vendas de balcão)
- ✅ Número de venda único por empresa
- ✅ Snapshot de dados do produto
- ✅ Migration completa
- ✅ Seed com 6 cenários
- 🚧 Integração com Financeiro (ContaReceber para FIADO)
- 🚧 Devolução (nova entidade)
- 🚧 Carrinho de compras (sessão para loja online)
- 🚧 Checkout (loja online)
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
**Progresso Geral**: 75% completo (↑13% - Multi-tenancy + Vendas implementados)

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
- ✅ Configuração Docker
- ✅ Cloudflare Tunnel para acesso externo
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
- ✅ Produtos (90% - falta histórico de preços, kits)
  - ✅ Lista com filtros
  - ✅ Cadastro
  - ✅ Edição
  - ✅ Detalhes
  - ✅ Gestão de variantes
  - ✅ Gestão de categorias
  - ✅ Upload de fotos
  - ✅ Gestão de fornecedores
  - 🚧 Histórico de preços
  - 🚧 Produtos compostos (kits)
- 🟡 Loja Online / E-commerce (50%)
  - ✅ Vitrine de produtos (lista pública)
  - ✅ Detalhes do produto
  - ✅ Filtros e busca
  - ✅ Design responsivo
  - ✅ Compartilhamento (WhatsApp, link)
  - 🚧 Carrinho de compras
  - 🚧 Checkout
  - 🚧 Área do cliente
  - 🚧 Rastreamento de pedidos
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
**Progresso Geral**: 52% completo (↑8% - Loja Online iniciada)

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

### Progresso Atual (Junho 2026)
- ✅ API Gateway: 85% completo
- ✅ Clientes Backend: 90% completo
- ✅ Produtos Backend: 95% completo (↑10% - Multi-tenancy, fornecedores, fotos)
- ✅ Estoque Backend: 95% completo (↑5% - Multi-tenancy, integração Vendas)
- ✅ Vendas Backend: 90% completo (↑85% - Implementação completa)
- ✅ Notificações: 75% completo
- 🔴 Financeiro Backend: 0% completo
- ✅ Frontend Infraestrutura: 90% completo
- ✅ Frontend Clientes: 85% completo
- ✅ Frontend Produtos: 90% completo (↑10%)
- 🟡 Frontend Loja Online: 50% completo (↑50% - Vitrine implementada)
- 🔴 Frontend Estoque: 0% completo
- 🔴 Frontend Vendas: 0% completo
- 🔴 Frontend Financeiro: 0% completo

**Destaques da Última Atualização (09/06/2026)**:
- ✅ Multi-tenancy 100% implementado em Produtos, Estoque, Vendas
- ✅ Serviço de Vendas implementado completamente do zero (~2.620 linhas)
- ✅ Workflow de vendas: 6 estados com transições automáticas
- ✅ Integração Vendas ↔ Estoque (reserva, liberação, baixa automáticas)
- ✅ Loja Online: Vitrine pública de produtos implementada
- ✅ 4 commits de funcionalidades (Produtos, Estoque, Vendas multi-tenancy, bug fix)

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
**Versão:** 1.2.0  
**Última Atualização**: 09 de Junho de 2026  
**Progresso Geral**: Backend 75% | Frontend 52% | Sistema 64%  
**Commits Recentes**: 5 (Multi-tenancy Produtos, Estoque, Vendas + Checklist atualizado + Bug fix catálogo)
