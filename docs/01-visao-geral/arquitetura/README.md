# Arquitetura do Runas

> **Documentação técnica completa** da arquitetura de microsserviços do MVP do Runas

---

## 📚 Índice da Documentação

Esta seção contém a especificação técnica completa do backend do Runas, dividida em módulos para facilitar a navegação:

### 1. [Visão Geral](./visao-geral.md)
- Contexto geral do projeto
- Stack tecnológica obrigatória
- Estrutura de pastas e organização
- Arquitetura de microsserviços

### 2. [Microsserviços](./microsservicos.md)
- **API Gateway** - Autenticação, roteamento, rate limiting
- **Serviço de Clientes** - Gestão de clientes, endereços, crédito
- **Serviço de Produtos** - Produtos, variantes, catálogo, fornecedores
- **Serviço de Estoque** - Controle de estoque e movimentações
- **Serviço de Vendas** - Carrinho, checkout, pedidos, pagamentos
- **Serviço Financeiro** - Contas a receber, pagamentos fiados
- **Serviço de Notificações** - WhatsApp via Evolution API

### 3. [Tecnologias e Padrões](./tecnologias.md)
- Docker Compose completo
- Configuração de ambiente (.env)
- Padrões de código obrigatórios
- Testes automatizados
- Automação de migrations e seed
- pgAdmin pré-configurado
- Makefile com comandos úteis
- Restrições e observações finais

---

## 🎯 Objetivo desta Documentação

Este conjunto de documentos serve como **prompt técnico completo** para implementação do MVP do Runas. Cada arquivo contém especificações detalhadas, modelos de dados, endpoints, regras de negócio e padrões de código que devem ser seguidos rigorosamente.

---

## 🚀 Quick Start

Para começar a implementação:

1. Leia a [Visão Geral](./visao-geral.md) para entender o contexto e a stack
2. Consulte [Microsserviços](./microsservicos.md) para detalhes de cada serviço
3. Siga os padrões em [Tecnologias e Padrões](./tecnologias.md) para implementação

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
