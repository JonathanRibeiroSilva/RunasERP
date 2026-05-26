# 📁 Nova Estrutura de Documentação

## Estrutura Proposta

```
docs/
├── README.md                          # Índice principal da documentação
│
├── 01-visao-geral/                    # Visão geral do projeto
│   ├── README.md                      # Sobre o projeto
│   ├── arquitetura.md                 # Arquitetura geral
│   ├── tecnologias.md                 # Stack tecnológico
│   └── glossario.md                   # Termos e conceitos
│
├── 02-setup/                          # Guias de instalação
│   ├── README.md                      # Índice de setup
│   ├── requisitos.md                  # Pré-requisitos
│   ├── instalacao-local.md            # Setup local
│   ├── instalacao-docker.md           # Setup com Docker
│   └── variaveis-ambiente.md          # Configuração de .env
│
├── 03-arquitetura/                    # Arquitetura detalhada
│   ├── README.md                      # Índice de arquitetura
│   ├── microservicos.md               # Arquitetura de microserviços
│   ├── comunicacao.md                 # Comunicação entre serviços
│   ├── banco-dados.md                 # Estrutura de banco de dados
│   ├── autenticacao.md                # Sistema de autenticação
│   └── diagramas/                     # Diagramas visuais
│       ├── arquitetura-geral.md
│       ├── fluxo-autenticacao.md
│       └── sequencia-vendas.md
│
├── 04-backend/                        # Documentação do backend
│   ├── README.md                      # Índice do backend
│   ├── api-gateway/                   # API Gateway
│   │   ├── README.md
│   │   ├── rotas.md
│   │   ├── autenticacao.md
│   │   └── middlewares.md
│   ├── servicos/                      # Microserviços
│   │   ├── clientes.md
│   │   ├── produtos.md
│   │   ├── estoque.md
│   │   ├── vendas.md
│   │   ├── financeiro.md
│   │   └── notificacoes.md
│   └── integracao/                    # Integrações externas
│       ├── evolution-api.md
│       └── whatsapp.md
│
├── 05-frontend/                       # Documentação do frontend
│   ├── README.md                      # Índice do frontend
│   ├── estrutura.md                   # Estrutura de pastas
│   ├── componentes.md                 # Componentes React
│   ├── rotas.md                       # Sistema de rotas
│   ├── autenticacao.md                # Autenticação no frontend
│   ├── design-system.md               # Design system
│   └── guias/                         # Guias específicos
│       ├── oauth-setup.md
│       ├── api-integration.md
│       └── testes.md
│
├── 06-features/                       # Features implementadas
│   ├── README.md                      # Índice de features
│   ├── autenticacao-oauth.md          # OAuth Google/Microsoft
│   ├── gestao-clientes.md             # CRUD de clientes
│   ├── gestao-produtos.md             # CRUD de produtos
│   ├── gestao-vendas.md               # Sistema de vendas
│   ├── gestao-estoque.md              # Controle de estoque
│   ├── gestao-financeiro.md           # Gestão financeira
│   └── notificacoes-whatsapp.md       # Notificações via WhatsApp
│
├── 07-desenvolvimento/                # Guias de desenvolvimento
│   ├── README.md                      # Índice de desenvolvimento
│   ├── padroes-codigo.md              # Padrões e convenções
│   ├── git-workflow.md                # Workflow Git
│   ├── testes.md                      # Estratégia de testes
│   ├── debug.md                       # Guia de debug
│   └── contribuicao.md                # Como contribuir
│
├── 08-deployment/                     # Deploy e produção
│   ├── README.md                      # Índice de deployment
│   ├── docker.md                      # Deploy com Docker
│   ├── nginx.md                       # Configuração Nginx
│   ├── ngrok.md                       # Uso do ngrok
│   ├── producao.md                    # Checklist de produção
│   └── monitoramento.md               # Logs e monitoramento
│
├── 09-troubleshooting/                # Resolução de problemas
│   ├── README.md                      # Índice de troubleshooting
│   ├── erros-comuns.md                # Erros comuns e soluções
│   ├── oauth-issues.md                # Problemas com OAuth
│   ├── docker-issues.md               # Problemas com Docker
│   └── faq.md                         # Perguntas frequentes
│
├── 10-api-reference/                  # Referência de APIs
│   ├── README.md                      # Índice de APIs
│   ├── api-gateway.md                 # Endpoints do Gateway
│   ├── clientes-api.md                # API de Clientes
│   ├── produtos-api.md                # API de Produtos
│   ├── vendas-api.md                  # API de Vendas
│   ├── estoque-api.md                 # API de Estoque
│   ├── financeiro-api.md              # API Financeiro
│   └── notificacoes-api.md            # API de Notificações
│
├── 11-regras-negocio/                 # Regras de negócio
│   ├── README.md                      # Índice de regras
│   ├── clientes.md                    # Regras de clientes
│   ├── produtos.md                    # Regras de produtos
│   ├── vendas.md                      # Regras de vendas
│   ├── estoque.md                     # Regras de estoque
│   └── financeiro.md                  # Regras financeiras
│
├── 12-changelog/                      # Histórico de mudanças
│   ├── README.md                      # Índice de changelog
│   ├── v1.0.0.md                      # Versão 1.0.0 (MVP)
│   └── roadmap.md                     # Roadmap futuro
│
└── _archive/                          # Arquivos obsoletos (não deletar)
    ├── documentacao-original/         # Docs originais do projeto
    └── historico/                     # Histórico de conversas
```

