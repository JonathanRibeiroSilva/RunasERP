# 🎯 Visão Geral - Runas

Bem-vindo à documentação do **Runas**, um sistema de gestão empresarial moderno e acessível para pequenos comércios.

---

## 📖 Sobre o Projeto

O Runas é um ERP (Enterprise Resource Planning) desenvolvido especificamente para atender as necessidades de pequenos comércios brasileiros. O sistema oferece uma solução completa e integrada para gestão de:

- 👥 **Clientes** - Cadastro, crédito e histórico
- 📦 **Produtos** - Catálogo, variantes e fornecedores
- 📊 **Estoque** - Controle, movimentações e lotes
- 🛒 **Vendas** - Carrinho, pedidos e pagamentos
- 💰 **Financeiro** - Contas a receber e vendas fiadas
- 📱 **Notificações** - WhatsApp via Evolution API

---

## 🎯 Objetivos

### Simplicidade
- Interface intuitiva e fácil de usar
- Processos diretos sem complexidade desnecessária
- Onboarding rápido para novos usuários

### Acessibilidade
- Solução de baixo custo
- Hospedagem flexível (local ou nuvem)
- Sem dependência de internet para operações básicas

### Controle
- Rastreabilidade completa de operações
- Relatórios e dashboards em tempo real
- Auditoria de todas as ações

### Flexibilidade
- Adaptável a diferentes tipos de negócio
- Configurável sem necessidade de código
- Integrações com serviços externos

---

## 🏗️ Arquitetura

O Runas utiliza uma **arquitetura de microserviços** moderna e escalável:

```
Frontend (React) → API Gateway (FastAPI) → Microserviços (Python)
                                          ↓
                                    PostgreSQL + Redis + RabbitMQ
```

### Componentes Principais

- **Frontend**: React + TypeScript + Tailwind CSS
- **API Gateway**: FastAPI com autenticação JWT
- **Microserviços**: 6 serviços independentes em Python
- **Banco de Dados**: PostgreSQL (1 banco por serviço)
- **Cache**: Redis para sessões e rate limiting
- **Mensageria**: RabbitMQ para eventos assíncronos
- **Notificações**: Evolution API para WhatsApp

---

## 🚀 Tecnologias

### Backend
- **Python 3.11+** - Linguagem principal
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **Alembic** - Migrações de banco
- **Pydantic** - Validação de dados
- **Celery** - Tarefas assíncronas
- **Pytest** - Testes automatizados

### Frontend
- **React 18** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Vite** - Build tool
- **Tailwind CSS** - Framework CSS
- **React Router** - Roteamento
- **Axios** - Cliente HTTP

### Infraestrutura
- **Docker** - Containerização
- **Docker Compose** - Orquestração
- **PostgreSQL 15** - Banco de dados
- **Redis 7** - Cache e sessões
- **RabbitMQ 3** - Mensageria
- **Nginx** - Proxy reverso

### Integrações
- **Mercado Pago** - Pagamentos PIX
- **Evolution API** - WhatsApp
- **OAuth2** - Google e Microsoft

---

## 📊 Status do Projeto

**Versão Atual**: 1.0.0 (MVP)  
**Data de Lançamento**: Maio de 2026  
**Status**: Em Desenvolvimento

### Progresso Geral

| Componente | Status | Progresso |
|------------|--------|-----------|
| Infraestrutura | ✅ Completo | 100% |
| API Gateway | 🟡 Em Progresso | 70% |
| Clientes | 🔴 Planejado | 5% |
| Produtos | 🔴 Planejado | 5% |
| Estoque | 🔴 Planejado | 5% |
| Vendas | 🔴 Planejado | 5% |
| Financeiro | 🔴 Planejado | 5% |
| Notificações | 🔴 Planejado | 5% |
| Frontend | 🟡 Em Progresso | 40% |
| Documentação | 🟡 Em Progresso | 60% |

---

## 👥 Equipe

**Desenvolvido por**: Equipe DenebCorp  
**Contato**: [contato@denebcorp.com](mailto:contato@denebcorp.com)

---

## 📚 Documentos Relacionados

- **[Arquitetura Completa](./arquitetura/)** - Especificação técnica detalhada dos microsserviços
  - [Visão Geral](./arquitetura/visao-geral.md)
  - [Microsserviços](./arquitetura/microsservicos.md)
  - [Tecnologias e Padrões](./arquitetura/tecnologias.md)
- [Status do Projeto](./status-projeto.md)
- [Glossário](./glossario.md) - Termos técnicos e conceitos
- [FAQ](./faq.md) - Perguntas frequentes
- [Roadmap](./roadmap.md) - Planejamento de desenvolvimento

---

## 🚀 Próximos Passos

1. **Completar API Gateway** - Roteamento e testes
2. **Implementar Clientes** - CRUD completo
3. **Implementar Produtos** - Catálogo e variantes
4. **Implementar Estoque** - Controle e movimentações
5. **Implementar Vendas** - Carrinho e checkout
6. **Implementar Financeiro** - Contas a receber
7. **Implementar Notificações** - WhatsApp
8. **Frontend Completo** - Todas as telas
9. **Testes** - Cobertura 100%
10. **Deploy** - Produção

---

## 📄 Licença

Este projeto está sob licença proprietária da DenebCorp.  
Todos os direitos reservados © 2026 DenebCorp.

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0  
**Autor**: Equipe DenebCorp
