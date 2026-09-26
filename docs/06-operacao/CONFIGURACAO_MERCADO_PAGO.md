# Configuração do Mercado Pago

Este guia explica como configurar o Mercado Pago para aceitar pagamentos online na loja.

## Como o sistema usa as credenciais (leia primeiro)

- As credenciais usadas em runtime ficam **no banco**, uma linha por empresa, em `vendas.configuracoes_pagamento`: access token e segredo do webhook cifrados (colunas `mercadopago_access_token_enc` e `mercadopago_webhook_secret_enc`, precisam de `INTEGRACOES_SECRET_KEY`), public key em claro (`services/vendas/models/venda.py`).
- As variáveis `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY` e `MP_WEBHOOK_SECRET` do `.env` **não são lidas pelo serviço de vendas em runtime** (`services/vendas/config.py` só declara `MP_ENVIRONMENT`). Elas servem de fonte para o script `services/vendas/scripts/set_mercadopago_credentials.py`, que as grava no banco (só em sandbox).
- `MP_ENVIRONMENT` (`sandbox` por padrão no código e no `docker-compose.dev.yml`; o `docker-compose.prod.yml` usa `production` por padrão) é a chave que decide sandbox x produção.
- Cada empresa (tenant) tem a sua própria configuração.

## 1. Criar Conta no Mercado Pago

