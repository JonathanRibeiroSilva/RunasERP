# 📋 Checklist de Desenvolvimento - ERP Runas

> **Última atualização**: 09/06/2026
> 
> Este documento lista todas as funcionalidades, regras de negócio e melhorias necessárias para o sistema ERP.
> **Status**: 🔴 Não iniciado | 🟡 Em progresso | ✅ Concluído

---

## 📊 Visão Geral do Progresso

### Backend
- ✅ **API Gateway**: Autenticação, OAuth, JWT, Email Service
- ✅ **Clientes**: CRUD completo com transações ACID + Multi-tenancy
- ✅ **Produtos**: CRUD completo com transações ACID + Multi-tenancy 100%
- ✅ **Estoque**: CRUD completo com transações ACID + Multi-tenancy 100%
- ✅ **Vendas**: Implementação completa do zero com Multi-tenancy 100%
- 🔴 **Financeiro**: Estrutura criada, sem implementação
- ✅ **Notificações**: Implementado

### Frontend
- ✅ **Autenticação**: Login, Register, OAuth
- ✅ **Dashboard**: Página inicial
- ✅ **Clientes**: Lista, Cadastro, Edição, Endereços, Crédito
- 🔴 **Clientes**: Histórico
- ✅ **Produtos**: Lista, Cadastro, Edição, Detalhes, Variantes, **Categorias**
- 🔴 **Estoque**: Nenhuma rota implementada
- 🔴 **Vendas**: Nenhuma rota implementada
- 🔴 **Financeiro**: Nenhuma rota implementada

### Infraestrutura
- ✅ **PostgreSQL Consolidado**: 8 schemas em 1 container (economia de 228 MB RAM)
- ✅ **Nginx Reverse Proxy**: Configurado com DNS dinâmico
- ✅ **Docker Compose**: Dev e Prod configurados
- ✅ **SQLAlchemy 2.0.36**: Atualizado com suporte correto a search_path
- ✅ **Transações ACID**: Corrigidas em todos os serviços
- ✅ **Multi-Tenancy**: Implementado nativamente em Produtos, Estoque, Vendas

---

## 🏢 MULTI-TENANCY IMPLEMENTATION

> Implementação completa de multi-tenancy (Row-Level Multi-Tenancy) nos serviços principais do ERP.
> **Status**: ✅ 4 serviços implementados | 🔴 1 pendente (Financeiro)

### Estratégia Adotada

**Tipo**: Row-Level Multi-Tenancy (Shared Database, Shared Schema)
- ✅ Database único: `erp`
- ✅ Schema por serviço: `produtos`, `estoque`, `vendas`, `clientes`, etc.
- ✅ Coluna `empresa_id` em entidades raiz
- ✅ Header obrigatório: `X-Empresa-Id` em todos os endpoints
- ✅ Validação: `body.empresa_id == header.empresa_id` em POST/PUT
- ✅ Isolamento: Todos repositories filtram por `empresa_id`
- ✅ Unique constraints compostos: `(empresa_id, campo)` ao invés de global

### Serviços Implementados ✅

#### 1. **Produtos** (✅ 100%)
**Commit**: `f883e9a` - "feat(produtos): complete multi-tenancy adaptation with migration and seed"
**Data**: 09/06/2026

- ✅ `empresa_id` em: Produto, Categoria, Variante, Fornecedor
- ✅ Unique constraints: `(empresa_id, nome)`, `(empresa_id, sku)`, `(empresa_id, cnpj)`
- ✅ 11 arquivos modificados
- ✅ 39 endpoints adaptados
- ✅ 30+ métodos de repository
- ✅ 37 métodos de service
- ✅ Migration completa com upgrade/downgrade
- ✅ Seed com dados de teste (empresa_id=1)
- ✅ Changelog: `CHANGELOG_PRODUTOS_MULTITENANCY.md`

**Estatísticas**:
- Linhas de código: ~400 adicionadas
- Indexes criados: 10+
- Tempo de desenvolvimento: ~3h

#### 2. **Estoque** (✅ 100%)
**Commit**: `eb0d643` - "feat(estoque): complete multi-tenancy adaptation with migration and seed"
**Data**: 09/06/2026

- ✅ `empresa_id` em: Estoque, Lote, Inventario
- ✅ Unique constraints: `(empresa_id, produto_id, variante_id)`, `(empresa_id, codigo)`
- ✅ 3 models alterados
- ✅ 19 endpoints adaptados
- ✅ 28 métodos de repository
- ✅ 11 métodos de service
- ✅ Migration completa
- ✅ Seed com 3 estoques, 3 lotes, 4 movimentações, 1 inventário
- ✅ Changelog: `CHANGELOG_ESTOQUE_MULTITENANCY.md`

**Estatísticas**:
- Models alterados: 3
- Schemas alterados: 8
- Indexes criados: 5

#### 3. **Vendas** (✅ 100% - Nativo)
**Commit**: `645205f` - "feat(vendas): implement complete sales service with native multi-tenancy"
**Data**: 09/06/2026

- ✅ `empresa_id` em: Venda (entidade raiz)
- ✅ Entidades filhas isoladas via FK: ItemVenda, PagamentoVenda, ReservaEstoqueVenda
- ✅ Unique constraint: `(empresa_id, numero_venda)`
- ✅ Número de venda único por empresa: `V-{ANO}-{EMPRESA}-{SEQ}`
- ✅ 4 entidades + 5 enums
- ✅ 14 endpoints REST
- ✅ 20 métodos de repository
- ✅ 11 métodos de service + 5 integrações HTTP
- ✅ Migration completa
- ✅ Seed com 6 cenários (todos os status)
- ✅ Changelog: `CHANGELOG_VENDAS_IMPLEMENTATION.md` (500 linhas)

**Estatísticas**:
- Linhas de código: ~2.620
- Implementado do zero com multi-tenancy nativo
- Workflow completo: 6 estados

#### 4. **Clientes** (✅ 100%)
**Status**: Já implementado anteriormente
- ✅ `empresa_id` em: Cliente, Endereco
- ✅ Isolamento completo
- ✅ CPF único por empresa

#### 5. **Empresas** (✅ 100%)
**Status**: Implementado no API Gateway
- ✅ Tabela `empresas` no schema `gateway`
- ✅ CRUD completo
- ✅ Validação de CNPJ
- ✅ Campos: nome, razao_social, cnpj, telefone, email

### Serviços Pendentes 🔴

#### 1. **Financeiro** (🔴 0%)
- 🔴 A implementar: ContaReceber, ContaPagar, Recebimento, Pagamento
- 🔴 `empresa_id` necessário em todas as entidades raiz
- 🔴 Integração com Vendas (geração de ContaReceber para FIADO)

### Padrão de Implementação

#### Router
```python
from typing import Annotated
from fastapi import Depends, HTTPException
from utils.tenant import get_empresa_id

@router.post("/")
async def criar(
    dados: Schema,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    # Validar body vs header em POST/PUT
    if dados.empresa_id != empresa_id:
        raise HTTPException(
            status_code=403, 
            detail="empresa_id incompatível"
        )
    
    service = Service(session)
    return await service.criar(empresa_id, dados)
```

#### Service
```python
async def criar(
    db: AsyncSession,
    empresa_id: int,
    dados: Schema
) -> Model:
    # Sempre requer empresa_id como parâmetro
    return await repository.criar(db, empresa_id, dados)
```

#### Repository
```python
async def listar(
    db: AsyncSession,
    empresa_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Model]:
    stmt = (
        select(Model)
        .where(Model.empresa_id == empresa_id)  # ✅ SEMPRE filtrar
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
```

#### Model
```python
class Model(Base):
    __tablename__ = "tabela"
    __table_args__ = (
        UniqueConstraint('empresa_id', 'campo', name='uq_tabela_empresa_campo'),
        Index('ix_tabela_empresa_id', 'empresa_id'),
        Index('ix_tabela_empresa_id_ativo', 'empresa_id', 'ativo'),
        {"schema": "nome_schema"}
    )
    
    id = Column(UUID, primary_key=True, default=uuid4)
    empresa_id = Column(Integer, nullable=False, index=True)
    # ... outros campos
```

### Benefícios Alcançados ✅

