# 📱 Evolution API (WhatsApp)

Como o ERP envia notificações de WhatsApp pela Evolution API: quem chama, quando, com qual credencial, e como subir a Evolution no ambiente de desenvolvimento.

## 📋 Estado atual (conferido no código)

- **Quem envia é o serviço de vendas, direto.** O envio está em `services/vendas/services/notificacao_service.py` (`NotificacaoService._enviar_mensagem`, linhas 338-389), que faz um `POST` HTTP para a Evolution API com `httpx`.
- **O serviço `notificacoes` não participa.** O `services/notificacoes/main.py` só expõe `GET /health`; não há router, cliente Evolution nem consumidor de fila. O arquivo `services/notificacoes/integrations/evolution.py` citado em versões antigas deste guia **não existe**.
- **Só texto.** O código chama um único endpoint da Evolution (`/message/sendText/{instance}`). Não há envio de imagem/documento nem recebimento de mensagens (webhook).
- **A Evolution não roda em produção.** `docker-compose.prod.yml` não tem o serviço `evolution-api` (comentário nas linhas 494-495). No dev, ela fica atrás do profile `whatsapp`, porque a imagem `atendai/evolution-api` saiu do Docker Hub (`docker-compose.dev.yml:133-134`).

## 📨 Mensagens enviadas e quando

Todas são texto, montadas em `services/vendas/services/notificacao_service.py`. Uma falha no envio só gera log e não interrompe a operação que a disparou.

| Método | Disparado em | Telefone usado | Passa `empresa_id`? |
|---|---|---|---|
| `enviar_confirmacao_pedido` | Checkout da loja: `LojaService.processar_checkout` (`services/loja_service.py:530`) | `cliente_info['telefone']` | Sim |
| `enviar_pagamento_confirmado` | `VendaService.confirmar_venda` (`services/venda_service.py:1065`) | `venda.cliente_convidado_telefone` | Sim |
| `enviar_pedido_separado` | `VendaService.separar_venda` (`services/venda_service.py:1267`) | `venda.cliente_convidado_telefone` | Sim |
| `enviar_pedido_entregue` | `VendaService.entregar_venda` (`services/venda_service.py:1357`) | `venda.cliente_convidado_telefone` | Sim |
| `enviar_pedido_cancelado` | Cancelamento automático por timeout de pagamento: `jobs/verificar_pagamentos_pendentes.py:227` | `venda.cliente_convidado_telefone` | **Não** (só a credencial global vale) |
| `enviar_pedido_cancelado` | `jobs/verificar_timeouts_separacao.py:109`. Esse script não é agendado por nada (ver [jobs/README.md](../../../services/vendas/jobs/README.md)) | `venda.cliente_convidado_telefone` | **Não** |

Os caminhos da tabela são relativos a `services/vendas/`. Nenhum outro cancelamento (manual, por exemplo) envia WhatsApp.

O telefone é reduzido a dígitos e recebe o prefixo `55` quando não começa com ele (`_formatar_telefone`, linhas 20-37).

## 🔑 De onde vem a credencial

`credenciais_whatsapp(empresa_id)` em `services/vendas/services/configuracao_integracao_service.py:85` resolve, nesta ordem:

1. **Credencial do tenant**: se existe `configuracao_integracao` da empresa com `whatsapp_ativo = true`, `evolution_url` e `evolution_api_key_enc`, usa essa URL, a chave (decifrada com `INTEGRACOES_SECRET_KEY`, ver `services/vendas/utils/crypto.py`) e `evolution_instance`.
2. **Fallback global**: `EVOLUTION_API_URL` + `EVOLUTION_API_KEY` (+ `EVOLUTION_INSTANCE`) do `Settings` do vendas (`services/vendas/config.py:28-30`).
3. Nenhuma das duas: log `evolution_api_nao_configurada` e a mensagem não sai.

### Configuração por tenant (tela e API)

- Tela: **Configurações > Integrações** (`/configuracoes/integracoes`, `frontend/src/pages/Configuracoes/IntegracoesPage.tsx`).
- API: `GET`, `PUT` e `DELETE /integracoes` no gateway, só para admin (`api-gateway/routers/proxy.py:508-519`, `require_admin`), repassados ao router `services/vendas/routers/admin_integracao.py`.
- Campos do `PUT`: `evolution_url`, `evolution_api_key`, `evolution_instance`, `whatsapp_ativo` (mais os campos de SMTP). O `GET` nunca devolve a chave; devolve só `evolution_api_key_configurado: bool`.
- `DELETE` apaga a configuração, e o tenant volta ao fallback global.

### Variáveis de ambiente: atenção aos nomes

| Variável | Quem lê | Observação |
|---|---|---|
| `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE` | vendas (`config.py:28-30`) | Nenhum compose repassa essas ao container do vendas. |
| `EVOLUTION_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE` | ninguém | O compose as injeta no **notificacoes** (`docker-compose.dev.yml:462-464`, `docker-compose.prod.yml:496-498`), cujo `Settings` não as declara. |
| `EVOLUTION_API_KEY` | container `evolution-api` | Vira `AUTHENTICATION_API_KEY` (`docker-compose.dev.yml:158`, default `change-me`). |
| `EVOLUTION_SERVER_URL` | container `evolution-api` | Vira `SERVER_URL` (`docker-compose.dev.yml:160`, default `http://localhost:8080`). |

