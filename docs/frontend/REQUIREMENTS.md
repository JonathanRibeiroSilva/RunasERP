# Requirements: Frontend ERP Runas

## 1. Visão Geral

O Frontend do ERP Runas é uma aplicação web moderna que fornece interface completa para gerenciamento de comércio de alimentos e bebidas. O sistema deve ser intuitivo, responsivo e integrado com o backend de microsserviços.

### 1.1. Objetivos

- Fornecer interface administrativa completa para gestão do ERP
- Suportar operações de clientes, produtos, vendas, estoque e financeiro
- Garantir experiência responsiva em desktop, tablet e mobile
- Implementar autenticação segura com JWT
- Oferecer feedback visual claro para todas as operações
- Manter performance otimizada mesmo com grandes volumes de dados

### 1.2. Escopo

**Incluído no MVP:**
- ✅ Sistema de autenticação (login, logout, refresh token)
- ✅ Dashboard com métricas principais
- ✅ Gestão completa de clientes (CRUD + endereços + crédito)
- ✅ Gestão completa de produtos (CRUD + variantes + categorias + fornecedores)
- ✅ Gestão de estoque (movimentações, alertas, inventário)
- ✅ Gestão de vendas (pedidos, status, cancelamento)
- ✅ Gestão financeira (contas a receber, pagamentos)
- ✅ Controle de acesso baseado em roles (ADMIN, OPERADOR)

**Fora do escopo do MVP:**
- ❌ Catálogo público (será desenvolvido separadamente)
- ❌ Carrinho de compras público
- ❌ Relatórios avançados e analytics
- ❌ Notificações em tempo real (WebSocket)
- ❌ Aplicativo mobile nativo

## 2. Requisitos Funcionais

### RF-001: Autenticação e Autorização

**Descrição:** Sistema deve permitir login seguro com JWT e controle de acesso baseado em roles.

**Critérios de Aceitação:**
- [ ] Usuário pode fazer login com email e senha
- [ ] Sistema valida credenciais via API Gateway
- [ ] Token JWT é armazenado de forma segura (httpOnly cookie ou localStorage)
- [ ] Refresh token renova automaticamente antes da expiração
- [ ] Logout invalida tokens no backend (blacklist Redis)
- [ ] Rotas protegidas redirecionam para login se não autenticado
- [ ] Permissões são verificadas antes de exibir funcionalidades
- [ ] ADMIN tem acesso total
- [ ] OPERADOR tem acesso limitado (leitura de produtos, criação de pedidos)

**Prioridade:** CRÍTICA

---

### RF-002: Dashboard

**Descrição:** Página inicial com visão geral das métricas principais do negócio.

**Critérios de Aceitação:**
- [ ] Exibe total de vendas do dia/mês
- [ ] Exibe total de clientes ativos
- [ ] Exibe produtos com estoque baixo (alerta)
- [ ] Exibe contas a receber vencidas
- [ ] Exibe pedidos pendentes de confirmação
- [ ] Gráficos de vendas por período
- [ ] Cards clicáveis levam para detalhes
- [ ] Atualização automática a cada 5 minutos

**Prioridade:** ALTA

---

### RF-003: Gestão de Clientes

**Descrição:** CRUD completo de clientes com gestão de endereços e crédito.

#### RF-003.1: Listar Clientes

**Critérios de Aceitação:**
- [ ] Exibe lista paginada de clientes (20 por página)
- [ ] Filtros: nome, CPF, bloqueado, ativo
- [ ] Busca em tempo real (debounce 300ms)
- [ ] Exibe: nome, CPF, telefone, crédito disponível, status
- [ ] Indicador visual para clientes bloqueados
- [ ] Botão "Novo Cliente"
- [ ] Ações: visualizar, editar, desativar

#### RF-003.2: Criar Cliente

**Critérios de Aceitação:**
- [ ] Formulário com validação em tempo real
- [ ] Campos obrigatórios: nome, CPF, telefone
- [ ] Campos opcionais: email, data de nascimento
- [ ] Validação de CPF (algoritmo brasileiro)
- [ ] Normalização de telefone para E.164
- [ ] Feedback de erro claro para cada campo
- [ ] Botão "Salvar" desabilitado se formulário inválido
- [ ] Mensagem de sucesso após criação
- [ ] Redirecionamento para detalhes do cliente

#### RF-003.3: Editar Cliente

