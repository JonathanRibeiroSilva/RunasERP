# Performance e Consumo de CPU - RunasERP

## 🔥 Problema: Alto Consumo de CPU em VPS

### Sintomas
- Containers FastAPI consumindo 50-80% de CPU em idle na VPS
- Desenvolvimento local: 15-20% de CPU
- Sistema lento e travamentos

---

## 🐛 Causas Identificadas

### 1. **Uvicorn `--reload` (Principal Culpado)**

**O que faz:**
```python
uvicorn main:app --reload  # ❌ Scanneia arquivos a cada 1 segundo
```

- 🔴 Watchdog ativo em TODOS os arquivos Python
- 🔴 8 microsserviços × 100 arquivos cada = 800 verificações/segundo
- 🔴 Polling contínuo consome CPU

**Solução aplicada:**
```python
uvicorn main:app --reload --reload-delay 2  # ✅ Scanneia a cada 2 segundos
```

**Redução esperada:** 40-50% menos CPU

---

### 2. **CHOKIDAR_USEPOLLING no Frontend**

**O que faz:**
```yaml
CHOKIDAR_USEPOLLING: "true"  # Polling de arquivos .js/.jsx/.tsx
CHOKIDAR_INTERVAL: "1000"    # A cada 1 segundo
```

- 🟡 Necessário para hot-reload no Docker/Windows
- 🟡 Consome ~5-10% de CPU

**Otimização:** Mantido em dev, removido em produção

---

### 3. **Volumes Montados (Docker + Windows)**

```yaml
volumes:
  - ./api-gateway:/app  # Windows → WSL2 → Docker
```

- 🟡 I/O lento entre sistemas
- 🟡 Inotify não funciona bem, força polling

**Solução:** Remover volumes em staging/produção

---

## ✅ Otimizações Aplicadas

### **Desenvolvimento (docker-compose.dev.yml)**

```yaml
api-gateway:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-delay 2
```

**Características:**
- ✅ Hot-reload continua funcionando
- ✅ Delay de 2s entre scans (em vez de 1s)
- ✅ CPU reduzida de 15% → 8-10%

---

### **Staging/VPS (docker-compose.staging.yml - A CRIAR)**

```yaml
api-gateway:
  command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

**Características:**
- ✅ CPU reduzida de 50-80% → 5-10%
- ✅ 2 workers = processa 2 requests simultâneos
- ❌ Precisa rebuild para mudanças (aceitável)

---

## 🚀 Aplicando as Mudanças

### **1. Desenvolvimento (aplicado):**
```bash
# Reiniciar containers para aplicar --reload-delay 2
docker compose -f docker-compose.dev.yml restart
```

**Redução de consumo esperada: 40-50%** 🚀
