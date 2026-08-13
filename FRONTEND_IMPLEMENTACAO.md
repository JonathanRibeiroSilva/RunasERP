# 🎨 Guia de Implementação Frontend - Runas ERP

> Roteiro completo para desenvolvimento do frontend módulo por módulo

**Última atualização**: Junho 2026  
**Status**: Loja Online 50% | Vendas/PDV e Estoque pendentes

---

## 📋 Visão Geral

Este guia apresenta o **plano de implementação do frontend** do Runas ERP, organizado em **sprints** com prioridades definidas.

### Progresso Atual

| Módulo | Status | Completude | Prioridade |
|--------|--------|-----------|-----------|
| 🔐 Autenticação | ✅ Completo | 100% | Alta |
| 👥 Clientes | 🟡 Quase Completo | 85% | Média |
| 📦 Produtos | 🟡 Quase Completo | 90% | Alta |
| 🛒 Loja Online | 🟡 Em Progresso | 50% | Alta |
| 💰 Vendas/PDV | 🔴 Não Iniciado | 0% | **Crítica** |
| 📊 Estoque | 🔴 Não Iniciado | 0% | **Crítica** |
| 💵 Financeiro | 🔴 Não Iniciado | 0% | Média |
| 📈 Dashboard | 🟡 Básico | 40% | Baixa |

---

## 🎯 Prioridades de Desenvolvimento

### Sprint 1: PDV/Vendas (PRIORIDADE MÁXIMA)
**Prazo**: 2 semanas  
**Objetivo**: Sistema funcional de vendas


**Componentes Necessários**:

1. **PDV (Ponto de Venda)**
   - Busca de produtos (código de barras, nome)
   - Carrinho de compras
   - Cálculo automático de totais
   - Seleção de cliente (opcional para vendas de balcão)
   - Múltiplas formas de pagamento
   - Finalização de venda

2. **Lista de Vendas**
   - Tabela com paginação, filtros e ordenação
   - Status da venda (rascunho, pendente, confirmada, etc)
   - Detalhes da venda (itens, pagamentos)
   - Ações (cancelar, devolver)

3. **Integração com Estoque**
   - Verificar disponibilidade
   - Reservar estoque durante venda
   - Baixar estoque ao confirmar

**APIs Backend Necessárias** (✅ Prontas):
- `POST /api/vendas` - Criar venda
- `GET /api/vendas` - Listar vendas
- `GET /api/vendas/{id}` - Detalhes da venda
- `PATCH /api/vendas/{id}/status` - Alterar status
- `GET /api/produtos` - Buscar produtos disponíveis


---

### Sprint 2: Gestão de Estoque (PRIORIDADE MÁXIMA)
**Prazo**: 2 semanas  
**Objetivo**: Controle completo de estoque

**Componentes Necessários**:

1. **Visão Geral do Estoque**
   - Dashboard com indicadores (estoque total, baixo, zerado)
   - Lista de produtos com níveis de estoque
   - Filtros por categoria, fornecedor
   - Alertas de estoque baixo/zerado

2. **Movimentações de Estoque**
   - Entrada de mercadorias
   - Saída manual
   - Ajustes de inventário
   - Devoluções
   - Histórico de movimentações

3. **Gestão de Lotes**
   - Controle de lotes por produto
   - Datas de validade
   - Rastreabilidade (lote → vendas)
   - Alertas de lotes próximos ao vencimento

4. **Inventário**
   - Contagem física
   - Comparação físico vs sistema
   - Ajustes em lote

**APIs Backend Necessárias** (✅ Prontas):
- `GET /api/estoque` - Listar estoque
- `POST /api/estoque/movimentacoes` - Registrar movimentação
- `GET /api/estoque/movimentacoes` - Histórico
- `GET /api/estoque/lotes` - Listar lotes


---

### Sprint 3: Loja Online - Finalização (PRIORIDADE ALTA)
**Prazo**: 1 semana  
**Objetivo**: E-commerce funcional

**Componentes Já Implementados** (✅):
- Vitrine de produtos
- Detalhes do produto
- Filtros e busca
- Compartilhamento (WhatsApp, link)

**Componentes a Implementar** (🔴):

1. **Carrinho de Compras**
   - Adicionar/remover produtos
   - Atualizar quantidades
   - Calcular subtotal/total
   - Persistência (localStorage)

2. **Checkout**
   - Dados do cliente (nome, CPF, telefone)
   - Endereço de entrega
   - Forma de pagamento
   - Confirmação do pedido

