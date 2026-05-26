# 🚀 Features Futuras - ERP Runas

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0-MVP

---

## 📊 Status Atual do Projeto

### ✅ Stacks Implementadas (100%)

| Stack | Status | Endpoints | Descrição |
|-------|--------|-----------|-----------|
| **API Gateway** | 🟢 100% | 15 | Autenticação JWT, RBAC, Proxy, Rate Limiting, Blacklist |
| **Serviço de Clientes** | 🟢 100% | 12 | CRUD de clientes (PF/PJ), endereços, crédito, validações |
| **Serviço de Produtos** | 🟢 100% | 25 | CRUD de produtos, categorias, variantes, fornecedores, catálogo |
| **Serviço de Estoque** | 🟢 100% | 18 | Controle de estoque, movimentações, lotes, inventário, reservas |

**Total Implementado**: 70 endpoints | ~15.000 linhas de código

### 🔴 Stacks NÃO Implementadas (Apenas Estrutura Base)

| Stack | Status | Descrição |
|-------|--------|-----------|
| **Serviço de Vendas** | 🔴 5% | Apenas estrutura base (Dockerfile, config, database, main.py com health check) |
| **Serviço Financeiro** | 🔴 5% | Apenas estrutura base (Dockerfile, config, database, main.py com health check) |
| **Serviço de Notificações** | 🔴 5% | Apenas estrutura base (Dockerfile, config, database, main.py com health check) |

**Estrutura base inclui**: Dockerfile, config.py, database.py, main.py (apenas health check), requirements.txt, alembic.ini  
**Faltam**: Modelos, Schemas, Repositories, Services, Routers (endpoints funcionais)

---

## 🔨 Stacks em Desenvolvimento

### 1. 🏭 Serviço de Estoque

**Prioridade**: 🔴 ALTA (Próximo na fila)  
**Status**: 🟡 5% (Estrutura base criada)  
**Estimativa**: 40-50 horas

#### Funcionalidades Planejadas

##### Modelos de Dados
- **Estoque**: Controle de quantidade por produto/variante
- **Movimentação**: Histórico de entradas e saídas
- **Lote**: Controle de lotes com validade
- **Inventário**: Contagens e ajustes de estoque

##### Endpoints Planejados (~15 endpoints)

**Gestão de Estoque**
- `GET /estoque` - Listar estoque de todos os produtos
- `GET /estoque/{produto_id}` - Consultar estoque de um produto
- `GET /estoque/baixo` - Produtos com estoque baixo (alerta)
- `GET /estoque/zerado` - Produtos sem estoque
- `PUT /estoque/{produto_id}/minimo` - Definir estoque mínimo

**Movimentações**
- `POST /movimentacoes/entrada` - Registrar entrada de estoque
- `POST /movimentacoes/saida` - Registrar saída de estoque
- `GET /movimentacoes` - Listar movimentações (com filtros)
- `GET /movimentacoes/{id}` - Detalhes de uma movimentação
- `GET /movimentacoes/produto/{produto_id}` - Histórico por produto

**Lotes**
- `POST /lotes` - Criar lote
- `GET /lotes` - Listar lotes
- `GET /lotes/vencendo` - Lotes próximos do vencimento
- `GET /lotes/{id}` - Detalhes de um lote

**Inventário**
- `POST /inventario` - Iniciar contagem de inventário
- `PUT /inventario/{id}/ajustar` - Ajustar estoque após contagem

#### Integrações
- ✅ Integração com **Serviço de Produtos** (consulta de produtos)
- ✅ Integração com **Serviço de Vendas** (baixa automática)
- ✅ Eventos RabbitMQ: `estoque.baixo`, `estoque.zerado`, `lote.vencendo`
- ✅ Notificações automáticas via WhatsApp

#### Regras de Negócio
- ✅ Estoque não pode ficar negativo
- ✅ Alerta quando estoque atingir o mínimo
- ✅ Controle de lotes FIFO (First In, First Out)
- ✅ Bloqueio de vendas quando estoque zerado
- ✅ Reserva de estoque durante checkout

---

### 2. 🛒 Serviço de Vendas

**Prioridade**: 🔴 ALTA  
**Status**: 🟡 5% (Estrutura base criada)  
**Estimativa**: 60-70 horas

#### Funcionalidades Planejadas

##### Modelos de Dados
- **Carrinho**: Carrinho de compras temporário
- **Venda**: Pedido finalizado
- **ItemVenda**: Produtos do pedido
- **Pagamento**: Dados de pagamento
- **StatusVenda**: Pendente, Pago, Cancelado, Entregue

##### Endpoints Planejados (~20 endpoints)