**Critérios de Aceitação:**
- [ ] Formulário pré-preenchido com dados atuais
- [ ] Mesmas validações da criação
- [ ] CPF não pode ser alterado (campo desabilitado)
- [ ] Mensagem de confirmação antes de salvar
- [ ] Feedback de sucesso/erro

#### RF-003.4: Visualizar Cliente

**Critérios de Aceitação:**
- [ ] Exibe todos os dados do cliente
- [ ] Lista de endereços cadastrados
- [ ] Histórico de crédito (últimas movimentações)
- [ ] Pedidos recentes
- [ ] Contas a receber (abertas e quitadas)
- [ ] Botões: editar, adicionar endereço, ajustar crédito, bloquear/desbloquear

#### RF-003.5: Gestão de Endereços

**Critérios de Aceitação:**
- [ ] Adicionar novo endereço
- [ ] Editar endereço existente
- [ ] Remover endereço
- [ ] Marcar endereço como principal
- [ ] Validação de CEP
- [ ] Busca automática de endereço por CEP (API ViaCEP)
- [ ] Campos: CEP, logradouro, número, complemento, bairro, cidade, UF

#### RF-003.6: Gestão de Crédito (ADMIN)

**Critérios de Aceitação:**
- [ ] Definir limite de crédito
- [ ] Definir dia de vencimento (1-28)
- [ ] Visualizar crédito disponível (calculado automaticamente)
- [ ] Histórico de movimentações de crédito
- [ ] Bloquear/desbloquear cliente manualmente
- [ ] Confirmação antes de bloquear

**Prioridade:** CRÍTICA

---

### RF-004: Gestão de Produtos

**Descrição:** CRUD completo de produtos, variantes, categorias e fornecedores.

#### RF-004.1: Listar Produtos

**Critérios de Aceitação:**
- [ ] Lista paginada de produtos (20 por página)
- [ ] Filtros: categoria, ativo, nome
- [ ] Busca em tempo real
- [ ] Exibe: nome, categoria, número de variantes, status
- [ ] Indicador visual para produtos inativos
- [ ] Botão "Novo Produto"
- [ ] Ações: visualizar, editar, desativar

#### RF-004.2: Criar Produto

**Critérios de Aceitação:**
- [ ] Formulário com validação
- [ ] Campos obrigatórios: nome, categoria
- [ ] Campo opcional: descrição
- [ ] Seleção de categoria (dropdown)
- [ ] Botão "Salvar e Adicionar Variantes"
- [ ] Mensagem de sucesso
- [ ] Redirecionamento para adicionar variantes

#### RF-004.3: Gestão de Variantes

**Critérios de Aceitação:**
- [ ] Adicionar variante ao produto
- [ ] Campos: SKU, preço de custo, markup %, preço de venda
- [ ] Atributos dinâmicos (chave-valor): cor, tamanho, etc
- [ ] Cálculo automático de preço de venda
- [ ] Opção de definir preço de venda manualmente
- [ ] Validação de SKU único
- [ ] Listar todas as variantes do produto
- [ ] Editar variante
- [ ] Desativar variante

#### RF-004.4: Gestão de Categorias

**Critérios de Aceitação:**
- [ ] Listar categorias
- [ ] Criar nova categoria
- [ ] Editar categoria
- [ ] Excluir categoria (apenas se não tiver produtos)
- [ ] Validação de nome único

#### RF-004.5: Gestão de Fornecedores

**Critérios de Aceitação:**
- [ ] Listar fornecedores
- [ ] Criar fornecedor
- [ ] Editar fornecedor
- [ ] Desativar fornecedor
- [ ] Vincular fornecedor a produto
- [ ] Definir preço de custo por fornecedor
- [ ] Marcar fornecedor principal

#### RF-004.6: Configuração de Catálogo (ADMIN)

**Critérios de Aceitação:**
- [ ] Marcar produto como visível no catálogo público
- [ ] Marcar produto como destaque
- [ ] Definir ordem de exibição
- [ ] Adicionar descrição pública (diferente da interna)
- [ ] Upload de fotos do produto
- [ ] Ordenar fotos
- [ ] Remover fotos

**Prioridade:** CRÍTICA

---

### RF-005: Gestão de Estoque

**Descrição:** Controle de estoque com movimentações, alertas e inventário.

#### RF-005.1: Visualizar Estoque

