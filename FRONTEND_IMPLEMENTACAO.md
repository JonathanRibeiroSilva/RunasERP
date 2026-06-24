# 🎨 Frontend - Guia de Implementação Completo

> **Última atualização**: 23/06/2026
> 
> Documento mestre para guiar a implementação do frontend do ERP Runas.  
> Este é o arquivo de referência principal para desenvolvimento frontend.

---

## 📊 Visão Geral do MVP

### Status Atual - Junho 2026

```
✅ Backend Completo: 78 endpoints funcionais
✅ Loja Online: 100% implementada e operacional
✅ Infraestrutura: Docker, responsividade, OAuth
🔴 Vendas/PDV: 0% (backend pronto, aguardando frontend)
🔴 Estoque: 0% (backend pronto, aguardando frontend)
```

---

## 🎯 Status Detalhado por Módulo

### ✅ MÓDULOS IMPLEMENTADOS (MVP FASE 1)

| Módulo | Rotas | Componentes | Status | Observações |
|--------|-------|-------------|--------|-------------|
| **🔐 Autenticação** | 3 | 5 | ✅ 100% | Login, Register, OAuth Google/Microsoft |
| **📊 Dashboard** | 1 | 8 | ✅ 100% | KPIs principais, gráficos |
| **👥 Clientes** | 6 | 12 | ✅ 90% | CRUD completo (falta: histórico detalhado) |
| **📦 Produtos** | 7 | 15 | ✅ 100% | CRUD + Categorias + Variantes |
| **🛒 Loja Online** | 6 | 18 | ✅ 100% | Catálogo → Carrinho → Checkout → Rastreamento |

**Total Implementado**: 23 rotas | 58 componentes | ~15.000 linhas de código

### 🔴 MÓDULOS PENDENTES (MVP FASE 2)

| Módulo | Rotas | Componentes | Prioridade | Backend | Estimativa |
|--------|-------|-------------|------------|---------|------------|
| **💰 Vendas/PDV** | 5 | 12 | 🔥 CRÍTICA | ✅ 100% | 2-3 semanas |
| **📦 Estoque** | 7 | 10 | 🔥 ALTA | ✅ 100% | 1-2 semanas |
| **💵 Financeiro** | 6 | 8 | 🟡 MÉDIA | 🔴 0% | Backend primeiro |

---

## 📈 Progresso Geral

```
Total Planejado:    47 rotas | 88 componentes
Total Implementado: 23 rotas | 58 componentes
Progresso Frontend: 48.9% (rotas) | 65.9% (componentes)
Progresso Backend:  85% (78/92 endpoints)
```

---

## 🛒 LOJA ONLINE - ✅ 100% IMPLEMENTADO

> **Status**: Totalmente funcional e operacional  
> **Backend**: ✅ 26 endpoints | **Frontend**: ✅ 6 rotas | 18 componentes  
> **Documentação**: `docs/03-changelogs/CHANGELOG_LOJA_ONLINE_FRONTEND_COMPLETO.md`

### ✅ Rotas Implementadas

| Rota | Status | Descrição |
|------|--------|-----------|
| `/c/:empresaSlug` | ✅ | Catálogo público com filtros e busca |
| `/c/:empresaSlug/produto/:id` | ✅ | Detalhes do produto + variantes |
| `/c/:empresaSlug/carrinho` | ✅ | Gerenciar carrinho de compras |
| `/c/:empresaSlug/checkout` | ✅ | Checkout 3 steps (dados, entrega, pagamento) |
| `/c/:empresaSlug/pedido/:numero` | ✅ | Rastreamento com timeline de status |
| `/c/:empresaSlug/minha-conta/pedidos` | ✅ | Lista de pedidos do cliente |

### ✅ Componentes-Chave Implementados

**Páginas**: `CatalogoPage`, `ProdutoDetalhePage`, `CarrinhoPage`, `CheckoutPage`, `RastreamentoPedidoPage`, `MeusPedidosPage`

**Componentes**: `ProdutoCard`, `BotaoAdicionarCarrinho`, `SeletorVariantes`, `FormEndereco`, `CalculadoraFrete`, `SeletorFormasPagamento`, `CalculadoraTroco`, `TimelineStatus`, `BadgeStatus`, `StepsIndicator`