3. **Área do Cliente**
   - Login/cadastro
   - Meus pedidos
   - Status de entrega
   - Histórico de compras

**APIs Backend Necessárias**:
- ✅ `GET /api/loja/produtos` - Produtos públicos (pronta)
- 🔴 `POST /api/loja/carrinho` - Criar carrinho (a fazer)
- 🔴 `POST /api/loja/checkout` - Finalizar compra (a fazer)
- 🔴 `GET /api/loja/pedidos` - Meus pedidos (a fazer)


---

### Sprint 4: Melhorias em Clientes e Produtos (PRIORIDADE MÉDIA)
**Prazo**: 1 semana  
**Objetivo**: Completar funcionalidades pendentes

**Clientes** (85% completo):
- ✅ CRUD completo
- ✅ Gestão de endereços
- ✅ Gestão de crédito
- 🔴 Histórico de compras (integrar com Vendas)
- 🔴 Relatório de inadimplência

**Produtos** (90% completo):
- ✅ CRUD completo
- ✅ Gestão de variantes
- ✅ Upload de fotos
- 🔴 Histórico de preços
- 🔴 Produtos compostos (kits)
- 🔴 Importação em lote (CSV/Excel)

---

### Sprint 5: Financeiro (PRIORIDADE MÉDIA)
**Prazo**: 2 semanas  
**Objetivo**: Gestão financeira básica

**Componentes Necessários**:

1. **Dashboard Financeiro**
   - Resumo de receitas/despesas
   - Contas a receber/pagar
   - Fluxo de caixa

2. **Contas a Receber**
   - Lista de recebíveis
   - Baixa manual
   - Envio de cobranças
   - Relatório de inadimplência

3. **Contas a Pagar**
   - Lista de pagamentos pendentes
   - Baixa manual
   - Agendamento de pagamentos

**APIs Backend Necessárias** (🔴 Não implementadas):
- `GET /api/financeiro/contas-receber`
- `GET /api/financeiro/contas-pagar`
- `POST /api/financeiro/baixa`


---

## 🏗️ Padrões de Implementação

### Estrutura de Componentes

Cada módulo deve seguir esta estrutura:

```typescript
frontend/src/
├── pages/
│   └── [Modulo]/
│       ├── [Modulo]ListPage.tsx      // Lista com tabela
│       ├── [Modulo]FormPage.tsx      // Cadastro/edição
│       ├── [Modulo]DetailPage.tsx    // Detalhes (opcional)
│       └── index.ts                   // Exports
├── components/
│   └── [modulo]/
│       ├── [Modulo]Table.tsx          // Tabela reutilizável
│       ├── [Modulo]Form.tsx           // Formulário reutilizável
│       ├── [Modulo]Card.tsx           // Card de resumo
│       └── index.ts
├── services/
│   └── api/
│       └── [modulo].ts                // API calls
├── types/
│   └── [modulo].ts                    // TypeScript types
└── hooks/
    └── use[Modulo].ts                 // Custom hook (opcional)
```

### Exemplo: Módulo de Vendas

```typescript
// types/venda.ts
export interface Venda {
  id: number;
  numero_venda: string;
  data_venda: string;
  status: 'RASCUNHO' | 'PENDENTE' | 'CONFIRMADA' | 'CANCELADA';
  cliente_id?: number;
  cliente_nome?: string;
  valor_total: number;
  itens: ItemVenda[];
  pagamentos: PagamentoVenda[];
}

export interface ItemVenda {
  produto_id: number;
  produto_nome: string;
  quantidade: number;
  preco_unitario: number;
  subtotal: number;
}
```


```typescript
// services/api/vendas.ts
import { api } from './api';
import { Venda, VendaCreate } from '@/types/venda';

export const vendasApi = {
  list: async (params?: any) => {
    const { data } = await api.get<Venda[]>('/api/vendas', { params });
    return data;
  },

  get: async (id: number) => {
    const { data } = await api.get<Venda>(`/api/vendas/${id}`);
    return data;
  },

  create: async (venda: VendaCreate) => {
    const { data } = await api.post<Venda>('/api/vendas', venda);
    return data;
  },

  updateStatus: async (id: number, status: string) => {
    const { data } = await api.patch<Venda>(`/api/vendas/${id}/status`, { status });
    return data;
  }
};
```