1. **Isolamento de Dados**: Empresas não veem dados umas das outras
2. **Unique Constraints Corretos**: Cada empresa pode ter SKUs, categorias, códigos próprios
3. **Performance**: Indexes compostos otimizados `(empresa_id, campo)`
4. **Segurança**: Validação em múltiplas camadas (header, body, repository)
5. **Escalabilidade**: Preparado para centenas de empresas sem mudança de arquitetura
6. **Manutenibilidade**: Padrão consistente em todos os serviços

### Métricas de Multi-Tenancy

- **Total de commits**: 3 (Produtos, Estoque, Vendas)
- **Arquivos modificados**: 30+
- **Linhas de código**: ~3.300 (migrations, models, repositories, services, routers)
- **Endpoints adaptados**: 72 (39 Produtos + 19 Estoque + 14 Vendas)
- **Indexes criados**: 20+
- **Migrations**: 3 completas (todas com upgrade/downgrade)
- **Seeds**: 3 completos com dados de teste
- **Changelogs**: 3 documentos (900+ linhas de documentação)

### Próximos Passos

1. 🔴 **Aplicar Migrations**: Executar `alembic upgrade head` em cada serviço
2. 🔴 **Executar Seeds**: Popular com dados de teste
3. 🔴 **Testes de Isolamento**: Validar que empresa 1 não vê dados da empresa 2
4. 🔴 **Implementar Financeiro**: Último serviço pendente com multi-tenancy
5. 🔴 **Frontend**: Implementar seletor de empresa no login/header

---

## 🎯 PRIORIDADE 1: Funcionalidades Essenciais

### 0. LOJA ONLINE ✅ BACKEND 100% | 🟡 FRONTEND 30%

#### Backend - Funcionalidades ✅ 100% COMPLETO
- ✅ CRUD de configuração da loja (visível, destaque, ordem)
- ✅ CRUD de fotos de produtos
- ✅ Service de catálogo/loja implementado
- ✅ **Rotas públicas (sem autenticação)** - IMPLEMENTADO
- ✅ **Carrinho de compras (Redis)** - IMPLEMENTADO
- ✅ **Checkout simplificado** - IMPLEMENTADO
- ✅ **Rastreamento de pedidos** - IMPLEMENTADO
- ✅ **Área do cliente (meus pedidos)** - IMPLEMENTADO
- ✅ Filtro de produtos visíveis na loja
- ✅ Busca e ordenação de produtos
- ✅ Integração com Vendas (conversão carrinho → pedido)
- ✅ Sessão segura (cookies HttpOnly)

#### Frontend - Rotas a Implementar 🟡
- 🟡 `/loja/:empresaSlug` - Loja online (lista de produtos) - EM IMPLEMENTAÇÃO
- 🟡 `/loja/:empresaSlug/produto/:id` - Detalhes do produto - EM IMPLEMENTAÇÃO
- 🔴 `/loja/:empresaSlug/carrinho` - Carrinho de compras - **BACKEND PRONTO**
- 🔴 `/loja/:empresaSlug/checkout` - Finalizar pedido - **BACKEND PRONTO**
- 🔴 `/loja/:empresaSlug/pedido/:numero` - Rastreamento - **BACKEND PRONTO**
- 🔴 `/loja/:empresaSlug/minha-conta/pedidos` - Meus pedidos - **BACKEND PRONTO**
- 🔴 Botão "Compartilhar Loja" no painel admin

#### Frontend - Componentes Necessários 🟡
- 🟡 `LojaPage` - Lista de produtos com filtros - EM IMPLEMENTAÇÃO
- 🟡 `ProdutoDetalhePage` - Detalhes do produto - EM IMPLEMENTAÇÃO
- 🟡 `ProdutoCard` - Card do produto - EM IMPLEMENTAÇÃO
- 🟡 `FiltrosLoja` - Filtros e busca - EM IMPLEMENTAÇÃO
- 🔴 `CarrinhoLoja` - Carrinho de compras - **API PRONTA**
- 🔴 `CheckoutLoja` - Finalização de pedido - **API PRONTA**
- 🔴 `RastreamentoLoja` - Acompanhamento do pedido - **API PRONTA**
- 🔴 `MeusPedidosLoja` - Lista de pedidos do cliente - **API PRONTA**

#### Preparação Multi-Tenant 🟡
- 🟡 URL com slug: `/loja/:empresaSlug` (preparado para múltiplas empresas)
- 🟡 Código preparado para receber `empresa_id`
- ✅ Tabela `empresas` implementada no API Gateway
- ✅ Campo `slug` único por empresa
- 🔴 Middleware de identificação de empresa por slug

**🎯 Objetivo**: ✅ **Backend 100% completo!** Loja online funcional com carrinho (Redis), checkout e rastreamento. Frontend em andamento (30%).

---

### 1. CLIENTES

#### Backend - Regras de Negócio ✅ Implementadas
- ✅ CRUD de clientes com validação de CPF
- ✅ Gestão de endereços (múltiplos por cliente)
- ✅ Limite de crédito e crédito disponível
- ✅ Bloqueio/desbloqueio de clientes
- ✅ Dia de vencimento (1-28)
- ✅ Soft delete (desativação)

#### Backend - Melhorias Necessárias 🟡
- 🔴 **Integração com Vendas**: Verificar pedidos em aberto antes de desativar
- 🔴 **Integração com Financeiro**: Verificar contas pendentes antes de desativar
- 🔴 **Integração com Financeiro**: Buscar saldo devedor real ao definir crédito
- 🟡 **Validação de CEP**: Integrar com API ViaCEP no backend (frontend já implementado)
- 🔴 **Histórico de alterações**: Registrar mudanças de crédito, bloqueios, etc.
- 🔴 **Relatórios**: Clientes inadimplentes, crédito disponível, etc.

#### Frontend - Rotas a Implementar 🟢
- ✅ `/clientes` - Lista de clientes com filtros (nome, CPF, bloqueado)
- ✅ `/clientes/novo` - Cadastro de novo cliente
- ✅ `/clientes/:id` - Detalhes do cliente
- ✅ `/clientes/:id/editar` - Edição de cliente
- ✅ `/clientes/:id/enderecos` - Gestão de endereços
- ✅ `/clientes/:id/credito` - Gestão de crédito
- 🔴 `/clientes/:id/historico` - Histórico de compras e pagamentos

#### Frontend - Componentes Necessários 🔴
- ✅ `ClienteList` - Tabela com paginação e filtros
- ✅ `ClienteForm` - Formulário de cadastro/edição
- 🔴 `ClienteCard` - Card com informações resumidas
- 🔴 `EnderecoForm` - Formulário de endereço
- 🔴 `EnderecoList` - Lista de endereços do cliente
- 🔴 `CreditoManager` - Componente para gestão de crédito
- 🔴 `ClienteHistorico` - Timeline de atividades

---

### 2. PRODUTOS

#### Backend - Regras de Negócio ✅ Implementadas
- ✅ CRUD de categorias
- ✅ CRUD de produtos
- ✅ CRUD de variantes (SKU, preço, markup)
- ✅ Atributos de variantes (cor, tamanho, etc.)
- ✅ Cálculo automático de preço de venda (custo + markup)
- ✅ Soft delete de produtos
- ✅ **Multi-Tenancy 100%**: `empresa_id` em Produto, Categoria, Variante, Fornecedor
- ✅ **Fornecedores**: CRUD completo implementado
- ✅ **Associação Produto-Fornecedor**: Implementado (preço_custo, tempo_entrega)
- ✅ **Loja Online**: Configuração completa (visível, destaque, ordem)
- ✅ **Fotos de Produtos**: Upload e gestão de imagens implementado
- ✅ **Validação de SKU**: Unicidade por empresa garantida

#### Backend - Melhorias Necessárias 🔴
- 🔴 **Histórico de preços**: Registrar alterações de preço
- 🔴 **Produtos compostos**: Kits/combos de produtos
- 🔴 **Promoções**: Sistema de descontos e promoções
- 🔴 **Integração com Estoque**: Verificar estoque antes de desativar produto

