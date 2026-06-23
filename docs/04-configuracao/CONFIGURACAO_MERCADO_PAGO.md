# Configuração do Mercado Pago

Este guia explica como configurar o Mercado Pago para aceitar pagamentos online na loja.

## 1. Criar Conta no Mercado Pago

1. Acesse [https://www.mercadopago.com.br](https://www.mercadopago.com.br)
2. Crie uma conta ou faça login
3. Acesse **Seu negócio** > **Configurações** > **Integrações**

## 2. Obter Credenciais de Teste (Sandbox)

### Access Token de Teste

1. No painel do Mercado Pago, vá em **Credenciais**
2. Selecione **Credenciais de teste**
3. Copie o **Access Token** (começa com `TEST-`)
4. Cole no arquivo `.env`:
   ```env
   MP_ACCESS_TOKEN=TEST-1234567890-123456-abc123def456-789012345
   ```

### Public Key de Teste

1. Na mesma página, copie a **Public Key** (também começa com `TEST-`)
2. Cole no arquivo `.env`:
   ```env
   MP_PUBLIC_KEY=TEST-abc123def-456789-012345-678901-abc123
   ```

### Webhook Secret

O webhook é fundamental para receber notificações de pagamento em tempo real.

#### Como configurar:

1. **Acesse o painel do Mercado Pago**: [https://www.mercadopago.com.br/developers/panel/webhooks](https://www.mercadopago.com.br/developers/panel/webhooks)

2. **Clique em "Criar webhook" ou "Nova URL"**

3. **Configure a URL do webhook**:
   ```
   https://pretty-dissuade-brunette.ngrok-free.dev/api/vendas/webhook/mercadopago
   ```
   ⚠️ **Importante**: Use sua URL do ngrok atual (a que está no `.env` em `FRONTEND_URL`)

4. **Selecione os eventos a serem notificados**:
   - ✅ `payment` - Quando um pagamento é criado/atualizado
   - ✅ `merchant_order` - Quando um pedido é criado/atualizado

5. **Copie o Secret gerado** pelo Mercado Pago

6. **Cole no arquivo `.env`**:
   ```env
   MP_WEBHOOK_SECRET=seu-webhook-secret-aqui
   ```

7. **Reinicie o serviço de vendas**:
   ```bash
   docker restart erp-vendas-dev
   ```

#### Testando o Webhook:

Após configurar, você pode testar enviando um evento de teste pelo painel do Mercado Pago:

1. No painel de webhooks, clique em "Testar"
2. Selecione o tipo de evento (ex: `payment`)
3. Envie o teste
4. Verifique os logs: `docker logs erp-vendas-dev`

Se ver uma linha como `INFO: Webhook recebido com sucesso`, está funcionando!

### Ambiente

Para testes, mantenha:
```env
MP_ENVIRONMENT=sandbox
```

## 3. Configurar Credenciais de Produção

Quando estiver pronto para produção:

1. Vá em **Credenciais de produção**
2. Complete o formulário de ativação de conta
3. Obtenha o **Access Token** e **Public Key** de produção
4. Atualize o `.env`:
   ```env
   MP_ACCESS_TOKEN=APP-1234567890123456-123456-abc123def456789012345678901234-789012345
   MP_PUBLIC_KEY=APP-abc123def456789012345678901234
   MP_ENVIRONMENT=production
   ```

## 4. Testar Pagamentos (Sandbox)

### Usuário de Teste do Mercado Pago

Use estas credenciais para fazer login no app Mercado Pago em modo teste:

- **Email/CPF**: TESTUSER4688266867233527599
- **Senha**: Cgm288PNKx
- **Código de verificação**: 634187

### Cartões de Teste

Use estes cartões para testar diferentes cenários:

| Cenário | Cartão | CVV | Validade |
|---------|--------|-----|----------|
| Aprovado | 5031 4332 1540 6351 | 123 | 11/25 |
| Recusado (fundos insuficientes) | 5031 4332 1540 6351 | 123 | 11/25 |
| Pendente | 5031 4332 1540 6351 | 123 | 11/25 |

**CPF para testes**: 12345678909

### PIX de Teste

1. Selecione PIX no checkout
2. O sistema gerará um QR Code
3. Use o app Mercado Pago em modo teste para pagar

## 5. Configurar Webhook

O webhook é essencial para receber notificações de pagamento:

1. URL do webhook:
   ```
   https://seu-dominio.com/api/vendas/webhook/mercadopago
   ```

2. Eventos a serem notificados:
   - `payment` - Pagamento criado/atualizado
   - `merchant_order` - Pedido criado/atualizado

3. O sistema processará automaticamente:
   - Pagamento aprovado → Confirma pedido
   - Pagamento recusado → Cancela reserva
   - Pagamento pendente → Aguarda confirmação

## 6. URLs de Redirecionamento

O sistema está configurado para redirecionar após o pagamento:

- **Sucesso**: `/c/{empresaSlug}/pedido/{numero_venda}`
- **Falha**: `/c/{empresaSlug}/checkout` (com mensagem de erro)
- **Pendente**: `/c/{empresaSlug}/pedido/{numero_venda}` (com status pendente)

## 7. Verificar Configuração

Execute este comando para verificar se as credenciais estão corretas:

```bash
curl -X GET \
  -H 'Authorization: Bearer SEU_ACCESS_TOKEN' \
  https://api.mercadopago.com/v1/payment_methods
```

Se retornar uma lista de métodos de pagamento, está configurado!

## 8. Documentação Oficial

- [Documentação Mercado Pago](https://www.mercadopago.com.br/developers/pt)
- [Credenciais](https://www.mercadopago.com.br/developers/panel/credentials)
- [Webhooks](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks)
- [Cartões de teste](https://www.mercadopago.com.br/developers/pt/docs/checkout-api/testing)

## Troubleshooting

### Erro: "Invalid credentials"

- Verifique se copiou o Access Token completo
- Certifique-se de usar credenciais de TEST em sandbox
- Reinicie o serviço de vendas após alterar o `.env`

### Webhook não está funcionando

- Verifique se a URL está acessível publicamente
- Use ngrok para testes locais
- Verifique os logs do serviço de vendas

### Pagamento não é confirmado

- Verifique se o webhook está configurado
- Veja os logs de webhook no painel do Mercado Pago
- Confirme que o `MP_WEBHOOK_SECRET` está correto

## Próximos Passos

Após configurar o Mercado Pago:

1. ✅ Teste um checkout completo em sandbox
2. ✅ Verifique se o webhook está sendo recebido
3. ✅ Confirme que o pedido é atualizado após pagamento
4. ✅ Solicite ativação das credenciais de produção
5. ✅ Atualize para credenciais de produção
6. ✅ Faça um pedido real de teste
