# Melhorias na UX da Loja Online

**Data**: 2026-06-12  
**Versão**: 1.2.0

## 🎯 Objetivo

Reorganizar a estrutura do menu "Loja Online" no sistema administrativo para separar claramente:
- **Gestão da Loja** (Admin) vs **Visualização do Catálogo** (Público)

---

## 📋 Problema Identificado

### **Antes:**

```
Sidebar:
└─ Loja Online
   ├─ Ver Catálogo         ← Redundante/confuso
   ├─ Pedidos Online
   └─ Configurações
```

**Problemas:**
1. ❌ "Ver Catálogo" é redundante (admin não precisa ver como cliente)
2. ❌ Mistura conceitos: gestão vs visualização
3. ❌ Admin precisa sair do sistema para ver a loja pública
4. ❌ Nome "Configurações" ambíguo (da loja ou do sistema?)

---

## ✅ Solução Implementada

### **Depois:**

```
Sidebar:
└─ Loja Online
   ├─ Pedidos Online              ← Gerenciar pedidos
   └─ Configurações da Loja       ← Configurar loja online

Navbar (topo):
[🔗 Ver Minha Loja]  [👤 User]  [🚪 Logout]
     ↑
Abre /c/{empresa-slug} em nova aba
```

---

## 🔧 Mudanças Implementadas

### 1. Sidebar Atualizado

**Arquivo**: `frontend/src/components/layout/Sidebar/Sidebar.tsx`

#### Removido:
```typescript
{ path: '/loja/catalogo', icon: <FiGlobe />, label: 'Ver Catálogo' }
```

#### Mantido e Renomeado:
```typescript
{ 
  icon: <FiGlobe />, 
  label: 'Loja Online',
  submenu: [
    { path: '/loja/pedidos', icon: <FiShoppingBag />, label: 'Pedidos Online' },
    { path: '/loja/configuracoes', icon: <FiSettings />, label: 'Configurações da Loja' }, // ← Renomeado
  ]
}
```

---

### 2. Botão "Ver Minha Loja" no Navbar

**Arquivo**: `frontend/src/components/layout/Navbar/Navbar.tsx`

#### Código Adicionado:
```typescript
const empresaSlug = 'empresa-1'; // TODO: Obter do user.empresa_slug

const handleVerLoja = () => {
  window.open(`/c/${empresaSlug}`, '_blank');
};

// JSX:
<button 
  className="btn-ver-loja" 
  onClick={handleVerLoja}
  title="Ver minha loja online"
>
  <FiExternalLink />
  <span>Minha Loja</span>
</button>
```

#### Comportamento:
- ✅ Abre catálogo público em **nova aba**
- ✅ Mantém admin logado no sistema
- ✅ Responsivo: esconde texto no mobile, mostra só ícone

---

### 3. Estilos do Botão

**Arquivo**: `frontend/src/components/layout/Navbar/Navbar.scss`

#### Características:
- 🎨 Gradiente roxo/azul
- 💫 Hover com elevação
- 📱 Responsivo (esconde texto no mobile)
- 🔗 Ícone de link externo

```scss
.btn-ver-loja {
  display: inline-flex;
  align-items: center;
  gap: $spacer-2;
  padding: $spacer-2 $spacer-3;
  background: linear-gradient(135deg, $primary 0%, $secondary 100%);
  color: white;
  border-radius: $border-radius;
  font-weight: $font-weight-medium;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }
}
```

---

### 4. Rota Removida

**Arquivo**: `frontend/src/App.tsx`

#### Removido:
```typescript
<Route path="loja/catalogo" element={<CatalogoRedirectPage />} />
```

**Justificativa**: Não há mais link no menu para essa rota. O acesso ao catálogo é via botão que abre URL pública diretamente.

---

## 🎨 UI/UX Resultante

### **Navbar (Topo)**

```
┌────────────────────────────────────────────────────────┐
│ [≡] Runas    [🔗 Ver Minha Loja]  [👤 User]  [🚪]     │
└────────────────────────────────────────────────────────┘
```

### **Sidebar (Menu)**

```
📊 Dashboard
👥 Clientes
🌐 Loja Online
   ├─ 🛍️ Pedidos Online
   └─ ⚙️ Configurações da Loja
📦 Produtos
   ├─ Produtos
   └─ Categorias
📊 Estoque
🛒 Vendas
💰 Financeiro
⚙️ Configurações (ADMIN)
👤 Meu Perfil
```

### **Mobile**

```
Navbar:
[≡] Runas  [🔗]  [👤]  [🚪]
           ↑
    Só ícone (sem texto)
```

---

## 🚀 Benefícios

### **1. Clareza**
- ✅ Menu "Loja Online" agora é claramente para **gestão**
- ✅ "Ver Minha Loja" é claramente para **visualização**