**Critérios de Aceitação:**
- [ ] Lista paginada de produtos em estoque
- [ ] Exibe: produto, variante, quantidade, quantidade mínima, localização
- [ ] Filtros: produto, abaixo do mínimo, zerado
- [ ] Indicador visual para estoque baixo (vermelho)
- [ ] Indicador visual para estoque zerado
- [ ] Busca por produto/SKU

#### RF-005.2: Entrada de Estoque

**Critérios de Aceitação:**
- [ ] Formulário de entrada
- [ ] Seleção de produto e variante
- [ ] Quantidade
- [ ] Motivo (compra, devolução, ajuste)
- [ ] Documento (nota fiscal, etc)
- [ ] Custo unitário (opcional)
- [ ] Observações
- [ ] Confirmação antes de salvar
- [ ] Atualização automática do estoque

#### RF-005.3: Saída de Estoque

**Critérios de Aceitação:**
- [ ] Formulário de saída
- [ ] Seleção de produto e variante
- [ ] Quantidade (validar disponibilidade)
- [ ] Motivo (venda, perda, doação)
- [ ] Documento
- [ ] Observações
- [ ] Validação: não permitir saída maior que disponível
- [ ] Confirmação antes de salvar

#### RF-005.4: Ajuste de Estoque

**Critérios de Aceitação:**
- [ ] Formulário de ajuste
- [ ] Seleção de produto e variante
- [ ] Quantidade atual (exibida)
- [ ] Nova quantidade
- [ ] Motivo obrigatório
- [ ] Observações
- [ ] Confirmação com destaque para diferença

#### RF-005.5: Histórico de Movimentações

**Critérios de Aceitação:**
- [ ] Lista paginada de movimentações
- [ ] Filtros: tipo, produto, período
- [ ] Exibe: data, tipo, produto, quantidade, motivo, usuário
- [ ] Ordenação por data (mais recente primeiro)
- [ ] Exportar para Excel/CSV

#### RF-005.6: Alertas de Estoque

**Critérios de Aceitação:**
- [ ] Dashboard de alertas
- [ ] Lista de produtos abaixo do mínimo
- [ ] Lista de produtos zerados
- [ ] Notificação visual no menu (badge com contador)
- [ ] Ação rápida: entrada de estoque

#### RF-005.7: Inventário

**Critérios de Aceitação:**
- [ ] Criar novo inventário
- [ ] Adicionar produtos ao inventário
- [ ] Registrar quantidade contada
- [ ] Calcular diferença automaticamente
- [ ] Visualizar diferenças (sobra/falta)
- [ ] Finalizar inventário (ajusta estoque automaticamente)
- [ ] Histórico de inventários
- [ ] Relatório de inventário (PDF)

**Prioridade:** ALTA

---

### RF-006: Gestão de Vendas

**Descrição:** Visualização e gestão de pedidos e vendas.

#### RF-006.1: Listar Pedidos

**Critérios de Aceitação:**
- [ ] Lista paginada de pedidos
- [ ] Filtros: status, origem, cliente, período
- [ ] Exibe: número, cliente, data, total, status
- [ ] Indicadores visuais por status (cores)
- [ ] Busca por número do pedido ou cliente
- [ ] Ordenação por data (mais recente primeiro)

#### RF-006.2: Visualizar Pedido

**Critérios de Aceitação:**
- [ ] Detalhes completos do pedido
- [ ] Dados do cliente
- [ ] Endereço de entrega (se aplicável)
- [ ] Lista de itens com preços
- [ ] Subtotal, frete, desconto, total
- [ ] Forma de pagamento
- [ ] Status atual
- [ ] Histórico de mudanças de status
- [ ] Botões de ação conforme status

#### RF-006.3: Atualizar Status do Pedido (ADMIN)

**Critérios de Aceitação:**
- [ ] Botão para avançar status
- [ ] Fluxo: PENDENTE → CONFIRMADO → SEPARANDO → ENVIADO → ENTREGUE
- [ ] Confirmação antes de mudar status
- [ ] Registro de data/hora de cada mudança
- [ ] Notificação ao cliente (via backend)

#### RF-006.4: Cancelar Pedido (ADMIN)

**Critérios de Aceitação:**
- [ ] Botão "Cancelar Pedido"
- [ ] Modal de confirmação
- [ ] Campo obrigatório: motivo do cancelamento
- [ ] Validação: apenas pedidos não finalizados
- [ ] Estorno automático (se fiado)
- [ ] Devolução de estoque (se já baixado)

