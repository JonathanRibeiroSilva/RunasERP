# 🎨 Frontend - Guia de Implementação Completo

> **Última atualização**: 11/06/2026
> 
> Guia completo para implementar as telas pendentes do frontend, com foco em **Loja Online** e **Vendas/PDV**.
> **Backend**: ✅ 100% Pronto | **Frontend**: 🔴 0% Implementado

---

## 📊 Visão Geral

### Status Atual
- ✅ **Backend**: API completa e testada
- ✅ **Componentes Responsivos**: Container, Table, Card
- ✅ **Layout Mobile-First**: Sidebar, Navbar com backdrop
- ✅ **Loja Online**: **100% implementado** 🎉
- 🔴 **Vendas/PDV**: 0% implementado

### O Que Precisa Ser Feito

| Módulo | Rotas | Componentes | Status | Prioridade |
|--------|-------|-------------|--------|------------|
| **Loja Online** | 6 rotas | 15+ componentes | ✅ **COMPLETO** | 🔥 Alta |
| **Vendas/PDV** | 6 rotas | 12+ componentes | 🔴 Pendente | 🔥 Alta |
| **Estoque** | 9 rotas | 10+ componentes | 🔴 Pendente | 🟡 Média |

---

## 🛒 LOJA ONLINE - ✅ IMPLEMENTAÇÃO COMPLETA

### 📋 Visão Geral

**Backend Status**: ✅ **100% Completo** (26 endpoints)  
**Frontend Status**: ✅ **100% IMPLEMENTADO** 🎉

#### Rotas Implementadas ✅
1. ✅ `/c/:empresaSlug` - Catálogo de produtos
2. ✅ `/c/:empresaSlug/produto/:id` - Detalhes do produto
3. ✅ `/c/:empresaSlug/carrinho` - Carrinho de compras
4. ✅ `/c/:empresaSlug/checkout` - Finalizar compra (3 steps)
5. ✅ `/c/:empresaSlug/pedido/:numero` - Rastreamento de pedido
6. ✅ `/c/:empresaSlug/minha-conta/pedidos` - Meus pedidos

#### Funcionalidades Implementadas ✅
- ✅ Hook `useCarrinho` para gerenciamento de estado
- ✅ Catálogo com filtros e busca
- ✅ Adicionar ao carrinho com feedback visual
- ✅ Gerenciar carrinho (adicionar, remover, atualizar)
- ✅ Checkout multi-step (dados, entrega, pagamento)
- ✅ Integração ViaCEP (busca automática de endereço)
- ✅ Cálculo de frete
- ✅ Múltiplas formas de pagamento (PIX, Débito, Crédito, Dinheiro, Fiado)
- ✅ Cálculo automático de troco
- ✅ Timeline visual de status do pedido
- ✅ Histórico de compras
- ✅ Filtro por status de pedidos
- ✅ Formatação automática (telefone, CPF, CEP)
- ✅ Validações em tempo real
- ✅ Estados de UI completos (loading, error, empty, success)
- ✅ Totalmente responsivo (mobile, tablet, desktop)

#### Documentação Completa ✅
- ✅ `CHANGELOG_CARRINHO_LOJA.md` - Implementação do carrinho
- ✅ `CHANGELOG_LOJA_ONLINE_FRONTEND_COMPLETO.md` - Documentação técnica
- ✅ `RESUMO_SESSAO_LOJA_ONLINE.md` - Resumo da implementação

**Status**: 🟢 **LOJA ONLINE OPERACIONAL E COMPLETA!**

---

## 🎯 FASE 1: Catálogo Público da Loja - ✅ COMPLETO

### Rotas Implementadas ✅

#### 1. `/c/:empresaSlug` - Página Principal da Loja ✅
**Status**: ✅ Implementado

**Funcionalidades**:
- ✅ Listar produtos visíveis (catalogo_ativo=true)
- ✅ Filtrar por categoria
- ✅ Buscar por nome
- ✅ Ordenar (menor preço, maior preço, nome A-Z, destaques)
- ✅ Paginação
- ✅ Grid responsivo (1 col mobile, 2 col tablet, 3-4 col desktop)
- ✅ Botão compartilhar (copiar link, WhatsApp)
- ✅ Indicador de carrinho com badge

---

