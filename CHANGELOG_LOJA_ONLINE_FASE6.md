# Changelog - Loja Online MVP - FASE 6: Endpoints Administrativos

## Data: 2026-06-11

## 📋 Resumo
Implementação completa de endpoints administrativos para configuração da loja online, incluindo gestão de entrega (taxas por bairro) e pagamento (credenciais Mercado Pago).

---

## 🆕 Novos Routers Criados

### 1. `routers/admin_entrega.py`
**Propósito**: Gerenciar configuração de entrega e taxas por bairro.

**Prefixo**: `/admin/entrega`

**Endpoints**:

#### Configuração da Loja
- `GET /admin/entrega/configuracao` - Obter configuração (taxa padrão)
- `PUT /admin/entrega/configuracao` - Atualizar taxa padrão

#### Faixas de Entrega (Exceções por Bairro)
- `GET /admin/entrega/faixas` - Listar todas as faixas
- `POST /admin/entrega/faixas` - Criar exceção para bairro
- `GET /admin/entrega/faixas/{faixa_id}` - Obter faixa específica
- `PUT /admin/entrega/faixas/{faixa_id}` - Atualizar faixa
- `DELETE /admin/entrega/faixas/{faixa_id}` - Deletar faixa

#### Simulação
- `GET /admin/entrega/simular/{cep}` - Simular cálculo de taxa para CEP

**Schemas**:
- `ConfiguracaoLojaResponse`: Configuração da loja
- `ConfiguracaoLojaUpdate`: Atualizar configuração
- `FaixaEntregaCreate`: Criar faixa
- `FaixaEntregaUpdate`: Atualizar faixa
- `FaixaEntregaResponse`: Resposta de faixa

**Funcionalidades**:
1. **Taxa Padrão**: Define taxa global para toda empresa
2. **Exceções por Bairro**: Permite configurar taxa diferente para bairros específicos
3. **Ativar/Desativar**: Controla se cobra taxa de entrega
4. **Simulação**: Testa cálculo antes de criar pedido

---

### 2. `routers/admin_pagamento.py`
**Propósito**: Gerenciar credenciais do Mercado Pago por empresa.

**Prefixo**: `/admin/pagamento`

**Endpoints**:

#### Status e Configuração
- `GET /admin/pagamento/status` - Verificar se está configurado (sem expor credenciais)
- `GET /admin/pagamento/configuracao` - Obter configuração
- `POST /admin/pagamento/configuracao` - Criar configuração
- `PUT /admin/pagamento/configuracao` - Atualizar configuração

#### Ativar/Desativar
- `PATCH /admin/pagamento/configuracao/ativar` - Ativar Mercado Pago
- `PATCH /admin/pagamento/configuracao/desativar` - Desativar Mercado Pago

#### Deletar
- `DELETE /admin/pagamento/configuracao` - Deletar configuração (irreversível)

**Schemas**:
- `ConfiguracaoPagamentoCreate`: Criar configuração
- `ConfiguracaoPagamentoUpdate`: Atualizar configuração
- `ConfiguracaoPagamentoResponse`: Resposta (não expõe access_token)
- `ConfiguracaoPagamentoStatusResponse`: Status (sem credenciais)

**Segurança**:
- ✅ `access_token` nunca é exposto nas respostas (apenas salvo no banco)
- ✅ `public_key` é exposto (necessário para frontend)
- ✅ Status endpoint não expõe credenciais

**Funcionalidades**:
1. **Multi-tenant**: Cada empresa tem suas próprias credenciais
2. **Ativar/Desativar**: Desabilita pagamento online sem deletar credenciais
3. **Rotação de Credenciais**: Atualizar tokens sem recriar configuração
4. **Status Público**: Verificar se está configurado sem expor dados sensíveis

---

## ♻️ Repositories Atualizados

### 3. `repositories/venda_repository.py`
**Adições**:

#### ConfiguracaoLojaRepository
**Métodos**:
- `criar()`: Cria configuração da loja
- `buscar_por_empresa()`: Busca por empresa_id
- `atualizar()`: Atualiza configuração

#### FaixaEntregaRepository
**Métodos**:
- `criar()`: Cria faixa de entrega
- `buscar_por_id()`: Busca por ID
- `buscar_por_bairro()`: Busca por empresa + bairro (case-insensitive)
- `listar()`: Lista faixas (com filtro de ativas)
- `atualizar()`: Atualiza faixa
- `deletar()`: Deleta faixa

**Características**:
- Busca case-insensitive para bairros (`.ilike()`)
- Suporta filtro por ativas/inativas
- Ordenação alfabética por bairro

---

## ♻️ Services Atualizados

### 4. `services/entrega_service.py`
**Mudanças**:

**Método atualizado**: `obter_config_loja()`
- Agora cria configuração padrão se não existir
- Retorna `ConfiguracaoLoja` (não mais `Optional`)

