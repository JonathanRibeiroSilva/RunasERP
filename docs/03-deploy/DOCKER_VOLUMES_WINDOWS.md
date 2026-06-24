# 🐳 Por que arquivos não sincronizavam?

## 🐛 O Problema

`vite.config.ts` editado no Windows não atualizava no container.

**Causa:** Arquivo não estava nos volumes bind mounts.

---

## 📋 Volumes Configurados

```yaml
volumes:
  - ./frontend/src:/app/src           # ✅ Sincroniza
  - ./frontend/public:/app/public     # ✅ Sincroniza
  - ./frontend/vite.config.ts:/app/vite.config.ts:ro  # ✅ CORRIGIDO
  - /app/node_modules                 # 🔒 Protegido
```

---

## ⚡ Por que não montar tudo?

**Montar `/frontend:/app` completo no Windows = LENTO**

- Docker Desktop + WSL2 = latência I/O
- Chokidar gera milhares de eventos
- Hot reload fica 2-5x mais lento

**Solução:** Montar apenas o necessário
- `src/` e `public/` mudam sempre
- Configs mudam raramente

---

## 🔧 Quando precisar rebuild

| Arquivo | Comando |
|---------|---------|
| `vite.config.ts` | ✅ Sincroniza automaticamente |
| `package.json` | `docker-compose up -d --build frontend-dev` |
| `tsconfig.json` | `docker-compose up -d --build frontend-dev` |

---

## 🛠️ Troubleshooting

**Arquivo não sincroniza:**
```powershell
docker cp frontend/arquivo.ts erp-frontend-dev:/app/arquivo.ts
docker restart erp-frontend-dev
```

**Hot reload não funciona:**
```powershell
docker-compose up -d --build --force-recreate frontend-dev
```