### **2. Usabilidade**
- ✅ Admin pode ver loja sem sair do sistema
- ✅ Abre em nova aba (não perde contexto)
- ✅ Um clique para acesso rápido

### **3. Organização**
- ✅ Menos items no submenu (2 vs 3)
- ✅ Nomes mais descritivos
- ✅ Separação lógica de conceitos

### **4. Mobile-Friendly**
- ✅ Botão responsivo
- ✅ Não sobrecarrega navbar no mobile

---

## 📱 Responsividade

### **Desktop (>768px)**
```
[🔗 Ver Minha Loja]  ← Texto + Ícone
```

### **Mobile (<768px)**
```
[🔗]  ← Só Ícone
```

---

## 🔮 Melhorias Futuras

### **1. Obter Slug Dinâmico** (TODO)

**Problema atual:**
```typescript
const empresaSlug = 'empresa-1'; // Hardcoded
```

**Solução:**
```typescript
// Backend deve retornar slug no user
interface User {
  id: string;
  nome: string;
  email: string;
  role: UserRole;
  empresa_id: number;
  empresa_slug: string; // ← ADICIONAR
}

// Frontend usa direto
const empresaSlug = user?.empresa_slug || 'empresa-1';
```

**Mudanças necessárias:**
1. ✅ Backend: Adicionar `empresa_slug` no JOIN da tabela `empresas`
2. ✅ Frontend: Usar `user.empresa_slug` em vez de hardcoded

---

### **2. Badge de Notificações** (Futuro)

```typescript
<button className="btn-ver-loja">
  <FiExternalLink />
  <span>Ver Minha Loja</span>
  {novoPedidosCount > 0 && (
    <span className="badge">{novoPedidosCount}</span>
  )}
</button>
```

---

### **3. Dropdown com Opções** (Futuro)

```
[🔗 Ver Minha Loja ▼]
  ├─ Ver Catálogo
  ├─ Compartilhar Link
  └─ Copiar URL
```

---

## 🧪 Como Testar

### **1. Verificar Menu**
```
✓ Login no sistema
✓ Abrir Loja Online no sidebar
✓ Verificar apenas 2 items:
  - Pedidos Online
  - Configurações da Loja
✓ "Ver Catálogo" NÃO deve aparecer
```

### **2. Testar Botão "Ver Minha Loja"**
```
✓ Clicar no botão no navbar
✓ Nova aba deve abrir com /c/empresa-1
✓ Admin continua logado na aba original
✓ Catálogo carrega corretamente
```

### **3. Testar Responsividade**
```
✓ Desktop: Botão mostra "Ver Minha Loja"
✓ Mobile: Botão mostra só ícone 🔗
✓ Hover funciona em ambos
```

### **4. Testar Navegação**
```
✓ Clicar em "Pedidos Online"
✓ Página de pedidos carrega
✓ Clicar em "Configurações da Loja"
✓ Página de configurações carrega
```

---

## 📊 Antes vs Depois

### **Antes:**
```
Menu: 3 items (Ver Catálogo, Pedidos, Configurações)
Acesso à loja: Via submenu "Ver Catálogo" → Redireciona
Problema: Confuso, redundante
```

### **Depois:**
```
Menu: 2 items (Pedidos Online, Configurações da Loja)
Acesso à loja: Botão no navbar → Nova aba
Benefício: Claro, direto, não perde contexto
```

---

## 📦 Arquivos Modificados

### Modificados:
- ✅ `frontend/src/components/layout/Sidebar/Sidebar.tsx`
- ✅ `frontend/src/components/layout/Navbar/Navbar.tsx`
- ✅ `frontend/src/components/layout/Navbar/Navbar.scss`
- ✅ `frontend/src/App.tsx`

### Não Modificados (Podem ser removidos se não usados):
- ⚠️ `frontend/src/pages/LojaOnline/CatalogoRedirectPage.tsx` (pode remover)

---

## ✅ Checklist de Deploy

- [x] Remover "Ver Catálogo" do sidebar
- [x] Renomear "Configurações" → "Configurações da Loja"
- [x] Adicionar botão "Ver Minha Loja" no navbar
- [x] Estilizar botão (gradiente, hover, responsivo)
- [x] Remover rota `/loja/catalogo`
- [x] Remover console.log de debug
- [ ] Testar em desenvolvimento
- [ ] Obter slug dinâmico do backend (TODO)
- [ ] Testar em produção

---

## 🔒 Notas de Segurança

- ✅ Botão visível para todos (ADMIN + OPERADOR)
- ✅ Catálogo público não requer autenticação
- ✅ Nova aba não expõe tokens (window.open é seguro)

---

**Autor**: Kiro AI  
**Revisão**: Pendente  
**Status**: Implementado (aguardando teste de slug dinâmico)
