# 🎨 Documentação do Frontend - Runas

> Documentação completa do frontend do sistema Runas

**Última atualização**: 26 de Maio de 2026  
**Status**: Em desenvolvimento

---

## 📋 Índice

### 🚀 Setup e Configuração
Guias para configurar o ambiente de desenvolvimento do frontend.

- **[Prerequisites](./setup/prerequisites.md)** - Pré-requisitos e dependências
- **[Docker](./setup/docker.md)** - Configuração completa com Docker
- **[Docker Quick Start](./setup/docker-quick-start.md)** - Início rápido com Docker

### 🎨 Design e UI
Documentação do design system e interface do usuário.

- **[Design](./design/design.md)** - Guia de design e padrões visuais
- **[Design System](./design/design-system.md)** - Sistema de design completo (componentes, cores, tipografia)

### 🔐 OAuth e Autenticação
Documentação sobre autenticação e OAuth.

- **[OAuth Summary](./oauth/oauth-summary.md)** - Resumo da implementação OAuth
- **[OAuth Fix Summary](./oauth/oauth-fix-summary.md)** - Correções aplicadas no OAuth
- **[Debug OAuth Redirect](./oauth/debug-oauth-redirect.md)** - Guia de debug de redirecionamentos

### 📚 Guias de Desenvolvimento
Guias práticos para desenvolvimento.

- **[API Examples](./guias/api-examples.md)** - Exemplos de uso da API
- **[Quick Test Guide](./guias/quick-test-guide.md)** - Guia rápido de testes
- **[Índice de Testes](./guias/indice-testes.md)** - Índice completo de testes

### 🚀 Deploy e Produção
Guias para deploy e produção.

- **[Production Checklist](./deployment/production-checklist.md)** - Checklist para produção

---

## 🏗️ Arquitetura do Frontend

### Stack Tecnológico

| Categoria | Tecnologia | Versão |
|-----------|-----------|--------|
| **Framework** | React | 18.x |
| **Linguagem** | TypeScript | 5.x |
| **Build Tool** | Vite | 5.x |
| **Roteamento** | React Router | 6.x |
| **Estado** | Zustand / Redux | - |
| **UI Library** | Material-UI / Ant Design | - |
| **Formulários** | React Hook Form | - |
| **Validação** | Zod / Yup | - |
| **HTTP Client** | Axios | - |
| **Autenticação** | OAuth2 + JWT | - |

### Estrutura de Pastas

```
frontend/
├── public/                 # Arquivos estáticos
├── src/
│   ├── assets/            # Imagens, fontes, etc
│   ├── components/        # Componentes reutilizáveis
│   │   ├── common/       # Componentes comuns
│   │   ├── forms/        # Componentes de formulário
│   │   └── layout/       # Componentes de layout
│   ├── pages/            # Páginas da aplicação
│   │   ├── auth/         # Páginas de autenticação
│   │   ├── clientes/     # Páginas de clientes
│   │   ├── produtos/     # Páginas de produtos
│   │   ├── estoque/      # Páginas de estoque
│   │   └── vendas/       # Páginas de vendas
│   ├── services/         # Serviços e API calls
│   ├── hooks/            # Custom hooks
│   ├── store/            # Estado global
│   ├── utils/            # Utilitários
│   ├── types/            # TypeScript types
│   ├── styles/           # Estilos globais
│   ├── App.tsx           # Componente principal
│   └── main.tsx          # Entry point
├── Dockerfile            # Docker para produção
├── docker-compose.yml    # Docker Compose
├── package.json          # Dependências
├── tsconfig.json         # Config TypeScript
└── vite.config.ts        # Config Vite
```

---

## 🚀 Quick Start

### Desenvolvimento Local

```bash
# 1. Instalar dependências
cd frontend
npm install

# 2. Configurar variáveis de ambiente
cp .env.example .env

# 3. Iniciar servidor de desenvolvimento
npm run dev

# Acesse: http://localhost:5173
```

### Com Docker

```bash
# Subir frontend com Docker
docker-compose up -d frontend

# Acesse: http://localhost:3000
```

📖 **Guia completo**: [Setup com Docker](./setup/docker.md)

---

## 🔐 Autenticação

O frontend utiliza **OAuth2 com JWT** para autenticação.

### Fluxo de Login

1. Usuário clica em "Login com Google/Microsoft"
2. Redirecionamento para provedor OAuth
3. Usuário autoriza a aplicação
4. Callback com código de autorização
5. Troca do código por tokens (access + refresh)
6. Armazenamento seguro dos tokens
7. Redirecionamento para dashboard

### Armazenamento de Tokens