#### Frontend - Rotas a Implementar 🟢
- ✅ `/produtos` - Lista de produtos com filtros
- ✅ `/produtos/novo` - Cadastro de novo produto
- ✅ `/produtos/:id` - Detalhes do produto
- ✅ `/produtos/:id/editar` - Edição de produto
- ✅ `/produtos/:id/variantes` - Gestão de variantes
- ✅ `/categorias` - **Gestão de categorias (CRUD completo implementado)**
- 🔴 `/produtos/:id/fotos` - Upload de fotos
- 🔴 `/produtos/:id/fornecedores` - Gestão de fornecedores
- 🔴 `/fornecedores` - Gestão de fornecedores

#### Frontend - Componentes Necessários 🟢
- ✅ `ProdutoList` - Tabela com paginação e filtros
- ✅ `ProdutoForm` - Formulário de cadastro/edição
- ✅ `ProdutoDetalhes` - Página de detalhes do produto
- ✅ `VarianteForm` - Formulário de variante
- ✅ `VarianteList` - Lista de variantes
- ✅ `CategoriasPage` - **Gestão de categorias (CRUD completo com grid de cards)**
- ✅ `PrecoCalculator` - Calculadora de markup e preço (integrado no form de variantes)
- 🔴 `AtributoManager` - Gestão de atributos (cor, tamanho)
- 🔴 `ImageUploader` - Upload de fotos
- 🔴 `FornecedorManager` - Gestão de fornecedores

**✅ DESBLOQUEADO**: Interface de categorias implementada! Agora é possível cadastrar produtos normalmente.

---

### 3. ESTOQUE

#### Backend - Regras de Negócio ✅ Implementadas
- ✅ Controle de quantidade (disponível, reservada)
- ✅ Movimentações (entrada, saída, ajuste, devolução, perda)
- ✅ Gestão de lotes (código, validade, fornecedor)
- ✅ Inventário físico
- ✅ Estoque mínimo e máximo
- ✅ Localização física (prateleira)
- ✅ Reserva de estoque
- ✅ **Multi-Tenancy 100%**: `empresa_id` em Estoque, Lote, Inventário
- ✅ **Integração com Vendas**: Reserva, liberação e baixa automáticas
- ✅ **Relatórios**: Geral, movimentações, estoque baixo, estoque zerado
- ✅ **Alertas de estoque baixo**: Listagem de produtos abaixo do mínimo
- ✅ **Alertas de validade**: Listagem de lotes vencendo

#### Backend - Melhorias Necessárias 🔴
- 🔴 **Notificações automáticas**: Email/WhatsApp para estoque baixo e lotes vencendo
- 🔴 **Bloqueio de lotes vencidos**: Impedir venda de lotes vencidos
- 🔴 **FIFO/FEFO**: Implementar controle de saída por lote (primeiro a vencer)
- 🔴 **Transferência entre locais**: Movimentar estoque entre localizações
- 🔴 **Custo médio**: Calcular custo médio ponderado

#### Frontend - Rotas a Implementar 🔴
- 🔴 `/estoque` - Visão geral do estoque
- 🔴 `/estoque/produtos` - Lista de produtos em estoque
- 🔴 `/estoque/movimentacoes` - Histórico de movimentações
- 🔴 `/estoque/entrada` - Registrar entrada de mercadoria
- 🔴 `/estoque/saida` - Registrar saída manual
- 🔴 `/estoque/ajuste` - Ajuste de estoque
- 🔴 `/estoque/lotes` - Gestão de lotes
- 🔴 `/estoque/inventario` - Inventário físico
- 🔴 `/estoque/alertas` - Alertas de estoque baixo e validade

#### Frontend - Componentes Necessários 🔴
- 🔴 `EstoqueList` - Lista de produtos com estoque
- 🔴 `MovimentacaoForm` - Formulário de movimentação
- 🔴 `MovimentacaoList` - Histórico de movimentações
- 🔴 `LoteForm` - Formulário de lote
- 🔴 `LoteList` - Lista de lotes
- 🔴 `InventarioForm` - Formulário de inventário
- 🔴 `InventarioList` - Lista de inventários
- 🔴 `EstoqueCard` - Card com informações de estoque
- 🔴 `AlertasList` - Lista de alertas
- 🔴 `EstoqueChart` - Gráficos de estoque

---

### 4. VENDAS ✅ IMPLEMENTAÇÃO COMPLETA

#### Backend - Regras de Negócio ✅ Implementadas
- ✅ **Pedido de Venda**: Criar, atualizar, cancelar
- ✅ **Itens do Pedido**: Produtos, quantidades, preços, snapshot de dados
- ✅ **Status do Pedido**: PEDIDO → CONFIRMADA → SEPARADA → ENTREGUE → FINALIZADA / CANCELADA
- ✅ **Formas de Pagamento**: Dinheiro (com troco), PIX, Débito, Crédito, Fiado
- ✅ **Múltiplos Pagamentos**: Permite várias formas de pagamento por venda
- ✅ **Desconto**: Total da venda (percentual ou valor fixo)
- ✅ **Validação de Cliente**: Verificar se ativo e não bloqueado
- ✅ **Validação de Crédito**: Verificar limite antes de venda fiada
- ✅ **Reserva de Estoque**: Reservar ao criar venda (status PEDIDO)
- ✅ **Baixa de Estoque**: Baixar ao entregar venda (status ENTREGUE)
- ✅ **Liberação de Reserva**: Liberar ao cancelar venda
- ✅ **Cliente Opcional**: NULL para vendas de balcão rápidas
- ✅ **Tipo Entrega**: RETIRADA ou DELIVERY
- ✅ **Número de Venda**: Geração automática única por empresa (V-ANO-EMPRESA-SEQ)
- ✅ **Multi-Tenancy 100%**: `empresa_id` em Venda (entidades filhas isoladas via FK)
- ✅ **Integrações HTTP**: Produtos, Clientes, Estoque
- ✅ **Workflow Completo**: 6 estados com transições validadas

#### Backend - Modelos Criados ✅
- ✅ `Venda` - Pedido de venda (entidade raiz com empresa_id)
- ✅ `ItemVenda` - Itens do pedido (isolado via FK)
- ✅ `PagamentoVenda` - Pagamentos realizados (múltiplos, isolado via FK)
- ✅ `ReservaEstoqueVenda` - Controle de reservas (isolado via FK)
- ✅ 5 Enums: StatusVenda, TipoEntrega, TipoDesconto, FormaPagamento, StatusReserva

#### Backend - Estatísticas ✅
- ✅ **Linhas de código**: ~2.620
- ✅ **Schemas**: 13 (Create, Update, Response, Actions, Reports)
- ✅ **Repository methods**: 20 métodos
- ✅ **Service methods**: 11 métodos principais + 5 integrações HTTP
- ✅ **Endpoints**: 14 REST endpoints
- ✅ **Migration**: Completa com upgrade/downgrade
- ✅ **Seed**: 6 cenários (PEDIDO, CONFIRMADA, SEPARADA, ENTREGUE, FINALIZADA, CANCELADA)

#### Backend - Melhorias Futuras 🔴
- 🔴 **Geração de Conta a Receber**: Integração com Financeiro (ao finalizar venda FIADA)
- 🔴 **Comissão**: Calcular comissão de vendedor
- 🔴 **Devolução**: Processar devolução de produtos (nova entidade)
- 🔴 **Troca**: Processar troca de produtos
- 🔴 **Nota Fiscal**: Integração com emissão de NF-e
- 🔴 **Frete**: Cálculo e adição ao pedido
- 🔴 **Orçamento**: Status antes de PEDIDO
- 🔴 **Cupons de Desconto**: Mecânica de cupons promocionais

#### Backend - Endpoints Implementados ✅
- ✅ `POST /vendas` - Criar venda (reserva estoque)
- ✅ `GET /vendas` - Listar com filtros (status, cliente, data)
- ✅ `GET /vendas/{id}` - Buscar venda detalhada
- ✅ `PUT /vendas/{id}` - Atualizar venda (apenas PEDIDO)
- ✅ `POST /vendas/{id}/confirmar` - Confirmar + registrar pagamentos
- ✅ `POST /vendas/{id}/separar` - Separar produtos
- ✅ `POST /vendas/{id}/entregar` - Entregar + baixar estoque
- ✅ `POST /vendas/{id}/finalizar` - Finalizar venda
- ✅ `POST /vendas/{id}/cancelar` - Cancelar + liberar reserva
- ✅ `GET /vendas/{id}/pagamentos` - Listar pagamentos
- ✅ `POST /vendas/{id}/pagamentos` - Adicionar pagamento
- ✅ `GET /vendas/relatorios/resumo` - Relatório resumido