1. Acesse [https://www.mercadopago.com.br](https://www.mercadopago.com.br)
2. Crie uma conta ou faça login
3. Acesse **Seu negócio** > **Configurações** > **Integrações**

## 2. Obter Credenciais de Teste (Sandbox)

### Access Token e Public Key de Teste

1. No painel do Mercado Pago, vá em **Credenciais**
2. Selecione **Credenciais de teste**
3. Copie o **Access Token** e a **Public Key** (ambos começam com `TEST-`)
4. Cole no arquivo `.env` (modelo em `.env.example`):
   ```env
   MP_ACCESS_TOKEN=TEST-<seu-access-token>
   MP_PUBLIC_KEY=TEST-<sua-public-key>
   MP_ENVIRONMENT=sandbox
   ```
5. Grave no banco (o container precisa ter sido **recriado** depois de mudar o `.env`, pois `docker restart` não relê variáveis: `docker compose -f docker-compose.dev.yml up -d vendas`):
   ```bash
   docker exec -it erp-vendas-dev python scripts/set_mercadopago_credentials.py [empresa_id ...]
   ```
   Sem argumentos o script atualiza apenas `empresa_id=4` (loja de teste padrão do script). Ele recusa rodar com `MP_ENVIRONMENT=production`.

   Alternativa: `POST /pagamentos/admin/configuracao` (ver seção 6).

### Webhook Secret

O webhook é fundamental para receber notificações de pagamento em tempo real. O sistema valida a assinatura (`x-signature`, HMAC-SHA256) quando o segredo está gravado para a empresa.

1. **Acesse o painel do Mercado Pago**: [https://www.mercadopago.com.br/developers/panel/webhooks](https://www.mercadopago.com.br/developers/panel/webhooks)
2. **Crie o webhook** com os eventos `payment` e `merchant_order` (os dois tópicos que a rota trata, `services/vendas/routers/webhook.py`).
3. **URL do webhook**. O sistema já envia a URL em cada preference (`notification_url`), no formato:
   ```
   {API_BASE_URL}/loja/{empresa_slug}/webhook/mercadopago
   ```
   Em produção `API_BASE_URL=https://app.runaserp.com.br/api` (`.env.production.example`), ou seja:
   `https://app.runaserp.com.br/api/loja/{empresa_slug}/webhook/mercadopago`. Para receber notificações em desenvolvimento local, `API_BASE_URL` precisa apontar para uma URL pública (ex.: túnel).
   A CONFIRMAR: se o painel do MP exige uma URL cadastrada para revelar o segredo de assinatura.
4. **Copie o Secret gerado** pelo Mercado Pago e coloque em `MP_WEBHOOK_SECRET` no `.env`:
   ```env
   MP_WEBHOOK_SECRET=<segredo-do-webhook>
   ```
5. Grave no banco com o script da seção anterior (ele também aplica `MP_WEBHOOK_SECRET`) ou informe `mercadopago_webhook_secret` no `PUT /pagamentos/admin/configuracao`.

Sem segredo gravado, a rota aceita notificações não assinadas (com warning no log); com segredo, uma assinatura errada devolve **401**.

#### Testando o Webhook

- Rota de verificação: `GET {API_BASE_URL}/loja/{empresa_slug}/webhook/mercadopago/test` deve responder `{"status":"ok", ...}`.
- Depois de enviar um evento de teste pelo painel do MP, veja os logs: `docker logs erp-vendas-dev`. Os logs são JSON (structlog): procure `webhook_mercadopago_recebido_completo` e, em caso de sucesso, `webhook_processado_sucesso`.

### Ambiente

Para testes, mantenha:
```env
MP_ENVIRONMENT=sandbox
```

## 3. Configurar Credenciais de Produção

Quando estiver pronto para produção:

1. Vá em **Credenciais de produção** no painel do MP
2. Complete o formulário de ativação de conta
3. Obtenha o **Access Token** e a **Public Key** de produção
4. Grave-os **pela API/tela de integrações** (`PUT /pagamentos/admin/configuracao`, seção 6): o script do passo anterior recusa `MP_ENVIRONMENT=production`.
5. Defina `MP_ENVIRONMENT=production` no ambiente do serviço de vendas.

## 4. Testar Pagamentos (Sandbox)

### Usuário de Teste do Mercado Pago

Crie um usuário de teste pelo painel (Contas de teste): [https://www.mercadopago.com.br/developers/panel/test-users](https://www.mercadopago.com.br/developers/panel/test-users). Não versione e-mail, senha ou código de verificação desses usuários.

### Cartões de Teste

O cartão de teste Mastercard usado nesta documentação é `5031 4332 1540 6351`, CVV `123`, validade: qualquer data futura. O resultado do pagamento (aprovado, recusado, pendente) **não** depende do número do cartão, e sim do nome do titular e do documento informados no checkout.

A CONFIRMAR: os nomes de titular que forçam cada cenário (aprovado, recusado, fundos insuficientes, pendente); consulte [Cartões de teste](https://www.mercadopago.com.br/developers/pt/docs/checkout-api/testing).

**CPF para testes**: 12345678909

### PIX de Teste

1. Selecione PIX no checkout
2. O sistema gerará um QR Code
3. Use o app Mercado Pago em modo teste para pagar

PIX em sandbox pode não estar disponível: ver `MERCADOPAGO_PIX_SANDBOX.md`.

## 5. Como o webhook é processado

Para cada pagamento notificado, o sistema relê o pagamento na API do MP pelo id e age conforme o status (`services/vendas/services/mercadopago_service.py`):

- **Aprovado** → confirma a venda (baixa de estoque) e limpa o carrinho.
- **Recusado/cancelado** em venda ainda não paga → a venda volta/permanece `PENDENTE_PAGAMENTO`, aguardando nova tentativa (não cancela na hora).
- **Reembolsado/chargeback** → devolve o estoque e marca a venda como reembolsada.
- A idempotência é garantida pela tabela `webhooks_processados`.

## 6. Endpoints administrativos de configuração

Prefixo `/pagamentos/admin` (o gateway encaminha `/pagamentos` ao serviço de vendas; `services/vendas/routers/admin_pagamento.py`). Todos operam na empresa do usuário logado:

| Verbo | Rota | O que faz |
|-------|------|-----------|
| GET | `/pagamentos/admin/status` | Diz se está configurado/ativo e se há segredo de webhook gravado (sem credenciais) |
| GET | `/pagamentos/admin/configuracao` | Lê a configuração (só `public_key`, nunca o access token); 404 se não existir |
| POST | `/pagamentos/admin/configuracao` | Cria; 409 se já existe |
| PUT | `/pagamentos/admin/configuracao` | Atualiza; 404 se não existe |
| PATCH | `/pagamentos/admin/configuracao/ativar` | Ativa |
| PATCH | `/pagamentos/admin/configuracao/desativar` | Desativa |
| DELETE | `/pagamentos/admin/configuracao` | Remove (irreversível) |

Corpo do POST/PUT: `mercadopago_access_token` e `mercadopago_public_key` (mínimo 20 caracteres cada), `mercadopago_webhook_secret` (opcional; vazio mantém o já gravado) e `ativo` (padrão `true`).

## 7. URLs de Redirecionamento

O sistema redireciona após o pagamento para a página do pedido, sempre a mesma rota, mudando só o parâmetro `status` (`mercadopago_service.py:151-153`):

- **Sucesso**: `{FRONTEND_URL}/c/{empresaSlug}/pedido/{numero_venda}?status=success`
- **Falha**: `{FRONTEND_URL}/c/{empresaSlug}/pedido/{numero_venda}?status=failure`
- **Pendente**: `{FRONTEND_URL}/c/{empresaSlug}/pedido/{numero_venda}?status=pending`

O `auto_return` só é enviado quando a URL de sucesso é HTTPS (o MP rejeita `localhost`); em dev local o comprador volta pelo botão do checkout.

## 8. Verificar Configuração

Execute este comando para verificar se as credenciais estão corretas:

```bash
curl -X GET \
  -H 'Authorization: Bearer SEU_ACCESS_TOKEN' \
  https://api.mercadopago.com/v1/payment_methods
```

Se retornar uma lista de métodos de pagamento, está configurado!

## 9. Documentação Oficial

- [Documentação Mercado Pago](https://www.mercadopago.com.br/developers/pt)
- [Credenciais](https://www.mercadopago.com.br/developers/panel/credentials)
- [Webhooks](https://www.mercadopago.com.br/developers/pt/docs/your-integrations/notifications/webhooks)
- [Cartões de teste](https://www.mercadopago.com.br/developers/pt/docs/checkout-api/testing)

## Troubleshooting

### Erro: "Invalid credentials"

- Verifique se copiou o Access Token completo
- Certifique-se de usar credenciais de TEST em sandbox
- Lembre que a credencial vigente é a do **banco**: depois de alterar o `.env`, rode de novo o script da seção 2 (ou o `PUT`)

### Webhook não está funcionando

- Verifique se a URL está acessível publicamente (`.../webhook/mercadopago/test`)
- Use ngrok (ou outro túnel) para testes locais e aponte `API_BASE_URL` para ele
- Verifique os logs do serviço de vendas

### Pagamento não é confirmado

- Verifique nos logs se chegou `webhook_mercadopago_recebido_completo`
- Veja os logs de webhook no painel do Mercado Pago
- `webhook_assinatura_invalida` (401) indica que o segredo gravado no banco não confere com o do painel

## Próximos Passos

Após configurar o Mercado Pago:

1. Teste um checkout completo em sandbox
2. Verifique se o webhook está sendo recebido
3. Confirme que o pedido é atualizado após pagamento
4. Solicite ativação das credenciais de produção
5. Grave as credenciais de produção (seção 3)
6. Faça um pedido real de teste
