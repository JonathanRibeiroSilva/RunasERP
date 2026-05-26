# Docker - Frontend ERP Runas

Guia completo para executar o frontend com Docker.

---

## 📦 Arquivos Docker

O projeto possui 3 arquivos Docker:

1. **`Dockerfile`** - Build de produção (otimizado, multi-stage)
2. **`Dockerfile.dev`** - Desenvolvimento com hot reload
3. **`nginx.conf`** - Configuração do Nginx para produção

---

## 🚀 Executar com Docker

### Opção 1: Produção (com docker-compose principal)

Executa todo o sistema (backend + frontend):

```bash
# Na raiz do projeto
docker-compose up -d

# Ou apenas o frontend
docker-compose up -d frontend
```

**Acesso:**
- Frontend: http://localhost (porta 80)
- Backend API: http://localhost:8000

### Opção 2: Desenvolvimento (com hot reload)

Executa apenas o frontend em modo desenvolvimento:

```bash
# Na raiz do projeto
docker-compose -f docker-compose.dev.yml up

# Ou em background
docker-compose -f docker-compose.dev.yml up -d
```

**Acesso:**
- Frontend: http://localhost:3000
- Hot reload ativo (mudanças refletem automaticamente)

### Opção 3: Build manual

```bash
# Build da imagem de produção
cd frontend
docker build -t erp-runas-frontend .

# Executar
docker run -p 80:80 erp-runas-frontend

# Build da imagem de desenvolvimento
docker build -f Dockerfile.dev -t erp-runas-frontend-dev .

# Executar com volume para hot reload
docker run -p 3000:3000 -v $(pwd):/app -v /app/node_modules erp-runas-frontend-dev
```

---

## 📁 Estrutura dos Dockerfiles

### Dockerfile (Produção)

```dockerfile
# Stage 1: Build
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Stage 2: Production (Nginx)
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Características:**
- ✅ Multi-stage build (imagem final pequena)
- ✅ Nginx para servir arquivos estáticos
- ✅ Otimizado para produção
- ✅ Health check incluído
- ✅ Compressão gzip
- ✅ Cache de assets
- ✅ SPA fallback (todas as rotas → index.html)

### Dockerfile.dev (Desenvolvimento)

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Características:**
- ✅ Hot reload ativo
- ✅ DevTools habilitados
- ✅ Volume mount para mudanças em tempo real
- ✅ Porta 3000 exposta

---

## 🔧 Configuração do Nginx

O `nginx.conf` inclui:

### 1. Compressão Gzip

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript;
```