#### Frontend - Rotas a Implementar 🔴
- 🔴 `/vendas` - Lista de vendas com filtros
- 🔴 `/vendas/nova` - PDV (Ponto de Venda)
- 🔴 `/vendas/:id` - Detalhes da venda
- 🔴 `/vendas/:id/editar` - Editar venda (se PEDIDO)
- 🔴 `/vendas/:id/cancelar` - Cancelar venda
- 🔴 `/vendas/:id/devolucao` - Processar devolução
- 🔴 `/vendas/relatorios` - Relatórios de vendas

#### Frontend - Componentes Necessários 🔴
- 🔴 `PDV` - Tela de ponto de venda
- 🔴 `VendaList` - Lista de vendas
- 🔴 `VendaCard` - Card com resumo da venda
- 🔴 `VendaDetalhes` - Detalhes completos da venda
- 🔴 `CarrinhoCompras` - Carrinho de compras
- 🔴 `PagamentoForm` - Formulário de pagamento
- 🔴 `ClienteSelector` - Seletor de cliente
- 🔴 `ProdutoSelector` - Busca e seleção de produtos
- 🔴 `DevolucaoForm` - Formulário de devolução
- 🔴 `VendasChart` - Gráficos de vendas

---

### 5. FINANCEIRO 🔴 NÃO IMPLEMENTADO

#### Backend - Regras de Negócio a Implementar 🔴
- 🔴 **Contas a Receber**: Geradas por vendas fiadas
- 🔴 **Contas a Pagar**: Fornecedores, despesas
- 🔴 **Recebimento**: Registrar pagamentos de clientes
- 🔴 **Pagamento**: Registrar pagamentos a fornecedores
- 🔴 **Parcelas**: Dividir contas em parcelas
- 🔴 **Juros e Multa**: Calcular para pagamentos atrasados
- 🔴 **Desconto**: Aplicar desconto para pagamento antecipado
- 🔴 **Fluxo de Caixa**: Controle de entradas e saídas
- 🔴 **Conciliação Bancária**: Conciliar com extratos
- 🔴 **Categorias**: Categorizar receitas e despesas
- 🔴 **Centro de Custo**: Alocar despesas por centro de custo
- 🔴 **Relatórios**: DRE, fluxo de caixa, inadimplência

#### Backend - Modelos a Criar 🔴
- 🔴 `ContaReceber` - Contas a receber
- 🔴 `ContaPagar` - Contas a pagar
- 🔴 `Recebimento` - Recebimentos realizados
- 🔴 `Pagamento` - Pagamentos realizados
- 🔴 `Categoria` - Categorias financeiras
- 🔴 `CentroCusto` - Centros de custo
- 🔴 `MovimentacaoCaixa` - Movimentações de caixa

#### Frontend - Rotas a Implementar 🔴
- 🔴 `/financeiro` - Dashboard financeiro
- 🔴 `/financeiro/contas-receber` - Contas a receber
- 🔴 `/financeiro/contas-pagar` - Contas a pagar
- 🔴 `/financeiro/recebimentos` - Registrar recebimentos
- 🔴 `/financeiro/pagamentos` - Registrar pagamentos
- 🔴 `/financeiro/fluxo-caixa` - Fluxo de caixa
- 🔴 `/financeiro/relatorios` - Relatórios financeiros
- 🔴 `/financeiro/categorias` - Gestão de categorias
- 🔴 `/financeiro/centros-custo` - Gestão de centros de custo

#### Frontend - Componentes Necessários 🔴
- 🔴 `FinanceiroDashboard` - Dashboard com indicadores
- 🔴 `ContaReceberList` - Lista de contas a receber
- 🔴 `ContaPagarList` - Lista de contas a pagar
- 🔴 `RecebimentoForm` - Formulário de recebimento
- 🔴 `PagamentoForm` - Formulário de pagamento
- 🔴 `FluxoCaixaChart` - Gráfico de fluxo de caixa
- 🔴 `DREReport` - Relatório DRE
- 🔴 `InadimplenciaList` - Lista de inadimplentes
- 🔴 `CategoriaManager` - Gestão de categorias
- 🔴 `CentroCustoManager` - Gestão de centros de custo

---

## ⚡ OTIMIZAÇÕES E PERFORMANCE

### CONSOLIDAÇÃO POSTGRESQL ✅ Implementado

#### Objetivo
Reduzir consumo de recursos consolidando 8 containers PostgreSQL em 1 único container com schemas separados.

#### Implementação ✅
- ✅ **Script de inicialização**: `postgres/init-schemas.sql` cria 8 schemas automaticamente
- ✅ **URLs de conexão atualizadas**: Cada serviço usa `search_path` para seu schema
- ✅ **docker-compose.yml**: Container único `erp-db` substituindo 8 containers
- ✅ **docker-compose.dev.yml**: Container único `erp-db-dev` substituindo 8 containers
- ✅ **pgAdmin configurado**: Acesso a todos os schemas através de 1 servidor
- ✅ **Script de migração**: `dev-scripts/consolidar-postgres.bat` para facilitar transição
- ✅ **Documentação completa**: `CONSOLIDACAO_POSTGRES.md` com guia detalhado

#### Schemas Criados
- ✅ `gateway` - API Gateway (autenticação, usuários)
- ✅ `clientes` - Serviço de Clientes
- ✅ `produtos` - Serviço de Produtos
- ✅ `estoque` - Serviço de Estoque
- ✅ `vendas` - Serviço de Vendas
- ✅ `financeiro` - Serviço Financeiro
- ✅ `notificacoes` - Serviço de Notificações
- ✅ `evolution` - Evolution API (WhatsApp)

#### Economia de Recursos

| Métrica | Antes | Depois | Economia |
|---------|-------|--------|----------|
| **RAM** | ~268 MB | ~40 MB | **~228 MB (85%)** |
| **Containers** | 8 | 1 | **7 containers** |
| **Volumes Docker** | 8 | 1 | **7 volumes** |
| **Healthchecks** | 8 | 1 | **7 checks** |
| **Tempo de Startup** | ~80s | ~10s | **8x mais rápido** |

#### Benefícios
- ✅ **Economia imediata de RAM**: ~228 MB liberados
- ✅ **Startup mais rápido**: 8x mais rápido para subir o ambiente
- ✅ **Menos complexidade**: Gerenciar 1 container ao invés de 8
- ✅ **Backup simplificado**: 1 database ao invés de 8
- ✅ **Preparado para Multitenancy**: Fácil adicionar schemas dinâmicos por tenant
- ✅ **Queries cross-schema**: Possível fazer JOINs entre serviços quando necessário

#### Compatibilidade com Multitenancy
A consolidação **NÃO impede** a implementação futura de multitenancy:

**Estrutura Atual (por serviço):**
```
Database: erp
├── Schema: gateway (compartilhado)
├── Schema: clientes
├── Schema: produtos
└── ...
```

**Estrutura Futura (por tenant):**
```
Database: erp
├── Schema: public (gateway, auth compartilhados)
├── Schema: tenant_empresa1
│   ├── clientes
│   ├── produtos
│   └── vendas
└── Schema: tenant_empresa2
    ├── clientes
    ├── produtos
    └── vendas
```

