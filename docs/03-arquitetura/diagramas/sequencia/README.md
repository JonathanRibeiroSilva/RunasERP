# 🔄 Diagramas de Sequência - Runas

**Data**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Status**: ✅ Documentação Completa

---

## 📑 Índice Geral

Esta documentação contém **28 diagramas de sequência** organizados por domínio de negócio.

### 🔐 [Autenticação](./autenticacao.md)
Fluxos de login, logout, refresh token e validação JWT.

- Login com credenciais
- Refresh token
- Logout e blacklist
- Validação de token

### 👥 [Clientes](./clientes.md)
Operações CRUD de clientes e endereços (6 diagramas).

- Criar cliente
- Listar clientes
- Buscar cliente por ID
- Atualizar cliente
- Adicionar endereço
- Desativar cliente

### 📦 [Produtos](./produtos.md)
Operações CRUD de produtos, variantes e fornecedores (5 diagramas).

- Criar produto
- Criar variante
- Listar produtos com filtros
- Vincular fornecedor
- Atualizar configuração de catálogo

### 📊 [Estoque](./estoque.md)
Controle de estoque, movimentações, lotes e inventário (8 diagramas).

- Criar registro de estoque
- Entrada de estoque
- Saída de estoque
- Reservar estoque
- Liberar reserva
- Confirmar reserva
- Realizar inventário
- Finalizar inventário e ajustar

### 🛒 [Vendas](./vendas.md)
Carrinho, pedidos e checkout (6 diagramas).

- Criar carrinho
- Adicionar item ao carrinho
- Remover item do carrinho
- Finalizar carrinho (checkout)
- Confirmar pagamento (webhook)
- Cancelar pedido

### 🔄 [Fluxos Integrados](./fluxos-integrados.md)
Fluxos que envolvem múltiplos serviços (3 diagramas).

- Fluxo completo: Criar venda com estoque
- Alerta de estoque baixo com notificação
- Verificação de lotes vencidos (job agendado)

### 📐 [Padrões e Convenções](./padroes.md)
Padrões técnicos, convenções e boas práticas.

- Padrões de autenticação
- Padrões de validação
- Padrões de resposta HTTP
- Padrões de eventos (RabbitMQ)
- Gestão de reservas de estoque
- Transações distribuídas
- Locks e concorrência
- Idempotência
- Fluxos de erro comuns
- Métricas e monitoramento
- Diagrama de estados
- Glossário técnico

---

## 📊 Estatísticas

| Categoria | Diagramas | Linhas |
|-----------|-----------|--------|
| **Autenticação** | 4 | ~150 |
| **Clientes** | 6 | ~250 |
| **Produtos** | 5 | ~220 |
| **Estoque** | 8 | ~400 |
| **Vendas** | 6 | ~350 |
| **Fluxos Integrados** | 3 | ~180 |
| **Padrões** | - | ~250 |
| **TOTAL** | **28** | **~1.800** |

---

## 🎯 Como Usar Esta Documentação

### Para Desenvolvedores

1. **Implementando um novo endpoint?**
   - Consulte o diagrama correspondente
   - Siga os padrões de validação e resposta
   - Implemente os eventos RabbitMQ necessários

2. **Debugando um problema?**
   - Identifique o fluxo no diagrama
   - Verifique os pontos de validação
   - Consulte os fluxos de erro comuns

3. **Integrando serviços?**
   - Consulte os fluxos integrados
   - Verifique as dependências entre serviços
   - Implemente tratamento de erros adequado

### Para Arquitetos

1. **Planejando novas features?**
   - Use os diagramas como referência
   - Mantenha consistência com padrões existentes
   - Documente novos fluxos seguindo o mesmo formato

2. **Revisando arquitetura?**
   - Verifique pontos de integração
   - Identifique gargalos potenciais
   - Avalie necessidade de otimizações

### Para QA/Testers

1. **Criando casos de teste?**
   - Use os diagramas como base
   - Teste todos os caminhos (happy path + erros)
   - Valide eventos RabbitMQ

2. **Validando comportamento?**
   - Compare comportamento real com diagramas
   - Reporte inconsistências
   - Sugira melhorias na documentação

---

## 🔍 Convenções dos Diagramas

### Participantes

```
U  = Usuário (Cliente final)
G  = API Gateway
A  = Auth Service
C  = Clientes Service
P  = Produtos Service
E  = Estoque Service
V  = Vendas Service
F  = Financeiro Service
N  = Notificações Service
DB = PostgreSQL (específico do serviço)
R  = Redis
MQ = RabbitMQ
W  = WhatsApp (Evolution API)
MP = Mercado Pago
S  = Scheduler (Celery)
```