### 2. Security Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
```

### 3. Cache de Assets

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 4. SPA Fallback

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### 5. Proxy para API (opcional)

```nginx
location /api {
    proxy_pass http://api-gateway:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## 🌐 Variáveis de Ambiente no Docker

### Desenvolvimento

Edite `docker-compose.dev.yml`:

```yaml
environment:
  - VITE_API_URL=http://localhost:8000
  - VITE_ENABLE_DEVTOOLS=true
  - VITE_GOOGLE_CLIENT_ID=seu-client-id
  - VITE_MICROSOFT_CLIENT_ID=seu-client-id
```

### Produção

As variáveis são "baked in" durante o build. Para mudar:

1. Edite `.env.production`
2. Rebuild a imagem:

```bash
docker-compose build frontend
docker-compose up -d frontend
```

**Alternativa:** Use build args:

```bash
docker build \
  --build-arg VITE_API_URL=https://api.seudominio.com \
  --build-arg VITE_GOOGLE_CLIENT_ID=seu-client-id \
  -t erp-runas-frontend .
```

---

## 📊 Comandos Úteis

### Ver logs

```bash
# Logs do frontend (produção)
docker-compose logs -f frontend

# Logs do frontend (desenvolvimento)
docker-compose -f docker-compose.dev.yml logs -f frontend-dev
```

### Parar containers

```bash
# Parar tudo
docker-compose down

# Parar apenas frontend
docker-compose stop frontend

# Parar desenvolvimento
docker-compose -f docker-compose.dev.yml down
```

### Rebuild

```bash
# Rebuild e restart
docker-compose up -d --build frontend

# Rebuild sem cache
docker-compose build --no-cache frontend
```

### Entrar no container

```bash
# Produção
docker exec -it erp-frontend sh

# Desenvolvimento
docker exec -it erp-frontend-dev sh
```

### Limpar volumes

```bash
# Remover volumes não usados
docker volume prune

# Remover tudo (cuidado!)
docker-compose down -v
```

---

## 🐛 Troubleshooting

### Erro: "Cannot find module"

**Causa:** node_modules não foi instalado corretamente

**Solução:**
```bash
docker-compose down
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Erro: "Port 3000 is already in use"

**Causa:** Porta já está sendo usada

**Solução:**
```bash
# Parar processo na porta 3000
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Ou mudar a porta no docker-compose.dev.yml
ports:
  - "3001:3000"
```

### Hot reload não funciona

**Causa:** Volume não está montado corretamente

**Solução:**
```bash
# Verificar se o volume está montado
docker inspect erp-frontend-dev

# Recriar container
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up
```

### Erro 404 ao acessar rotas

**Causa:** SPA fallback não configurado

**Solução:**
- Verifique se `nginx.conf` tem `try_files $uri $uri/ /index.html;`
- Rebuild a imagem

### API não responde

**Causa:** Frontend não consegue acessar o backend

**Solução:**
1. Verifique se o backend está rodando:
   ```bash
   docker-compose ps
   ```
2. Verifique a URL da API no `.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
3. Teste a API diretamente:
   ```bash
   curl http://localhost:8000/health
   ```

---

## 🔒 Segurança em Produção

### 1. HTTPS

Use um reverse proxy (Nginx, Traefik, Caddy) com SSL:

```yaml
# docker-compose.yml
services:
  nginx-proxy:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl
      - ./nginx-proxy.conf:/etc/nginx/nginx.conf
```

### 2. Secrets

Não commite secrets no `.env`. Use Docker secrets:

```yaml
services:
  frontend:
    secrets:
      - google_client_id
      - microsoft_client_id

secrets:
  google_client_id:
    file: ./secrets/google_client_id.txt
  microsoft_client_id:
    file: ./secrets/microsoft_client_id.txt
```

### 3. Health Checks

O Dockerfile já inclui health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1
```

Verifique:
```bash
docker ps
# Deve mostrar "healthy" na coluna STATUS
```

---

## 📈 Performance

### Tamanho da Imagem

```bash
# Ver tamanho
docker images | grep erp-runas-frontend

# Produção: ~25MB (nginx:alpine + build)
# Desenvolvimento: ~400MB (node + node_modules)
```

### Build Time

```bash
# Primeira build: ~2-5 minutos
# Rebuilds: ~30 segundos (com cache)
```

### Otimizações

1. **Multi-stage build** - Imagem final não inclui node_modules
2. **npm ci** - Instalação mais rápida e determinística
3. **Layer caching** - COPY package.json antes do código
4. **.dockerignore** - Não copia node_modules, dist, etc

---

## 🚀 Deploy em Produção

### Docker Hub

```bash
# Login
docker login

# Tag
docker tag erp-runas-frontend seu-usuario/erp-runas-frontend:latest

# Push
docker push seu-usuario/erp-runas-frontend:latest
```

### Docker Compose em Servidor

```bash
# No servidor
git clone seu-repo
cd RunasERP

# Configurar .env
cp .env.example .env
nano .env

# Subir
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Kubernetes (opcional)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: erp-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: erp-frontend
  template:
    metadata:
      labels:
        app: erp-frontend
    spec:
      containers:
      - name: frontend
        image: seu-usuario/erp-runas-frontend:latest
        ports:
        - containerPort: 80
```

---

## ✅ Checklist de Deploy

- [ ] `.env.production` configurado
- [ ] OAuth Client IDs configurados
- [ ] Build testado localmente
- [ ] Imagem enviada para registry
- [ ] HTTPS configurado
- [ ] Health checks funcionando
- [ ] Logs sendo coletados
- [ ] Backup configurado
- [ ] Monitoramento ativo

---

**Última Atualização:** 2026-05-25  
**Versão:** 1.0.0
