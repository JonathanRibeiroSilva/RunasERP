# 📱 Configuração da Evolution API (WhatsApp)

Guia completo para configurar a Evolution API para envio de notificações via WhatsApp.

## 📋 Sobre a Evolution API

A Evolution API é uma solução open-source para integração com WhatsApp Business API, permitindo:
- ✅ Envio de mensagens de texto
- ✅ Envio de imagens e documentos
- ✅ Webhooks para recebimento de mensagens
- ✅ Múltiplas instâncias
- ✅ QR Code para autenticação

## 🚀 Setup Inicial

### 1. A Evolution API já está no Docker Compose

O serviço já está configurado no `docker-compose.yml`:

```yaml
evolution-api:
  image: atendai/evolution-api:latest
  container_name: erp-evolution-api
  environment:
    DATABASE_PROVIDER: postgresql
    DATABASE_CONNECTION_URI: postgresql://erp:erp@db-evolution:5432/evolution
    AUTHENTICATION_API_KEY: ${EVOLUTION_API_KEY}
  ports:
    - "8080:8080"
```

### 2. Configurar API Key

No arquivo `.env`, defina uma API Key segura:

```bash
# Gerar uma API Key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Adicionar no .env
EVOLUTION_API_KEY=sua-api-key-aqui
EVOLUTION_INSTANCE=runas
```

### 3. Subir a Evolution API

```bash
# Subir apenas a Evolution API e seu banco
docker-compose up -d evolution-api db-evolution

# Verificar logs
docker-compose logs -f evolution-api

# Aguardar até ver: "Server started on port 8080"
```

### 4. Acessar a Interface

Abra no navegador: http://localhost:8080

## 📱 Conectar WhatsApp

### Método 1: Via Interface Web

1. Acesse http://localhost:8080
2. Clique em "Create Instance"
3. Nome da instância: `runas`
4. Clique em "Create"
5. Será exibido um QR Code
6. Abra o WhatsApp no celular
7. Vá em: **Configurações > Aparelhos conectados > Conectar um aparelho**
8. Escaneie o QR Code
9. Aguarde a conexão

### Método 2: Via API

```bash
# 1. Criar instância
curl -X POST http://localhost:8080/instance/create \
  -H "apikey: sua-api-key-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "runas",
    "qrcode": true
  }'

# 2. Obter QR Code
curl -X GET http://localhost:8080/instance/connect/runas \
  -H "apikey: sua-api-key-aqui"

# Resposta incluirá o QR Code em base64
```

## 🧪 Testar Envio de Mensagem

### Via cURL

```bash
curl -X POST http://localhost:8080/message/sendText/runas \
  -H "apikey: sua-api-key-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "5511999999999",
    "text": "Olá! Esta é uma mensagem de teste do ERP Runas."
  }'
```

### Via Python

```python
import httpx
import asyncio

async def testar_envio():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8080/message/sendText/runas",
            headers={
                "apikey": "sua-api-key-aqui",
                "Content-Type": "application/json"
            },
            json={
                "number": "5511999999999",
                "text": "Teste do ERP Runas"
            }
        )
        print(response.json())

asyncio.run(testar_envio())
```

## 📝 Templates de Mensagens

### Pedido Confirmado

```python
def mensagem_pedido_confirmado(pedido_id: str, total: float) -> str:
    return f"""
🎉 *Pedido Confirmado!*

Seu pedido #{pedido_id} foi confirmado com sucesso!

💰 Total: R$ {total:.2f}

Obrigado por comprar conosco! 🛒
    """.strip()
```

### Pedido Cancelado

```python
def mensagem_pedido_cancelado(pedido_id: str, motivo: str) -> str:
    return f"""
❌ *Pedido Cancelado*

Seu pedido #{pedido_id} foi cancelado.

Motivo: {motivo}

Se tiver dúvidas, entre em contato conosco.
    """.strip()
```

### Lembrete de Cobrança

```python
def mensagem_cobranca_lembrete(valor: float, data_vencimento: str) -> str:
    return f"""
📅 *Lembrete de Pagamento*

Olá! Seu pagamento de *R$ {valor:.2f}* vence em 3 dias.

📆 Data de vencimento: {data_vencimento}

Para evitar bloqueios, realize o pagamento até a data.

Obrigado! 🙏
    """.strip()
```

### Cobrança Vencida

```python
def mensagem_cobranca_vencida(valor: float, dias_atraso: int) -> str:
    return f"""
⚠️ *Pagamento Vencido*

Seu pagamento de *R$ {valor:.2f}* está vencido há {dias_atraso} dia(s).

Por favor, regularize sua situação o quanto antes para evitar bloqueios.

Entre em contato para mais informações.
    """.strip()
```

### Conta Quitada

```python
def mensagem_conta_quitada(valor: float) -> str:
    return f"""
✅ *Pagamento Confirmado!*

Recebemos seu pagamento de *R$ {valor:.2f}*.

Sua conta está quitada! 🎉

Obrigado pela confiança! 💚
    """.strip()
```