**Hooks**: `useCarrinho`, `useCheckout`, `useCEP`, `useFormatacao`

### ✅ Features Completas

- ✅ Catálogo responsivo com filtros (categoria, busca, ordenação, paginação)
- ✅ Detalhes de produto (galeria, variantes, estoque, relacionados)
- ✅ Carrinho com persistência em cookie
- ✅ Checkout 3 steps (dados, entrega, pagamento)
- ✅ Busca CEP via ViaCEP
- ✅ Cálculo automático de frete
- ✅ Múltiplas formas de pagamento (PIX, débito, crédito, dinheiro, fiado)
- ✅ Pagamento misto
- ✅ Calculadora de troco
- ✅ Rastreamento com timeline de status
- ✅ Histórico de pedidos
- ✅ Formatação automática (telefone, CPF, CEP)
- ✅ Validações em tempo real
- ✅ Totalmente responsivo (mobile, tablet, desktop)
- ✅ Estados de UI completos (loading, error, empty, success)

**Status**: 🟢 **LOJA ONLINE 100% OPERACIONAL!**

---

## 💰 VENDAS/PDV - 🔴 0% IMPLEMENTADO (PRIORIDADE CRÍTICA)

> **Status**: Aguardando implementação frontend  
> **Backend**: ✅ 100% Pronto (14 endpoints funcionais)  
> **Prioridade**: 🔥 CRÍTICA - Próxima sprint  
> **Estimativa**: 2-3 semanas  
> **Documentação Backend**: `CHANGELOG_VENDAS_IMPLEMENTATION.md`

### Rotas a Implementar

#### 1. `/vendas` - Lista de Vendas
**Objetivo**: Dashboard vendas com filtros

**Layout**:
```tsx
<VendasPage>
  <Header>
    <BotaoNovaVenda />
    <Filtros>
      <SelectStatus />
      <SelectCliente />
      <InputPeriodo />
      <InputNumero />
    </Filtros>
  </Header>
  
  <ResponsiveTable>
    <Column>Número</Column>
    <Column>Cliente</Column>
    <Column>Data</Column>
    <Column>Valor</Column>
    <Column>Status</Column>
    <Column>Ações</Column>
  </ResponsiveTable>
  
  <Paginacao />
</VendasPage>
```

**Endpoints**:
- `GET /vendas?status=&cliente_id=&data_inicio=&data_fim=&skip=0&limit=20`

**Features**:
- [  ] Listar vendas com paginação
- [  ] Filtros avançados (status, cliente, período, número)
- [  ] Badge colorido por status
- [  ] Ações contextuais (editar só se PEDIDO)
- [  ] Buscar por número

---

#### 2. `/vendas/nova` - PDV (Ponto de Venda)
**Objetivo**: Tela principal de vendas

**Layout** (Desktop - 2 colunas):
```tsx
<PDVPage>
  <Grid>
    {/* Coluna Esquerda: Produtos */}
    <PainelProdutos>
      <BuscaProduto>
        <InputAutocomplete />
        <BotaoScanner />
      </BuscaProduto>
      
      <ResultadosBusca>
        <ProdutoCard>
          <Foto />
          <Nome />
          <Preco />
          <BotaoAdicionar />
        </ProdutoCard>
      </ResultadosBusca>
      
      <CategoriasRapidas />
    </PainelProdutos>
    
    {/* Coluna Direita: Venda */}
    <PainelVenda>
      <ClienteSelector>
        <BuscaCliente />
        <InfoCredito />
      </ClienteSelector>
      
      <ItensVenda>
        <ItemVenda>
          <Produto />
          <Quantidade />
          <Preco />
          <Subtotal />
          <BotaoRemover />
        </ItemVenda>
      </ItensVenda>
      
      <Resumo>
        <Subtotal />
        <Desconto>
          <RadioPercentual />
          <RadioValorFixo />
        </Desconto>
        <Total />
      </Resumo>
      
      <BotaoFinalizar />
    </PainelVenda>
  </Grid>
  
  <ModalPagamento>
    <FormasPagamento>
      <BotaoPix />
      <BotaoDebito />
      <BotaoCredito />
      <BotaoDinheiro />
      <BotaoFiado />
    </FormasPagamento>
    
    <PagamentosAdicionados>
      <ItemPagamento />
      <TotalPago />
      <RestaPagar />
    </PagamentosAdicionados>
  </ModalPagamento>
</PDVPage>
```