#### RF-006.5: Ajustar Frete (ADMIN)

**Critérios de Aceitação:**
- [ ] Campo editável de frete
- [ ] Apenas para pedidos PENDENTES
- [ ] Recalcula total automaticamente
- [ ] Confirmação antes de salvar

#### RF-006.6: Confirmar Pagamento Manual (ADMIN)

**Critérios de Aceitação:**
- [ ] Botão "Confirmar Pagamento"
- [ ] Apenas para pagamentos em dinheiro/cartão
- [ ] Campos: valor recebido, troco (se dinheiro)
- [ ] Confirmação
- [ ] Atualização de status para PAGO

**Prioridade:** ALTA

---

### RF-007: Gestão Financeira

**Descrição:** Controle de contas a receber e pagamentos.

#### RF-007.1: Listar Contas a Receber

**Critérios de Aceitação:**
- [ ] Lista paginada de contas
- [ ] Filtros: status, cliente, vencimento
- [ ] Exibe: cliente, valor original, valor pago, saldo, vencimento, status
- [ ] Indicadores visuais: vencidas (vermelho), a vencer (amarelo), quitadas (verde)
- [ ] Busca por cliente
- [ ] Ordenação por vencimento

#### RF-007.2: Visualizar Conta

**Critérios de Aceitação:**
- [ ] Detalhes da conta
- [ ] Dados do cliente
- [ ] Pedido relacionado
- [ ] Valor original, valor pago, saldo devedor
- [ ] Data de vencimento
- [ ] Histórico de pagamentos
- [ ] Botão "Registrar Pagamento"

#### RF-007.3: Registrar Pagamento

**Critérios de Aceitação:**
- [ ] Modal de pagamento
- [ ] Campos: valor, forma (dinheiro, PIX, cartão), observação
- [ ] Validação: valor > 0 e <= saldo devedor
- [ ] Cálculo automático de saldo restante
- [ ] Confirmação
- [ ] Atualização de status (PARCIAL ou QUITADO)
- [ ] Crédito automático no cliente

#### RF-007.4: Contas Vencidas

**Critérios de Aceitação:**
- [ ] Dashboard de contas vencidas
- [ ] Lista de contas com vencimento passado
- [ ] Total em atraso
- [ ] Ação rápida: registrar pagamento
- [ ] Ação: enviar lembrete (via backend)

#### RF-007.5: Contas a Vencer

**Critérios de Aceitação:**
- [ ] Lista de contas que vencem nos próximos N dias
- [ ] Filtro de período (7, 15, 30 dias)
- [ ] Total a receber no período
- [ ] Ação: enviar lembrete

**Prioridade:** ALTA

---

## 3. Requisitos Não Funcionais

### RNF-001: Performance

- [ ] Tempo de carregamento inicial < 3 segundos
- [ ] Tempo de resposta de ações < 1 segundo
- [ ] Paginação para listas com mais de 20 itens
- [ ] Lazy loading de imagens
- [ ] Debounce em buscas (300ms)
- [ ] Cache de dados estáticos (categorias, etc)

### RNF-002: Responsividade

- [ ] Layout responsivo para desktop (1920x1080)
- [ ] Layout responsivo para tablet (768x1024)
- [ ] Layout responsivo para mobile (375x667)
- [ ] Menu lateral colapsável em mobile
- [ ] Tabelas com scroll horizontal em mobile
- [ ] Formulários adaptados para touch

### RNF-003: Usabilidade

- [ ] Interface intuitiva e consistente
- [ ] Feedback visual para todas as ações
- [ ] Mensagens de erro claras e acionáveis
- [ ] Loading states em todas as operações assíncronas
- [ ] Confirmação para ações destrutivas
- [ ] Atalhos de teclado para ações comuns
- [ ] Breadcrumbs para navegação

### RNF-004: Segurança

- [ ] Tokens JWT armazenados de forma segura
- [ ] Refresh automático de tokens
- [ ] Logout em caso de token inválido
- [ ] Sanitização de inputs
- [ ] Proteção contra XSS
- [ ] HTTPS obrigatório em produção
- [ ] Validação de permissões no frontend e backend

### RNF-005: Acessibilidade

- [ ] Contraste adequado (WCAG AA)
- [ ] Navegação por teclado
- [ ] Labels em todos os inputs
- [ ] Mensagens de erro associadas aos campos
- [ ] Foco visível em elementos interativos
- [ ] Textos alternativos em imagens

