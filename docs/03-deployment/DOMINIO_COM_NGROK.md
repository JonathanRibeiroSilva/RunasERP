# 🌐 Usar Domínio Próprio com Ngrok

## ⚠️ Importante

Para usar domínio customizado com ngrok, você precisa do **plano pago** (Pro ou superior).

**Custos ngrok**:
- Free: $0 (apenas subdomínios `*.ngrok-free.app`)
- Personal: $8/mês (1 domínio customizado)
- Pro: $20/mês (3 domínios customizados)

**Alternativa gratuita**: Use **Cloudflare Tunnel** (veja `CLOUDFLARE_TUNNEL.md`)

---

## Se Você Tem Plano Pago do Ngrok

### Passo 1: Adicionar Domínio no Ngrok Dashboard

1. Ir para: https://dashboard.ngrok.com/cloud-edge/domains
2. Clicar em "New Domain"
3. Adicionar: `runaserp.com.br`
4. Ngrok vai fornecer um registro CNAME

### Passo 2: Configurar DNS

No painel do Registro.br, adicione:

```
Tipo: CNAME
Nome: @
Valor: <valor fornecido pelo ngrok>
TTL: 300
```

### Passo 3: Atualizar .env.ngrok

```env
NGROK_DOMAIN=runaserp.com.br
NGROK_AUTHTOKEN=seu-token-aqui
```

### Passo 4: Atualizar docker-compose.nginx.yml

```yaml
ngrok:
  image: ngrok/ngrok:latest
  container_name: erp-ngrok
  command: http --domain=runaserp.com.br nginx:80
  ports:
    - "4040:4040"
  depends_on:
    - nginx
  networks:
    - erp-network
  environment:
    NGROK_AUTHTOKEN: ${NGROK_AUTHTOKEN}
  restart: unless-stopped
```

### Passo 5: Subir Sistema

```powershell
docker-compose -f docker-compose.yml -f docker-compose.nginx.yml up -d
```

### Passo 6: Atualizar .env Principal

```env
FRONTEND_URL=https://runaserp.com.br
API_BASE_URL=https://runaserp.com.br/api
```

---

## 💰 Comparação: Ngrok vs Cloudflare Tunnel

| Recurso | Ngrok (Pago) | Cloudflare Tunnel (Free) |
|---------|--------------|--------------------------|
| **Custo** | $8-20/mês | **GRATUITO** ✅ |
| **SSL** | Incluído | Incluído |
| **DDoS Protection** | Limitado | Incluído |
| **CDN Cache** | Não | Sim |
| **Bandwidth** | Limitado | Ilimitado |
| **Domínio Customizado** | 1-3 domínios | Ilimitado |

---

## 💡 Recomendação

Use **Cloudflare Tunnel** (gratuito) em vez de ngrok pago:

```powershell
# Ver documentação completa
code docs/03-deployment/CLOUDFLARE_TUNNEL.md
```

---

## Alternativa: Ngrok Free + Subdomínio

Se quiser continuar no plano Free do ngrok:

```yaml
# Usar subdomínio ngrok gratuito
ngrok:
  command: http nginx:80
  # URL será: https://algo-aleatorio.ngrok-free.app
```

**Desvantagem**: URL muda a cada restart (a menos que reserve um subdomínio estático no plano Personal)

---

## ✅ Conclusão

Para produção com domínio próprio:
- ✅ **Cloudflare Tunnel** (gratuito, recomendado)
- ❌ Ngrok (pago, $8-20/mês)