**Endpoints**:
- `GET /produtos?busca=&empresa_id=`
- `GET /clientes?busca=&empresa_id=`
- `POST /vendas`

**Features**:
- [  ] Busca produtos (autocomplete)
- [  ] Busca clientes (autocomplete)
- [  ] Adicionar itens carrinho
- [  ] Editar quantidade inline
- [  ] Remover item
- [  ] Aplicar desconto (% ou R$)
- [  ] Múltiplas formas pagamento
- [  ] Calcular troco
- [  ] Validar crédito FIADO
- [  ] Atalhos teclado (F2, F3, F9)

**Componentes Necessários**:
- [  ] `PDVPage` - Página principal
- [  ] `BuscaProduto` - Autocomplete produtos
- [  ] `BuscaCliente` - Autocomplete clientes
- [  ] `ClienteSelector` - Seletor com info crédito
- [  ] `ItemVenda` - Card item no carrinho
- [  ] `DescontoCalculator` - Input desconto
- [  ] `ResumoVenda` - Totais
- [  ] `ModalPagamento` - Modal pagamentos múltiplos
- [  ] `usePDV` - Hook gerenciamento PDV

---

#### 3. `/vendas/:id` - Detalhes da Venda
**Objetivo**: Ver venda completa

**Layout**:
```tsx
<VendaDetalhesPage>
  <Header>
    <NumeroVenda />
    <BadgeStatus />
    <AcoesVenda>
      <BotaoEditar />
      <BotaoConfirmar />
      <BotaoSeparar />
      <BotaoEntregar />
      <BotaoFinalizar />
      <BotaoCancelar />
      <BotaoImprimir />
    </AcoesVenda>
  </Header>
  
  <DadosVenda>
    <SectionCliente />
    <SectionItens />
    <SectionPagamentos />
    <SectionResumo />
  </DadosVenda>
  
  <Timeline>
    <StepStatus>
      PEDIDO → CONFIRMADA
      23/06/2026 14:30
      Por: João Silva
    </StepStatus>
  </Timeline>
</VendaDetalhesPage>
```

**Endpoints**:
- `GET /vendas/{id}`

**Features**:
- [  ] Visualizar todos dados
- [  ] Timeline mudanças status
- [  ] Ações contextuais por status
- [  ] Imprimir cupom (futuro)

---

#### 4. Modais de Workflow

**Modal Confirmar** (PEDIDO → CONFIRMADA):
```tsx
<ModalConfirmarVenda>
  <ResumoVenda />
  <PagamentosAdicionar />
  <InputObservacao />
  <BotaoConfirmar />
</ModalConfirmarVenda>
```

**Modal Separar** (CONFIRMADA → SEPARADA):
```tsx
<ModalSepararVenda>
  <ChecklistItens>
    <Item checked />
  </ChecklistItens>
  <InputObservacao />
  <BotaoSeparar />
</ModalSepararVenda>
```

**Modal Entregar** (SEPARADA → ENTREGUE):
```tsx
<ModalEntregarVenda>
  <InfoEntrega />
  <AssinaturaCanvas />
  <FotoComprovante />
  <InputObservacao />
  <BotaoEntregar />
</ModalEntregarVenda>
```

**Modal Cancelar**:
```tsx
<ModalCancelarVenda>
  <AlertaCancelamento>
    Estoque será liberado
  </AlertaCancelamento>
  <TextareaMotivo required />
  <BotaoCancelar />
</ModalCancelarVenda>
```

---

#### 5. `/vendas/relatorios` - Relatórios
**Objetivo**: Analytics de vendas

