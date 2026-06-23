# Como Habilitar PIX no Mercado Pago Sandbox

## 🔍 Problema

PIX não aparece nas opções de pagamento ao ser redirecionado para o Mercado Pago, mesmo estando em modo Sandbox.

## ✅ Solução

### 1. **Verificar Configuração da Conta de Teste**

O PIX no Mercado Pago Sandbox tem algumas limitações:

#### **Importante sobre PIX em Sandbox:**
- ⚠️ **PIX nem sempre está disponível em todas as contas de teste sandbox**
- ⚠️ **Algumas contas sandbox antigas não suportam PIX**
- ⚠️ **PIX sandbox funciona apenas com credenciais específicas**

### 2. **Verificar suas Credenciais**

Acesse o Mercado Pago Developers:
1. Vá para: https://www.mercadopago.com.br/developers/panel
2. Entre com sua conta
3. Vá em **"Suas integrações"** → **"Credenciais de teste"**
4. Verifique se há uma seção sobre **"PIX"**

### 3. **Criar Novo Usuário de Teste com PIX**

Se sua conta não suporta PIX em sandbox, crie um novo usuário de teste:

```bash
# API para criar usuários de teste
POST https://api.mercadopago.com/users/test_user
Authorization: Bearer YOUR_ACCESS_TOKEN

{
  "site_id": "MLB"  # Brasil
}
```

Ou pelo painel: https://www.mercadopago.com.br/developers/panel/test-users

### 4. **Alternativa: Usar Produção**

⚠️ **IMPORTANTE**: Em produção, o PIX funciona normalmente. O problema é específico do Sandbox.

Para mudar para produção:

1. **Obter credenciais de produção**:
   - Acesse: https://www.mercadopago.com.br/developers/panel
   - Vá em **"Credenciais de produção"**
   - Copie o `Access Token` de produção

2. **Atualizar no banco de dados**:
```sql
UPDATE vendas.configuracoes_pagamento
SET 
  mercadopago_access_token = 'SEU_TOKEN_DE_PRODUCAO',
  mercadopago_public_key = 'SEU_PUBLIC_KEY_DE_PRODUCAO',
  environment = 'production'
WHERE empresa_id = 4;
```

3. **⚠️ ATENÇÃO**: Em produção, **pagamentos reais serão processados**!

### 5. **Verificar Configuração Atual**

Execute no banco de dados para ver sua configuração:

```sql
SELECT 
  empresa_id,
  mercadopago_access_token,
  mercadopago_public_key,
  environment,
  ativo
FROM vendas.configuracoes_pagamento
WHERE empresa_id = 4;
```

### 6. **Documentação Oficial do Mercado Pago**

📚 **Sobre PIX em Sandbox**:
- https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/integration-test/test-payments
- https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/payment-methods/pix

**Limitações conhecidas do PIX em Sandbox:**
- Pode não aparecer em todas as contas de teste
- Fluxo simulado (não gera QR Code real)
- Apenas para testes de integração

### 7. **Workaround para Desenvolvimento**

Se você só quer testar o **fluxo de pagamento** (não o PIX em si):

1. Use **Cartão de Crédito** no sandbox (sempre disponível)
2. Use os cartões de teste do Mercado Pago:
   - **Aprovado**: `5031 4332 1540 6351` (MasterCard)
   - **Rejeitado**: `5031 7557 3453 0604` (MasterCard)
   - CVV: `123`
   - Validade: Qualquer data futura

### 8. **Testar se PIX está Habilitado**

Execute um teste direto na API do Mercado Pago:

```bash
curl -X POST \
  'https://api.mercadopago.com/checkout/preferences' \
  -H 'Authorization: Bearer SEU_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "items": [
      {
        "title": "Teste PIX",
        "quantity": 1,
        "unit_price": 10.00
      }
    ],
    "payment_methods": {
      "excluded_payment_types": [],
      "excluded_payment_methods": []
    }
  }'
```

Depois acesse o `init_point` retornado e veja se PIX aparece.

### 9. **Nosso Código Está Correto**

O código já está configurado corretamente para suportar PIX:

```python
"payment_methods": {
    "excluded_payment_methods": [],  # Não excluir nenhum
    "excluded_payment_types": [],    # Inclui todos os tipos (PIX, cartão, boleto)
    "installments": 12,
    "default_installments": 1
},
"binary_mode": False  # Permite pagamentos pendentes (PIX)
```

### 10. **Próximos Passos Recomendados**

**Opção A - Continuar Testando (sem PIX real):**
- Use cartão de crédito de teste
- Foque em testar o fluxo de checkout, webhooks, etc.
- PIX será testado em produção

**Opção B - Testar com PIX (recomendado):**
1. Mude para **produção** no Mercado Pago
2. Use valores baixos (R$ 1,00) para testes reais
3. Tenha um celular com app bancário para escanear QR Code
4. ⚠️ **IMPORTANTE**: Configure webhook em produção também

**Opção C - Criar nova conta sandbox:**
1. Crie uma nova conta no Mercado Pago
2. Ative a conta para vendas
3. Gere novas credenciais de teste
4. Verifique se PIX está disponível

---

## 📊 Comparação Sandbox vs Produção

| Recurso | Sandbox | Produção |
|---------|---------|----------|
| PIX | ⚠️ Limitado (pode não aparecer) | ✅ Funciona perfeitamente |
| Cartão de Crédito | ✅ Cartões de teste | ✅ Cartões reais |
| Boleto | ⚠️ Simulado | ✅ Real |
| Webhooks | ✅ Funciona | ✅ Funciona |
| QR Code PIX | ❌ Não gera | ✅ Gera QR Code real |
| Cobranças | ❌ Simuladas | ✅ Reais (cuidado!) |

---

## ⚠️ IMPORTANTE

Se você decidir usar **produção** para testes com PIX:

1. ✅ Use valores pequenos (R$ 1,00)
2. ✅ Configure webhook de produção
3. ✅ Teste com pagamentos reais
4. ✅ Esteja preparado para processar estornos se necessário
5. ⚠️ **NÃO use em produção até estar 100% testado**

---

## 🆘 Se Nada Funcionar

Contate o suporte do Mercado Pago:
- https://www.mercadopago.com.br/developers/pt/support
- Pergunte especificamente sobre **"PIX em ambiente de testes (sandbox)"**

Ou considere usar produção com valores baixos para testes reais.