### Notações

- **Seta sólida (→)**: Chamada síncrona (HTTP)
- **Seta tracejada (-->)**: Resposta
- **Note over**: Comentário/explicação
- **alt/else**: Fluxo condicional
- **loop**: Iteração
- **par**: Execução paralela

### Códigos HTTP

- `200 OK` - Sucesso (GET, PUT)
- `201 Created` - Recurso criado (POST)
- `204 No Content` - Sucesso sem retorno (DELETE)
- `400 Bad Request` - Erro de validação
- `401 Unauthorized` - Token inválido
- `403 Forbidden` - Sem permissão
- `404 Not Found` - Recurso não encontrado
- `409 Conflict` - Conflito (duplicidade)
- `500 Internal Server Error` - Erro interno

---

## 🚀 Quick Links

### Fluxos Mais Consultados

1. **[Criar Venda Completa](./fluxos-integrados.md#41-fluxo-completo-criar-venda-com-estoque)** - Fluxo end-to-end de venda
2. **[Gestão de Reservas](./padroes.md#61-gestão-de-reservas-de-estoque)** - Como funciona o sistema de reservas
3. **[Checkout com Carrinho](./vendas.md#394-finalizar-carrinho-criar-pedido)** - Processo completo de checkout
4. **[Entrada de Estoque](./estoque.md#32-entrada-de-estoque)** - Como registrar entrada de mercadoria
5. **[Webhook Mercado Pago](./vendas.md#395-confirmar-pagamento-e-converter-pedido-em-venda)** - Processamento de pagamentos

### Documentação Relacionada

- **[Arquitetura Geral](../../README.md)** - Visão geral da arquitetura
- **[Comunicação entre Serviços](../../comunicacao.md)** - Padrões de comunicação
- **[Diagrama de Arquitetura](../arquitetura-geral.md)** - Diagrama visual da arquitetura
- **[Regras de Negócio](../../../11-regras-negocio/README.md)** - Regras de negócio por domínio
- **[API Reference](../../../10-api-reference/README.md)** - Referência completa das APIs

---

## 📝 Contribuindo

### Adicionando Novos Diagramas

1. Identifique o domínio correto (clientes, produtos, estoque, etc.)
2. Siga o formato Mermaid dos diagramas existentes
3. Inclua:
   - Título descritivo
   - Todos os participantes necessários
   - Fluxos de sucesso E erro
   - Validações importantes
   - Eventos RabbitMQ (se aplicável)
4. Atualize o índice neste README
5. Atualize as estatísticas

### Atualizando Diagramas Existentes

1. Mantenha compatibilidade com implementação atual
2. Documente mudanças no changelog
3. Atualize diagramas relacionados se necessário
4. Revise com a equipe antes de commitar

---

## 🐛 Reportando Problemas

Encontrou uma inconsistência entre diagrama e implementação?

1. Verifique se a implementação está correta
2. Se o diagrama estiver desatualizado:
   - Abra uma issue descrevendo a inconsistência
   - Sugira a correção
   - Referencie o código relevante
3. Se a implementação estiver incorreta:
   - Abra uma issue de bug
   - Referencie o diagrama correto
   - Descreva o comportamento esperado vs atual

---

## 📚 Recursos Adicionais

### Ferramentas

- **Mermaid Live Editor**: https://mermaid.live
- **Mermaid Documentation**: https://mermaid-js.github.io/mermaid/
- **Sequence Diagram Guide**: https://mermaid-js.github.io/mermaid/#/sequenceDiagram

### Leitura Recomendada

- **Microservices Patterns** - Chris Richardson
- **Building Microservices** - Sam Newman
- **Domain-Driven Design** - Eric Evans
- **Enterprise Integration Patterns** - Gregor Hohpe

---

## 📞 Suporte

Para dúvidas sobre os diagramas:

- **Email**: arquitetura@runas.com
- **Slack**: #arquitetura
- **Wiki**: https://wiki.runas.com/diagramas

---

**Última atualização**: 26 de Maio de 2026  
**Versão**: 2.0.0  
**Mantido por**: Equipe DenebCorp  
**Status**: ✅ Completo e Revisado

---

<div align="center">

**[⬆ Voltar ao topo](#-diagramas-de-sequência---runas)**

</div>