#### 2. `/c/:empresaSlug/produto/:produtoId` - Detalhes do Produto ✅
**Status**: ✅ Implementado

**Funcionalidades**:
- ✅ Galeria de fotos com zoom (lightbox)
- ✅ Seletor de variantes (cor, tamanho, etc)
- ✅ Atualização de preço ao mudar variante
- ✅ Verificação de estoque em tempo real
- ✅ Controle de quantidade (+/-)
- ✅ Adicionar ao carrinho (com feedback visual - 3 estados)
- ✅ Botão "Ver Carrinho" (quando há itens)
- ✅ Produtos relacionados (mesma categoria)
- ✅ Compartilhamento (copiar link, WhatsApp)

---

#### 3. `/c/:empresaSlug/carrinho` - Carrinho de Compras ✅
**Status**: ✅ Implementado

**Funcionalidades**:
- ✅ Listar itens do carrinho (cookie de sessão)
- ✅ Atualizar quantidade inline (+/-)
- ✅ Remover item individual
- ✅ Limpar carrinho (com confirmação)
- ✅ Calcular subtotal
- ✅ Simular frete por CEP (opcional antes do checkout)
- ✅ Botão "Continuar comprando" volta ao catálogo
- ✅ Botão "Finalizar compra" vai para checkout
- ✅ Empty state amigável
- ✅ Resumo com totais

---

#### 4. `/c/:empresaSlug/checkout` - Finalizar Compra ✅
**Status**: ✅ Implementado

**Step 1: Dados do Cliente** ✅
- ✅ Nome completo (obrigatório)
- ✅ Telefone WhatsApp (obrigatório, formatado)
- ✅ E-mail (opcional)
- ✅ CPF (opcional, formatado)
- ✅ Validações em tempo real

**Step 2: Tipo de Entrega** ✅
- ✅ Retirada no local (grátis)
- ✅ Delivery com endereço completo
  - ✅ CEP com busca automática (ViaCEP)
  - ✅ Preenchimento automático do endereço
  - ✅ Cálculo de frete
- ✅ Validação de campos obrigatórios

**Step 3: Forma de Pagamento** ✅
- ✅ PIX (Mercado Pago)
- ✅ Cartão de Débito (Mercado Pago)
- ✅ Cartão de Crédito (Mercado Pago)
- ✅ Dinheiro (pagamento na entrega/retirada)
  - ✅ Input de troco com cálculo automático
- ✅ FIADO (validação backend)

**Resumo Lateral** ✅
- ✅ Lista de itens
- ✅ Subtotal
- ✅ Frete
- ✅ Total destacado
- ✅ Sticky no desktop

**Finalização** ✅
- ✅ Validação de cliente convidado (telefone DDD + 9 dígitos)
- ✅ Buscar CEP via ViaCEP e preencher endereço
- ✅ Calcular frete automaticamente (backend)
- ✅ Validar limite de crédito se FIADO
- ✅ Pagamento misto (ex: Fiado R$ 50 + PIX R$ 50)
- ✅ Redirecionar para Mercado Pago se pagamento online
- ✅ Mostrar mensagem de sucesso com número do pedido

---

#### 5. `/c/:empresaSlug/pedido/:numeroPedido` - Rastreamento ✅
**Status**: ✅ Implementado

**Funcionalidades**:
- ✅ Timeline visual de mudanças de status
- ✅ Mostrar data/hora de cada mudança
- ✅ Observações de cada etapa
- ✅ Previsão de entrega (se DELIVERY)
- ✅ Dados de contato da loja
- ✅ Detalhes do pedido (itens, valores, forma de pagamento)
- ✅ Histórico completo de alterações
- ✅ Badge de status colorido
- ✅ Estados especiais (cancelada, reembolsada)

---

#### 6. `/c/:empresaSlug/minha-conta/pedidos` - Meus Pedidos ✅
**Status**: ✅ Implementado

**Funcionalidades**:
- ✅ Listar pedidos do cliente (cookie de sessão)
- ✅ Filtrar por status
- ✅ Ordenar por data (mais recente primeiro)
- ✅ Paginação
- ✅ Link direto para rastreamento
- ✅ Cards com informações resumidas
- ✅ Grid responsivo
- ✅ Empty state (sem pedidos)

---

### 🎨 Design System da Loja - ✅ Implementado

