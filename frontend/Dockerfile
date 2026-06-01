# Multi-stage build para otimizar o tamanho da imagem

# Stage 1: Build
FROM node:22-alpine AS build

WORKDIR /app

# Instalar dependências de build necessárias para módulos nativos
RUN apk add --no-cache python3 make g++ curl

# Copiar package files
COPY package*.json ./

# Limpar cache e reinstalar
RUN rm -rf node_modules package-lock.json && npm install

# Copiar código fonte
COPY . .

# Build da aplicação
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copiar build do stage anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuração customizada do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expor porta 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Comando para iniciar nginx
CMD ["nginx", "-g", "daemon off;"]