```typescript
// hooks/usePDV.ts
import { useState } from 'react';
import { ItemVenda } from '@/types/venda';
import { Produto } from '@/types/produto';

export const usePDV = () => {
  const [itens, setItens] = useState<ItemVenda[]>([]);

  const adicionarProduto = (produto: Produto, quantidade: number = 1) => {
    // Verifica se produto já existe no carrinho
    const existente = itens.find(i => i.produto_id === produto.id);

    if (existente) {
      setItens(itens.map(i => 
        i.produto_id === produto.id 
          ? { ...i, quantidade: i.quantidade + quantidade }
          : i
      ));
    } else {
      setItens([...itens, {
        produto_id: produto.id,
        produto_nome: produto.nome,
        quantidade,
        preco_unitario: produto.preco_venda,
        subtotal: produto.preco_venda * quantidade
      }]);
    }
  };

  const removerProduto = (produtoId: number) => {
    setItens(itens.filter(i => i.produto_id !== produtoId));
  };

  const limparCarrinho = () => setItens([]);

  const valorTotal = itens.reduce((acc, item) => acc + item.subtotal, 0);

  return { itens, adicionarProduto, removerProduto, limparCarrinho, valorTotal };
};
```


---

## 🎨 Componentes Reutilizáveis

### DataTable (Tabela Genérica)

```typescript
// components/common/DataTable.tsx
interface DataTableProps<T> {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  onRowClick?: (row: T) => void;
  pagination?: PaginationProps;
}

export function DataTable<T>({ data, columns, loading, onRowClick, pagination }: DataTableProps<T>) {
  // Implementação com Bootstrap Table
  // - Paginação
  // - Ordenação
  // - Loading skeleton
  // - Empty state
}
```

### FormField (Campo de Formulário)

```typescript
// components/forms/FormField.tsx
interface FormFieldProps {
  label: string;
  name: string;
  type?: 'text' | 'number' | 'email' | 'tel';
  mask?: 'cpf' | 'telefone' | 'cep' | 'currency';
  required?: boolean;
  error?: string;
}

export function FormField({ label, name, type, mask, required, error }: FormFieldProps) {
  // Implementação com React Hook Form
  // - Validação
  // - Máscaras
  // - Mensagens de erro
}
```

### StatusBadge (Badge de Status)

```typescript
// components/common/StatusBadge.tsx
interface StatusBadgeProps {
  status: 'RASCUNHO' | 'PENDENTE' | 'CONFIRMADA' | 'CANCELADA';
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variants = {
    RASCUNHO: 'secondary',
    PENDENTE: 'warning',
    CONFIRMADA: 'success',
    CANCELADA: 'danger'
  };

  return <Badge bg={variants[status]}>{status}</Badge>;
}
```


---

## 🔧 Utilitários Essenciais

### Máscaras e Validações

```typescript
// utils/masks.ts
export const masks = {
  cpf: (value: string) => {
    return value
      .replace(/\D/g, '')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})/, '$1-$2')
      .replace(/(-\d{2})\d+?$/, '$1');
  },

  telefone: (value: string) => {
    return value
      .replace(/\D/g, '')
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{5})(\d)/, '$1-$2')
      .replace(/(-\d{4})\d+?$/, '$1');
  },

  currency: (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  }
};
```

### Formatação de Datas

```typescript
// utils/date.ts
import { format, parseISO } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export const formatDate = (date: string | Date, pattern = 'dd/MM/yyyy') => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, pattern, { locale: ptBR });
};

export const formatDateTime = (date: string | Date) => {
  return formatDate(date, 'dd/MM/yyyy HH:mm');
};
```

### Tratamento de Erros

```typescript
// utils/errors.ts
import { toast } from 'react-toastify';
import { AxiosError } from 'axios';

export const handleApiError = (error: unknown) => {
  if (error instanceof AxiosError) {
    const message = error.response?.data?.detail || 'Erro ao processar requisição';
    toast.error(message);
  } else {
    toast.error('Erro inesperado');
  }
};
```


---

## 🎯 Checklist por Feature

### PDV/Vendas

#### Backend (✅ 90% completo)
- [x] API de vendas implementada
- [x] Workflow de status (6 estados)
- [x] Integração com estoque (reserva/baixa)
- [x] Validação de crédito
- [x] Múltiplas formas de pagamento
- [ ] API de carrinho (sessão)

#### Frontend (🔴 0% completo)
- [ ] Página PDV
  - [ ] Busca de produtos (código de barras, nome)
  - [ ] Carrinho de compras
  - [ ] Seleção de cliente
  - [ ] Múltiplas formas de pagamento
  - [ ] Finalização de venda