#### Cores por Status ✅
```scss
PEDIDO:      #6c757d (cinza)
PENDENTE:    #ffc107 (amarelo)
CONFIRMADA:  #17a2b8 (ciano)
SEPARADA:    #fd7e14 (laranja)
EM_ENTREGA:  #0dcaf0 (azul claro)
ENTREGUE:    #28a745 (verde)
FINALIZADA:  #198754 (verde escuro)
CANCELADA:   #dc3545 (vermelho)
REEMBOLSADA: #6f42c1 (roxo)
```

#### Componentes Compartilhados ✅
- ✅ Hook `useCarrinho` - Gerenciamento de estado do carrinho
- ✅ Formatação automática (telefone, CPF, CEP, preço)
- ✅ Validações (telefone DDD+9, CPF, CEP)
- ✅ Estados de UI (loading, error, empty, success)
- ✅ Timeline de status (rastreamento)
- ✅ Steps indicator (checkout)
- ✅ Badge de status colorido

---

## 💰 VENDAS/PDV - Implementação Completa

### 📋 Visão Geral

**Backend Status**: ✅ **100% Completo** (14 endpoints)  
**Frontend Status**: 🔴 **0% Implementado**

#### Features do Backend Prontas
- ✅ CRUD de vendas
- ✅ Workflow completo (6 status)
- ✅ Múltiplas formas de pagamento
- ✅ Desconto (percentual ou valor fixo)
- ✅ Validação de cliente (ativo, bloqueado, crédito)
- ✅ Reserva/baixa de estoque automática
- ✅ Cliente opcional (vendas de balcão)
- ✅ Histórico de mudanças de status
- ✅ Relatórios (resumo, por período)

---

## 🎯 FASE 2: Ponto de Venda (PDV)

### Rotas a Implementar

#### 1. `/vendas` - Lista de Vendas
**Descrição**: Dashboard de vendas com filtros

**Componentes Necessários**:
```tsx
<VendasPage>
  <VendasHeader>
    <BotaoNovaVenda />         // + Nova Venda (vai para PDV)
    <FiltrosVendas>
      <SelectStatus />
      <SelectCliente />
      <InputPeriodo />         // Date range picker
      <InputNumero />          // Buscar por número
    </FiltrosVendas>
  </VendasHeader>
  
  <ResponsiveTable>
    <thead>
      <tr>
        <th>Número</th>
        <th>Cliente</th>
        <th>Data</th>
        <th>Valor</th>
        <th>Status</th>
        <th>Ações</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>#V-2026-00001</td>
        <td>João Silva</td>
        <td>11/06/2026</td>
        <td>R$ 150,00</td>
        <td><BadgeStatus /></td>
        <td>
          <BotaoVer />
          <BotaoEditar />       // Se PEDIDO
          <BotaoCancelar />
        </td>
      </tr>
    </tbody>
  </ResponsiveTable>
  
  <Paginacao />
</VendasPage>
```

**Endpoints Usados**:
```typescript
// GET /vendas?status=&cliente_id=&data_inicio=&data_fim=&numero=&skip=0&limit=20
```

**Funcionalidades**:
- ✅ Listar vendas com filtros avançados
- ✅ Badges coloridos por status
- ✅ Buscar por número de venda
- ✅ Filtrar por cliente
- ✅ Filtrar por período
- ✅ Paginação
- ✅ Ações contextuais (editar só se PEDIDO)

---

#### 2. `/vendas/nova` - PDV (Ponto de Venda)
**Descrição**: Tela de venda completa (mais complexa)