**Layout**:
```tsx
<RelatoriosPage>
  <Filtros>
    <SelectPeriodo />
    <SelectVendedor />
    <SelectCategoria />
  </Filtros>
  
  <CardsResumo>
    <Card title="Vendas Hoje" value="R$ 3.450" />
    <Card title="Ticket Médio" value="R$ 125" />
    <Card title="Total Vendas" value="28" />
  </CardsResumo>
  
  <Graficos>
    <GraficoLinha title="Vendas por Dia" />
    <GraficoPizza title="Formas Pagamento" />
    <GraficoBarra title="Top 10 Produtos" />
  </Graficos>
  
  <BotoesExportar>
    <BotaoExportarPDF />
    <BotaoExportarExcel />
  </BotoesExportar>
</RelatoriosPage>
```

**Endpoints**:
- `GET /vendas/relatorios/resumo?data_inicio=&data_fim=`

**Features**:
- [  ] KPIs principais em cards
- [  ] Gráficos interativos (Chart.js)
- [  ] Filtros período
- [  ] Comparação períodos
- [  ] Exportar PDF/Excel
- [  ] Ranking produtos

---

## 📦 ESTOQUE - 🔴 0% IMPLEMENTADO (PRIORIDADE ALTA)

> **Status**: Aguardando implementação frontend  
> **Backend**: ✅ 100% Pronto (19 endpoints funcionais)  
> **Prioridade**: 🔥 ALTA - Sprint após Vendas/PDV  
> **Estimativa**: 1-2 semanas

### Rotas a Implementar

#### 1. `/estoque` - Dashboard Estoque
**Objetivo**: Visão geral do estoque

**Layout**:
```tsx
<EstoquePage>
  <CardsResumo>
    <Card title="Produtos Estoque" value="245" />
    <Card title="Estoque Baixo" value="12" color="warning" />
    <Card title="Sem Estoque" value="5" color="danger" />
    <Card title="Lotes Vencendo" value="3" color="warning" />
  </CardsResumo>
  
  <Grafico>
    <GraficoLinha title="Movimentações 30 dias" />
  </Grafico>
  
  <Alertas>
    <AlertaEstoqueBaixo />
    <AlertaLoteVencendo />
  </Alertas>
</EstoquePage>
```

---

#### 2. `/estoque/produtos` - Lista Produtos
**Objetivo**: Ver estoque de todos produtos

**Layout**:
```tsx
<EstoqueProdutosPage>
  <Filtros>
    <InputBusca />
    <SelectCategoria />
    <SelectStatus />
  </Filtros>
  
  <ResponsiveTable>
    <Column>Produto</Column>
    <Column>Disponível</Column>
    <Column>Reservado</Column>
    <Column>Mínimo</Column>
    <Column>Status</Column>
    <Column>Ações</Column>
  </ResponsiveTable>
</EstoqueProdutosPage>
```

**Endpoints**:
- `GET /estoque?skip=0&limit=20`

---

#### 3. `/estoque/movimentacoes` - Histórico
**Objetivo**: Ver todas movimentações

**Layout**:
```tsx
<MovimentacoesPage>
  <Filtros>
    <SelectTipo />
    <InputPeriodo />
    <SelectProduto />
  </Filtros>
  
  <Timeline>
    <MovimentacaoCard>
      <Tipo badge />
      <Produto />
      <Quantidade />
      <Data />
      <Usuario />
    </MovimentacaoCard>
  </Timeline>
</MovimentacoesPage>
```

**Endpoints**:
- `GET /estoque/movimentacoes?tipo=&data_inicio=&skip=0&limit=20`

---

#### 4. `/estoque/entrada` - Registrar Entrada
**Objetivo**: Dar entrada em produtos

**Layout**:
```tsx
<EntradaEstoquePage>
  <FormEntrada>
    <SeletorProduto />
    <SeletorVariante />
    <InputQuantidade />
    <InputCustoUnitario />
    
    <DadosLote>
      <InputCodigoLote />
      <InputDataValidade />
      <SelectFornecedor />
    </DadosLote>
    
    <InputObservacao />
    <BotaoRegistrar />
  </FormEntrada>
</EntradaEstoquePage>
```

**Endpoints**:
- `POST /estoque/movimentacoes`

---

#### 5. `/estoque/saida` - Registrar Saída
**Objetivo**: Dar saída manual