- **Access Token**: `localStorage` (expira em 30 minutos)
- **Refresh Token**: `httpOnly cookie` (expira em 7 dias)

📖 **Documentação completa**: [OAuth Summary](./oauth/oauth-summary.md)

---

## 🎨 Design System

### Cores Principais

```css
/* Cores primárias */
--primary: #1976d2;
--secondary: #dc004e;
--success: #4caf50;
--warning: #ff9800;
--error: #f44336;
--info: #2196f3;

/* Cores neutras */
--gray-50: #fafafa;
--gray-100: #f5f5f5;
--gray-200: #eeeeee;
--gray-300: #e0e0e0;
--gray-400: #bdbdbd;
--gray-500: #9e9e9e;
--gray-600: #757575;
--gray-700: #616161;
--gray-800: #424242;
--gray-900: #212121;
```

### Tipografia

```css
/* Fontes */
--font-primary: 'Inter', sans-serif;
--font-secondary: 'Roboto', sans-serif;

/* Tamanhos */
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

📖 **Design System completo**: [Design System](./design/design-system.md)

---

## 📚 Componentes Principais

### Componentes de Layout

- **AppLayout** - Layout principal da aplicação
- **Sidebar** - Menu lateral
- **Header** - Cabeçalho com navegação
- **Footer** - Rodapé

### Componentes de Formulário

- **Input** - Campo de texto
- **Select** - Seleção
- **Checkbox** - Caixa de seleção
- **Radio** - Botão de rádio
- **DatePicker** - Seletor de data
- **FileUpload** - Upload de arquivos

### Componentes de Dados

- **Table** - Tabela de dados
- **DataGrid** - Grid de dados avançado
- **Card** - Cartão de informações
- **List** - Lista de itens

### Componentes de Feedback

- **Alert** - Alertas
- **Toast** - Notificações temporárias
- **Modal** - Janelas modais
- **Loader** - Indicadores de carregamento

---

## 🧪 Testes

### Executar Testes

```bash
# Testes unitários
npm run test

# Testes com coverage
npm run test:coverage

# Testes E2E
npm run test:e2e
```

### Estrutura de Testes

```
src/
├── components/
│   └── Button/
│       ├── Button.tsx
│       └── Button.test.tsx
├── pages/
│   └── Login/
│       ├── Login.tsx
│       └── Login.test.tsx
└── services/
    └── api/
        ├── api.ts
        └── api.test.ts
```

📖 **Guia de testes**: [Quick Test Guide](./guias/quick-test-guide.md)

---

## 🚀 Build e Deploy

### Build para Produção

```bash
# Build otimizado
npm run build

# Preview do build
npm run preview
```

### Deploy com Docker

```bash
# Build da imagem
docker build -t runas-frontend:latest .

# Run container
docker run -p 3000:80 runas-frontend:latest
```

### Deploy em Produção

```bash
# Com Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Com Nginx
npm run build
cp -r dist/* /var/www/html/
```

📖 **Checklist de produção**: [Production Checklist](./deployment/production-checklist.md)

---

## 🔧 Configuração

### Variáveis de Ambiente

```env
# API
VITE_API_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# OAuth
VITE_GOOGLE_CLIENT_ID=your-google-client-id
VITE_MICROSOFT_CLIENT_ID=your-microsoft-client-id
VITE_OAUTH_REDIRECT_URI=http://localhost:5173/auth/callback

# Features
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_SENTRY=false
```

### Configuração do Vite

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## 📖 Recursos Adicionais

### Documentação Externa

- **React**: https://react.dev
- **TypeScript**: https://www.typescriptlang.org
- **Vite**: https://vitejs.dev
- **Material-UI**: https://mui.com
- **React Router**: https://reactrouter.com

### Documentação Interna

- **[API Reference](../10-api-reference/README.md)** - Referência da API
- **[Regras de Negócio](../11-regras-negocio/README.md)** - Regras de negócio
- **[Arquitetura](../03-arquitetura/README.md)** - Arquitetura do sistema

---

## 🤝 Contribuindo

Para contribuir com o frontend:

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Siga o guia de estilo do projeto
3. Escreva testes para novas funcionalidades
4. Commit suas mudanças: `git commit -m 'Add nova feature'`
5. Push para a branch: `git push origin feature/nova-feature`
6. Abra um Pull Request

---

## 📞 Suporte

Para dúvidas sobre o frontend:

- **Email**: frontend@runas.com
- **Documentação**: [docs/05-frontend/](.)
- **Issues**: Abra uma issue no repositório

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 1.0.0-MVP  
**Desenvolvido por**: Equipe DenebCorp

---

<div align="center">

**[⬆ Voltar ao topo](#-documentação-do-frontend---runas)**

</div>
