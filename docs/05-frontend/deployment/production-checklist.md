# Checklist de Produção - Frontend

Este documento lista todas as verificações necessárias antes de colocar o frontend em produção.

## ✅ Segurança

- [ ] Remover todos os `console.log` de debug (exceto erros críticos)
- [ ] Validar que `CLIENT_SECRET` não está exposto no frontend
- [ ] Configurar HTTPS obrigatório
- [ ] Implementar Content Security Policy (CSP)
- [ ] Configurar CORS adequadamente no backend
- [ ] Validar todos os inputs do usuário
- [ ] Implementar rate limiting no backend
- [ ] Configurar tokens com expiração adequada
- [ ] Implementar refresh token rotation
- [ ] Adicionar proteção contra XSS
- [ ] Adicionar proteção contra CSRF (já implementado via state)

## ✅ Performance

- [ ] Executar build de produção: `npm run build`
- [ ] Verificar tamanho dos bundles (< 500KB ideal)
- [ ] Implementar code splitting
- [ ] Otimizar imagens (WebP, lazy loading)
- [ ] Configurar cache adequado
- [ ] Minificar CSS e JavaScript
- [ ] Remover dependências não utilizadas
- [ ] Implementar Service Worker (PWA)
- [ ] Configurar CDN para assets estáticos

## ✅ Variáveis de Ambiente

### Backend (.env)

```env
# Produção
NODE_ENV=production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379

# JWT
JWT_SECRET=seu-secret-super-seguro-aqui-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth Google
GOOGLE_CLIENT_ID=seu-client-id-producao
GOOGLE_CLIENT_SECRET=seu-client-secret-producao

# OAuth Microsoft
MICROSOFT_CLIENT_ID=seu-client-id-producao
MICROSOFT_CLIENT_SECRET=seu-client-secret-producao
MICROSOFT_TENANT_ID=common

# CORS
CORS_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
```

### Frontend (.env.production)

```env
# API
VITE_API_URL=https://api.seu-dominio.com
VITE_API_TIMEOUT=30000

# App
VITE_APP_NAME=ERP Runas
VITE_APP_VERSION=1.0.0
VITE_ENABLE_DEVTOOLS=false
VITE_ENABLE_ANALYTICS=true

# OAuth
VITE_GOOGLE_CLIENT_ID=seu-client-id-producao
VITE_MICROSOFT_CLIENT_ID=seu-client-id-producao
VITE_OAUTH_REDIRECT_URI=https://seu-dominio.com/auth/callback
```

## ✅ OAuth Providers

### Google OAuth

- [ ] Criar projeto no Google Cloud Console (produção)
- [ ] Configurar OAuth consent screen
- [ ] Adicionar redirect URI de produção: `https://seu-dominio.com/auth/callback`
- [ ] Obter Client ID e Client Secret de produção
- [ ] Configurar domínios autorizados
- [ ] Testar fluxo completo em produção

### Microsoft OAuth

- [ ] Criar aplicação no Azure AD (produção)
- [ ] Configurar redirect URI de produção: `https://seu-dominio.com/auth/callback`
- [ ] Obter Application ID e Client Secret de produção
- [ ] Configurar permissões adequadas
- [ ] Grant admin consent (se necessário)
- [ ] Testar fluxo completo em produção

## ✅ Build e Deploy

### Build

```bash
# Frontend
cd frontend
npm run build

# Verificar tamanho dos bundles
ls -lh dist/assets/

# Backend
cd api-gateway
# Não precisa build (Python)
```

### Docker

```bash
# Build imagens de produção
docker-compose -f docker-compose.yml build

# Testar localmente
docker-compose -f docker-compose.yml up

# Push para registry
docker tag runaserp-frontend:latest registry.com/runaserp-frontend:1.0.0
docker push registry.com/runaserp-frontend:1.0.0
```

## ✅ Monitoramento

- [ ] Configurar Sentry ou similar para error tracking
- [ ] Implementar logging estruturado
- [ ] Configurar alertas para erros críticos
- [ ] Implementar health checks
- [ ] Configurar métricas (Prometheus, Grafana)
- [ ] Monitorar performance (Lighthouse, Web Vitals)
- [ ] Configurar uptime monitoring

## ✅ Testes

- [ ] Executar todos os testes unitários
- [ ] Executar testes de integração
- [ ] Testar fluxo OAuth completo (Google e Microsoft)
- [ ] Testar em diferentes navegadores
- [ ] Testar em diferentes dispositivos (mobile, tablet, desktop)
- [ ] Testar com conexão lenta
- [ ] Testar offline (se PWA)
- [ ] Testar acessibilidade (WCAG 2.1)

## ✅ SEO e Meta Tags

```html
<!-- index.html -->
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="ERP Runas - Sistema de gestão para pequenos comércios" />
  <meta name="keywords" content="erp, gestão, vendas, estoque, financeiro" />
  <meta name="author" content="Runas" />
  
  <!-- Open Graph -->
  <meta property="og:title" content="ERP Runas" />
  <meta property="og:description" content="Sistema de gestão para pequenos comércios" />
  <meta property="og:image" content="https://seu-dominio.com/og-image.png" />
  <meta property="og:url" content="https://seu-dominio.com" />
  
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="ERP Runas" />
  <meta name="twitter:description" content="Sistema de gestão para pequenos comércios" />
  <meta name="twitter:image" content="https://seu-dominio.com/twitter-image.png" />
  
  <link rel="canonical" href="https://seu-dominio.com" />
</head>
```

## ✅ Documentação

- [ ] Atualizar README.md
- [ ] Documentar API endpoints
- [ ] Documentar variáveis de ambiente
- [ ] Criar guia de deploy
- [ ] Documentar troubleshooting comum
- [ ] Criar changelog (CHANGELOG.md)

## ✅ Legal e Compliance

- [ ] Adicionar Política de Privacidade
- [ ] Adicionar Termos de Uso
- [ ] Implementar LGPD/GDPR compliance
- [ ] Adicionar cookie consent (se necessário)
- [ ] Configurar data retention policies

## ✅ Backup e Disaster Recovery

- [ ] Configurar backup automático do banco de dados
- [ ] Testar restore de backup
- [ ] Documentar procedimento de disaster recovery
- [ ] Configurar replicação de dados (se necessário)

## ✅ Pós-Deploy

- [ ] Verificar logs de erro
- [ ] Monitorar performance
- [ ] Verificar métricas de uso
- [ ] Coletar feedback dos usuários
- [ ] Planejar próximas iterações

## Comandos Úteis

### Build de Produção

```bash
# Frontend
npm run build
npm run preview  # Testar build localmente

# Analisar bundle size
npm run build -- --mode production
```

### Docker Produção

```bash
# Build
docker-compose -f docker-compose.yml build

# Deploy
docker-compose -f docker-compose.yml up -d

# Logs
docker-compose -f docker-compose.yml logs -f

# Stop
docker-compose -f docker-compose.yml down
```

### Verificar Segurança

```bash
# Audit de dependências
npm audit
npm audit fix

# Verificar vulnerabilidades
npm run security-check
```

## Recursos

- [Vite Production Build](https://vitejs.dev/guide/build.html)
- [React Production Build](https://react.dev/learn/start-a-new-react-project#production-grade-react-frameworks)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