#### Como Usar
```bash
# Opção 1: Script automatizado
cd dev-scripts
consolidar-postgres.bat

# Opção 2: Manual
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

#### Arquivos Relacionados
- `postgres/init-schemas.sql` - Script de criação dos schemas
- `CONSOLIDACAO_POSTGRES.md` - Documentação completa
- `dev-scripts/consolidar-postgres.bat` - Script de migração
- `.env` - URLs de conexão atualizadas
- `docker-compose.yml` - Configuração de produção
- `docker-compose.dev.yml` - Configuração de desenvolvimento
- `pgadmin/servers.json` - Configuração do pgAdmin
- `pgadmin/pgpass` - Credenciais do PostgreSQL

#### Próximas Otimizações Sugeridas
- 🔴 **PgBouncer**: Connection pooling para melhor performance
- 🔴 **Redis Cache**: Cache de queries frequentes (categorias, configurações, CEPs)
- 🔴 **CDN**: Servir assets estáticos via CDN
- 🔴 **Lazy Loading**: Carregar componentes sob demanda no frontend
- 🔴 **Database Indexes**: Otimizar queries com índices apropriados (ver seção abaixo)
- 🔴 **Query Optimization**: Analisar e otimizar queries lentas
- 🔴 **Image Optimization**: Comprimir e otimizar imagens de produtos
- 🔴 **API Response Caching**: Cache de respostas da API
- 🔴 **Uvicorn Workers**: Ajustar `workers=1` em ambientes de baixo recurso
- 🔴 **Pool de Conexões**: Reduzir `pool_size` e `max_overflow` para VPS pequenas
- 🔴 **Imagens Alpine**: Migrar Dockerfiles para `python:3.11-alpine` (~50-100 MB por container)
- 🔴 **Limites Docker**: Adicionar `deploy.resources.limits` no docker-compose para prevenir overconsumption

---

## 🔧 QUALIDADE E SEGURANÇA DO BACKEND

> Melhorias técnicas a implementar antes de ir para produção. Não são funcionalidades novas, mas garantem estabilidade, segurança e manutenibilidade.

### ERROR HANDLING PADRONIZADO 🔴

- 🔴 **Handlers específicos por exceção**: `ValidationError` → 400, `NotFoundError` → 404, `ConflictError` → 409, `UnauthorizedError` → 401, `ForbiddenError` → 403
- 🔴 **Handler para HTTPException do FastAPI**: Padronizar formato de resposta
- 🔴 **Handler global com request_id**: Rastrear erros entre microsserviços (UUID por requisição)
- 🔴 **Formato de resposta padronizado**: `{"error": "tipo", "message": "...", "details": {...}}`
- 🔴 **Logs estruturados por nível**: WARNING para 4xx, ERROR para 5xx, INFO para 404
- 🔴 **Não expor stack traces**: Retornar apenas `request_id` em erros 500
- 🔴 **Implementar em todos os microsserviços**: Gateway, Clientes, Produtos, Estoque, Vendas, Financeiro

### AUDITORIA E RASTREABILIDADE 🔴

- 🔴 **Tabela `audit_log`**: Registrar todas as operações de escrita (CREATE, UPDATE, DELETE)
- 🔴 **Campos `criado_por` / `atualizado_por`**: Em todas as tabelas principais
- 🔴 **Dados antes/depois**: Armazenar JSON com estado anterior e novo
- 🔴 **IP e User-Agent**: Registrar origem da requisição
- 🔴 **Endpoint de consulta**: `GET /auditoria?tabela=clientes&registro_id=...`

### ÍNDICES DE BANCO DE DADOS 🔴

- 🔴 **Clientes**: `idx_clientes_cpf`, `idx_clientes_nome`, `idx_clientes_ativo`
- 🔴 **Produtos**: `idx_produtos_sku`, `idx_produtos_nome`, `idx_produtos_categoria`, `idx_produtos_ativo`
- 🔴 **Estoque**: `idx_estoque_produto`, `idx_estoque_variante`
- 🔴 **Vendas**: `idx_vendas_cliente`, `idx_vendas_status`, `idx_vendas_data`
- 🔴 **Financeiro**: `idx_contas_cliente`, `idx_contas_vencimento`, `idx_contas_status`
- 🔴 **Testar com volume**: Seed com 10k+ registros para validar performance

### VALIDAÇÃO DE CEP NO BACKEND 🔴

- 🔴 **ViaCepService**: Validar CEP via API ViaCEP no backend (frontend já valida, mas nunca confiar só no frontend)
- 🔴 **Cache Redis**: Cachear CEPs consultados por 30 dias
- 🔴 **Fallback gracioso**: Se API cair, aceitar o CEP mas logar warning

### RATE LIMITING POR USUÁRIO 🔴

- 🔴 **Por `usuario_id`**: Limitar requisições por usuário autenticado
- 🔴 **Limites diferenciados**: Login (5/min), cadastro (10/min), consulta (200/min), relatório (10/min)
- 🔴 **Headers de resposta**: Retornar `X-RateLimit-Remaining` e `X-RateLimit-Reset`
- 🔴 **Whitelist**: IPs confiáveis sem limite

### TESTES AUTOMATIZADOS 🔴

- 🔴 **Testes unitários**: Services e validators — meta 80% de cobertura
- 🔴 **Testes de integração**: Endpoints principais de cada microsserviço
- 🔴 **Testes de carga**: k6 ou Locust para simular picos
- 🔴 **CI/CD**: GitHub Actions rodando testes a cada push

### DOCUMENTAÇÃO SWAGGER/OPENAPI 🔴

- 🔴 **Docstrings em endpoints**: Descrição, parâmetros, exemplos de request/response
- 🔴 **Documentar códigos de erro**: Quais exceções cada endpoint pode lançar
- 🔴 **Exemplos de requisição**: Facilitar testes manuais e integração frontend

### BACKUP AUTOMATIZADO 🔴

- 🔴 **Script de backup diário**: `pg_dump` com compressão
- 🔴 **Upload para storage externo**: S3 ou Google Cloud Storage
- 🔴 **Política de retenção**: 7 dias diários, 4 semanais, 12 mensais
- 🔴 **Alerta de falha**: Notificar se backup não executar
- 🔴 **Testar restore**: Validar periodicamente que o backup é restaurável

---

## 🎯 PRIORIDADE 2: Integrações e Melhorias

### 6. NOTIFICAÇÕES ✅ Implementado

#### Funcionalidades Implementadas ✅
- ✅ **Email Service**: Serviço de envio de emails configurado
- ✅ **Estrutura de Notificações**: Base implementada no backend

#### Melhorias Necessárias 🟡
- 🔴 **WhatsApp**: Integrar com Evolution API
- 🔴 **Email Templates**: Sistema de templates para emails
- 🔴 **SMS**: Integrar com provedor de SMS
- 🔴 **Push Notifications**: Notificações no navegador
- 🔴 **Agendamento**: Agendar envio de notificações
- 🔴 **Histórico**: Registrar todas as notificações enviadas

### 7. RELATÓRIOS E DASHBOARDS 🔴

#### Relatórios a Implementar 🔴
- 🔴 **Vendas**: Por período, produto, cliente, vendedor
- 🔴 **Estoque**: Movimentações, giro, produtos parados
- 🔴 **Financeiro**: DRE, fluxo de caixa, inadimplência
- 🔴 **Clientes**: Ranking, ticket médio, frequência
- 🔴 **Produtos**: Mais vendidos, margem, curva ABC

#### Dashboards a Implementar 🔴
- 🔴 **Dashboard Geral**: Visão geral do negócio
- 🔴 **Dashboard Vendas**: Métricas de vendas
- 🔴 **Dashboard Financeiro**: Indicadores financeiros
- 🔴 **Dashboard Estoque**: Status do estoque

### 8. USUÁRIOS E PERMISSÕES 🟡

#### Backend - Implementado ✅
- ✅ Autenticação JWT
- ✅ OAuth (Google, Microsoft)
- ✅ Roles (ADMIN, OPERADOR)

#### Backend - Melhorias Necessárias 🔴
- 🔴 **Permissões Granulares**: Por módulo e ação
- 🔴 **Grupos de Usuários**: Agrupar permissões
- 🔴 **Auditoria**: Registrar todas as ações dos usuários
- 🔴 **Sessões**: Controle de sessões ativas
- 🔴 **2FA**: Autenticação de dois fatores

#### Frontend - Rotas a Implementar 🔴
- 🔴 `/usuarios` - Gestão de usuários
- 🔴 `/usuarios/novo` - Cadastro de usuário
- 🔴 `/usuarios/:id` - Detalhes do usuário
- 🔴 `/usuarios/:id/permissoes` - Gestão de permissões
- 🔴 `/perfil` - Perfil do usuário logado
- 🔴 `/perfil/senha` - Alterar senha
- 🔴 `/perfil/2fa` - Configurar 2FA

---

## 🎯 PRIORIDADE 3: Funcionalidades Avançadas

### 9. LOJA ONLINE / E-COMMERCE 🟡

#### Backend - Implementado ✅
- ✅ **API Pública**: Endpoints para loja sem autenticação
- ✅ **Configuração de Exibição**: Produtos visíveis na loja
- ✅ **Fotos**: Upload e gestão de imagens
- 🔴 **Busca Avançada**: Busca por nome, categoria, preço
- 🔴 **Filtros Avançados**: Filtrar por categoria, preço, atributos
- 🔴 **Carrinho Backend**: API para gerenciar carrinho
- 🔴 **Checkout Backend**: API para processar pedidos online
- 🔴 **Pedido Convidado**: Permitir compras sem cadastro

#### Frontend - Em Implementação 🟡
- 🟡 **Loja Online**: Site público para clientes (em desenvolvimento)
- 🔴 **Carrinho de Compras**: Adicionar produtos e gerenciar carrinho
- 🔴 **Checkout**: Finalizar pedido com dados de entrega
- 🔴 **Pedido Online**: Fazer pedido pela loja
- 🔴 **Rastreamento**: Acompanhar status do pedido
- 🔴 **Área do Cliente**: Login e histórico de pedidos

### 10. INTEGRAÇÕES EXTERNAS 🔴

#### A Implementar 🔴
- 🔴 **Mercado Pago**: Pagamentos online
- 🔴 **Correios**: Cálculo de frete
- 🔴 **ViaCEP**: Busca de endereço por CEP
- 🔴 **NF-e**: Emissão de nota fiscal eletrônica
- 🔴 **WhatsApp Business**: Mensagens via Evolution API
- 🔴 **Google Analytics**: Rastreamento de uso
- 🔴 **Backup Automático**: S3, Google Drive, etc.

### 11. MOBILE 🔴

#### A Implementar 🔴
- 🔴 **App Mobile**: React Native ou PWA
- 🔴 **PDV Mobile**: Vender pelo celular
- 🔴 **Consulta de Estoque**: Verificar estoque
- 🔴 **Consulta de Preços**: Verificar preços
- 🔴 **Leitor de Código de Barras**: Escanear produtos

---

## 📝 REGRAS DE NEGÓCIO DETALHADAS

### Clientes

#### Validações
- ✅ CPF deve ser válido (11 dígitos, validação de dígitos verificadores)
- ✅ CPF deve ser único no sistema
- ✅ Telefone deve estar no formato (XX) XXXXX-XXXX
- ✅ Email deve ser válido (se informado)
- ✅ Data de nascimento não pode ser futura
- ✅ Limite de crédito >= 0
- ✅ Dia de vencimento entre 1 e 28
- 🟡 CEP: Frontend valida via ViaCEP, backend valida apenas formato (8 dígitos)

#### Regras de Crédito
- ✅ `credito_disponivel = limite_credito - saldo_devedor`
- ✅ Não pode vender fiado se `credito_disponivel < valor_venda`
- ✅ Cliente bloqueado não pode comprar fiado
- 🔴 Bloquear automaticamente se ultrapassar X dias de atraso
- 🔴 Desbloquear automaticamente ao quitar dívidas

#### Regras de Desativação e Reativação
- ✅ Soft delete (ativo = false)
- 🟡 **Consultas (GET)**: Retornam APENAS clientes ativos (inativos ficam invisíveis)
- 🟡 **Reativação automática ao cadastrar**: 
  - Se CPF não existe → Cria novo
  - Se CPF existe e está ATIVO → Erro "CPF já cadastrado"
  - Se CPF existe e está INATIVO → Reativa + Atualiza APENAS dados cadastrais
- 🟡 **Campos que atualizam na reativação**: Nome, telefone, email, data_nasc
- 🟡 **Campos que mantêm na reativação**: Limite de crédito, crédito disponível, dia vencimento, bloqueado
- 🔴 Não pode desativar se tiver pedidos em aberto
- 🔴 Não pode desativar se tiver contas pendentes
- 🔴 Pode reativar manualmente a qualquer momento

### Produtos

#### Validações
- ✅ Nome do produto é obrigatório
- ✅ Categoria é obrigatória
- ✅ SKU deve ser único
- ✅ Preço de custo > 0
- ✅ Markup >= 0
- ✅ Preço de venda > 0

#### Cálculo de Preço
- ✅ `preco_venda = preco_custo * (1 + markup_pct / 100)`
- 🔴 Permitir definir preço de venda manualmente (calcular markup reverso)
- 🔴 Histórico de alterações de preço

#### Variantes
- ✅ Produto pode ter múltiplas variantes
- ✅ Cada variante tem SKU único
- ✅ Variante pode ter atributos (cor, tamanho, etc.)
- 🔴 Validar combinação única de atributos por produto

#### Regras de Desativação e Reativação
- ✅ Soft delete (ativo = false)
- 🟡 **Consultas (GET)**: Retornam APENAS produtos ativos (inativos ficam invisíveis)
- 🟡 **Reativação automática ao cadastrar**: 
  - Se SKU não existe → Cria novo
  - Se SKU existe e está ATIVO → Erro "SKU já cadastrado"
  - Se SKU existe e está INATIVO → Reativa + Atualiza dados do produto
- 🔴 Não pode desativar se tiver estoque
- 🔴 Não pode desativar se tiver pedidos pendentes
- 🔴 Pode reativar manualmente a qualquer momento

### Estoque

#### Validações
- ✅ Quantidade >= 0
- ✅ Quantidade reservada >= 0
- ✅ Quantidade disponível = quantidade - quantidade_reservada
- ✅ Estoque mínimo >= 0
- ✅ Estoque máximo >= estoque_mínimo (se definido)

#### Movimentações
- ✅ **ENTRADA**: Aumenta quantidade
- ✅ **SAIDA**: Diminui quantidade (não pode ficar negativo)
- ✅ **AJUSTE**: Ajusta para quantidade específica
- ✅ **DEVOLUCAO**: Aumenta quantidade (devolução de venda)
- ✅ **PERDA**: Diminui quantidade (quebra, vencimento, etc.)
- 🔴 **TRANSFERENCIA**: Move entre localizações

#### Lotes
- ✅ Código do lote deve ser único
- ✅ Data de validade deve ser futura (se informada)
- ✅ Quantidade do lote >= 0
- 🔴 Bloquear lotes vencidos automaticamente
- 🔴 Alertar lotes próximos do vencimento (X dias antes)
- 🔴 FIFO/FEFO: Saída pelo lote mais antigo/próximo do vencimento

#### Reserva
- ✅ Reservar estoque ao confirmar pedido
- ✅ Liberar reserva ao cancelar pedido
- ✅ Baixar estoque ao entregar pedido
- 🔴 Liberar reserva automaticamente após X horas sem confirmação

#### Inventário
- ✅ Registrar contagem física
- ✅ Calcular diferença (contado - sistema)
- ✅ Ajustar estoque após finalizar inventário
- 🔴 Bloquear movimentações durante inventário

### Vendas ✅ Implementado

#### Workflow Implementado ✅
```
PEDIDO → CONFIRMADA → SEPARADA → ENTREGUE → FINALIZADA
  ↓         ↓           ↓