### Estoque Mínimo (Alerta Interno)

```python
def mensagem_estoque_minimo(sku: str, quantidade: int, minimo: int) -> str:
    return f"""
⚠️ *ALERTA DE ESTOQUE*

Produto: {sku}
Quantidade atual: {quantidade}
Quantidade mínima: {minimo}

Reabastecer urgentemente!
    """.strip()
```

## 🔧 Configuração no Serviço de Notificações

O cliente Evolution já está implementado em:
`services/notificacoes/integrations/evolution.py`

### Uso no Service

```python
from integrations.evolution import EvolutionAPIClient

class NotificacaoService:
    def __init__(self):
        self.evolution = EvolutionAPIClient()
    
    async def enviar_notificacao(
        self,
        tipo: TipoNotificacao,
        destinatario: str,
        dados: dict
    ):
        # Gerar mensagem baseada no tipo
        mensagem = self._gerar_mensagem(tipo, dados)
        
        # Enviar via Evolution API
        try:
            await self.evolution.enviar_mensagem(
                numero=destinatario,
                mensagem=mensagem
            )
            return True
        except Exception as e:
            log.error("evolution.send_failed", error=str(e))
            return False
```

## 🔄 Webhooks (Opcional)

Para receber mensagens dos clientes:

### 1. Configurar Webhook

```bash
curl -X POST http://localhost:8080/webhook/set/runas \
  -H "apikey: sua-api-key-aqui" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://api-gateway:8000/webhooks/whatsapp",
    "events": ["messages.upsert"]
  }'
```

### 2. Criar Endpoint no Gateway

```python
@app.post("/webhooks/whatsapp")
async def webhook_whatsapp(request: Request):
    """Recebe mensagens do WhatsApp."""
    data = await request.json()
    
    # Processar mensagem
    if data.get("event") == "messages.upsert":
        message = data["data"]["message"]
        from_number = message["key"]["remoteJid"]
        text = message["message"]["conversation"]
        
        # Processar comando
        # Ex: "SALDO" -> retorna saldo do cliente
        
    return {"status": "ok"}
```

## 🐛 Troubleshooting

### Problema: QR Code não aparece

**Solução**:
```bash
# Verificar logs
docker-compose logs evolution-api

# Recriar instância
curl -X DELETE http://localhost:8080/instance/delete/runas \
  -H "apikey: sua-api-key-aqui"

curl -X POST http://localhost:8080/instance/create \
  -H "apikey: sua-api-key-aqui" \
  -H "Content-Type: application/json" \
  -d '{"instanceName": "runas", "qrcode": true}'
```

### Problema: Mensagens não são enviadas

**Solução**:
```bash
# 1. Verificar se instância está conectada
curl -X GET http://localhost:8080/instance/connectionState/runas \
  -H "apikey: sua-api-key-aqui"

# Deve retornar: {"state": "open"}

# 2. Verificar logs
docker-compose logs -f evolution-api

# 3. Reconectar WhatsApp
# Escanear QR Code novamente
```

### Problema: Instância desconecta frequentemente

**Solução**:
- Certifique-se de que o celular está com internet estável
- Não use o WhatsApp Web em outro lugar simultaneamente
- Mantenha o WhatsApp atualizado no celular

### Problema: Erro de autenticação

**Solução**:
```bash
# Verificar se API Key está correta no .env
cat .env | grep EVOLUTION_API_KEY

# Testar API Key
curl -X GET http://localhost:8080/instance/fetchInstances \
  -H "apikey: sua-api-key-aqui"
```

## 📊 Monitoramento

### Verificar Status da Instância

```bash
curl -X GET http://localhost:8080/instance/connectionState/runas \
  -H "apikey: sua-api-key-aqui"
```

### Listar Todas as Instâncias

```bash
curl -X GET http://localhost:8080/instance/fetchInstances \
  -H "apikey: sua-api-key-aqui"
```

### Logs em Tempo Real

```bash
docker-compose logs -f evolution-api
```

## 🔐 Segurança

### Boas Práticas

1. **Nunca exponha a API Key**
   - Use variáveis de ambiente
   - Não commite no Git
   - Rotacione periodicamente

2. **Restrinja acesso à porta 8080**
   - Em produção, use apenas rede interna
   - Configure firewall

3. **Use HTTPS em produção**
   - Configure reverse proxy (Nginx)
   - Obtenha certificado SSL

4. **Valide números de telefone**
   - Sempre use formato E.164
   - Valide antes de enviar

## 📚 Documentação Oficial

- **Evolution API**: https://doc.evolution-api.com/
- **GitHub**: https://github.com/EvolutionAPI/evolution-api
- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp

## 🆘 Suporte

Para problemas com a Evolution API:
- Issues no GitHub: https://github.com/EvolutionAPI/evolution-api/issues
- Documentação: https://doc.evolution-api.com/

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0