**Layout**: Similar à entrada, sem dados de lote

---

#### 6. `/estoque/ajuste` - Ajuste Inventário
**Objetivo**: Corrigir divergências

**Layout**:
```tsx
<AjusteInventarioPage>
  <FormAjuste>
    <SeletorProduto />
    <SeletorVariante />
    
    <Grid>
      <InputQuantidadeSistema disabled />
      <InputQuantidadeFisica />
      <DisplayDivergencia />
    </Grid>
    
    <SelectMotivo>
      <Option>Inventário</Option>
      <Option>Perda</Option>
      <Option>Dano</Option>
      <Option>Outro</Option>
    </SelectMotivo>
    
    <InputObservacao required />
    <BotaoAjustar />
  </FormAjuste>
</AjusteInventarioPage>
```

**Endpoints**:
- `POST /estoque/movimentacoes` (tipo: AJUSTE)

---

#### 7. `/estoque/alertas` - Alertas
**Objetivo**: Ver alertas de estoque

**Layout**:
```tsx
<AlertasPage>
  <Tabs>
    <Tab title="Estoque Baixo">
      <ProdutoCard>
        <Nome />
        <EstoqueAtual badge="danger" />
        <EstoqueMinimo />
        <BotaoEntrada />
      </ProdutoCard>
    </Tab>
    
    <Tab title="Sem Estoque">
      <ProdutoCard />
    </Tab>
    
    <Tab title="Lotes Vencendo">
      <LoteCard>
        <Produto />
        <CodigoLote />
        <DataValidade badge="warning" />
        <DiasRestantes />
        <BotaoMarcarVencido />
      </LoteCard>
    </Tab>
  </Tabs>
</AlertasPage>
```

**Endpoints**:
- `GET /estoque/alertas/baixo`
- `GET /estoque/alertas/zerado`
- `GET /estoque/alertas/lotes-vencendo`

---

## 🎨 Componentes Compartilhados

### Já Implementados ✅

```tsx
// Layout
<ResponsiveContainer maxWidth="xl" />
<ResponsiveTable striped hover />
<ResponsiveCard title="..." />

// Forms
<MaskedInput mask="cpf" />
<MaskedInput mask="phone" />
<MaskedInput mask="cep" />

// UI
<StatusBadge status="CONFIRMADA" />
<LoadingSpinner />
<EmptyState message="..." />
<ErrorMessage error={...} />
```

### A Criar 🔴

```tsx
// Busca
<AutocompleteInput
  placeholder="Buscar produto..."
  onSearch={handleSearch}
  onSelect={handleSelect}
  renderItem={(item) => <ProdutoItem />}
/>

// Seletores
<ClienteSelector
  value={clienteId}
  onChange={setClienteId}
  showCredito={true}
/>

<ProdutoSelector
  value={produtoId}
  onChange={setProdutoId}
  showEstoque={true}
/>

// Calculadoras
<DescontoCalculator
  subtotal={subtotal}
  onDescontoChange={setDesconto}
/>

<TrocoCalculator
  total={total}
  valorRecebido={valorRecebido}
/>

// Resumos
<ResumoValores
  subtotal={subtotal}
  desconto={desconto}
  frete={frete}
  total={total}
/>

// Timeline
<Timeline>
  <TimelineItem
    date="23/06/2026"
    title="Confirmada"
    description="Pagamento recebido"
    icon={<CheckIcon />}
    color="success"
  />
</Timeline>
```

---

## 🎯 Hooks Customizados

### Implementados ✅

```typescript
// Carrinho (Loja Online)
const useCarrinho = () => {
  const { data, mutate } = useSWR('/loja/carrinho');
  
  return {
    carrinho: data,
    adicionarItem,
    removerItem,
    atualizarQuantidade,
    limparCarrinho,
    calcularTotal
  };
};
```

### A Criar 🔴