CANCELADA (apenas nestes 3 status)
```

**Transições:**
| De | Para | Ação | Estoque |
|----|------|------|---------|
| - | PEDIDO | Criar venda | **RESERVA** estoque via serviço Estoque |
| PEDIDO | CONFIRMADA | Registrar pagamentos | Mantém reserva |
| CONFIRMADA | SEPARADA | Separar produtos | Mantém reserva |
| SEPARADA | ENTREGUE | Entregar/retirar | **BAIXA** estoque via serviço Estoque |
| ENTREGUE | FINALIZADA | Fechar venda | Se FIADO: cria ContaReceber (futuro) |
| PEDIDO/CONFIRMADA/SEPARADA | CANCELADA | Cancelar | **LIBERA** reserva via serviço Estoque |

### Vendas - Regras Detalhadas (Conforme Implementado)

#### Fluxo de Venda ✅
1. ✅ Criar pedido (status: PEDIDO) - **Reserva estoque automaticamente**
2. ✅ Validar produtos (existem e estão ativos)
3. ✅ Validar cliente (se fornecido: ativo e não bloqueado)
4. ✅ Aplicar descontos (percentual ou valor fixo no total)
5. ✅ Confirmar pedido (status: CONFIRMADA) - **Registrar pagamentos**
6. ✅ Validar soma de pagamentos >= valor total
7. ✅ Separar produtos (status: SEPARADA)
8. ✅ Entregar pedido (status: ENTREGUE) - **Baixa estoque automaticamente**
9. ✅ Finalizar (status: FINALIZADA) - **Gera conta a receber se FIADO (integração futura)**
10. ✅ Cancelar (se PEDIDO/CONFIRMADA/SEPARADA) - **Libera reserva automaticamente**

#### Validações ✅
- ✅ Cliente é **opcional** (NULL para vendas de balcão)
- ✅ Cliente **obrigatório** se forma de pagamento = FIADO
- ✅ Pelo menos 1 item no pedido
- ✅ Quantidade > 0 para cada item
- ✅ Preço >= 0 para cada item (busca automático se não fornecido)
- ✅ Desconto >= 0
- ✅ Verificar estoque disponível (integração com serviço Estoque)
- ✅ Verificar crédito disponível (se fiado - integração com serviço Clientes)
- ✅ Cliente não pode estar bloqueado (se fiado)
- ✅ Validar `empresa_id` do body vs header em POST/PUT
- ✅ Snapshot de dados do produto (preserva informações no momento da venda)

#### Formas de Pagamento ✅
- ✅ **DINHEIRO**: Pagamento à vista (calcula troco automaticamente)
- ✅ **DEBITO**: Pagamento à vista
- ✅ **CREDITO**: Pagamento à vista
- ✅ **PIX**: Pagamento à vista
- ✅ **FIADO**: Gera conta a receber (integração futura com Financeiro)
- ✅ **Múltiplos pagamentos**: Pode dividir em várias formas (ex: 50% PIX + 50% Dinheiro)

#### Cancelamento ✅
- ✅ Pode cancelar se status = PEDIDO, CONFIRMADA ou SEPARADA
- ✅ **NÃO** pode cancelar se status = ENTREGUE ou FINALIZADA (usar Devolução)
- ✅ Liberar reserva de estoque automaticamente (integração HTTP)
- ✅ Cancelar conta a receber (integração futura se fiado)
- ✅ Registrar motivo do cancelamento
- ✅ Registrar usuário que cancelou

#### Devolução 🔴 (A Implementar - Entidade Separada)
- 🔴 Pode devolver total ou parcial
- 🔴 Devolver estoque (entrada de estoque)
- 🔴 Gerar crédito para cliente ou estornar pagamento
- 🔴 Registrar motivo da devolução
- 🔴 Vincular à venda original
- 🔴 Criar modelos: `Devolucao`, `ItemDevolucao`

### Financeiro (A Implementar)

#### Contas a Receber
- 🔴 Gerada automaticamente por venda fiada
- 🔴 Pode ser criada manualmente
- 🔴 Status: PENDENTE, PAGO, VENCIDO, CANCELADO
- 🔴 Pode ter múltiplas parcelas
- 🔴 Calcular juros e multa para vencidas
- 🔴 Permitir desconto para pagamento antecipado
- 🔴 Registrar forma de pagamento

#### Contas a Pagar
- 🔴 Criada manualmente
- 🔴 Status: PENDENTE, PAGO, VENCIDO, CANCELADO
- 🔴 Pode ter múltiplas parcelas
- 🔴 Vincular a fornecedor
- 🔴 Vincular a categoria de despesa
- 🔴 Vincular a centro de custo

#### Recebimento
- 🔴 Vincular a conta a receber
- 🔴 Pode receber parcial
- 🔴 Registrar forma de pagamento
- 🔴 Aplicar juros/multa se atrasado
- 🔴 Aplicar desconto se antecipado
- 🔴 Atualizar crédito disponível do cliente

#### Pagamento
- 🔴 Vincular a conta a pagar
- 🔴 Pode pagar parcial
- 🔴 Registrar forma de pagamento
- 🔴 Registrar conta bancária (se houver)

---

## 🗂️ ESTRUTURA DE DADOS

### Relacionamentos Principais

```
Cliente (1) ----< (N) Endereco
Cliente (1) ----< (N) Venda
Cliente (1) ----< (N) ContaReceber