**Método atualizado**: `obter_faixa_por_bairro()`
- Usa `FaixaEntregaRepository`
- Mais eficiente e padronizado

**Método atualizado**: `calcular_taxa_entrega()`
- Aceita `bairro` opcional (evita revalidar CEP)
- Retorna apenas `Decimal` (não mais tuple)
- Mais simples e direto

**Integração**: Usa repositories para CRUD completo

---

## 📊 Fluxo de Configuração

### Configuração de Entrega

1. **Admin acessa**: `GET /admin/entrega/configuracao`
   - Retorna taxa padrão (ou cria com R$ 0,00)

2. **Admin atualiza taxa padrão**: `PUT /admin/entrega/configuracao`
   - Body: `{"taxa_entrega_padrao": 5.00, "cobrar_taxa_entrega": true}`

3. **Admin cria exceção para bairro**: `POST /admin/entrega/faixas`
   - Body: `{"bairro": "Centro", "taxa": 3.00, "ativo": true}`

4. **Cliente faz checkout**:
   - Sistema busca CEP → extrai bairro
   - Se bairro="Centro": usa R$ 3,00 (exceção)
   - Se bairro="Outro": usa R$ 5,00 (padrão)

5. **Admin simula cálculo**: `GET /admin/entrega/simular/12345678`
   - Retorna: bairro, taxa calculada, tipo (exceção ou padrão)

---

### Configuração de Pagamento

1. **Admin verifica status**: `GET /admin/pagamento/status`
   - Retorna: `{"configurado": false, "ativo": false}`

2. **Admin cria configuração**: `POST /admin/pagamento/configuracao`
   - Body: `{"mercadopago_access_token": "...", "mercadopago_public_key": "...", "ativo": true}`
   - Sistema salva credenciais no banco

3. **Cliente faz checkout com pagamento online**:
   - Sistema busca `access_token` do banco
   - Cria preferência no Mercado Pago
   - Retorna `init_point` para cliente pagar

4. **Admin desativa temporariamente**: `PATCH /admin/pagamento/configuracao/desativar`
   - Clientes não conseguem usar pagamento online
   - Credenciais permanecem salvas

5. **Admin reativa**: `PATCH /admin/pagamento/configuracao/ativar`
   - Pagamento online volta a funcionar

6. **Admin rotaciona credenciais**: `PUT /admin/pagamento/configuracao`
   - Atualiza `access_token` e `public_key`
   - Não perde configuração anterior

---

## 🔒 Segurança

### Proteção de Credenciais
✅ `access_token` nunca é exposto em respostas  
✅ Apenas `public_key` é retornado (necessário para frontend)  
✅ Endpoint de status não expõe credenciais sensíveis  

### Isolamento Multi-tenant
✅ `get_empresa_id()` garante isolamento por empresa  
✅ Queries filtram por `empresa_id`  
✅ Cada empresa gerencia suas próprias configurações  

### Validações
✅ Tokens mínimo 20 caracteres  
✅ Bairro mínimo 2 caracteres  
✅ Taxa de entrega >= 0  
✅ Não permite duplicar bairro (unique constraint)  

---

## 📝 Exemplos de Uso

### Exemplo 1: Configurar Taxa de Entrega

**Cenário**: Loja cobra R$ 8,00 de entrega, mas no Centro cobra apenas R$ 5,00.

```bash
# 1. Configurar taxa padrão
PUT /admin/entrega/configuracao
{
  "taxa_entrega_padrao": 8.00,
  "cobrar_taxa_entrega": true
}

# 2. Criar exceção para Centro
POST /admin/entrega/faixas
{
  "bairro": "Centro",
  "taxa": 5.00,
  "ativo": true
}

# 3. Simular cálculo
GET /admin/entrega/simular/01310100
# Retorna: {"bairro": "Centro", "taxa_calculada": 5.00, "tipo": "excecao"}

GET /admin/entrega/simular/04567890
# Retorna: {"bairro": "Vila Mariana", "taxa_calculada": 8.00, "tipo": "padrao"}
```

---

### Exemplo 2: Configurar Mercado Pago

**Cenário**: Loja quer habilitar pagamento online.

```bash
# 1. Verificar se já está configurado
GET /admin/pagamento/status
# Retorna: {"configurado": false, "ativo": false}

# 2. Criar configuração
POST /admin/pagamento/configuracao
{
  "mercadopago_access_token": "APP_USR-1234567890abcdef...",
  "mercadopago_public_key": "APP_USR-abcdef1234567890...",
  "ativo": true
}

# 3. Cliente faz checkout com PIX
# Sistema usa access_token do banco para criar preferência

# 4. Desativar temporariamente
PATCH /admin/pagamento/configuracao/desativar

# 5. Reativar
PATCH /admin/pagamento/configuracao/ativar
```

---