```typescript
// PDV (Vendas)
const usePDV = () => {
  const [itens, setItens] = useState([]);
  const [cliente, setCliente] = useState(null);
  const [desconto, setDesconto] = useState({ tipo: null, valor: 0 });
  
  return {
    itens,
    cliente,
    desconto,
    total,
    adicionarProduto,
    removerItem,
    setCliente,
    aplicarDesconto,
    finalizarVenda
  };
};

// Estoque
const useEstoque = () => {
  const { data } = useSWR('/estoque');
  
  return {
    estoque: data,
    registrarEntrada,
    registrarSaida,
    ajustarInventario,
    buscarProduto
  };
};

// Validações
const useValidacoes = () => {
  return {
    validarTelefone,
    validarCPF,
    validarCEP,
    validarEmail
  };
};
```

---

## 📚 Bibliotecas

### ✅ Instaladas e em Uso

```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "react-router-dom": "^6.20.0",
  "axios": "^1.6.2",
  "@tanstack/react-query": "^5.12.2",
  "react-hook-form": "^7.49.2",
  "zod": "^3.22.4",
  "@hookform/resolvers": "^3.3.2",
  "bootstrap": "^5.3.2",
  "react-bootstrap": "^2.9.1",
  "react-icons": "^4.12.0",
  "sass": "^1.69.5",
  "date-fns": "^2.30.0",
  "react-toastify": "^9.1.3",
  "react-loading-skeleton": "^3.3.1",
  "chart.js": "^4.4.1",
  "react-chartjs-2": "^5.2.0"
}
```

### 🔴 A Instalar para Vendas/Estoque

```bash
npm install react-select react-datepicker currency.js react-input-mask qrcode.react
```

**Justificativas**:
- `react-select`: Autocomplete avançado (busca produtos/clientes no PDV)
- `react-datepicker`: Seletor de período nos filtros e relatórios
- `currency.js`: Formatação precisa de valores monetários
- `react-input-mask`: Máscaras para inputs (CPF, telefone, CEP)
- `qrcode.react`: Gerar QR Code PIX (pagamentos)

---

## 🚀 Priorização

### Sprint 1-2: Vendas/PDV 🔥 URGENTE
- [  ] VendasPage - Lista
- [  ] PDVPage - Ponto de venda completo
- [  ] VendaDetalhesPage
- [  ] Modais workflow
- [  ] Componentes compartilhados

**Entregável**: PDV funcional

### Sprint 3: Estoque 🔥 ALTA
- [  ] EstoquePage - Dashboard
- [  ] EstoqueProdutosPage - Lista
- [  ] MovimentacoesPage - Histórico
- [  ] EntradaEstoquePage
- [  ] AlertasPage

**Entregável**: Gestão estoque funcional

### Sprint 4: Melhorias UX 🟡
- [  ] Relatórios avançados
- [  ] Gráficos interativos
- [  ] Exportação PDF/Excel
- [  ] Atalhos teclado
- [  ] Impressão cupom

**Entregável**: Sistema production-ready

---

## 📝 Checklist Implementação

### Para Cada Rota

- [  ] Criar componente página
- [  ] Criar arquivo SCSS
- [  ] Implementar layout responsivo
- [  ] Integrar com API (axios)
- [  ] Implementar loading states
- [  ] Implementar error handling
- [  ] Implementar empty states
- [  ] Validações formulários
- [  ] Feedback visual (toasts)
- [  ] Testar em mobile
- [  ] Adicionar ao router

### Para Cada Componente

- [  ] Props interface TypeScript
- [  ] Documentação JSDoc
- [  ] Responsivo (mobile-first)
- [  ] Acessibilidade (ARIA)
- [  ] Estados (loading, error, empty)
- [  ] Testes unitários (futuro)

---

## 📊 Status Final

| Módulo | Backend | Frontend | Próximo Passo |
|--------|---------|----------|---------------|
| **Loja Online** | ✅ | ✅ | - |
| **Clientes** | ✅ | ✅ | Histórico |
| **Produtos** | ✅ | ✅ | - |
| **Vendas/PDV** | ✅ | 🔴 | **Implementar** |
| **Estoque** | ✅ | 🔴 | **Implementar** |
| **Financeiro** | 🔴 | 🔴 | Backend primeiro |

---

**Versão**: 2.0.0  
**Última atualização**: 23/06/2026  
**Foco atual**: Vendas/PDV Frontend