**Carrinho de Compras**
- `POST /carrinho` - Criar carrinho
- `GET /carrinho/{token}` - Consultar carrinho
- `POST /carrinho/{token}/item` - Adicionar item
- `PUT /carrinho/{token}/item/{item_id}` - Atualizar quantidade
- `DELETE /carrinho/{token}/item/{item_id}` - Remover item
- `DELETE /carrinho/{token}` - Limpar carrinho
- `GET /carrinho/{token}/total` - Calcular total

**Checkout e Pagamento**
- `POST /carrinho/{token}/checkout` - Finalizar compra
- `POST /vendas/{id}/pagamento/pix` - Gerar PIX (Mercado Pago)
- `POST /vendas/{id}/pagamento/fiado` - Venda fiada
- `POST /vendas/{id}/pagamento/dinheiro` - Pagamento em dinheiro
- `POST /vendas/{id}/pagamento/cartao` - Pagamento em cartão

**Gestão de Vendas**
- `GET /vendas` - Listar vendas (com filtros)
- `GET /vendas/{id}` - Detalhes de uma venda
- `GET /vendas/cliente/{cliente_id}` - Vendas de um cliente
- `PUT /vendas/{id}/status` - Atualizar status
- `POST /vendas/{id}/cancelar` - Cancelar venda
- `GET /vendas/relatorio/diario` - Relatório de vendas do dia
- `GET /vendas/relatorio/periodo` - Relatório por período

**Webhooks**
- `POST /webhooks/mercadopago` - Webhook do Mercado Pago

#### Integrações
- ✅ Integração com **Mercado Pago** (PIX)
- ✅ Integração com **Serviço de Clientes** (crédito fiado)
- ✅ Integração com **Serviço de Produtos** (preços e dados)
- ✅ Integração com **Serviço de Estoque** (baixa automática)
- ✅ Integração com **Serviço Financeiro** (contas a receber)
- ✅ Eventos RabbitMQ: `venda.criada`, `venda.paga`, `venda.cancelada`

#### Regras de Negócio
- ✅ Validar estoque antes de finalizar venda
- ✅ Reservar estoque durante checkout (15 minutos)
- ✅ Verificar limite de crédito para vendas fiadas
- ✅ Gerar conta a receber para vendas fiadas
- ✅ Baixa automática no estoque após pagamento confirmado
- ✅ Cancelamento de venda devolve estoque
- ✅ Notificação automática ao cliente após venda

---

### 3. 💰 Serviço Financeiro

**Prioridade**: 🟡 MÉDIA  
**Status**: 🟡 5% (Estrutura base criada)  
**Estimativa**: 50-60 horas

#### Funcionalidades Planejadas

##### Modelos de Dados
- **ContaReceber**: Contas a receber de clientes
- **ContaPagar**: Contas a pagar a fornecedores
- **Pagamento**: Registro de pagamentos
- **FluxoCaixa**: Movimentações de caixa
- **CategoriaFinanceira**: Categorias de receitas/despesas

##### Endpoints Planejados (~18 endpoints)

**Contas a Receber**
- `GET /contas-receber` - Listar contas a receber
- `GET /contas-receber/{id}` - Detalhes de uma conta
- `GET /contas-receber/vencidas` - Contas vencidas
- `GET /contas-receber/vencendo` - Contas vencendo (próximos 7 dias)
- `GET /contas-receber/cliente/{cliente_id}` - Contas de um cliente
- `POST /contas-receber/{id}/receber` - Registrar recebimento
- `POST /contas-receber/{id}/parcelar` - Parcelar conta

**Contas a Pagar**
- `POST /contas-pagar` - Criar conta a pagar
- `GET /contas-pagar` - Listar contas a pagar
- `GET /contas-pagar/{id}` - Detalhes de uma conta
- `GET /contas-pagar/vencidas` - Contas vencidas
- `GET /contas-pagar/vencendo` - Contas vencendo
- `POST /contas-pagar/{id}/pagar` - Registrar pagamento

**Fluxo de Caixa**
- `GET /fluxo-caixa/hoje` - Fluxo de caixa do dia
- `GET /fluxo-caixa/periodo` - Fluxo por período
- `GET /fluxo-caixa/saldo` - Saldo atual
- `POST /fluxo-caixa/entrada` - Registrar entrada manual
- `POST /fluxo-caixa/saida` - Registrar saída manual

#### Integrações
- ✅ Integração com **Serviço de Vendas** (criar contas a receber)
- ✅ Integração com **Serviço de Clientes** (atualizar crédito)
- ✅ Eventos RabbitMQ: `conta.vencida`, `conta.recebida`, `conta.paga`
- ✅ Notificações de cobrança via WhatsApp

