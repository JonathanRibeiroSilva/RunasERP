# ✅ Teste: Criação de Conta Durante Checkout

**Data**: 21/06/2026  
**Status**: ✅ **IMPLEMENTADO E PRONTO PARA TESTE**

---

## 📦 O Que Foi Implementado

### Backend
1. ✅ Serviço de email (`services/vendas/services/email_service.py`)
2. ✅ Lógica de criação de conta no checkout (`services/vendas/services/loja_service.py`)
3. ✅ Endpoint interno no API Gateway (`/auth/cliente/registrar-interno`)
4. ✅ Schemas atualizados com campos de autenticação
5. ✅ Configurações e variáveis de ambiente adicionadas
6. ✅ Dependências instaladas (passlib, python-jose, aiosmtplib)
7. ✅ Containers reconstruídos e rodando

### Frontend
1. ✅ Checkbox "Criar uma conta para mim" no checkout
2. ✅ Campo `criar_conta` enviado no payload
3. ✅ Tratamento da resposta com token JWT
4. ✅ Armazenamento do token no localStorage

---

## 🧪 Como Testar

### Passo 1: Acessar a Loja Online
```
https://pretty-dissuade-brunette.ngrok-free.dev/loja/distribuidora-central
```

### Passo 2: Adicionar Produtos ao Carrinho
1. Navegue pelo catálogo
2. Clique em "Adicionar ao Carrinho" em alguns produtos
3. Clique no ícone do carrinho para ir ao checkout

### Passo 3: Fazer Checkout Como Convidado COM Criação de Conta
1. Na tela inicial do checkout, clique em **"Continuar como convidado"**
2. Preencha os dados:
   - **Nome**: Seu nome completo
   - **Email**: Use um email real para receber as credenciais
   - **Telefone**: 11999999999 (ou seu número)
   - **CPF**: 10600071936 (CPF válido de teste)
3. ✅ **IMPORTANTE**: Marque a checkbox **"Criar uma conta para mim"**
4. Escolha tipo de entrega (Retirada ou Delivery)
5. Escolha forma de pagamento
6. Clique em "Finalizar Pedido"

### Passo 4: Verificar Resultado
Após finalizar, você deve ver:

✅ **No Frontend**:
- Toast de sucesso: "Pedido criado com sucesso! Sua conta foi criada! Verifique seu email para a senha de acesso."
- Redirecionamento para Mercado Pago (se escolheu pagamento online)

✅ **No Email** (verificar caixa de entrada):
- Email de boas-vindas da Runas ERP
- Credenciais de acesso:
  - Email: o email que você forneceu
  - Senha temporária: 8 caracteres aleatórios
- Link para acessar a conta

✅ **No Navegador** (DevTools > Application > Local Storage):
- Deve ter uma chave `access_token` com o JWT

### Passo 5: Fazer Login Com as Credenciais
1. Vá para: `https://pretty-dissuade-brunette.ngrok-free.dev/loja/login`
2. Use o email e senha temporária recebidos
3. Deve fazer login com sucesso

---

## 🔍 Como Verificar no Banco de Dados

### Verificar Cliente Criado
```sql
SELECT id, nome, email, cpf, telefone, criado_em
FROM clientes.clientes
WHERE email = 'SEU_EMAIL@example.com'
ORDER BY criado_em DESC
LIMIT 1;
```

### Verificar Autenticação Criada
```sql
SELECT id, email, cliente_id, empresa_id, ativo, criado_em
FROM gateway.clientes_auth
WHERE email = 'SEU_EMAIL@example.com'
ORDER BY criado_em DESC
LIMIT 1;
```

### Verificar Venda Vinculada ao Cliente
```sql
SELECT 
    v.numero_venda,
    v.cliente_id,
    c.nome as cliente_nome,
    c.email as cliente_email,
    v.valor_total,
    v.status,
    v.criado_em
FROM vendas.vendas v
LEFT JOIN clientes.clientes c ON v.cliente_id = c.id
WHERE c.email = 'SEU_EMAIL@example.com'
ORDER BY v.criado_em DESC
LIMIT 1;
```

---

## 🐛 Troubleshooting

### Problema: Não recebeu email
**Causas possíveis**:
- Email foi para spam (verificar pasta de spam)
- Configuração SMTP não está funcionando
- Email inválido

**Solução**:
1. Verificar logs do serviço de vendas:
```bash
docker logs erp-vendas --tail 50 | Select-String "email"
```

