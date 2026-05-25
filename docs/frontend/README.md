# 🎨 Frontend - ERP Runas

> Documentação completa do frontend web do ERP Runas

---

## 📚 Documentação

### ⭐ [IMPLEMENTATION-LOG.md](./IMPLEMENTATION-LOG.md) - **LOG DE IMPLEMENTAÇÃO**
Registro detalhado do progresso da implementação, decisões técnicas e próximos passos.

### 📋 [REQUIREMENTS.md](./REQUIREMENTS.md)
Especificação completa de requisitos funcionais e não funcionais do frontend.

**Conteúdo:**
- Requisitos funcionais (RF-001 a RF-009)
- Requisitos não funcionais (performance, segurança, acessibilidade)
- Regras de negócio
- Integrações com backend
- Critérios de aceitação

### 🏗️ [DESIGN.md](./DESIGN.md)
Arquitetura e design técnico da aplicação frontend.

**Conteúdo:**
- Tech stack (React, TypeScript, Bootstrap, React Query)
- Arquitetura de componentes
- Estrutura de pastas completa
- Padrões de código (Auth, API, Forms)
- UI/UX design (cores, tipografia, responsividade)
- Performance e segurança
- Estratégia de testes

### 🎨 [DESIGN-SYSTEM.md](./DESIGN-SYSTEM.md)
Sistema de design completo com identidade visual Runas.

**Conteúdo:**
- Paleta de cores (Dark Mode First)
- Filosofia visual (clareza, inteligência, controle)
- Tipografia e espaçamento
- Componentes (botões, cards, inputs, modais, tabelas, badges)
- Glassmorphism e gradientes (uso sutil)
- Sombras e transições
- Acessibilidade (WCAG AA)
- Exemplos de uso correto e incorreto

### ✅ [TASKS.md](./TASKS.md)
Plano de implementação com tarefas detalhadas.

**Conteúdo:**
- 28 tarefas organizadas em 10 fases
- Estimativa total: 162h (195h com buffer)
- Subtarefas e critérios de aceitação
- Cronograma sugerido

### 🔧 [DOCKER.md](./DOCKER.md)
Guia completo para executar o frontend com Docker (desenvolvimento e produção).

### 🔐 [OAUTH-SETUP.md](./OAUTH-SETUP.md)
Configuração detalhada do login social com Google e Microsoft.

### 🔌 [API-EXAMPLES.md](./API-EXAMPLES.md)
Exemplos de integração com todas as APIs do backend.

---

## 🚀 Quick Start

### Pré-requisitos

- Node.js 18+
- npm ou yarn
- Backend ERP Runas rodando (porta 8000)

### Instalação

```bash
# Clonar repositório
git clone <repo-url>
cd RunasERP/frontend

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Iniciar servidor de desenvolvimento
npm run dev
```

### Acessar Aplicação

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Login Padrão

```
Email: admin@runas.com
Senha: Admin@123
```

---

## 🛠️ Tech Stack

### Core
- **React** 18.2+ - Library UI
- **TypeScript** 5.0+ - Type safety
- **Vite** 4.0+ - Build tool
- **React Router** 6.0+ - Roteamento

### UI/Styling
- **Bootstrap** 5.3+ - Framework CSS
- **React Bootstrap** 2.8+ - Componentes React
- **React Icons** 4.10+ - Ícones
- **SASS** - Preprocessador CSS

### State Management
- **React Query** 4.0+ - Server state
- **Context API** - Global state (auth, theme)

### Forms & Validation
- **React Hook Form** 7.45+ - Gerenciamento de formulários
- **Zod** 3.21+ - Schema validation

### HTTP & API
- **Axios** 1.4+ - HTTP client

### Utils
- **date-fns** 2.30+ - Manipulação de datas
- **react-toastify** 9.1+ - Notificações
- **chart.js** - Gráficos

---

## 📦 Estrutura do Projeto