#### Regras de Negócio
- ✅ Criar conta a receber automaticamente para vendas fiadas
- ✅ Atualizar crédito do cliente após recebimento
- ✅ Bloquear cliente com contas vencidas
- ✅ Enviar lembrete de cobrança 3 dias antes do vencimento
- ✅ Enviar notificação de vencimento no dia
- ✅ Calcular juros e multa para pagamentos em atraso
- ✅ Gerar relatórios financeiros automáticos

---

### 4. 📱 Serviço de Notificações

**Prioridade**: 🟡 MÉDIA  
**Status**: 🟡 5% (Estrutura base criada)  
**Estimativa**: 30-40 horas

#### Funcionalidades Planejadas

##### Modelos de Dados
- **Notificacao**: Registro de notificações enviadas
- **Template**: Templates de mensagens
- **Fila**: Fila de envio
- **Log**: Log de envios (sucesso/falha)

##### Endpoints Planejados (~10 endpoints)

**Envio de Notificações**
- `POST /notificacoes/whatsapp` - Enviar WhatsApp
- `POST /notificacoes/email` - Enviar email
- `POST /notificacoes/sms` - Enviar SMS

**Gestão de Templates**
- `GET /templates` - Listar templates
- `POST /templates` - Criar template
- `PUT /templates/{id}` - Atualizar template
- `DELETE /templates/{id}` - Deletar template

**Histórico e Logs**
- `GET /notificacoes` - Listar notificações enviadas
- `GET /notificacoes/{id}` - Detalhes de uma notificação
- `GET /notificacoes/logs` - Logs de envio

#### Integrações
- ✅ **Evolution API** (WhatsApp)
- ✅ **SMTP** (Email)
- ✅ **Twilio** (SMS - opcional)
- ✅ Consumer RabbitMQ para processar eventos
- ✅ Celery para envios agendados

#### Tipos de Notificações
- ✅ Confirmação de pedido
- ✅ Pagamento confirmado
- ✅ Pedido em separação
- ✅ Pedido saiu para entrega
- ✅ Pedido entregue
- ✅ Lembrete de cobrança (3 dias antes)
- ✅ Notificação de vencimento
- ✅ Conta vencida
- ✅ Estoque baixo (para admin)
- ✅ Lote vencendo (para admin)

#### Regras de Negócio
- ✅ Fila de envio com retry automático
- ✅ Limite de envios por minuto (rate limiting)
- ✅ Blacklist de números bloqueados
- ✅ Templates personalizáveis
- ✅ Variáveis dinâmicas nos templates
- ✅ Agendamento de envios
- ✅ Relatório de envios

---

## 🎯 Roadmap de Implementação

### Q2 2026 (Maio - Junho)

**Semana 1-2**: Serviço de Estoque
- [ ] Implementar modelos de dados
- [ ] Criar repositories e services
- [ ] Implementar endpoints de estoque
- [ ] Implementar controle de lotes
- [ ] Integrar com Produtos
- [ ] Testes unitários

**Semana 3-4**: Serviço de Vendas (Parte 1)
- [ ] Implementar modelos de dados
- [ ] Criar carrinho de compras
- [ ] Implementar checkout
- [ ] Integrar com Estoque
- [ ] Integrar com Clientes

### Q3 2026 (Julho - Setembro)

**Semana 1-2**: Serviço de Vendas (Parte 2)
- [ ] Integrar Mercado Pago (PIX)
- [ ] Implementar webhooks
- [ ] Implementar vendas fiadas
- [ ] Relatórios de vendas
- [ ] Testes unitários

**Semana 3-4**: Serviço Financeiro
- [ ] Implementar modelos de dados
- [ ] Criar contas a receber/pagar
- [ ] Implementar fluxo de caixa
- [ ] Integrar com Vendas
- [ ] Relatórios financeiros
- [ ] Testes unitários

**Semana 5-6**: Serviço de Notificações
- [ ] Implementar modelos de dados
- [ ] Integrar Evolution API
- [ ] Criar templates de mensagens
- [ ] Implementar fila de envio
- [ ] Consumer RabbitMQ
- [ ] Jobs Celery
- [ ] Testes unitários

### Q4 2026 (Outubro - Dezembro)

**Melhorias e Otimizações**
- [ ] Testes de integração completos
- [ ] Testes de carga
- [ ] Otimização de performance
- [ ] Documentação completa
- [ ] CI/CD pipeline
- [ ] Monitoramento (Prometheus + Grafana)
- [ ] Logs centralizados (ELK Stack)

---

## 🔮 Features Futuras (Longo Prazo)

### Dashboard Administrativo
**Estimativa**: 80-100 horas

- Interface web para administração
- Dashboard com métricas em tempo real
- Gráficos de vendas e estoque
- Relatórios customizáveis
- Gestão de usuários e permissões

**Tecnologias**:
- Frontend: React + TypeScript
- UI: Material-UI ou Ant Design
- Gráficos: Chart.js ou Recharts
- Estado: Redux ou Zustand