**Componentes Necessários**:
```tsx
<PDVPage>
  <PDVHeader>
    <BotaoVoltar />
    <InfoVendedor />           // Usuário logado
  </PDVHeader>
  
  <PDVGrid>
    {/* Coluna Esquerda: Produtos */}
    <PainelProdutos>
      <BuscaProduto>           // Busca por nome/SKU/código barras
        <InputBusca />         // Autocomplete
        <BotaoScanCodigo />    // Ícone de câmera (futuro)
      </BuscaProduto>
      
      <ResultadosBusca>
        <ProdutoResultado>     // Card com foto, nome, preço
          <BotaoAdicionar />
        </ProdutoResultado>
      </ResultadosBusca>
      
      <CategoriasRapidas />    // Botões de categorias frequentes
    </PainelProdutos>
    
    {/* Coluna Direita: Carrinho e Finalização */}
    <PainelVenda>
      <SeletorCliente>         // Opcional
        <BuscaCliente />       // Autocomplete
        <InfoCliente />        // Crédito disponível, histórico
        <BotaoNovoCliente />
      </SeletorCliente>
      
      <ItensVenda>
        <ItemVenda>            // Produto, quantidade, preço, subtotal
          <QuantidadeEditor />
          <BotaoRemover />
        </ItemVenda>
      </ItensVenda>
      
      <ResumoVenda>
        <Subtotal />
        <Desconto>             // Input % ou R$
          <RadioPercentual />
          <RadioValorFixo />
          <InputDesconto />
        </Desconto>
        <ValorTotal />         // Grande e destacado
      </ResumoVenda>
      
      <BotaoFinalizarVenda />  // Abre modal de pagamento
    </PainelVenda>
  </PDVGrid>
  
  {/* Modal de Pagamento */}
  <ModalPagamento>
    <FormasPagamento>
      <BotaoPix />
      <BotaoDebito />
      <BotaoCredito />
      <BotaoDinheiro>          // Abre calc de troco
        <InputValorRecebido />
        <DisplayTroco />
      </BotaoDinheiro>
      <BotaoFiado>            // Valida crédito
        <AlertaCredito />
      </BotaoFiado>
    </FormasPagamento>
    
    <PagamentosMixtos>         // Lista de pagamentos adicionados
      <PagamentoItem />
      <TotalPago />
      <RestaPagar />
    </PagamentosMixtos>
    
    <BotaoConfirmarVenda />
  </ModalPagamento>
</PDVPage>
```

**Endpoints Usados**:
```typescript
// GET /produtos?busca=&empresa_id=
// GET /clientes?busca=&empresa_id=
// POST /vendas
interface CriarVendaRequest {
  empresa_id: number;
  cliente_id?: string;               // Opcional (venda balcão)
  itens: {
    produto_id: string;
    variante_id: string;
    quantidade: number;
    preco_unitario: number;
  }[];
  desconto_tipo?: 'PERCENTUAL' | 'VALOR_FIXO';
  desconto_valor?: number;
  tipo_entrega: 'RETIRADA' | 'DELIVERY';
  observacao?: string;
}
```

**Funcionalidades**:
- ✅ Busca de produtos (autocomplete)
- ✅ Suporte a código de barras (futuro: câmera)
- ✅ Adicionar itens ao carrinho
- ✅ Editar quantidade inline
- ✅ Remover itens
- ✅ Buscar cliente (autocomplete)
- ✅ Ver crédito disponível do cliente
- ✅ Aplicar desconto (% ou R$)
- ✅ Múltiplas formas de pagamento
- ✅ Calcular troco automaticamente
- ✅ Validar limite de crédito (FIADO)
- ✅ Atalhos de teclado (F2 cliente, F3 produto, F9 finalizar)
- ✅ Imprimir cupom (futuro)

---

#### 3. `/vendas/:id` - Detalhes da Venda
**Descrição**: Visualizar venda completa

**Componentes Necessários**:
```tsx
<VendaDetalhesPage>
  <VendaHeader>
    <NumeroVenda />            // #V-2026-00001
    <BadgeStatus />
    <AcoesVenda>
      <BotaoEditar />          // Se PEDIDO
      <BotaoConfirmar />       // Se PEDIDO
      <BotaoSeparar />         // Se CONFIRMADA
      <BotaoEntregar />        // Se SEPARADA
      <BotaoFinalizar />       // Se ENTREGUE
      <BotaoCancelar />        // Se != FINALIZADA
      <BotaoImprimir />
    </AcoesVenda>
  </VendaHeader>
  
  <VendaInfo>
    <DadosCliente />           // Nome, telefone, crédito usado
    <DadosVenda />             // Data, tipo entrega, observação
    <ItensVenda />             // Tabela de itens
    <Pagamentos />             // Lista de pagamentos
    <Resumo />                 // Subtotal, desconto, total
  </VendaInfo>
  
  <HistoricoStatus>            // Timeline
    <StepStatus>
      PEDIDO → CONFIRMADA
      11/06/2026 10:35
      Por: João Silva
    </StepStatus>
  </HistoricoStatus>
</VendaDetalhesPage>
```

