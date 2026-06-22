# Changelog: Implementação de Criação de Conta Durante Checkout

**Data**: 21/06/2026  
**Tipo**: Feature (Nova Funcionalidade)  
**Escopo**: Loja Online - Checkout com Criação de Conta

---

## 📋 Resumo

Implementação completa do fluxo de criação de conta durante o checkout na loja online. Agora clientes convidados podem optar por criar uma conta automaticamente durante a finalização da compra, recebendo credenciais por email.

---

## ✅ Funcionalidades Implementadas

### 1. **Frontend - Checkbox "Criar Conta"**
- ✅ Checkbox "Criar uma conta para mim" no Step 1 do checkout (modo guest)
- ✅ Campo `criar_conta` adicionado ao payload do checkout
- ✅ Exibição de toast quando conta é criada com sucesso
- ✅ Armazenamento automático do token JWT no localStorage

**Arquivo**: `frontend/src/pages/CatalogoPublico/CheckoutPage.tsx`

### 2. **Backend - Serviço de Email**
- ✅ Criado `email_service.py` no serviço de vendas
- ✅ Função `enviar_email_credenciais()` para envio de boas-vindas
- ✅ Template HTML responsivo com credenciais
- ✅ Configuração SMTP (Gmail) via variáveis de ambiente

**Arquivo**: `services/vendas/services/email_service.py`

### 3. **Backend - Lógica de Criação de Conta**
- ✅ Geração de senha temporária aleatória (8 caracteres)
- ✅ Criação do cliente no serviço de Clientes via HTTP
- ✅ Criação de autenticação no API Gateway
- ✅ Hash de senha usando bcrypt
- ✅ Geração de JWT token para o cliente
- ✅ Vinculação da venda ao cliente criado
- ✅ Envio de email com credenciais (não bloqueia checkout se falhar)

**Arquivo**: `services/vendas/services/loja_service.py` (método `processar_checkout`)

### 4. **API Gateway - Endpoint Interno**
- ✅ Novo endpoint `POST /auth/cliente/registrar-interno`
- ✅ Aceita hash de senha já gerado (não recalcula)
- ✅ Cria registro na tabela `gateway.clientes_auth`
- ✅ Validação de email duplicado

**Arquivo**: `api-gateway/routers/auth_cliente.py`

### 5. **Schemas**
- ✅ Campo `criar_conta: bool` adicionado a `CheckoutRequest`
- ✅ Campos `access_token`, `cliente_id`, `conta_criada` adicionados a `CheckoutResponse`

**Arquivo**: `services/vendas/schemas/loja.py`

### 6. **Configurações**
- ✅ Variáveis SMTP adicionadas ao `config.py` do vendas
- ✅ Variável `API_GATEWAY_URL` adicionada ao `.env`
- ✅ Variáveis `SECRET_KEY` e `ALGORITHM` para JWT

**Arquivos**: 
- `services/vendas/config.py`
- `.env`

### 7. **Dependências**
- ✅ `passlib[bcrypt]` - hash de senhas
- ✅ `python-jose[cryptography]` - geração de JWT
- ✅ `aiosmtplib` - envio de emails assíncronos

**Arquivo**: `services/vendas/requirements.txt`

---

## 🔄 Fluxo Completo

### Sem Criar Conta (Fluxo Existente)
1. Cliente preenche dados pessoais
2. Finaliza checkout como convidado
3. Venda é criada com `cliente_convidado_*` preenchidos
4. Pedido concluído

### Com Criação de Conta (Novo Fluxo)
1. Cliente preenche dados pessoais
2. ✅ Marca checkbox "Criar uma conta para mim"
3. Finaliza checkout
4. **Backend cria conta automaticamente**:
   - Gera senha temporária
   - Cria cliente no serviço de Clientes
   - Cria autenticação no API Gateway
   - Gera token JWT
   - Envia email com credenciais
5. **Frontend recebe resposta**:
   - `conta_criada: true`
   - `access_token: "eyJ..."`
   - `cliente_id: "uuid"`
6. Token é armazenado no localStorage
7. Toast exibe: "Conta criada! Verifique seu email para senha"
8. Cliente pode acessar área logada imediatamente

---

## 📧 Template de Email

O email enviado contém:
- 🎉 Mensagem de boas-vindas
- 📧 Email de login
- 🔑 Senha temporária
- 🔗 Link para acessar a conta
- ⚠️ Aviso de segurança