### Exemplo 3: Listar e Gerenciar Faixas

**Cenário**: Admin quer ver todas as exceções de bairro.

```bash
# 1. Listar todas as faixas
GET /admin/entrega/faixas
# Retorna: [
#   {"bairro": "Centro", "taxa": 5.00, "ativo": true},
#   {"bairro": "Zona Sul", "taxa": 12.00, "ativo": true}
# ]

# 2. Listar apenas ativas
GET /admin/entrega/faixas?apenas_ativas=true

# 3. Atualizar taxa da Zona Sul
PUT /admin/entrega/faixas/{faixa_id}
{
  "taxa": 15.00,
  "ativo": true
}

# 4. Desativar exceção (volta a usar taxa padrão)
PUT /admin/entrega/faixas/{faixa_id}
{
  "taxa": 12.00,
  "ativo": false
}

# 5. Deletar exceção
DELETE /admin/entrega/faixas/{faixa_id}
```

---

## 🧪 Testes Pendentes

### Testes de Entrega
- [ ] Criar configuração de loja
- [ ] Atualizar taxa padrão
- [ ] Criar faixa para bairro
- [ ] Validar que não aceita bairro duplicado
- [ ] Simular cálculo com exceção
- [ ] Simular cálculo com taxa padrão
- [ ] Desativar exceção (deve usar taxa padrão)
- [ ] Deletar exceção
- [ ] Listar faixas ativas/inativas

### Testes de Pagamento
- [ ] Verificar status (não configurado)
- [ ] Criar configuração
- [ ] Validar que não aceita empresa duplicada
- [ ] Obter configuração (não expõe access_token)
- [ ] Atualizar credenciais
- [ ] Desativar configuração
- [ ] Reativar configuração
- [ ] Deletar configuração
- [ ] Verificar status (configurado e ativo)

---

## 📚 Documentação Adicional

### Como Obter Credenciais do Mercado Pago

1. Acesse: https://www.mercadopago.com.br/developers
2. Faça login com sua conta Mercado Pago
3. Vá em "Suas aplicações" → "Criar aplicação"
4. Preencha os dados da aplicação:
   - Nome: "Loja Online - [Nome da Empresa]"
   - Descrição: "Integração de pagamentos online"
5. Copie as credenciais:
   - **Access Token** (privado - nunca compartilhar)
   - **Public Key** (público - pode ser exposto no frontend)
6. Configure as URLs de webhook:
   - Produção: `https://api.seudominio.com/loja/{empresa_slug}/webhook/mercadopago`
   - Desenvolvimento: `https://webhook.site/...` (para testes)

**Importante**: Cada empresa deve ter sua própria aplicação no Mercado Pago para fins contábeis e fiscais.

---

### Como Encontrar Nome do Bairro

O nome do bairro usado nas exceções deve corresponder ao retornado pela **API ViaCEP**.

**Método 1 - Simular**:
```bash
GET /admin/entrega/simular/01310100
# Retorna: {"bairro": "Bela Vista", ...}
```

**Método 2 - Testar ViaCEP**:
```bash
curl https://viacep.com.br/ws/01310100/json/
# Retorna: {"bairro": "Bela Vista", ...}
```

**Dica**: Use o nome exato retornado pela API (ex: "Bela Vista", não "bela vista" ou "Bela vista").

---

## 📊 Banco de Dados

### Tabelas Utilizadas
- `configuracoes_loja`: Taxa padrão de entrega por empresa
- `faixas_entrega`: Exceções de taxa por bairro
- `configuracoes_pagamento`: Credenciais Mercado Pago por empresa

### Constraints
- `uq_faixa_empresa_bairro`: Unique constraint (empresa_id, bairro)
- `configuracoes_pagamento.empresa_id`: Unique (uma config por empresa)
- `configuracoes_loja.empresa_id`: Unique (uma config por empresa)

---

## 🚀 Integração com Main

### Routers Registrados
```python
app.include_router(admin_entrega_router)  # /admin/entrega
app.include_router(admin_pagamento_router)  # /admin/pagamento
```

### Documentação Swagger
Acesse: `http://localhost:8004/docs`

**Tags**:
- `admin-entrega`: Configuração de Entrega
- `admin-pagamento`: Configuração de Pagamento

---

## ✅ Status

**FASE 6: COMPLETA** ✅

Todos os endpoints administrativos foram implementados e documentados. Sistema está pronto para:
1. Configurar taxa de entrega (padrão + exceções)
2. Gerenciar credenciais do Mercado Pago
3. Ativar/desativar funcionalidades
4. Testar via Swagger
5. Prosseguir para FASE 7 (Melhorias e Ajustes Finais)

**Próximo**: FASE 7 - Melhorias e Ajustes Finais
- Integrar histórico em todos os métodos de VendaService
- Melhorar rastreamento com histórico
- Edge cases e validações extras