**Endpoints Usados**:
```typescript
// GET /vendas/{id}
```

**Funcionalidades**:
- ✅ Visualizar todos os dados da venda
- ✅ Timeline de mudanças de status
- ✅ Ações contextuais por status
- ✅ Imprimir cupom/nota
- ✅ Histórico de quem alterou

---

#### 4. `/vendas/:id/editar` - Editar Venda (se PEDIDO)
**Descrição**: Editar venda antes de confirmar

**Componentes**: Similar ao PDV, mas carregado com dados da venda

**Endpoints Usados**:
```typescript
// GET /vendas/{id}
// PUT /vendas/{id}
```

**Funcionalidades**:
- ✅ Só permitir se status = PEDIDO
- ✅ Editar itens (adicionar, remover, quantidade)
- ✅ Editar desconto
- ✅ Alterar cliente
- ✅ Atualizar observação

---

#### 5. Modais de Ações

**Modal Confirmar Venda** (PEDIDO → CONFIRMADA)
```tsx
<ModalConfirmarVenda>
  <ResumoVenda />              // Itens, valor total
  <PagamentosAdicionar>        // Se não tiver pagamentos
    <FormPagamento />
  </PagamentosAdicionar>
  <InputObservacao />
  <BotaoConfirmar />
</ModalConfirmarVenda>
```

**Modal Separar Venda** (CONFIRMADA → SEPARADA)
```tsx
<ModalSepararVenda>
  <ChecklistItens>             // Marcar itens separados
    <ItemSeparacao checked />
  </ChecklistItens>
  <InputObservacao />
  <BotaoSeparar />
</ModalSepararVenda>
```

**Modal Entregar Venda** (SEPARADA → ENTREGUE)
```tsx
<ModalEntregarVenda>
  <InfoEntrega />              // Endereço ou "Retirada no local"
  <AssinaturaCliente />        // Canvas para assinar (futuro)
  <FotoComprovante />          // Upload (futuro)
  <InputObservacao />
  <BotaoEntregar />            // Baixa estoque aqui!
</ModalEntregarVenda>
```

**Modal Cancelar Venda**
```tsx
<ModalCancelarVenda>
  <AlertaCancelamento>
    ⚠️ Esta ação liberará o estoque reservado
  </AlertaCancelamento>
  <TextareaMotivo />           // Obrigatório
  <BotaoCancelar color="danger" />
</ModalCancelarVenda>
```

---

#### 6. `/vendas/relatorios` - Relatórios de Vendas
**Descrição**: Dashboard analítico

**Componentes Necessários**:
```tsx
<RelatoriosVendasPage>
  <FiltrosRelatorio>
    <SelectPeriodo />          // Hoje, semana, mês, customizado
    <SelectVendedor />
    <SelectCategoria />
  </FiltrosRelatorio>
  
  <CardsResumo>
    <CardMetrica>
      <Titulo>Vendas Hoje</Titulo>
      <Valor>R$ 3.450,00</Valor>
      <Variacao>+15% vs ontem</Variacao>
    </CardMetrica>
    <CardMetrica>
      <Titulo>Ticket Médio</Titulo>
      <Valor>R$ 125,00</Valor>
    </CardMetrica>
    <CardMetrica>
      <Titulo>Vendas Realizadas</Titulo>
      <Valor>28</Valor>
    </CardMetrica>
  </CardsResumo>
  
  <GraficosVendas>
    <GraficoLinha title="Vendas por Dia" />
    <GraficoPizza title="Formas de Pagamento" />
    <GraficoBarra title="Top 10 Produtos" />
    <GraficoBarra title="Vendas por Categoria" />
  </GraficosVendas>
  
  <TabelaDetalhada>
    <ResponsiveTable>
      {/* Lista de vendas do período */}
    </ResponsiveTable>
  </TabelaDetalhada>
  
  <BotoesExportar>
    <BotaoExportarPDF />
    <BotaoExportarExcel />
  </BotoesExportar>
</RelatoriosVendasPage>
```

**Endpoints Usados**:
```typescript
// GET /vendas/relatorios/resumo?data_inicio=&data_fim=
interface RelatorioResumo {
  total_vendas: number;
  total_valor: number;
  ticket_medio: number;
  vendas_por_status: { status: string; quantidade: number }[];
  vendas_por_pagamento: { forma: string; valor: number }[];
  produtos_mais_vendidos: { produto: string; quantidade: number }[];
}
```