- [ ] Página Lista de Vendas
  - [ ] Tabela com filtros
  - [ ] Detalhes da venda
  - [ ] Ações (cancelar, devolver)
- [ ] Hook `usePDV`
- [ ] Componente `VendaTable`
- [ ] Componente `PagamentoForm`

---

### Gestão de Estoque

#### Backend (✅ 95% completo)
- [x] API de estoque implementada
- [x] Movimentações (entrada, saída, ajuste, devolução)
- [x] Gestão de lotes
- [x] Inventário físico
- [x] Alertas de estoque baixo/zerado
- [ ] Notificações automáticas (lotes vencendo)

#### Frontend (🔴 0% completo)
- [ ] Dashboard de Estoque
  - [ ] Indicadores (total, baixo, zerado)
  - [ ] Lista de produtos com níveis
  - [ ] Filtros por categoria/fornecedor
- [ ] Página Movimentações
  - [ ] Formulário de entrada/saída
  - [ ] Histórico de movimentações
- [ ] Página Lotes
  - [ ] Lista de lotes
  - [ ] Alertas de vencimento
- [ ] Página Inventário
  - [ ] Formulário de contagem
  - [ ] Comparação físico vs sistema
- [ ] Hook `useEstoque`


---

## 📚 Recursos e Referências

### Documentação Interna
- [Frontend README](./docs/05-frontend/README.md) - Arquitetura completa
- [Design System](./docs/05-frontend/design/design.md) - Padrões visuais
- [Componentes](./docs/05-frontend/design/componentes.md) - Biblioteca de componentes
- [API Reference](./docs/10-api-reference/README.md) - Endpoints disponíveis
- [Roadmap](./docs/01-visao-geral/roadmap.md) - Planejamento geral

### Stack Tecnológico
- **React 18** - https://react.dev
- **TypeScript** - https://www.typescriptlang.org
- **Vite** - https://vitejs.dev
- **React Router** - https://reactrouter.com
- **React Bootstrap** - https://react-bootstrap.github.io
- **React Hook Form** - https://react-hook-form.com
- **TanStack Query** - https://tanstack.com/query

### Ferramentas
- **Figma** (design) - Layouts e protótipos
- **Postman** (APIs) - Testar endpoints backend
- **React DevTools** - Debug de componentes
- **Redux DevTools** - Debug de estado (se necessário)

---

## 🚀 Como Começar

### 1. Setup do Ambiente

```powershell
# Clone o repositório
git clone https://github.com/seu-repo/runas-erp.git
cd runas-erp

# Instalar dependências do frontend
cd frontend
npm install

# Configurar variáveis de ambiente
cp .env.example .env

# Iniciar servidor de desenvolvimento
npm run dev
```

### 2. Escolher uma Feature

Consulte as **Sprints** acima e escolha a feature de maior prioridade:
- **Sprint 1**: PDV/Vendas (CRÍTICO)
- **Sprint 2**: Estoque (CRÍTICO)
- **Sprint 3**: Loja Online (ALTA)

### 3. Seguir o Padrão

Use os **exemplos de código** deste guia como referência:
- Estrutura de pastas
- Nomenclatura de arquivos
- Tipos TypeScript
- API services
- Custom hooks


### 4. Implementar

Siga o **Checklist de Desenvolvimento** em cada etapa:
- Criar tipos TypeScript
- Implementar API service
- Criar componentes
- Integrar na página
- Testar manualmente
- Build sem erros

### 5. Testar

```powershell
# Verificar tipos
npm run type-check

# Linter
npm run lint

# Build
npm run build

# Testar no navegador
npm run dev
```

### 6. Commitar

```bash
# Conventional Commits (em inglês)
git add .
git commit -m "feat(vendas): add PDV page with product search"
git push origin feat/pdv-implementation
```

---

## 📞 Suporte

### Dúvidas sobre o Frontend

- **Documentação**: [docs/05-frontend/](./docs/05-frontend/)
- **Convenções**: [.kiro/steering/git-conventions.md](./.kiro/steering/git-conventions.md)
- **Checklist**: [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md)

### Problemas Comuns

- **API não responde**: Verificar se backend está rodando (`docker-compose ps`)
- **CORS error**: Verificar configuração no API Gateway
- **401 Unauthorized**: Token JWT expirado, fazer login novamente
- **Build error**: Rodar `npm install` novamente

---

<div align="center">

**Runas ERP** | Frontend Implementation Guide  
**Última atualização**: Junho 2026  
**Progresso Geral**: 52% completo

</div>

