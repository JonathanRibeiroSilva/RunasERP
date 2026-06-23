# ✅ MVP - Checklist de Testes

## Data: 12/06/2026

---

## 🎯 Funcionalidades Implementadas

### 1. Autenticação Separada
- ✅ Login de operadores via `/login` (email/senha)
- ✅ Login de clientes via `/auth/cliente/*` (OAuth + registro público)
- ✅ JWT com `user_type` e `empresa_id`

### 2. Controle de Acesso (RBAC)
- ✅ Menu "Configurações" visível apenas para ADMIN
- ✅ Menu "Meu Perfil" para todos usuários
- ✅ Rotas protegidas por role
- ✅ Usuário de teste: `operador@runas.com` / `Operador@123` (OPERADOR)

### 3. Loja Online - UX
- ✅ Botão "Ver Minha Loja" no Sidebar (dentro de "Loja Online")
- ✅ Abre catálogo público em nova aba
- ✅ Menu reorganizado (removido "Ver Catálogo")

### 4. Catálogo Público
- ✅ Endpoint `/empresas/publico/{slug}` implementado
- ✅ Frontend carrega `nome_fantasia` e `catalogo_titulo`
- ✅ Título dinâmico: `catalogo_titulo` → `nome_fantasia` → fallback
- ✅ 3 empresas seed criadas com nomes fantasia

---

## 🧪 Testes para Realizar

### Teste 1: Login de Operadores
1. Acessar `http://localhost/login`
2. Testar login com:
   - **ADMIN**: `admin@runas.com` / `Admin@123`
   - **OPERADOR**: `operador@runas.com` / `Operador@123`
3. ✅ Verificar redirecionamento para `/dashboard`

### Teste 2: Controle de Acesso por Role
1. **Como ADMIN**:
   - ✅ Menu "Configurações" deve estar visível
   - ✅ Clicar em "Configurações" → deve expandir submenu
   - ✅ Pode acessar "Empresa", "Usuários", "Integrações"

2. **Como OPERADOR**:
   - ✅ Menu "Configurações" **NÃO** deve aparecer
   - ✅ Menu "Meu Perfil" deve estar visível
   - ✅ Pode acessar Dashboard, Clientes, Produtos, Vendas, etc.

### Teste 3: Ver Minha Loja
1. Como ADMIN ou OPERADOR logado
2. No Sidebar, expandir "Loja Online"
3. Clicar em "Ver Minha Loja" (ícone de link externo)
4. ✅ Deve abrir `/c/distribuidora-central` em nova aba
5. ✅ Verificar se abre sem necessidade de login

### Teste 4: Nome Fantasia no Catálogo
1. Acessar `http://localhost/c/distribuidora-central` (sem login)
2. ✅ **VERIFICAR**: Título deve mostrar:
   - `"Catálogo Online - Distribuidora Central"` (catalogo_titulo)
   - OU `"Distribuidora Central"` (nome_fantasia)
3. ✅ Descrição: "Alimentos e bebidas com os melhores preços da região!"
4. ✅ Produtos devem aparecer (se houver seed de produtos)

### Teste 5: Outras Empresas (Slug)
1. Acessar `http://localhost/c/mercadinho-do-joao`
2. ✅ Título: "Mercadinho do João - Catálogo"
3. ✅ Descrição: "Seu mercadinho de bairro com qualidade e preço justo!"
4. ✅ Produtos do Mercadinho do João (se houver)

---

## 🐛 Problemas Conhecidos

### 1. Slug Hardcoded
- **Problema**: Botão "Ver Minha Loja" usa slug fixo `distribuidora-central`
- **Impacto**: Operadores de outras empresas não conseguem ver sua própria loja
- **Solução futura**: Backend retornar `empresa_slug` no JWT/user
- **Prioridade**: 🟡 Baixa (apenas 1 empresa em produção inicial)

### 2. Painel de Usuários
- **Problema**: `/configuracoes/usuarios` é apenas placeholder
- **Impacto**: ADMIN não consegue criar novos operadores via UI
- **Workaround**: Usar endpoint direto ou seed
- **Prioridade**: 🟡 Média (pode criar via API)

### 3. Produtos no Catálogo
- **Problema**: Não sabemos se existem produtos seed
- **Impacto**: Catálogo pode aparecer vazio
- **Solução**: Verificar seed de produtos ou criar manualmente
- **Prioridade**: 🔴 Alta (catálogo vazio não demonstra nada)

---

## 📋 Próximos Passos (Pós-MVP)

1. **Implementar painel de usuários** (CRUD completo)
2. **Slug dinâmico** (retornar `empresa_slug` no user)
3. **Seed de produtos** (popular catálogo para demonstração)
4. **Carrinho de compras** (já tem estrutura, testar fluxo)
5. **Pedidos online** (backend + frontend)
6. **Configurações da loja** (personalização de cores, logo, etc.)

---

## 🚀 Como Rodar

```bash
# Subir containers
docker-compose up -d

# Verificar logs
docker-compose logs -f api-gateway
docker-compose logs -f empresas

# Acessar aplicação
http://localhost
```

---

## 📞 Suporte

Se encontrar algum problema:
1. Verificar logs do Docker
2. Verificar se todos os containers estão rodando: `docker-compose ps`
3. Verificar se migrations rodaram: `docker-compose logs api-gateway | grep alembic`