**Funcionalidades**:
- ✅ KPIs principais em cards
- ✅ Gráficos interativos (Chart.js/Recharts)
- ✅ Filtros de período
- ✅ Comparação com períodos anteriores
- ✅ Exportar relatórios (PDF/Excel)
- ✅ Ranking de produtos
- ✅ Análise de formas de pagamento

---

## 🛠️ Componentes Compartilhados

### Componentes Gerais
```tsx
// Busca com Autocomplete
<BuscaAutocomplete
  placeholder="Buscar produto..."
  onSearch={handleSearch}
  onSelect={handleSelect}
  resultados={produtos}
  renderItem={(item) => <ProdutoItem produto={item} />}
/>

// Seletor de Cliente
<ClienteSelector
  value={clienteId}
  onChange={setClienteId}
  showCredito={true}
/>

// Badge de Status
<StatusBadge status="CONFIRMADA" />

// Timeline de Status
<StatusTimeline historico={historico} />

// Calculadora de Desconto
<DescontoCalculator
  subtotal={subtotal}
  onDescontoChange={setDesconto}
/>

// Resumo de Valores
<ResumoValores
  subtotal={subtotal}
  desconto={desconto}
  frete={frete}
  total={total}
/>
```

### Hooks Customizados
```typescript
// Hook para carrinho (Loja)
const useCarrinho = () => {
  const { data, mutate } = useSWR('/loja/carrinho');
  
  const adicionarItem = async (item) => { /* ... */ };
  const removerItem = async (id) => { /* ... */ };
  const atualizarQuantidade = async (id, qtd) => { /* ... */ };
  const limparCarrinho = async () => { /* ... */ };
  
  return { carrinho: data, adicionarItem, removerItem, ... };
};

// Hook para PDV (Vendas)
const usePDV = () => {
  const [itens, setItens] = useState([]);
  const [cliente, setCliente] = useState(null);
  const [desconto, setDesconto] = useState({ tipo: null, valor: 0 });
  
  const adicionarProduto = (produto, variante, quantidade) => { /* ... */ };
  const calcularTotal = () => { /* ... */ };
  const finalizarVenda = async (pagamentos) => { /* ... */ };
  
  return { itens, cliente, desconto, total, ... };
};

// Hook para validações
const useValidacoes = () => {
  const validarTelefone = (tel) => /^\d{10,11}$/.test(tel);
  const validarCPF = (cpf) => { /* lógica */ };
  const validarCEP = (cep) => /^\d{8}$/.test(cep);
  
  return { validarTelefone, validarCPF, validarCEP };
};
```

---

## 📦 Bibliotecas Recomendadas

### UI Components
```json
{
  "react-bootstrap": "^2.9.1",           // ✅ Já instalado
  "react-icons": "^4.12.0",              // ✅ Já instalado
  "react-select": "^5.8.0",              // Autocomplete avançado
  "react-datepicker": "^4.21.0",         // Date range picker
  "react-image-lightbox": "^5.1.4",      // Galeria de fotos com zoom
  "react-hot-toast": "^2.4.1"            // Notificações toast
}
```

### Charts
```json
{
  "chart.js": "^4.4.1",                  // ✅ Já instalado
  "react-chartjs-2": "^5.2.0",           // ✅ Já instalado
  "recharts": "^2.10.3"                  // Alternativa Chart.js
}
```

### Formulários
```json
{
  "react-hook-form": "^7.49.2",          // ✅ Já instalado
  "zod": "^3.22.4",                      // ✅ Já instalado
  "@hookform/resolvers": "^3.3.2"        // ✅ Já instalado
}
```

### Utilitários
```json
{
  "date-fns": "^2.30.0",                 // ✅ Já instalado
  "currency.js": "^2.0.4",               // Formatação de moeda
  "react-input-mask": "^2.0.4",          // Máscaras de input
  "qrcode.react": "^3.1.0"               // QR Code PIX
}
```

---

## 🎨 Paleta de Cores por Status

