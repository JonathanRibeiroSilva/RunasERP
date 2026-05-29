# 🔮 Features Futuras - Runas ERP

> **Escopo**: Features de longo prazo planejadas para **após a conclusão do MVP**.  
> Para o status atual do desenvolvimento, sprints em andamento e regras de negócio, consulte o [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md).

**Última atualização**: 28/05/2026  
**Versão do MVP**: 1.0.0

---

## 📌 Contexto

O MVP do Runas ERP cobre os módulos essenciais:

```
API Gateway → Clientes → Produtos → Estoque → Vendas → Financeiro → Notificações
```

As features listadas aqui são planejadas para **após o MVP completo** e não bloqueiam nenhum módulo atual.

---

## 🚚 Módulo de Delivery

**Estimativa**: 60-80 horas  
**Dependências**: Vendas, Produtos, Notificações

### Funcionalidades
- Integração com marketplaces: iFood, Rappi, Uber Eats
- Painel unificado de pedidos delivery
- Rastreamento de entrega em tempo real
- Cálculo de frete (Correios + Google Maps)
- Notificações automáticas de status ao cliente

### Tecnologias
- Google Maps API (rastreamento e frete)
- Webhooks dos marketplaces (iFood, Rappi)
- WebSockets (rastreamento em tempo real)

---

## 🎁 Módulo de Fidelidade

**Estimativa**: 40-50 horas  
**Dependências**: Vendas, Clientes

### Funcionalidades
- Programa de pontos por compra (configurável por produto/categoria)
- Cashback com regras personalizadas
- Cupons de desconto (por cliente, por segmento, por data)
- Promoções personalizadas baseadas em histórico de compras
- Gamificação: níveis de cliente (Bronze, Prata, Ouro), badges

### Regras de Negócio
- Pontos expiram após X dias sem compra (configurável)
- Cashback só pode ser usado acima de valor mínimo de compra
- Cupons têm limite de uso e validade

---

## 📊 BI e Analytics

**Estimativa**: 60-80 horas  
**Dependências**: Todos os módulos do MVP

### Funcionalidades
- Data warehouse analítico (PostgreSQL separado, somente leitura)
- Pipeline ETL para consolidar dados dos serviços (Apache Airflow)
- Dashboards analíticos self-service (Metabase ou Apache Superset)
- Previsão de demanda com Machine Learning (Python + Scikit-learn)
- Análise de clientes: curva ABC, RFM (Recência, Frequência, Valor)
- Análise de produtos: giro, margem, sazonalidade

### Tecnologias
- Apache Airflow (orquestração de ETL)
- PostgreSQL (data warehouse)
- Metabase ou Apache Superset (BI)
- Python + Scikit-learn + Pandas (ML e análise)

---

## 🔗 Integrações Adicionais

**Estimativa**: 40-60 horas

| Integração | Finalidade | Prioridade |
|------------|-----------|-----------|
| **NF-e / NFC-e** | Emissão de nota fiscal eletrônica | Alta |
| **Conta Azul / Omie** | Sincronização contábil | Média |
| **Boletos bancários** | Itaú, Bradesco, BB via API | Média |
| **Stone / Cielo** | Maquininhas de cartão (além do Mercado Pago) | Média |
| **Correios** | Cálculo de frete e rastreamento de encomendas | Baixa |
| **API Aberta** | Integração com ERPs externos via REST | Baixa |

---

## 🏗️ Infraestrutura Avançada

**Estimativa**: 60 horas  
**Dependências**: MVP completo em produção estável

### Mensageria e Jobs
- **RabbitMQ**: Eventos assíncronos entre serviços
  - `venda.criada`, `venda.paga`, `venda.cancelada`
  - `estoque.baixo`, `estoque.zerado`, `lote.vencendo`
  - `conta.vencida`, `conta.recebida`
- **Celery + Celery Beat**: Jobs agendados
  - Lembretes de cobrança (3 dias antes do vencimento)
  - Relatórios automáticos diários/semanais
  - Limpeza de carrinhos abandonados

### Performance
- **PgBouncer**: Connection pooling para PostgreSQL em produção
- **Redis Cache**: Cache de queries frequentes e sessões
- **CDN**: Assets estáticos (imagens de produtos, frontend)

### Observabilidade
- **Prometheus + Grafana**: Métricas de performance e alertas
- **ELK Stack**: Logs centralizados (Elasticsearch, Logstash, Kibana)
- **Sentry**: Rastreamento de erros em produção

### CI/CD
- **GitHub Actions**: Pipeline de build, testes e deploy automatizado
- **Testes de carga**: k6 ou Locust (simular picos de uso)
- **Ambientes**: staging → produção com aprovação manual

---

## 📱 App Mobile

**Estimativa**: 120-150 horas  
**Dependências**: MVP completo + API estável

### Funcionalidades
- App para vendedores (Android e iOS)
- PDV mobile: criar vendas pelo celular
- Consulta de estoque e preços em tempo real
- Leitor de código de barras (câmera do celular)
- Modo offline: criar vendas sem internet, sincronizar depois
- Notificações push (pedidos, alertas de estoque)

### Tecnologias
- React Native + TypeScript
- Expo (build simplificado)
- AsyncStorage (dados offline)
- React Query (sincronização)
- Expo Camera (leitor de código de barras)

---

## 📅 Estimativa de Esforço

| Módulo | Horas | Dependências |
|--------|-------|-------------|
| Delivery | 60-80h | Vendas, Notificações |
| Fidelidade | 40-50h | Vendas, Clientes |
| BI e Analytics | 60-80h | MVP completo |
| Integrações Adicionais | 40-60h | Financeiro, Vendas |
| Infraestrutura Avançada | 60h | MVP em produção |
| App Mobile | 120-150h | MVP completo + API estável |
| **TOTAL** | **~380-480h** | — |

**Estimativa com 1 dev full-time**: ~3-4 meses após o MVP

---

## 🔗 Documentos Relacionados

- [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md) — Status atual, sprints, regras de negócio
- [docs/01-visao-geral/roadmap.md](./docs/01-visao-geral/roadmap.md) — Visão geral do roadmap
- [docs/03-arquitetura/](./docs/03-arquitetura/) — Arquitetura e diagramas

---

<div align="center">

**[⬆ Voltar ao topo](#-features-futuras---runas-erp)**

Desenvolvido por **Equipe DenebCorp**

</div>
