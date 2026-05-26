# 📚 Documentação - Runas

Bem-vindo à documentação completa do **Runas**, um sistema de gestão empresarial moderno e acessível para pequenos comércios.

## 🗂️ Índice da Documentação

### 📖 [01. Visão Geral](./01-visao-geral/)
Entenda o projeto, sua arquitetura e tecnologias utilizadas.
- [Sobre o Projeto](./01-visao-geral/README.md)
- [Arquitetura](./01-visao-geral/arquitetura/)
- [Glossário](./01-visao-geral/glossario.md)
- [FAQ](./01-visao-geral/faq.md)
- [Roadmap](./01-visao-geral/roadmap.md)
- [Status do Projeto](./01-visao-geral/status-projeto.md)

### 🔧 [02. Setup e Instalação](./02-setup/)
Guias para configurar o ambiente de desenvolvimento.
- [Guia de Setup](./02-setup/README.md)
- [Requisitos](./02-setup/requisitos.md)
- [Tecnologias](./02-setup/tecnologias.md)
- [Troubleshooting](./02-setup/troubleshooting.md)

### 🏗️ [03. Arquitetura](./03-arquitetura/)
Arquitetura detalhada do sistema.
- [Visão Geral](./03-arquitetura/README.md)
- [Comunicação entre Serviços](./03-arquitetura/comunicacao.md)
- [Diagramas](./03-arquitetura/diagramas/)

### ⚙️ [04. Backend](./04-backend/)
Documentação dos serviços backend.
- [API Gateway](./04-backend/api-gateway/)
- [Microserviços](./04-backend/servicos/)
- [Integrações Externas](./04-backend/integracao/)

### 🎨 [05. Frontend](./05-frontend/)
Documentação do frontend React.
- [Visão Geral](./05-frontend/README.md)
- [Setup](./05-frontend/setup/)
- [Design System](./05-frontend/design/)
- [OAuth](./05-frontend/oauth/)
- [Guias](./05-frontend/guias/)
- [Deployment](./05-frontend/deployment/)

### 👨‍💻 [07. Desenvolvimento](./07-desenvolvimento/)
Guias para desenvolvedores.
- [Guia de Implementação](./07-desenvolvimento/guia-implementacao.md)

### 🔧 [09. Troubleshooting](./09-troubleshooting/)
Resolução de problemas comuns.
- [Problemas com OAuth](./09-troubleshooting/oauth-issues.md)
- [Problemas com Docker](./09-troubleshooting/docker-issues.md)

### 📡 [10. Referência de APIs](./10-api-reference/)
Documentação completa das APIs (~3.271 linhas).
- [Visão Geral](./10-api-reference/README.md)
- [API de Clientes](./10-api-reference/clientes-api.md) (236 linhas)
- [API de Produtos](./10-api-reference/produtos-api.md) (510 linhas)
- [API de Estoque](./10-api-reference/estoque-api.md) (291 linhas)
- [API de Vendas](./10-api-reference/vendas-api.md) (573 linhas)
- [API Financeiro](./10-api-reference/financeiro-api.md) (439 linhas)
- [Guia de Autenticação](./10-api-reference/guia-autenticacao.md) (334 linhas)
- [Exemplos Práticos](./10-api-reference/exemplos-praticos.md) (400 linhas)
- [OpenAPI Specification](./10-api-reference/openapi.yaml)

### 📋 [11. Regras de Negócio](./11-regras-negocio/)
Regras de negócio do sistema.
- [Clientes](./11-regras-negocio/clientes.md)
- [Produtos](./11-regras-negocio/produtos.md)
- [Vendas](./11-regras-negocio/vendas.md)
- [Estoque](./11-regras-negocio/estoque.md)
- [Financeiro](./11-regras-negocio/financeiro.md)

### 📝 [12. Changelog](./12-changelog/)
Histórico de versões e mudanças.
- [Changelog Completo](./12-changelog/CHANGELOG.md)
- [Versão 1.0.0 (MVP)](./12-changelog/v1.0.0.md)

---

## 🚀 Quick Start

Se você é novo no projeto, comece por aqui:

1. **[Visão Geral](./01-visao-geral/README.md)** - Entenda o que é o Runas
2. **[Requisitos](./02-setup/requisitos.md)** - Verifique os pré-requisitos
3. **[Setup](./02-setup/README.md)** - Configure o ambiente
4. **[Quick Start Guide](../QUICK-START.md)** - Comece a usar em 5 minutos

## 🆘 Precisa de Ajuda?

- **Problemas comuns?** Veja [Troubleshooting](./09-troubleshooting/)
- **Dúvidas sobre APIs?** Consulte [Referência de APIs](./10-api-reference/)
- **Quer contribuir?** Leia [Como Contribuir](../CONTRIBUTING.md)

## 📦 Estrutura do Projeto

```
RunasERP/
├── api-gateway/          # API Gateway (FastAPI)
├── services/             # Microserviços
│   ├── clientes/
│   ├── produtos/
│   ├── estoque/
│   ├── vendas/
│   ├── financeiro/
│   └── notificacoes/
├── frontend/             # Frontend (React + TypeScript)
├── nginx/                # Configuração Nginx
├── shared/               # Código compartilhado
├── tests/                # Testes
└── docs/                 # Documentação (você está aqui!)
```

## 📊 Estatísticas da Documentação

| Seção | Arquivos | Descrição |
|-------|----------|-----------|
| 01-visao-geral | 6 | Visão geral, arquitetura, glossário, FAQ, roadmap |
| 02-setup | 4 | Guias de instalação e configuração |
| 03-arquitetura | 3+ | Arquitetura e diagramas de sequência |
| 04-backend | Múltiplos | Documentação dos microserviços |
| 05-frontend | Múltiplos | Documentação do frontend React |
| 07-desenvolvimento | 1 | Guias para desenvolvedores |
| 09-troubleshooting | 2 | Resolução de problemas |
| 10-api-reference | 9 | ~3.271 linhas de documentação de APIs |
| 11-regras-negocio | 5 | Regras de negócio por domínio |
| 12-changelog | 3 | Histórico de versões |
| **TOTAL** | **~40+** | Documentação completa e organizada |

## 📦 Arquivo

Documentos obsoletos e versões antigas foram movidos para [`_archive/`](./_archive/README.md).

## 🔗 Links Úteis

- [README Principal](../README.md)
- [Quick Start](../QUICK-START.md)
- [Como Contribuir](../CONTRIBUTING.md)
- [Licença](../LICENSE.md)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Última atualização:** 26 de Maio de 2026  
**Versão:** 1.0.0