## Arquivos a Manter na Raiz

```
/
├── README.md                          # README principal do projeto
├── QUICK-START.md                     # Guia rápido de início
├── CONTRIBUTING.md                    # Guia de contribuição
├── CHANGELOG.md                       # Histórico de versões
├── LICENSE.md                         # Licença
└── .github/                           # GitHub configs (futuro)
    └── workflows/                     # CI/CD (futuro)
```

## Arquivos a Remover/Consolidar

### Duplicados
- `docs/INDICE.md` → Consolidar em `docs/README.md`
- `docs/INDICE-DOCUMENTACAO.md` → Consolidar em `docs/README.md`
- `docs/ORGANIZACAO-DOCUMENTACAO.md` → Remover (substituído por esta estrutura)

### Obsoletos
- `docs/ARQUIVOS-CRIADOS.md` → Mover para `_archive/`
- `docs/ARQUIVOS-FALTANTES.md` → Mover para `_archive/`
- `docs/frontend/IMPLEMENTATION-LOG.md` → Mover para `_archive/`
- `docs/frontend/DEBUG-OAUTH-REDIRECT.md` → Consolidar em troubleshooting

### A Reorganizar
- `docs/ARQUITETURA-COMUNICACAO.md` → `docs/03-arquitetura/comunicacao.md`
- `docs/ARQUITETURA-VISUAL.md` → `docs/03-arquitetura/diagramas/arquitetura-geral.md`
- `docs/DIAGRAMAS-SEQUENCIA.md` → `docs/03-arquitetura/diagramas/`
- `docs/ESPECIFICACAO-TECNICA.md` → `docs/01-visao-geral/arquitetura.md`
- `docs/EVOLUTION-API-SETUP.md` → `docs/04-backend/integracao/evolution-api.md`
- `docs/REGRAS-DE-NEGOCIO.md` → `docs/11-regras-negocio/`
- `docs/MAPEAMENTO-ROTAS.md` → `docs/10-api-reference/`

### Frontend
- `docs/frontend/DESIGN-SYSTEM.md` → `docs/05-frontend/design-system.md`
- `docs/frontend/OAUTH-*.md` → Consolidar em `docs/05-frontend/guias/oauth-setup.md`
- `docs/frontend/DOCKER*.md` → `docs/02-setup/instalacao-docker.md`
- `docs/frontend/PRODUCTION-CHECKLIST.md` → `docs/08-deployment/producao.md`

## Novos Arquivos Criados Hoje

Estes arquivos foram criados para resolver o problema de OAuth:

- `docs/OAUTH-FIX-NGROK.md` → `docs/09-troubleshooting/oauth-issues.md`
- `docs/OAUTH-QUICK-FIX.md` → Consolidar em oauth-issues.md
- `docs/OAUTH-FLOW-DIAGRAM.md` → `docs/03-arquitetura/diagramas/fluxo-autenticacao.md`
- `docs/OAUTH-TROUBLESHOOTING.md` → `docs/09-troubleshooting/oauth-issues.md`
- `docs/CHANGES-SUMMARY.md` → `docs/12-changelog/v1.0.0.md`
- `docs/TESTE-MANUAL-PASSO-A-PASSO.md` → `docs/07-desenvolvimento/testes.md`
- `docs/REBUILD-COMPLETE.md` → Remover (temporário)

## Benefícios da Nova Estrutura

1. **Organização Clara**: Numeração facilita navegação
2. **Separação por Contexto**: Cada pasta tem um propósito específico
3. **Fácil Manutenção**: Sabe-se onde adicionar novos docs
4. **Onboarding Rápido**: Novos devs encontram info facilmente
5. **Versionamento**: Changelog organizado por versão
6. **Histórico Preservado**: Archive mantém docs antigos

## Próximos Passos

1. Criar estrutura de pastas
2. Mover arquivos existentes
3. Consolidar conteúdo duplicado
4. Criar READMEs de cada seção
5. Atualizar README principal
6. Criar CHANGELOG.md
7. Atualizar QUICK-START.md