### App Mobile
**Estimativa**: 120-150 horas

- App para vendedores (Android/iOS)
- Consulta de produtos e estoque
- Criação de vendas offline
- Sincronização automática
- Notificações push

**Tecnologias**:
- React Native + TypeScript
- Expo
- AsyncStorage (offline)
- Push Notifications

### Módulo de Delivery
**Estimativa**: 60-80 horas

- Integração com iFood, Rappi, Uber Eats
- Gestão de pedidos delivery
- Rastreamento de entrega
- Cálculo de frete
- Integração com Google Maps

### Módulo de Fidelidade
**Estimativa**: 40-50 horas

- Programa de pontos
- Cashback
- Cupons de desconto
- Promoções personalizadas
- Gamificação

### Módulo de BI e Analytics
**Estimativa**: 60-80 horas

- Data warehouse
- ETL de dados
- Dashboards analíticos
- Previsão de vendas (ML)
- Análise de comportamento

**Tecnologias**:
- Apache Airflow (ETL)
- PostgreSQL (Data Warehouse)
- Metabase ou Superset (BI)
- Python + Scikit-learn (ML)

### Integrações Adicionais
**Estimativa**: 40-60 horas

- **Contabilidade**: Integração com Conta Azul, Omie
- **Nota Fiscal**: Emissão de NF-e, NFC-e
- **Boletos**: Integração com bancos
- **Cartões**: Integração com Stone, Cielo
- **ERP Externo**: API para integração com outros sistemas

---

## 📊 Estimativa Total de Horas

| Fase | Horas | Status |
|------|-------|--------|
| **MVP Atual** | 125h | ✅ Concluído |
| **Serviço de Estoque** | 50h | 🔴 Próximo |
| **Serviço de Vendas** | 70h | 🔴 Planejado |
| **Serviço Financeiro** | 60h | 🟡 Planejado |
| **Serviço de Notificações** | 40h | 🟡 Planejado |
| **Testes e Otimizações** | 60h | 🟡 Planejado |
| **Dashboard Web** | 100h | ⚪ Futuro |
| **App Mobile** | 150h | ⚪ Futuro |
| **Módulos Extras** | 200h | ⚪ Futuro |
| **TOTAL** | **855h** | - |

**Tempo estimado com 1 dev full-time**: ~5-6 meses para MVP completo

---

## 🎯 Priorização

### Prioridade ALTA (Essencial para MVP)
1. ✅ API Gateway (Concluído)
2. ✅ Serviço de Clientes (Concluído)
3. ✅ Serviço de Produtos (Concluído)
4. 🔴 Serviço de Estoque
5. 🔴 Serviço de Vendas

### Prioridade MÉDIA (Importante)
6. 🟡 Serviço Financeiro
7. 🟡 Serviço de Notificações
8. 🟡 Testes Unitários (80% coverage)

### Prioridade BAIXA (Desejável)
9. ⚪ Dashboard Web
10. ⚪ CI/CD Pipeline
11. ⚪ Monitoramento
12. ⚪ App Mobile

### Prioridade FUTURA (Longo Prazo)
13. ⚪ Módulo de Delivery
14. ⚪ Módulo de Fidelidade
15. ⚪ BI e Analytics
16. ⚪ Integrações Adicionais

---

## 📝 Notas Importantes

### Dependências entre Serviços

```
API Gateway (✅)
    ↓
Clientes (✅) + Produtos (✅)
    ↓
Estoque (🔴) ← Depende de Produtos
    ↓
Vendas (🔴) ← Depende de Clientes, Produtos, Estoque
    ↓
Financeiro (🟡) ← Depende de Vendas, Clientes
    ↓
Notificações (🟡) ← Depende de todos os anteriores
```

### Tecnologias Adicionais Necessárias

- **Celery**: Para jobs agendados (cobranças, relatórios)
- **Celery Beat**: Para agendamento de tasks
- **Redis**: Para cache e fila do Celery
- **RabbitMQ**: Para eventos entre serviços
- **Prometheus**: Para métricas
- **Grafana**: Para dashboards de monitoramento
- **ELK Stack**: Para logs centralizados (opcional)

---

## 🤝 Contribuindo

Para sugerir novas features:
1. Abra uma issue no repositório
2. Descreva a feature detalhadamente
3. Justifique a necessidade
4. Aguarde análise da equipe

---

## 📞 Contato

Para dúvidas sobre o roadmap:
- **Email**: dev@runas.com
- **Documentação**: [docs/](./docs/)

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0-MVP  
**Próxima revisão**: 2026-06-01

---

<div align="center">

**[⬆ Voltar ao topo](#-features-futuras---erp-runas)**

Feito com ❤️ pela equipe **Runas**

</div>
