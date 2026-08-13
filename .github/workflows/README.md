# GitHub Actions Workflows

Este diretório contém workflows automatizados do GitHub Actions para o projeto RunasERP.

---

## 📋 Workflows Disponíveis

### 🔄 `graphify-update.yml` - Auto-Update Graphify Knowledge Graph

**Propósito**: Mantém o grafo de conhecimento Graphify sempre sincronizado com o código.

#### ⚙️ Como Funciona

1. **Trigger**: Dispara automaticamente após push nas branches principais (`main`, `master`, `Developer`)
2. **Detecção Inteligente**: Só roda se houver mudanças em arquivos de código (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`)
3. **Atualização**: Executa `graphify update` para regenerar o grafo
4. **Commit Automático**: Commita os arquivos atualizados do `graphify-out/` de volta ao repositório
5. **Prevenção de Loops**: Usa `[skip graphify]` para evitar loops infinitos

#### 🎯 Benefícios

- ✅ **Grafo sempre atualizado** - Nenhum dev precisa lembrar de rodar `graphify update`
- ✅ **Kiro AI preciso** - O assistente AI sempre tem dados corretos para análise
- ✅ **Zero configuração** - Funciona automaticamente para todos os devs
- ✅ **Versionado** - Histórico completo do grafo junto com o código
- ✅ **Multiplataforma** - Funciona independente do SO do dev (Windows/Linux/Mac)

#### 📝 Exemplo de Uso

```bash
# Desenvolvedor faz mudanças normalmente
git add frontend/src/pages/CheckoutPage.tsx
git commit -m "fix(checkout): corrige scroll duplo"
git push origin Developer

# GitHub Actions detecta automaticamente:
# ✅ Push na branch Developer
# ✅ Arquivo .tsx modificado
# ✅ Roda graphify update
# ✅ Commita: "chore(graphify): auto-update knowledge graph [skip graphify]"
# ✅ Push automático de volta

# Resultado: Grafo sincronizado sem esforço manual!
```

#### 🚀 Execução Manual

Você pode executar o workflow manualmente:

1. Vá para **Actions** no GitHub
2. Selecione **Auto-Update Graphify Knowledge Graph**
3. Clique em **Run workflow**

#### 🔗 Integração com Kiro AI

O Kiro AI usa o grafo automaticamente para:
- Responder perguntas sobre arquitetura
- Analisar dependências entre componentes
- Sugerir mudanças baseadas em impacto

**Com este workflow, o Kiro AI sempre tem:**
- ✅ Dados atualizados do projeto
- ✅ Mapeamento correto de dependências  
- ✅ Análise precisa de impacto
- ✅ Respostas baseadas no código real

---

**Última atualização**: 2026-06-24  
**Mantido por**: RunasERP Team
