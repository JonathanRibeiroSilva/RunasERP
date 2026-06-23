# 📚 Documentação de Desenvolvimento

> Guias e referências para desenvolvimento do ERP Runas

---

## 📋 Índice de Documentos

### 🎨 Frontend

#### Guia Principal
- **[FRONTEND_IMPLEMENTACAO.md](./FRONTEND_IMPLEMENTACAO.md)** ⭐  
  Documento oficial de implementação do frontend.  
  **MVP**: ✅ Auth | Dashboard | Clientes | Produtos | Loja Online  
  **Próximos**: 🔴 Vendas/PDV | Estoque | Financeiro

#### Guias Específicos
- **[GUIA_MASCARAS_VALIDACOES.md](./GUIA_MASCARAS_VALIDACOES.md)**  
  Referência de máscaras (CPF, telefone, CEP) e validações

#### Checklist
- **[CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md)**  
  Checklist geral de qualidade e padrões

---

## 📊 Status do Projeto

### ✅ MVP Entregue (98%)

| Módulo | Frontend | Backend |
|--------|----------|---------|
| Autenticação | ✅ 100% | ✅ 100% |
| Dashboard | ✅ 100% | ✅ 100% |
| Clientes | ✅ 90% | ✅ 100% |
| Produtos | ✅ 100% | ✅ 100% |
| Loja Online | ✅ 100% | ✅ 100% |

### 🔴 Próximas Entregas

| Módulo | Frontend | Backend | Prioridade |
|--------|----------|---------|------------|
| Vendas/PDV | 🔴 0% | ✅ 100% | 🔥 Crítica |
| Estoque | 🔴 0% | ✅ 100% | 🔥 Alta |
| Financeiro | 🔴 0% | 🔴 0% | 🟡 Média |

---

## 🚀 Quick Start - Frontend

### Ver Status Atual
```bash
# Abrir documento principal
code docs/02-desenvolvimento/FRONTEND_IMPLEMENTACAO.md
```

### Próxima Implementação
**Sprint 1: Vendas/PDV** 🔥 Crítica

Rotas pendentes:
1. `/vendas` - Lista de vendas
2. `/vendas/nova` - PDV (Ponto de Venda)
3. `/vendas/:id` - Detalhes
4. Modals workflow
5. `/vendas/relatorios` - Analytics

---

## 🎯 Guias Rápidos

### Para Implementar Nova Rota
1. Criar componente página (`src/pages/`)
2. Criar arquivo SCSS
3. Layout responsivo (mobile-first)
4. Integrar com API (axios)
5. Estados (loading, error, empty)
6. Validações (Zod)
7. Adicionar ao router

### Para Criar Componente
1. Props TypeScript interface
2. Documentação JSDoc
3. Responsivo
4. Acessibilidade (ARIA)
5. Estados UI

---

## 💡 Convenções

### Commits (English)
```
feat(vendas): add PDV page
fix(estoque): correct stock calculation
docs(frontend): update implementation guide
```

### Código (PT-BR)
- Variáveis/funções: português
- Comentários: PT-BR
- Commits: English
- Docs: PT-BR

---

**Última atualização**: 23/06/2026