```scss
// Status de Vendas
$status-pedido: #6c757d;           // Cinza
$status-pendente: #ffc107;         // Amarelo
$status-confirmada: #17a2b8;       // Ciano
$status-separada: #fd7e14;         // Laranja
$status-em-entrega: #0dcaf0;       // Azul claro
$status-entregue: #28a745;         // Verde
$status-finalizada: #198754;       // Verde escuro
$status-cancelada: #dc3545;        // Vermelho
$status-reembolsada: #6f42c1;      // Roxo
```

---

## ⚡ Priorização de Implementação

### ~~Sprint 1 (2 semanas) - Loja Online Básica~~ ✅ COMPLETO
**Objetivo**: Cliente consegue comprar
1. ✅ Página do catálogo (`/c/:slug`)
2. ✅ Detalhes do produto
3. ✅ Carrinho
4. ✅ Checkout (3 steps completos)
5. ✅ Rastreamento
6. ✅ Meus pedidos

**Resultado**: ✅ Loja funcional end-to-end com todas as features

### Sprint 2 (1 semana) - PDV Básico
**Objetivo**: Vendedor consegue vender
1. ✅ Lista de vendas
2. ✅ PDV simplificado (sem busca avançada)
3. ✅ Confirmar venda
4. ✅ Detalhes da venda

**Resultado**: PDV funcional para vendas presenciais

### Sprint 3 (1 semana) - Integrações
**Objetivo**: Automações funcionando
1. ✅ Mercado Pago no checkout
2. ✅ Webhooks (já funcionam no backend)
3. ✅ Notificações WhatsApp
4. ✅ Meus pedidos

**Resultado**: Experiência completa automatizada

### Sprint 4 (1 semana) - Melhorias
**Objetivo**: UX polida
1. ✅ PDV com busca avançada
2. ✅ Atalhos de teclado
3. ✅ Relatórios de vendas
4. ✅ Painel administrativo

**Resultado**: Sistema production-ready

---

## 📝 Checklist de Implementação

### Loja Online ✅ COMPLETO
- [x] CatalogoPage (vitrine)
- [x] ProdutoDetalhePage (detalhes)
- [x] CarrinhoPage (revisão)
- [x] CheckoutPage (pagamento)
- [x] RastreamentoPedidoPage (status)
- [x] MeusPedidosPage (histórico)
- [x] ProdutoCard component
- [x] BotaoAdicionarCarrinho component
- [x] FormEndereco component
- [x] CalculadoraFrete component
- [x] TimelineStatus component
- [x] useCarrinho hook
- [x] Integração Mercado Pago
- [x] Validação ViaCEP
- [x] Formatação automática (telefone, CPF, CEP)
- [x] Steps indicator (checkout)
- [x] Badge de status colorido
- [x] Estados de UI (loading, error, empty, success)
- [x] Responsividade completa

### Vendas/PDV
- [ ] VendasPage (lista)
- [ ] PDVPage (ponto de venda)
- [ ] VendaDetalhesPage (detalhes)
- [ ] VendaEditarPage (edição)
- [ ] RelatoriosVendasPage (analytics)
- [ ] BuscaProduto component
- [ ] BuscaCliente component
- [ ] ItemVenda component
- [ ] ModalPagamento component
- [ ] ModalConfirmarVenda component
- [ ] ModalSepararVenda component
- [ ] ModalEntregarVenda component
- [ ] ModalCancelarVenda component
- [ ] DescontoCalculator component
- [ ] ResumoVenda component
- [ ] usePDV hook
- [ ] Atalhos de teclado (F2, F3, F9)
- [ ] Impressão de cupom

---

## 🚀 Comandos para Iniciar

```bash
# Instalar dependências novas
npm install react-select react-datepicker react-image-lightbox react-hot-toast currency.js react-input-mask qrcode.react

# Rodar frontend
cd frontend
npm run dev

# Acessar
# Loja: http://localhost:3000/c/empresa-slug
# Vendas: http://localhost:3000/vendas
```

---

## 📚 Documentação de Referência

- **Backend Loja Online**: `LOJA_ONLINE_MVP_COMPLETO.md`
- **Backend Vendas**: `CHANGELOG_VENDAS_IMPLEMENTATION.md`
- **Responsividade**: `MELHORIAS_RESPONSIVIDADE.md`
- **Swagger Backend**: `http://localhost:8004/docs` (Vendas)

---

**Pronto para começar a implementar! 🎨🚀**