### RNF-006: Compatibilidade

- [ ] Chrome 90+
- [ ] Firefox 88+
- [ ] Safari 14+
- [ ] Edge 90+

### RNF-007: Manutenibilidade

- [ ] Código TypeScript com tipagem forte
- [ ] Componentes reutilizáveis
- [ ] Separação clara de responsabilidades
- [ ] Documentação de componentes complexos
- [ ] Testes unitários para lógica crítica
- [ ] Testes de integração para fluxos principais

## 4. Regras de Negócio

### RN-001: Autenticação

- Token JWT expira em 30 minutos
- Refresh token expira em 7 dias
- Sistema renova automaticamente 5 minutos antes da expiração
- Logout invalida ambos os tokens

### RN-002: Permissões

- ADMIN: acesso total
- OPERADOR: leitura de produtos, criação de pedidos, consulta de clientes
- Funcionalidades restritas são ocultadas visualmente

### RN-003: Validações de Cliente

- CPF deve ser válido (algoritmo brasileiro)
- Telefone deve estar no formato E.164
- Email deve ser válido (se fornecido)
- Nome deve ter mínimo 3 caracteres

### RN-004: Validações de Produto

- SKU deve ser único
- Preço de custo > 0
- Markup >= 0
- Preço de venda = custo * (1 + markup/100)

### RN-005: Validações de Estoque

- Quantidade nunca pode ser negativa
- Saída não pode ser maior que disponível
- Movimentações são imutáveis (não podem ser editadas)

### RN-006: Validações de Venda

- Cliente não pode estar bloqueado
- Estoque deve estar disponível
- Frete só pode ser ajustado em pedidos PENDENTES
- Cancelamento só para pedidos não finalizados

### RN-007: Validações Financeiras

- Valor de pagamento > 0
- Valor de pagamento <= saldo devedor
- Pagamento credita automaticamente no cliente

## 5. Integrações

### INT-001: API Gateway

- Base URL: `http://localhost:8000` (dev) / `https://api.runas.com` (prod)
- Autenticação: Bearer Token no header `Authorization`
- Formato: JSON
- Timeout: 30 segundos

### INT-002: Endpoints Principais

Ver documentação completa em: `/docs/MAPEAMENTO-ROTAS.md`

**Autenticação:**
- POST `/auth/login`
- POST `/auth/refresh`
- POST `/auth/logout`

**Clientes:**
- GET/POST `/clientes`
- GET/PATCH/DELETE `/clientes/{id}`
- GET/POST `/clientes/{id}/enderecos`

**Produtos:**
- GET/POST `/produtos`
- GET/PATCH/DELETE `/produtos/{id}`
- GET/POST `/produtos/{id}/variantes`

**Estoque:**
- GET/POST `/estoque`
- POST `/estoque/{variante_id}/entrada`
- POST `/estoque/{variante_id}/saida`

**Vendas:**
- GET `/pedidos`
- GET/PATCH `/pedidos/{id}`
- DELETE `/pedidos/{id}/cancelar`

**Financeiro:**
- GET `/contas`
- GET `/contas/{id}`
- POST `/contas/{id}/pagamentos`

## 6. Critérios de Aceitação Gerais

- [ ] Todas as funcionalidades listadas implementadas
- [ ] Testes manuais passando em todos os fluxos
- [ ] Interface responsiva em desktop, tablet e mobile
- [ ] Performance dentro dos limites definidos
- [ ] Sem erros no console do navegador
- [ ] Código revisado e aprovado
- [ ] Documentação atualizada

## 7. Dependências

- Backend ERP Runas (API Gateway + Microsserviços)
- API ViaCEP (busca de endereço por CEP)

## 8. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Backend indisponível | Alto | Baixa | Mensagens de erro claras, retry automático |
| Token expirado durante operação | Médio | Média | Refresh automático, retry da operação |
| Perda de conexão | Alto | Média | Detecção de offline, queue de operações |
| Performance com muitos dados | Médio | Alta | Paginação, virtualização de listas |

## 9. Glossário

- **JWT**: JSON Web Token - formato de token de autenticação
- **CRUD**: Create, Read, Update, Delete
- **SKU**: Stock Keeping Unit - código único de produto
- **E.164**: Formato internacional de telefone
- **Debounce**: Técnica para atrasar execução de função
- **Lazy Loading**: Carregamento sob demanda
- **WCAG**: Web Content Accessibility Guidelines
