# Frontend - ERP Runas

Sistema de gestão empresarial para pequenos comércios de alimentos e bebidas.

## 🚀 Tecnologias

- **React** 18.2+ com TypeScript
- **Vite** - Build tool e dev server
- **React Router** - Roteamento
- **React Query** - Gerenciamento de estado do servidor
- **Axios** - Cliente HTTP
- **React Hook Form + Zod** - Formulários e validação
- **Bootstrap + SASS** - Estilização
- **React Icons** - Ícones
- **React Toastify** - Notificações

## 📋 Pré-requisitos

- Node.js 18+ 
- npm ou yarn
- Backend ERP Runas rodando na porta 8000

## 🔧 Instalação

```bash
# Instalar dependências
npm install

# Copiar arquivo de ambiente
## 🔧 Pré-requisitos

- **Docker** e **Docker Compose** instalados
- Backend ERP Runas rodando (porta 8000)

## 🚀 Executar

### Desenvolvimento (com hot reload)

```bash
# Na raiz do projeto RunasERP
docker-compose -f docker-compose.dev.yml up

# Ou em background
docker-compose -f docker-compose.dev.yml up -d

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f frontend-dev
```

**Acesso:** http://localhost:3000

### Produção

```bash
# Na raiz do projeto RunasERP
docker-compose up -d frontend

# Ou todo o sistema
docker-compose up -d

# Ver logs
docker-compose logs -f frontend
```

**Acesso:** http://localhost (porta 80)

Consulte [docs/frontend/DOCKER.md](../docs/frontend/DOCKER.md) para mais detalhes.

## 🔐 Login

Credenciais padrão para teste:

```
Email: admin@runas.com
Senha: Admin@123
```

### Login Social (OAuth)

O sistema também suporta login com:
- ✅ **Google** (Gmail)
- ✅ **Microsoft** (Outlook/Office 365)

Para configurar, consulte: [docs/frontend/OAUTH-SETUP.md](../docs/frontend/OAUTH-SETUP.md)

## 📁 Estrutura do Projeto

```
frontend/
├── public/              # Arquivos estáticos
├── src/
│   ├── components/      # Componentes React
│   │   ├── common/      # Componentes reutilizáveis
│   │   ├── layout/      # Layout (Navbar, Sidebar)
│   │   └── ...          # Componentes por módulo
│   ├── pages/           # Páginas da aplicação
│   ├── services/        # Serviços de API
│   │   ├── api/         # Cliente Axios
│   │   └── auth/        # Autenticação
│   ├── hooks/           # Custom hooks
│   ├── contexts/        # Context providers
│   ├── types/           # TypeScript types
│   ├── utils/           # Utilitários
│   ├── config/          # Configurações
│   ├── styles/          # Estilos globais (SASS)
│   ├── App.tsx          # Componente principal
│   └── main.tsx         # Entry point
├── .env.example         # Exemplo de variáveis de ambiente
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 🎨 Design System

O projeto utiliza o **Runas Design System** com:

- **Dark Mode First** - Interface escura sofisticada
- **Paleta de cores** inspirada em Linear, Vercel, Stripe
- **Componentes** consistentes e acessíveis
- **Tipografia** Inter font
- **Espaçamento** baseado em múltiplos de 8px

Consulte `docs/frontend/DESIGN-SYSTEM.md` para detalhes completos.

## 🧪 Testes

```bash
# Executar testes
npm run test

# Testes com coverage
npm run test:coverage

# Testes em modo watch
npm run test:watch
```

## 📝 Scripts Disponíveis

- `npm run dev` - Inicia servidor de desenvolvimento
- `npm run build` - Build para produção
- `npm run preview` - Preview do build
- `npm run lint` - Executa linting
- `npm run format` - Formata código com Prettier
- `npm run test` - Executa testes

## 🔗 Integração com Backend

O frontend se comunica com o backend através do API Gateway na porta 8000.

Endpoints principais:
- **Auth**: `/auth/login`, `/auth/logout`, `/auth/me`
- **Clientes**: `/clientes/*`
- **Produtos**: `/produtos/*`
- **Vendas**: `/vendas/*`
- **Estoque**: `/estoque/*`
- **Financeiro**: `/financeiro/*`

Documentação completa da API: http://localhost:8000/docs

## 🚧 Status do Projeto

### ✅ Implementado

- [x] Setup inicial do projeto
- [x] Configuração de Axios com interceptors
- [x] Autenticação JWT com refresh token
- [x] Context de autenticação
- [x] Layout principal (Navbar + Sidebar)
- [x] Página de Login
- [x] **OAuth Google e Microsoft**
- [x] Página de Dashboard (básica)
- [x] Design System Runas
- [x] Roteamento protegido
- [x] **Docker (desenvolvimento e produção)**
- [x] **Nginx configurado**

### 🚧 Em Desenvolvimento

- [ ] Módulo de Clientes
- [ ] Módulo de Produtos
- [ ] Módulo de Vendas
- [ ] Módulo de Estoque
- [ ] Módulo Financeiro
- [ ] Componentes comuns (Button, Input, Modal, Table, etc)
- [ ] Gráficos no Dashboard
- [ ] Testes unitários

## 📚 Documentação

Documentação completa disponível em `docs/frontend/`:

- **IMPLEMENTATION-READY.md** - Guia de implementação
- **REQUIREMENTS.md** - Requisitos funcionais
- **DESIGN.md** - Arquitetura técnica
- **DESIGN-SYSTEM.md** - Sistema de design
- **TASKS.md** - Plano de implementação
- **API-EXAMPLES.md** - Exemplos de API

## 🤝 Contribuindo

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Commit suas mudanças: `git commit -m 'Add nova feature'`
3. Push para a branch: `git push origin feature/nova-feature`
4. Abra um Pull Request

## 📄 Licença

Este projeto é parte do ERP Runas.

---

**Versão:** 1.0.0  
**Data:** 2026-05-25  
**Status:** 🚧 Em Desenvolvimento