**Design**: Template HTML responsivo com gradientes e tema dark

---

## 🔐 Segurança

- ✅ Senha temporária com 8 caracteres aleatórios (letras + números)
- ✅ Hash bcrypt antes de armazenar
- ✅ JWT com expiração de 30 minutos
- ✅ Validação de email duplicado
- ✅ Logs estruturados de todas as operações
- ✅ Erros na criação de conta não bloqueiam o checkout
- ✅ Email de erro não expõe dados sensíveis

---

## 🧪 Para Testar

### 1. **Reiniciar Serviços** (instalar novas dependências)
```bash
docker-compose down
docker-compose up -d --build
```

### 2. **Verificar Logs**
```bash
docker logs erp-vendas-dev -f
docker logs erp-api-gateway-dev -f
```

### 3. **Testar Checkout**
1. Acesse a loja online
2. Adicione produtos ao carrinho
3. Vá para checkout
4. Selecione "Continuar como convidado"
5. Preencha dados (nome, email, telefone, CPF)
6. ✅ **Marque** "Criar uma conta para mim"
7. Finalize a compra
8. Verifique:
   - Toast de sucesso com mensagem de conta criada
   - Email recebido com credenciais
   - Token JWT armazenado no localStorage
   - Venda criada com `cliente_id` preenchido

### 4. **Verificar Banco de Dados**
```sql
-- Cliente criado
SELECT * FROM clientes.clientes WHERE email = 'teste@example.com';

-- Autenticação criada
SELECT * FROM gateway.clientes_auth WHERE email = 'teste@example.com';

-- Venda vinculada ao cliente
SELECT numero_venda, cliente_id, cliente_convidado_email 
FROM vendas.vendas 
WHERE cliente_convidado_email = 'teste@example.com'
ORDER BY criado_em DESC LIMIT 1;
```

---

## 🐛 Possíveis Erros e Soluções

### Erro: "SMTP não configurado"
**Solução**: Verificar variáveis no `.env`:
```env
SMTP_USER=noreply.runas@gmail.com
SMTP_PASSWORD=jwlnfpjthjkpewio
```

### Erro: "Erro ao criar cliente" (500)
**Solução**: Verificar se serviço de clientes está rodando:
```bash
docker ps | grep clientes
docker logs erp-clientes-dev
```

### Erro: "Email já cadastrado"
**Solução**: Email já existe no sistema. Use outro email ou faça login.

### Erro: Dependências não instaladas
**Solução**: Rebuild dos containers:
```bash
docker-compose down
docker-compose up -d --build
```

---

## 📝 Próximos Passos (Melhorias Futuras)

1. **Alterar Senha**: Endpoint para cliente alterar senha temporária
2. **Recuperar Senha**: Fluxo de "Esqueci minha senha"
3. **Validação de CPF**: Verificar se CPF já está cadastrado antes de criar conta
4. **Email Template**: Permitir customização do template por empresa
5. **SMS**: Enviar senha também por SMS/WhatsApp
6. **Confirmação de Email**: Adicionar link de ativação de conta
7. **Unificar Contas**: Fluxo para unificar pedidos convidados com conta criada

---

## 📊 Impacto

- ✅ Melhora a experiência do usuário (menos fricção)
- ✅ Aumenta conversão (não precisa criar conta antes)
- ✅ Facilita compras futuras (cliente já tem conta)
- ✅ Mantém histórico de compras vinculado
- ✅ Permite marketing direcionado

---

## 🔗 Arquivos Modificados

**Frontend**:
- ✅ `frontend/src/pages/CatalogoPublico/CheckoutPage.tsx`
- ✅ `frontend/src/pages/CatalogoPublico/CheckoutPage.scss`

**Backend - Vendas**:
- ✅ `services/vendas/config.py`
- ✅ `services/vendas/services/loja_service.py`
- ✅ `services/vendas/services/email_service.py` (novo)
- ✅ `services/vendas/schemas/loja.py`
- ✅ `services/vendas/requirements.txt`

**Backend - API Gateway**:
- ✅ `api-gateway/routers/auth_cliente.py`

**Configuração**:
- ✅ `.env`

**Documentação**:
- ✅ `CHANGELOG_CHECKOUT_CRIAR_CONTA.md` (este arquivo)

---

## ✅ Status: IMPLEMENTADO - PRONTO PARA TESTE

Aguardando reinicialização dos containers e testes.
