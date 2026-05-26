# Problemas com Docker - Runas

> **Soluções específicas** para problemas relacionados ao Docker

---

## 🐳 Problemas Comuns

### 1. Containers não sobem

**Sintomas:**
```bash
docker-compose up -d
ERROR: Cannot start service X
```

**Causas Comuns:**
- Portas já em uso
- Falta de memória
- Volumes corrompidos
- Imagens desatualizadas

**Soluções:**

#### Verificar portas em uso
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Matar processo
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

#### Limpar e reconstruir
```bash
# Parar tudo
docker-compose down

# Limpar volumes
docker-compose down -v

# Limpar sistema
docker system prune -a

# Subir novamente
docker-compose up -d
```

---

### 2. Erro "no space left on device"

**Sintomas:**
```
Error response from daemon: no space left on device
```

**Soluções:**

```bash
# Verificar uso de espaço
docker system df

# Limpar imagens não utilizadas
docker image prune -a

# Limpar volumes não utilizados
docker volume prune

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes
```

---

### 3. Container reiniciando constantemente

**Sintomas:**
```bash
docker ps
# Status: Restarting (X) Y seconds ago
```

**Soluções:**

```bash
# Ver logs do container
docker logs <container-name> --tail 100

# Ver logs em tempo real
docker logs -f <container-name>

# Inspecionar health check
docker inspect <container-name> | grep -A 10 Health

# Desabilitar restart temporariamente
# Editar docker-compose.yml:
restart: "no"  # ao invés de "unless-stopped"
```

---

### 4. Erro de permissão em volumes

**Sintomas:**
```
Permission denied: '/var/lib/postgresql/data'
```

**Soluções:**

```bash
# Linux/Mac - Ajustar permissões
sudo chown -R $USER:$USER ./volumes

# Ou usar volumes nomeados (recomendado)
# docker-compose.yml:
volumes:
  pgdata-clientes:
```

---

### 5. Erro "network not found"

**Sintomas:**
```
ERROR: Network erp-network declared as external, but could not be found
```

**Soluções:**

```bash
# Criar rede manualmente
docker network create erp-network

# Ou remover "external: true" do docker-compose.yml
```

---

### 6. Imagens não atualizam

**Sintomas:**
```
Código atualizado mas container usa versão antiga
```

**Soluções:**

```bash
# Rebuild sem cache
docker-compose build --no-cache

# Rebuild serviço específico
docker-compose build --no-cache clientes

# Forçar recreação
docker-compose up -d --force-recreate
```

---

### 7. Erro "port is already allocated"

**Sintomas:**
```
Error starting userland proxy: listen tcp 0.0.0.0:8000: bind: address already in use
```

**Soluções:**

```bash
# Opção 1: Matar processo na porta
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Opção 2: Mudar porta no docker-compose.yml
ports:
  - "8001:8000"  # Usar porta 8001 no host
```

---

### 8. Container não consegue conectar ao banco

**Sintomas:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Soluções:**

```bash
# Verificar se banco está rodando
docker ps | grep postgres

# Verificar logs do banco
docker logs db-clientes

# Aguardar health check
docker inspect db-clientes | grep Health

# Testar conexão manualmente
docker exec -it db-clientes psql -U erp -d clientes
```

---

### 9. Docker Compose versão incompatível

**Sintomas:**
```
ERROR: Version in "./docker-compose.yml" is unsupported
```

**Soluções:**

```bash
# Verificar versão
docker-compose --version

# Atualizar Docker Compose
# Windows/Mac: Atualizar Docker Desktop
# Linux:
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

---

### 10. Erro de memória insuficiente

**Sintomas:**
```
Container killed due to memory limit
```

**Soluções:**

```bash
# Aumentar memória do Docker Desktop
# Settings > Resources > Memory: 4GB+

# Ou limitar memória por serviço
# docker-compose.yml:
services:
  clientes:
    mem_limit: 512m
```

---

## 🔧 Comandos Úteis

### Diagnóstico

```bash
# Ver todos os containers
docker ps -a

# Ver uso de recursos
docker stats

# Ver logs de todos os serviços
docker-compose logs

# Ver logs de um serviço específico
docker-compose logs clientes

# Inspecionar container
docker inspect <container-name>

# Ver processos dentro do container
docker top <container-name>
```

### Limpeza

```bash
# Parar todos os containers
docker stop $(docker ps -aq)

# Remover todos os containers
docker rm $(docker ps -aq)

# Remover todas as imagens
docker rmi $(docker images -q)

# Limpar tudo (CUIDADO!)
docker system prune -a --volumes
```

### Acesso

```bash
# Entrar no container
docker exec -it <container-name> bash

# Executar comando no container
docker exec <container-name> <comando>

# Copiar arquivo do container
docker cp <container-name>:/path/to/file ./local/path

# Copiar arquivo para container
docker cp ./local/file <container-name>:/path/to/
```

---

## 🆘 Reset Completo

Se nada funcionar, reset completo:

```bash
# 1. Parar tudo
docker-compose down -v

# 2. Limpar sistema
docker system prune -a --volumes

# 3. Remover pasta de volumes (se existir)
rm -rf ./volumes

# 4. Rebuild
docker-compose build --no-cache

# 5. Subir
docker-compose up -d

# 6. Migrations
make migrate

# 7. Seed
make seed
```

---

## 📚 Recursos Adicionais

- [Documentação Oficial do Docker](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Troubleshooting Geral](../02-setup/troubleshooting.md)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