2. Se houver erro de SMTP, verificar variáveis no `.env`:
```env
SMTP_USER=noreply.runas@gmail.com
SMTP_PASSWORD=jwlnfpjthjkpewio
```

### Problema: Erro 500 ao finalizar checkout
**Solução**:
1. Verificar logs:
```bash
docker logs erp-vendas --tail 50
docker logs erp-api-gateway --tail 50
```

2. Se erro de conexão com clientes service:
```bash
docker ps | Select-String "clientes"
docker logs erp-clientes --tail 30
```

### Problema: Token não foi salvo no localStorage
**Solução**:
1. Abrir DevTools > Console
2. Verificar se há erros JavaScript
3. Verificar se resposta do checkout tem `conta_criada: true`

### Problema: Email já cadastrado
**Solução**:
Se você já testou antes com o mesmo email, use outro email ou delete o registro:
```sql
-- CUIDADO: Apenas em desenvolvimento!
DELETE FROM gateway.clientes_auth WHERE email = 'SEU_EMAIL@example.com';
DELETE FROM clientes.clientes WHERE email = 'SEU_EMAIL@example.com';
```

---

## 📋 Checklist de Teste

- [ ] Acessei a loja online
- [ ] Adicionei produtos ao carrinho
- [ ] Escolhi "Continuar como convidado"
- [ ] Preenchi todos os dados corretamente
- [ ] ✅ Marquei "Criar uma conta para mim"
- [ ] Finalizei o pedido com sucesso
- [ ] Recebi toast de confirmação
- [ ] Recebi email com credenciais
- [ ] Token JWT foi salvo no localStorage
- [ ] Consegui fazer login com as credenciais
- [ ] Venda foi vinculada ao cliente no banco

---

## 📊 Comparação: Com vs Sem Criação de Conta

### Sem Marcar Checkbox (Fluxo Antigo)
```json
// Response
{
  "venda_id": "uuid",
  "numero_venda": "V-2026-4-00001",
  "status": "PENDENTE_PAGAMENTO",
  "valor_total": 100.00,
  "mercadopago_init_point": "https://...",
  "mensagem": "Pedido criado com sucesso! Complete o pagamento...",
  "access_token": null,
  "cliente_id": null,
  "conta_criada": false
}

// Banco de dados
vendas.vendas:
  - cliente_id: NULL
  - cliente_convidado_nome: "João Silva"
  - cliente_convidado_email: "joao@email.com"
```

### ✅ Com Checkbox Marcada (Fluxo Novo)
```json
// Response
{
  "venda_id": "uuid",
  "numero_venda": "V-2026-4-00001",
  "status": "PENDENTE_PAGAMENTO",
  "valor_total": 100.00,
  "mercadopago_init_point": "https://...",
  "mensagem": "Pedido criado! Sua conta foi criada! Verifique seu email...",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "cliente_id": "uuid-do-cliente",
  "conta_criada": true
}

// Banco de dados
clientes.clientes:
  - id: uuid-do-cliente
  - nome: "João Silva"
  - email: "joao@email.com"
  - cpf: "10600071936"
  - criado_em: 2026-06-21 ...

gateway.clientes_auth:
  - id: uuid
  - email: "joao@email.com"
  - senha_hash: "$2b$12$..."
  - cliente_id: uuid-do-cliente
  - empresa_id: 4

vendas.vendas:
  - cliente_id: uuid-do-cliente (vinculado!)
  - cliente_convidado_nome: "João Silva"
  - cliente_convidado_email: "joao@email.com"
```

---

## ✅ Status Final

**Implementação**: ✅ COMPLETA  
**Backend**: ✅ RODANDO (vendas + api-gateway)  
**Dependências**: ✅ INSTALADAS  
**Variáveis de Ambiente**: ✅ CONFIGURADAS  
**Pronto para Teste**: ✅ **SIM**

---

## 📞 Suporte

Se encontrar problemas durante o teste:

1. Verifique os logs:
```bash
docker logs erp-vendas --tail 100
docker logs erp-api-gateway --tail 100
docker logs erp-clientes --tail 50
```

2. Verifique se todos os serviços estão rodando:
```bash
docker ps
```

3. Se necessário, reinicie os serviços:
```bash
docker-compose restart vendas api-gateway clientes
```

**Boa sorte com os testes! 🚀**
