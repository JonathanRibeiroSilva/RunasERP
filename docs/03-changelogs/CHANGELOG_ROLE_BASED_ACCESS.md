# Controle de Acesso Baseado em Role

**Data**: 2026-06-12  
**Versão**: 1.1.0

## 🎯 Objetivo

Implementar controle de acesso baseado em role (ADMIN/OPERADOR) para separar permissões no frontend:
- **ADMIN**: Acesso total incluindo configurações da empresa
- **OPERADOR**: Acesso limitado às operações do dia a dia

---

## 📋 Mudanças Implementadas

### 1. Sidebar com Controle de Acesso

**Arquivo**: `frontend/src/components/layout/Sidebar/Sidebar.tsx`

#### Mudanças:
- ✅ Adicionado `useAuth()` para pegar usuário atual
- ✅ Adicionado campo `requiredRole?: UserRole[]` nos tipos `NavItem` e `SubMenuItem`
- ✅ Função `canViewItem()` que verifica permissão baseada em role
- ✅ Filtro `visibleNavItems` que mostra apenas items permitidos
- ✅ Menu "Configurações" agora **só aparece para ADMIN**
- ✅ Novo item "Meu Perfil" para **todos os usuários**

#### Estrutura do Menu:

```typescript
// Todos os usuários veem:
- Dashboard
- Clientes
- Loja Online
- Produtos
- Estoque
- Vendas
- Financeiro
- Meu Perfil ← NOVO

// Apenas ADMIN vê:
- Configurações
  - Empresa
  - Usuários
  - Integrações
```

#### Código de Controle:
```typescript
const navItems: NavItem[] = [
  // ... outros items
  { 
    icon: <FiSettings />, 
    label: 'Configurações',
    requiredRole: ['ADMIN'], // ← Restrição
    submenu: [
      { path: '/configuracoes/empresa', ... },
      { path: '/configuracoes/usuarios', ... },
      { path: '/configuracoes/integracoes', ... },
    ]
  },
  {
    path: '/perfil',
    icon: <FiUser />,
    label: 'Meu Perfil' // ← Sem restrição
  },
];

// Filtrar por permissão
const canViewItem = (requiredRole?: UserRole[]): boolean => {
  if (!requiredRole || requiredRole.length === 0) return true;
  if (!user) return false;
  return requiredRole.includes(user.role);
};

const visibleNavItems = navItems.filter(item => canViewItem(item.requiredRole));
```

---

### 2. Página "Meu Perfil"

**Arquivo**: `frontend/src/pages/Perfil/PerfilPage.tsx`

#### Funcionalidades:
- ✅ Exibir informações do usuário:
  - Nome
  - Email
  - Cargo (ADMIN/OPERADOR)
  - Status (Ativo/Inativo)
  - Membro desde
- ✅ Alterar senha com validação:
  - Senha atual
  - Nova senha (8-20 caracteres, maiúsculas, minúsculas, números, especiais)
  - Confirmar senha
- ✅ Design responsivo e moderno
- ✅ Feedback visual com toast

#### Screenshots Conceituais:

```
┌────────────────────────────────────────┐
│  Meu Perfil                            │
├────────────────────────────────────────┤
│                                        │
│  📋 Informações da Conta               │
│  ┌──────────────────────────────────┐ │
│  │ Nome:    João Silva              │ │
│  │ Email:   joao@loja.com           │ │
│  │ Cargo:   [ADMIN]                 │ │
│  │ Status:  ✓ Ativo                 │ │
│  │ Membro:  12 de junho de 2026     │ │
│  └──────────────────────────────────┘ │
│                                        │
│  🔒 Segurança                          │
│  ┌──────────────────────────────────┐ │
│  │ Senha Atual:  [••••••••]  👁      │ │
│  │ Nova Senha:   [••••••••]  👁      │ │
│  │ Confirmar:    [••••••••]  👁      │ │
│  │                                   │ │
│  │ ⚠ A senha deve conter:           │ │
│  │  • Mínimo de 8 caracteres        │ │
│  │  • Letras maiúsculas e minúsculas│ │
│  │  • Números                       │ │
│  │  • Caracteres especiais          │ │
│  │                                   │ │
│  │  [💾 Alterar Senha]              │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

---

### 3. Proteção de Rotas por Role

**Arquivo**: `frontend/src/components/common/RoleProtectedRoute.tsx`

#### Componente:
```typescript
<RoleProtectedRoute requiredRole={['ADMIN']}>
  <EmpresaPage />
</RoleProtectedRoute>
```

#### Comportamento:
- ✅ Verifica se `user.role` está em `requiredRole`
- ✅ Redireciona para `/dashboard` se sem permissão
- ✅ Exibe toast de erro: "Você não tem permissão para acessar esta página"
- ✅ Evita toasts duplicados com `toastId`

---

### 4. Rotas Atualizadas

**Arquivo**: `frontend/src/App.tsx`

#### Rotas Protegidas por Role:

```typescript
// Rota de Perfil - Todos
<Route path="perfil" element={<PerfilPage />} />

// Rotas de Configurações - Apenas ADMIN
<Route 
  path="configuracoes/empresa" 
  element={
    <RoleProtectedRoute requiredRole={['ADMIN']}>
      <EmpresaPage />
    </RoleProtectedRoute>
  } 
/>
<Route 
  path="configuracoes/usuarios" 
  element={
    <RoleProtectedRoute requiredRole={['ADMIN']}>
      <UsuariosPage />
    </RoleProtectedRoute>
  } 
