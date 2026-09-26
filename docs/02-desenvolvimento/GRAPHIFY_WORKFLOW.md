# Graphify - Grafo de Conhecimento Automático

## 📊 O que é Graphify?

Graphify mantém um **grafo de conhecimento** do projeto em `graphify-out/`, mapeando:
- **Componentes**: arquivos, classes, funções, rotas
- **Relacionamentos**: imports, chamadas, dependências
- **Comunidades**: clusters de código relacionado

## 🤖 Atualização Automática via GitHub Actions

O Graphify é atualizado **automaticamente** pelo GitHub Actions quando você faz push de commits com mudanças em código.

### ✅ Workflow Correto

```powershell
# 1. Fazer commit das mudanças
git add .
git commit -m "feat(vendas): add order tracking"

# 2. Fazer push
git push

# 3. GitHub Actions atualiza o Graphify automaticamente
#    - Detecta mudanças em código (.py, .ts, .tsx, .js, .jsx, .vue)
#    - Roda graphify update
#    - Commita e faz push do grafo atualizado
#    ⏱️ Aguarde ~2-3 minutos para conclusão
```

### ❌ NÃO precisa rodar manualmente após commits

```powershell
# ❌ NÃO FAÇA ISSO (o GitHub Actions já faz)
git commit -m "feat(vendas): add order tracking"
graphify update  # ← Desnecessário!
git add graphify-out/
git commit -m "chore(graphify): update"
git push
```

**Por quê?** O GitHub Actions detecta automaticamente mudanças em código e atualiza o grafo para você.

## 🔍 Quando Rodar Manualmente

### 1. Desenvolvimento Local (antes de commitar)

```powershell
# Para testar queries antes do commit
graphify update
graphify query "como funciona o módulo de vendas?"
```

Use para explorar o código localmente sem fazer push.

### 2. Troubleshooting

```powershell
# Grafo corrompido ou inconsistente
Remove-Item -Recurse -Force graphify-out
graphify --update  # Recria do zero

# Verificar logs de erros
cat graphify-out/.graphify_uncached.txt
```

### 3. Update Completo com Docs/Imagens

```powershell
# O GitHub Actions roda apenas "graphify update" (código)
# Para incluir docs e imagens, rode localmente:
graphify --update
```

## 📊 Como Funciona o GitHub Actions

**Arquivo**: `.github/workflows/graphify-update.yml`

### Gatilhos

O workflow é disparado quando há:
- ✅ Push para `main`, `master`, ou `Developer`
- ✅ Mudanças em arquivos: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`

### Proteções Anti-Loop

- ❌ Não roda se o commit contém `[skip graphify]`
- ❌ Não roda se não houver mudanças em código
- ✅ Commit automático feito por `github-actions[bot]`

### Processo Automático

1. **Detecta** mudanças em código no último commit
2. **Remove** cache antigo do Windows (se existir)
3. **Executa** `graphify update`
4. **Verifica** se o grafo foi modificado
5. **Commita** com mensagem: `chore(graphify): auto-update knowledge graph [skip graphify]`
6. **Faz push** automático para o branch

### Exemplo de Execução

```bash
# Seu commit
feat(vendas): add order tracking

# GitHub Actions detecta e cria automaticamente
chore(graphify): auto-update knowledge graph [skip graphify]
Updated by GitHub Actions after code changes
Modified 6 graphify files
Triggered by commit: abc123...
Branch: Developer
```

## 🎯 Quando o GitHub Actions NÃO Atualiza

O workflow **não é disparado** para:

- ❌ Commits apenas de documentação (`.md` files)
- ❌ Commits de configuração (`.env`, `docker-compose.yml`)
- ❌ Commits de assets (imagens, fontes)
- ❌ Commits de dados (seeds, migrations)

Isso é **por design** — o grafo mapeia apenas código-fonte.

## 💡 Usando o Grafo no Kiro AI

O assistente AI usa o Graphify para responder perguntas sobre o código:

```
# Exemplos de queries
"Quais componentes dependem do módulo de vendas?"
"Mostre o fluxo de autenticação"
"Qual a estrutura do serviço de produtos?"
"Como os microsserviços se comunicam?"
```

**⚠️ Importante**: 
- Se o grafo estiver desatualizado localmente, aguarde o GitHub Actions completar
- Ou rode `graphify update` manualmente para queries locais

## 📈 Status do Grafo Atual

- **Nós**: ~9.432 componentes
- **Edges**: ~12.236 relacionamentos
- **Comunidades**: ~706 clusters
- **Atualização**: Automática via GitHub Actions
- **Última atualização**: Verificar `graphify-out/.graphify_root`

## 🔧 Configuração do Projeto

### Instalação Local (Opcional)

```powershell
# Instalar graphify globalmente
pip install graphifyy

# Verificar versão
graphify --version
```

### Estrutura de Arquivos

```
RunasERP/
├── .github/
│   └── workflows/
│       └── graphify-update.yml    # ← Workflow automático
├── graphify-out/                  # ← Grafo gerado
│   ├── graph.json                 # Grafo completo
│   ├── GRAPH_REPORT.md            # Relatório legível
│   ├── RunasERP-callflow.html     # Visualização de fluxo
│   └── cache/                     # Cache de AST
└── ...
```

### Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `graph.json` | Grafo completo em formato JSON |
| `GRAPH_REPORT.md` | Relatório legível com estatísticas |
| `RunasERP-callflow.html` | Visualização interativa de fluxos |
| `.graphify_root` | Metadados da última atualização |
| `.graphify_uncached.txt` | Log de erros (se houver) |

## 🚀 Benefícios do Workflow Automático

1. ✅ **Zero manutenção manual** — grafo sempre atualizado
2. ✅ **Não esquece** — impossível esquecer de atualizar
3. ✅ **Consistência** — sempre roda no ambiente Linux do GitHub
4. ✅ **Histórico completo** — cada atualização fica registrada
5. ✅ **Sem loops infinitos** — proteção `[skip graphify]`
6. ✅ **CI/CD integrado** — parte do pipeline de desenvolvimento

## 🐛 Troubleshooting

### Grafo não foi atualizado após push

1. Verifique se houve mudanças em código (não apenas docs)
2. Verifique a aba **Actions** no GitHub
3. Veja se o workflow rodou com sucesso
4. Verifique logs do workflow para erros

### Grafo desatualizado localmente

```powershell
# Sincronizar com remote
git pull

# Ou atualizar localmente
graphify update
```

### Loop infinito de commits

Não deve acontecer graças ao `[skip graphify]`, mas se ocorrer:

1. Force push do último commit bom
2. Verifique se alguém modificou o workflow
3. Desabilite o workflow temporariamente

## 📚 Referências

- [Graphify Documentation](https://github.com/graysonhead/graphify)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Workflow File](../../.github/workflows/graphify-update.yml)

---

**Última atualização**: 2026-06-24  
**Versão do Graphify**: 0.8.46  
**Ambiente**: GitHub Actions Ubuntu Latest
