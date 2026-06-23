# 🧪 Guia de Teste - Checkout com Máscaras e Validações

## ✅ O que foi implementado até agora:

### CheckoutPage
- ✅ Máscaras nos inputs (CPF, Telefone, CEP)
- ✅ Validação em tempo real
- ✅ Toast notifications (sem alerts)
- ✅ Remoção de máscaras antes de enviar ao backend
- ✅ Email opcional (não obrigatório)

### LoginPage
- ✅ Toast notifications
- ✅ Loading com feedback visual

---

## 🎯 Como Testar o Checkout

### Passo 1: Acessar o Catálogo
1. Abra: `https://pretty-dissuade-brunette.ngrok-free.dev/c/distribuidora-central`
2. Adicione pelo menos 1 produto ao carrinho
3. Clique no botão **"Carrinho"** (agora sempre visível)

### Passo 2: Página do Carrinho
1. Verifique se o produto está no carrinho
2. Clique em **"Finalizar Compra"**

### Passo 3: Dados do Cliente (Step 1)

#### Teste 1: Validação de campos obrigatórios
- Deixe todos os campos vazios
- Clique em **"Continuar"**
- ✅ **Esperado**: Toast vermelho com erro "Nome é obrigatório"

#### Teste 2: Validação de telefone
- **Nome**: João Silva
- **Telefone**: Digite `11` e pare
- Clique fora do campo (blur)
- ✅ **Esperado**: Erro em vermelho abaixo do campo "Telefone deve ter 10 ou 11 dígitos"

#### Teste 3: Máscara de telefone
- **Telefone**: Digite `11987654321`
- ✅ **Esperado**: Deve formatar automaticamente para `(11) 98765-4321`

#### Teste 4: Validação de CPF (opcional, mas se preenchido deve ser válido)
- **CPF**: Digite `12345678901`
- Clique fora do campo
- ✅ **Esperado**: Erro "CPF inválido" (dígitos verificadores incorretos)

#### Teste 5: CPF válido
- **CPF**: Digite `12345678909` (CPF de teste válido)
- ✅ **Esperado**: Formata para `123.456.789-09` e não mostra erro

#### Teste 6: Email opcional
- Deixe o email vazio
- Preencha os outros campos corretamente
- ✅ **Esperado**: Deve permitir continuar sem email

#### Teste 7: Email inválido
- **Email**: Digite `emailinvalido`
- Clique fora do campo
- ✅ **Esperado**: Erro "Email inválido"

### Passo 4: Entrega (Step 2)

#### Teste 8: Retirada
- Selecione **"Retirar no local"**
- Clique em **"Continuar"**
- ✅ **Esperado**: Deve avançar para Step 3 (Pagamento)

#### Teste 9: Delivery com CEP
- Volte para Step 2 (botão "Voltar")
- Selecione **"Entrega em domicílio"**
- **CEP**: Digite `01310100`
- ✅ **Esperado**: 
  - Formata para `01310-100`
  - Aparece "Buscando endereço..." 
  - Preenche automaticamente: Avenida Paulista, Bela Vista, São Paulo, SP
- Preencha o **Número**: 1000
- Clique em **"Continuar"**

### Passo 5: Pagamento (Step 3)

#### Teste 10: Finalizar com PIX
- Selecione **PIX**
- Clique em **"Finalizar Compra"**
- ✅ **Esperado**:
  - Toast azul aparece: "Processando pedido..."
  - Se sucesso: Toast verde "Pedido realizado com sucesso!"
  - **Antes**: Deveria redirecionar para Mercado Pago (se webhook configurado)
  - **Agora**: Redireciona para página de rastreamento

---

## 🔍 Verificando o Backend

### Ver logs do serviço:
```bash
docker logs -f erp-vendas-dev
```

### O que você deve ver:
```
INFO: POST /loja/checkout HTTP/1.1 200 OK
```

Se ver `422`, significa que ainda tem erro de validação.

---

## 🐛 Troubleshooting

### Erro 422 ainda aparece?
1. Verifique os logs: `docker logs erp-vendas-dev | tail -50`
2. Abra DevTools (F12) → Network → Selecione a requisição POST `/loja/checkout`
3. Veja a resposta (Response tab) para detalhes do erro

### Toast não aparece?
1. Verifique se não tem erro no console (F12)
2. O ToastContainer está no `main.tsx`

### Máscaras não funcionam?
1. Verifique se o componente `MaskedInput` está sendo importado corretamente
2. Limpe o cache do navegador (Ctrl+Shift+R)

### Email fake sendo enviado?
- ❌ **NÃO deve mais** - Foi corrigido para enviar `undefined` se vazio

---

## 📸 Comportamentos Esperados

### ✅ Sucesso:
- Máscaras aplicadas enquanto digita
- Validações em tempo real (vermelho abaixo do campo)
- Toast verde no sucesso
- Toast azul durante processamento
- Toast vermelho em erro (sem alert!)

### ❌ O que NÃO deve acontecer:
- ❌ Alerts do navegador (window.alert)
- ❌ Erro 422 no checkout
- ❌ Enviar dados com máscara para o backend
- ❌ Campos aceitarem valores inválidos

---

## 🎯 Checklist de Validação

### Máscaras Visuais:
- [ ] CPF: `123.456.789-09`
- [ ] Telefone: `(11) 98765-4321`
- [ ] CEP: `01310-100`

### Validações:
- [ ] CPF com dígitos verificadores
- [ ] Telefone com 10 ou 11 dígitos
- [ ] Email formato válido
- [ ] CEP com 8 dígitos

### Toast:
- [ ] Loading azul ao processar
- [ ] Sucesso verde
- [ ] Erro vermelho
- [ ] Sem alerts do navegador

### Backend:
- [ ] Recebe dados SEM máscara
- [ ] Aceita email vazio (undefined)
- [ ] Retorna 200 OK (não 422)

---

## 📝 Dados de Teste Válidos

### Cliente:
```
Nome: João Silva
Telefone: (11) 98765-4321
Email: joao@teste.com (opcional - pode deixar vazio)
CPF: 123.456.789-09 (opcional - CPF de teste válido)
```

### Endereço (Delivery):
```
CEP: 01310-100 (Av. Paulista, SP - preenche automático)
Número: 1000
Complemento: Apt 101 (opcional)
```

---

## 🚀 Próximos Testes

Após validar o Checkout, testar:
1. **LoginPage** - Toast nas mensagens de erro
2. **RegisterPage** - Máscaras e validações (próxima implementação)
3. **ClienteFormPage** - Formulário completo com máscaras

---

## 📊 Status Atual

| Tela | Máscaras | Validações | Toast | Status |
|------|----------|------------|-------|--------|
| CheckoutPage | ✅ | ✅ | ✅ | **Testar agora** |
| LoginPage | N/A | ✅ | ✅ | **Testar agora** |
| RegisterPage | ⏳ | ⏳ | ⏳ | Pendente |
| ClienteFormPage | ⏳ | ⏳ | ⏳ | Pendente |

---

**Última atualização**: 2026-06-12 19:51 UTC  
**Versão**: Fase 1 - Parcial