```
frontend/
├── public/                 # Arquivos estáticos
├── src/
│   ├── components/         # Componentes React
│   │   ├── common/         # Componentes reutilizáveis
│   │   ├── layout/         # Layout (Navbar, Sidebar, Footer)
│   │   ├── clientes/       # Componentes de clientes
│   │   ├── produtos/       # Componentes de produtos
│   │   ├── vendas/         # Componentes de vendas
│   │   ├── estoque/        # Componentes de estoque
│   │   └── financeiro/     # Componentes financeiros
│   ├── pages/              # Páginas da aplicação
│   ├── services/           # Serviços de API
│   ├── hooks/              # Custom hooks
│   ├── contexts/           # Context providers
│   ├── types/              # TypeScript types
│   ├── utils/              # Utilitários
│   ├── config/             # Configurações
│   └── styles/             # Estilos globais
├── .env.example            # Exemplo de variáveis de ambiente
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 🎯 Módulos Principais

### 1. Dashboard
- Métricas principais do negócio
- Gráficos de vendas
- Alertas de estoque e contas vencidas

### 2. Clientes
- CRUD completo de clientes
- Gestão de endereços
- Controle de crédito fiado
- Histórico de compras

### 3. Produtos
- CRUD de produtos e variantes
- Gestão de categorias
- Gestão de fornecedores
- Configuração de catálogo público

### 4. Estoque
- Visualização de estoque
- Entrada e saída de mercadorias
- Ajustes e inventário
- Alertas de estoque baixo

### 5. Vendas
- Listagem de pedidos
- Detalhes e gestão de pedidos
- Atualização de status
- Confirmação de pagamentos

### 6. Financeiro
- Contas a receber
- Registro de pagamentos
- Contas vencidas e a vencer
- Histórico financeiro

---

## 🔐 Autenticação

O sistema utiliza **JWT (JSON Web Tokens)** para autenticação.

### Fluxo de Autenticação

1. Usuário faz login com email e senha
2. Backend retorna `access_token` e `refresh_token`
3. `access_token` é enviado em todas as requisições (header Authorization)
4. Token é renovado automaticamente antes da expiração
5. Logout invalida tokens no backend

### Roles

- **ADMIN**: Acesso total a todos os módulos
- **OPERADOR**: Acesso limitado (leitura de produtos, criação de pedidos)

---

## 🧪 Testes

```bash
# Executar testes unitários
npm run test

# Executar testes com coverage
npm run test:coverage

# Executar testes em modo watch
npm run test:watch
```

---

## 📊 Scripts Disponíveis

```bash
npm run dev          # Inicia servidor de desenvolvimento
npm run build        # Build para produção
npm run preview      # Preview do build de produção
npm run test         # Executa testes
npm run lint         # Executa linting
npm run format       # Formata código com Prettier
```

---

## 🚀 Deploy

### Build de Produção

```bash
npm run build
# Output: dist/
```

### Docker

```bash
# Build da imagem
docker build -t erp-runas-frontend .

# Executar container
docker run -p 80:80 erp-runas-frontend
```

---

## 📖 Documentação Adicional

### Backend
- [Especificação Técnica](../ESPECIFICACAO-TECNICA.md)
- [Mapeamento de Rotas](../MAPEAMENTO-ROTAS.md)
- [Regras de Negócio](../REGRAS-DE-NEGOCIO.md)

### Geral
- [README Principal](../../README.md)
- [Guia de Implementação](../GUIA-IMPLEMENTACAO.md)

---

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Commit suas mudanças: `git commit -m 'Add nova feature'`
3. Push para a branch: `git push origin feature/nova-feature`
4. Abra um Pull Request

---

## 📝 Roadmap

### Fase Atual: MVP
- [x] Documentação completa
- [ ] Setup inicial do projeto
- [ ] Autenticação e layout
- [ ] Módulo de clientes
- [ ] Módulo de produtos
- [ ] Módulo de estoque
- [ ] Módulo de vendas
- [ ] Módulo financeiro
- [ ] Dashboard
- [ ] Testes e otimizações

### Futuro
- [ ] Catálogo público
- [ ] Carrinho de compras
- [ ] Relatórios avançados
- [ ] Notificações em tempo real
- [ ] App mobile

---

## 📞 Suporte

Para dúvidas ou problemas:
- Consulte a documentação completa nesta pasta
- Abra uma issue no repositório
- Entre em contato: suporte@runas.com

---

**Versão:** 1.0.0  
**Data:** 2026-05-25  
**Status:** 📝 Documentação Completa - Pronto para Implementação

---

<div align="center">

**[⬆ Voltar ao topo](#-frontend---erp-runas)**

Feito com ❤️ pela equipe **Runas**

</div>