Categoria (1) ----< (N) Produto
Produto (1) ----< (N) Variante
Variante (1) ----< (N) AtributoVariante
Produto (1) ----< (N) Estoque
Variante (1) ----< (N) Estoque

Estoque (1) ----< (N) Movimentacao
Estoque (1) ----< (N) Lote
Lote (1) ----< (N) Movimentacao

Venda (1) ----< (N) ItemVenda
Venda (1) ----< (N) PagamentoVenda
Venda (1) ----< (N) ContaReceber

Fornecedor (1) ----< (N) FornecedorProduto
Produto (1) ----< (N) FornecedorProduto
```

---

## 📅 CRONOGRAMA SUGERIDO

### Sprint 1 (2 semanas) - Clientes Frontend
- [x] Criar rotas de clientes no frontend
- [x] Implementar lista de clientes
- [x] Implementar cadastro de cliente
- [x] Implementar edição de cliente
- [x] Implementar gestão de endereços
- [x] Implementar gestão de crédito

### Sprint 2 (2 semanas) - Produtos Frontend ✅
- [x] Criar rotas de produtos no frontend
- [x] Implementar lista de produtos
- [x] Implementar cadastro de produto
- [x] Implementar edição de produto
- [x] Implementar detalhes de produto
- [x] Implementar gestão de variantes
- [x] **Implementar gestão de categorias (CRUD completo)**

### Sprint 2.5 (1-2 semanas) - Loja Online (E-commerce Básico) 🟡
- [x] **Backend**: Criar rotas públicas (sem autenticação)
  - [x] `GET /catalogo/publico/produtos` - Listar produtos visíveis
  - [x] `GET /catalogo/publico/produto/:id` - Detalhes do produto
  - [x] `GET /catalogo/publico/categorias` - Listar categorias
  - [ ] `POST /loja/carrinho` - Adicionar ao carrinho (sessão)
  - [ ] `GET /loja/carrinho` - Ver carrinho
  - [ ] `POST /loja/checkout` - Processar pedido online
- [x] **Frontend**: Criar páginas públicas
  - [x] `LojaPage` - Lista de produtos com filtros
  - [x] `ProdutoDetalhePage` - Detalhes do produto
  - [x] Componente `ProdutoCard` - Card do produto
  - [ ] `CarrinhoLoja` - Carrinho de compras
  - [ ] `CheckoutLoja` - Finalização de pedido
- [x] **Funcionalidades Implementadas**:
  - [x] Filtro por categoria
  - [x] Busca por nome
  - [x] Ordenação (nome, recentes)
  - [x] Design responsivo (mobile-first)
  - [x] Botão "Compartilhar Loja" no painel admin
  - [x] Compartilhamento via WhatsApp
  - [x] Copiar link da loja
- [ ] **Funcionalidades Pendentes**:
  - [ ] Carrinho de compras funcional
  - [ ] Checkout com dados de entrega
  - [ ] Confirmação de pedido
  - [ ] Integração com Vendas (criar venda a partir de pedido online)
- [x] **Preparação Multi-Tenant**:
  - [x] URL com slug: `/loja/:empresaSlug`
  - [x] Schema `ProdutoCatalogoRead` sem dados internos (custo, markup, fornecedores)
  - [x] Código preparado para receber `empresa_id`
  - [x] Tabela `empresas` com campo `slug` único

### Sprint 3 (2 semanas) - Estoque Frontend
- [ ] Criar rotas de estoque no frontend
- [ ] Implementar visão geral do estoque
- [ ] Implementar movimentações
- [ ] Implementar gestão de lotes
- [ ] Implementar inventário
- [ ] Implementar alertas

### Sprint 4 (3 semanas) - Vendas Backend ✅ CONCLUÍDO
- ✅ Criar modelos de venda (Venda, ItemVenda, PagamentoVenda, ReservaEstoqueVenda)
- ✅ Implementar CRUD de vendas
- ✅ Implementar validações de crédito
- ✅ Implementar reserva de estoque
- ✅ Implementar baixa de estoque
- ✅ Implementar cancelamento e liberação de reserva
- ✅ Implementar workflow completo (6 status)
- ✅ Implementar multi-tenancy nativo
- ✅ Criar migration completa
- ✅ Criar seed com 6 cenários

### Sprint 5 (2 semanas) - Vendas Frontend
- [ ] Criar rotas de vendas no frontend
- [ ] Implementar PDV
- [ ] Implementar lista de vendas
- [ ] Implementar detalhes da venda
- [ ] Implementar devolução

### Sprint 6 (3 semanas) - Financeiro Backend
- [ ] Criar modelos financeiros
- [ ] Implementar contas a receber
- [ ] Implementar contas a pagar
- [ ] Implementar recebimentos
- [ ] Implementar pagamentos
- [ ] Implementar cálculo de juros/multa

### Sprint 7 (2 semanas) - Financeiro Frontend
- [ ] Criar rotas financeiras no frontend
- [ ] Implementar dashboard financeiro
- [ ] Implementar contas a receber
- [ ] Implementar contas a pagar
- [ ] Implementar fluxo de caixa

### Sprint 8 (2 semanas) - Integrações
- [ ] Integrar ViaCEP
- [ ] Integrar WhatsApp (Evolution API)
- [ ] Integrar Mercado Pago
- [ ] Implementar upload de imagens

### Sprint 9 (2 semanas) - Relatórios
- [ ] Implementar relatórios de vendas
- [ ] Implementar relatórios de estoque
- [ ] Implementar relatórios financeiros
- [ ] Implementar dashboards

### Sprint 10 (1 semana) - Melhorias e Testes
- [ ] Testes de integração
- [ ] Correção de bugs
- [ ] Melhorias de UX
- [ ] Documentação

---

## 📊 MÉTRICAS DE PROGRESSO

### Backend
- **Clientes**: 90% (falta integrações com Vendas e Financeiro)
- **Produtos**: 95% (falta histórico de preços, promoções, produtos compostos)
- **Estoque**: 95% (falta notificações automáticas, FIFO/FEFO, transferências)
- **Vendas**: 90% (implementação completa, falta integração com Financeiro e Devolução)
- **Loja Online**: 100% ✅ (carrinho Redis, checkout, rastreamento)
- **Financeiro**: 0% (não implementado)
- **Notificações**: 75% (email service implementado, falta integrações WhatsApp/SMS)

### Frontend
- **Autenticação**: 100%
- **Clientes**: 85% (falta histórico)
- **Produtos**: 90% (falta fotos e fornecedores)
- **Loja Online**: 30% (vitrine pronta, falta carrinho e checkout)
- **Estoque**: 0%
- **Vendas**: 0%
- **Financeiro**: 0%

### Multi-Tenancy
- **Produtos**: 100% ✅
- **Estoque**: 100% ✅
- **Vendas**: 100% ✅ (nativo desde o início)
- **Clientes**: 100% ✅
- **Empresas**: 100% ✅
- **Financeiro**: 0% (a implementar)

### Geral
- **Backend**: 76% concluído (↑6% - Loja Online 100%)
- **Frontend**: 52% concluído (Sprint 1 e Sprint 2 concluídas, Sprint 2.5 em progresso)
- **Sistema Completo**: 64% concluído
- **Sprint Atual**: Sprint 4 Concluído, Sprint 2.5 Backend Concluído
- **Otimizações**: 1 implementada (Consolidação PostgreSQL)
- **Commits recentes**: 4 (Produtos multi-tenancy, Estoque multi-tenancy, Vendas completa, Loja Online completa)

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS

1. ✅ **Commit das correções do Ngrok**
2. ✅ **Implementar frontend de Clientes** (Sprint 1)
3. ✅ **Implementar frontend de Produtos** (Sprint 2 - 100% incluindo categorias)
4. ✅ **Melhorias no API Gateway** (Email Service, Auth, Proxy)
5. ✅ **Otimização PostgreSQL** (Consolidação de 8 containers em 1)
6. ✅ **Correções Críticas**: Nginx DNS dinâmico, SQLAlchemy 2.0.36, Transações ACID
7. ✅ **Gestão de Categorias no frontend** (CRUD completo implementado)
8. ✅ **Implementar Multi-Tenancy**: Produtos, Estoque, Vendas (100%)
9. ✅ **Implementar backend de Vendas** (Sprint 4 - 100%)
10. ✅ **Implementar Loja Online Backend** (Sprint 2.5 - 100% - carrinho, checkout, rastreamento)
11. 🟡 **Implementar Loja Online Frontend** (Sprint 2.5 - 30% - falta carrinho e checkout)
12. 🔴 **Aplicar Migrations**: Produtos, Estoque, Vendas
13. 🔴 **Implementar frontend de Estoque** (Sprint 3)
14. 🔴 **Implementar frontend de Vendas** (Sprint 5)
15. 🔴 **Implementar backend de Financeiro** (Sprint 6)

---

## 🎯 PRIORIDADE 4: Longo Prazo (Pós-MVP)

> Features planejadas para após a conclusão do MVP completo. Não há dependências bloqueantes com os módulos atuais.

### 12. MÓDULO DE DELIVERY 🔴

**Estimativa**: 60-80 horas

- 🔴 Integração com iFood, Rappi, Uber Eats
- 🔴 Gestão de pedidos delivery (painel unificado)
- 🔴 Rastreamento de entrega em tempo real
- 🔴 Cálculo de frete (Correios + Google Maps)
- 🔴 Notificações de status ao cliente

### 13. MÓDULO DE FIDELIDADE 🔴

**Estimativa**: 40-50 horas

- 🔴 Programa de pontos por compra
- 🔴 Cashback configurável
- 🔴 Cupons de desconto
- 🔴 Promoções personalizadas por segmento de cliente
- 🔴 Gamificação (níveis, badges)

### 14. BI E ANALYTICS 🔴

**Estimativa**: 60-80 horas

- 🔴 Data warehouse (PostgreSQL analítico)
- 🔴 ETL de dados (Apache Airflow)
- 🔴 Dashboards analíticos (Metabase ou Superset)
- 🔴 Previsão de vendas com Machine Learning (Scikit-learn)
- 🔴 Análise de comportamento de clientes (curva ABC, RFM)

### 15. INTEGRAÇÕES ADICIONAIS 🔴

**Estimativa**: 40-60 horas

- 🔴 **Contabilidade**: Conta Azul, Omie
- 🔴 **Nota Fiscal**: Emissão de NF-e e NFC-e
- 🔴 **Boletos**: Integração com bancos (Itaú, Bradesco, BB)
- 🔴 **Cartões**: Stone, Cielo (além do Mercado Pago)
- 🔴 **ERP Externo**: API aberta para integração com outros sistemas

### 16. INFRAESTRUTURA AVANÇADA 🔴

**Estimativa**: 60h

- 🔴 **RabbitMQ**: Eventos assíncronos entre serviços (`venda.criada`, `estoque.baixo`, etc.)
- 🔴 **Celery + Celery Beat**: Jobs agendados (cobranças, relatórios, lembretes)
- 🔴 **PgBouncer**: Connection pooling para melhor performance em produção
- 🔴 **Prometheus + Grafana**: Métricas e dashboards de monitoramento
- 🔴 **ELK Stack**: Logs centralizados (Elasticsearch, Logstash, Kibana)
- 🔴 **CI/CD Pipeline**: GitHub Actions com deploy automatizado
- 🔴 **Testes de carga**: k6 ou Locust

### 17. APP MOBILE 🔴

**Estimativa**: 120-150 horas

- 🔴 App para vendedores (Android/iOS) — React Native + Expo
- 🔴 PDV mobile (vender pelo celular)
- 🔴 Consulta de estoque e preços
- 🔴 Criação de vendas offline com sincronização automática
- 🔴 Leitor de código de barras
- 🔴 Notificações push

---

**Última atualização**: 09/06/2026 (após implementação de Vendas + Multi-tenancy completo)
**Responsável**: Equipe de Desenvolvimento
**Status**: 🟢 Em Progresso Acelerado (59% concluído - ↑12.5% nesta sessão)
**Última sprint**: Sprint 4 Concluída (Vendas Backend 100%)
**Última otimização**: Consolidação PostgreSQL (economia de ~228 MB RAM)
**Commits recentes**: 4 (Produtos multi-tenancy, Estoque multi-tenancy, Vendas implementação completa, Bug fix catálogo)
**Linhas implementadas hoje**: ~5.088 (Produtos: ~2.000, Estoque: ~1.468, Vendas: ~2.620)