/>
<Route 
  path="configuracoes/integracoes" 
  element={
    <RoleProtectedRoute requiredRole={['ADMIN']}>
      <IntegracoesPage />
    </RoleProtectedRoute>
  } 
/>
```

---

## 🔐 Níveis de Acesso

### ADMIN (Administrador)
**Pode ver e acessar**:
- ✅ Dashboard
- ✅ Clientes
- ✅ Loja Online
- ✅ Produtos
- ✅ Estoque
- ✅ Vendas
- ✅ Financeiro
- ✅ **Configurações** ← Exclusivo
  - Empresa
  - Usuários (criar/editar/remover operadores)
  - Integrações (Mercado Pago, etc.)
- ✅ Meu Perfil

### OPERADOR (Operador)
**Pode ver e acessar**:
- ✅ Dashboard
- ✅ Clientes
- ✅ Loja Online
- ✅ Produtos
- ✅ Estoque
- ✅ Vendas
- ✅ Financeiro
- ✅ Meu Perfil
- ❌ **Configurações** ← Não vê no menu

**O que acontece se tentar acessar via URL?**
- Redireciona para `/dashboard`
- Exibe toast: "Você não tem permissão para acessar esta página"

---

## 🎨 UI/UX

### Menu Dinâmico
- **ADMIN**: Vê 9 items (inclui Configurações)
- **OPERADOR**: Vê 8 items (sem Configurações)
- Menu se adapta automaticamente baseado no role

### Indicadores Visuais
- Badge de cargo na página de perfil:
  - **ADMIN**: Roxo com gradiente
  - **OPERADOR**: Rosa com gradiente
- Status ativo/inativo

---

## 🧪 Testes Necessários

### Testes Manuais:

#### 1. Login como ADMIN
```
1. Fazer login com usuário ADMIN
2. Verificar menu:
   ✓ Item "Configurações" aparece
   ✓ Submenu: Empresa, Usuários, Integrações
3. Acessar /configuracoes/empresa
   ✓ Página carrega normalmente
4. Acessar /perfil
   ✓ Mostra cargo "Administrador"
```

#### 2. Login como OPERADOR
```
1. Fazer login com usuário OPERADOR
2. Verificar menu:
   ✓ Item "Configurações" NÃO aparece
   ✓ Item "Meu Perfil" aparece
3. Tentar acessar /configuracoes/empresa via URL
   ✓ Redireciona para /dashboard
   ✓ Exibe toast de erro
4. Acessar /perfil
   ✓ Mostra cargo "Operador"
```

#### 3. Alterar Senha
```
1. Em /perfil, clicar em "Alterar Senha"
2. Preencher formulário:
   - Senha atual: [senha correta]
   - Nova senha: Test@123
   - Confirmar: Test@123
3. Clicar em "Alterar Senha"
   ✓ Exibe toast de sucesso
   ✓ Formulário limpa
```

#### 4. Validação de Senha
```
1. Tentar senha fraca:
   - Nova senha: "123"
   ✓ Erro: "Senha deve ter no mínimo 8 caracteres"
2. Tentar senha sem maiúscula:
   - Nova senha: "test@123"
   ✓ Erro: "Deve conter ao menos uma letra maiúscula"
3. Tentar senhas diferentes:
   - Nova senha: "Test@123"
   - Confirmar: "Test@456"
   ✓ Erro: "As senhas não coincidem"
```

---

## 📦 Arquivos Criados/Modificados

### Criados:
- ✅ `frontend/src/pages/Perfil/PerfilPage.tsx`
- ✅ `frontend/src/pages/Perfil/PerfilPage.scss`
- ✅ `frontend/src/components/common/RoleProtectedRoute.tsx`

### Modificados:
- ✅ `frontend/src/components/layout/Sidebar/Sidebar.tsx`
- ✅ `frontend/src/App.tsx`

---

## 🚀 Deploy

### Checklist:
1. ✅ Sidebar com controle de acesso
2. ✅ Página "Meu Perfil" criada
3. ✅ Proteção de rotas por role
4. ✅ Rotas configuradas no App.tsx
5. ⏳ Testar login como ADMIN
6. ⏳ Testar login como OPERADOR
7. ⏳ Testar proteção de rotas
8. ⏳ Testar alteração de senha

---

## 🔄 Integrações Futuras

### Backend (TODO):
- [ ] Endpoint `POST /auth/change-password`:
  ```typescript
  {
    "current_password": "SenhaAtual123!",
    "new_password": "NovaSenha123!"
  }
  ```
- [ ] Validar senha atual no backend
- [ ] Invalidar tokens após alterar senha (força novo login)

### Middleware (TODO):
- [ ] Criar middleware de autorização no backend
- [ ] Proteger endpoints de configuração:
  ```python
  @router.post("/configuracoes/empresa")
  async def atualizar_empresa(
      user: Usuario = Depends(require_admin)  # ← Middleware
  ):
      ...
  ```

---

## 📝 Notas Importantes

### 1. Segurança
- ⚠️ **Nunca confiar apenas no frontend**
- Backend DEVE validar permissões em TODOS os endpoints
- Frontend é apenas para UX (esconder botões/menus)

### 2. Extensibilidade
- Fácil adicionar novos roles (`requiredRole: ['ADMIN', 'GERENTE']`)
- Fácil adicionar permissões granulares

### 3. Manutenibilidade
- Lógica centralizada em `RoleProtectedRoute`
- Menu configurado declarativamente

---

**Autor**: Kiro AI  
**Revisão**: Pendente  
**Status**: Implementado (aguardando testes)