Na prática, o fallback global só funciona se `EVOLUTION_API_URL` e `EVOLUTION_API_KEY` chegarem ao processo do vendas por outro caminho. O `Settings` do vendas também lê um `.env` no diretório de trabalho (`env_file=".env"`). A CONFIRMAR: se algum ambiente fornece essas variáveis ao vendas. Sem isso, só funciona a credencial por tenant.

## 🚀 Subir a Evolution no desenvolvimento

O serviço `evolution-api` (`docker-compose.dev.yml:135-176`):

- imagem `atendai/evolution-api:latest`, container `erp-evolution-api-dev`, profile `whatsapp`;
- banco: o Postgres compartilhado `db`, schema `evolution` (`postgresql://erp:erp@db:5432/erp?schema=evolution`; o schema é criado por `postgres/init-schemas.sql`);
- cache: Redis `redis://redis:6379/2`, prefixo `evolution`;
- porta `8080:8080` publicada em todas as interfaces do host;
- healthcheck: `wget` em `http://localhost:8080/`.

```bash
# Chave da Evolution: defina EVOLUTION_API_KEY no .env da raiz (o .env.example mostra o formato)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Subir (a imagem precisa estar disponível localmente ou em outro registry)
docker compose -f docker-compose.dev.yml --profile whatsapp up -d evolution-api

# Logs
docker compose -f docker-compose.dev.yml logs -f evolution-api
```

De dentro da rede `erp-network`, a URL da Evolution é `http://evolution-api:8080`. É ela que vai em `evolution_url` na tela de Integrações (ou em `EVOLUTION_API_URL`, para o fallback global).

## 📱 Conectar um número (API da própria Evolution)

Os comandos abaixo usam endpoints da Evolution API, não do ERP. O código do ERP não os chama. A CONFIRMAR: o formato exato contra a versão da imagem em uso (`latest`), porque a v2 da Evolution exige campos extras em `instance/create`, como `integration`. Confira na [documentação oficial](https://doc.evolution-api.com/).

```bash
# Criar instância
curl -X POST http://localhost:8080/instance/create \
  -H "apikey: SUA_CHAVE" \
  -H "Content-Type: application/json" \
  -d '{"instanceName": "runas", "qrcode": true}'

# Obter o QR Code (base64) para escanear em WhatsApp > Aparelhos conectados
curl http://localhost:8080/instance/connect/runas -H "apikey: SUA_CHAVE"

# Estado da conexão
curl http://localhost:8080/instance/connectionState/runas -H "apikey: SUA_CHAVE"

# Listar instâncias (também serve para testar a chave)
curl http://localhost:8080/instance/fetchInstances -H "apikey: SUA_CHAVE"
```

A CONFIRMAR: se a imagem em uso tem interface web (manager) e em qual caminho.

## 🧪 Testar o envio (mesma chamada que o vendas faz)

`_enviar_mensagem` faz exatamente isto: `POST {url}/message/sendText/{instance}`, header `apikey`, corpo `{"number", "text"}`, timeout de 10s. Só `200` ou `201` contam como sucesso (`notificacao_service.py:359-378`).

```bash
curl -X POST http://localhost:8080/message/sendText/runas \
  -H "apikey: SUA_CHAVE" \
  -H "Content-Type: application/json" \
  -d '{"number": "5511999999999", "text": "Teste do ERP Runas"}'
```

## 🐛 Troubleshooting

Eventos de log do vendas, emitidos por `notificacao_service.py`:

| Log | Significado |
|---|---|
| `evolution_api_nao_configurada` | Nem credencial do tenant nem fallback global. Configure em Integrações, com `whatsapp_ativo` ligado. |
| `evolution_api_erro` | A Evolution respondeu com status diferente de 200/201 (`status_code` e `response` vêm no log). |
| `erro_enviar_mensagem_evolution` | Exceção de rede ou timeout (ex.: container `evolution-api` fora do ar, que é o caso em produção). |

- Cancelamento por timeout não notificou, mas o tenant tem WhatsApp configurado: esperado. Os jobs chamam `enviar_pedido_cancelado` sem `empresa_id`, então só o fallback global é tentado.
- Cliente logado não recebeu "pagamento confirmado", "separado" ou "entregue": essas mensagens usam só `cliente_convidado_telefone` da venda.
- Para conferir a chave, não abra o `.env`. Teste com `instance/fetchInstances` (acima).

## 🔐 Segurança

- A chave por tenant é gravada cifrada (`evolution_api_key_enc`). Sem `INTEGRACOES_SECRET_KEY`, a gravação falha em vez de salvar texto plano (`services/vendas/utils/crypto.py`).
- A API nunca devolve a chave. A tela mostra só se há uma configurada.
- No dev, a porta 8080 fica publicada em todas as interfaces do host (`"8080:8080"`). Não exponha a máquina com a chave padrão `change-me`.

## 📚 Documentação oficial

- Evolution API: https://doc.evolution-api.com/
- GitHub: https://github.com/EvolutionAPI/evolution-api
