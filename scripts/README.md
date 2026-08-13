# Scripts Utilitários - RunasERP

Este diretório contém scripts auxiliares para automação e configuração do projeto.

---

## 📜 Scripts Disponíveis

### `setup-graphify-hook.ps1`

**Gerenciador de Hook Git para Graphify**

Automatiza a atualização do grafo de conhecimento Graphify após cada commit que modifica código.

#### 🚀 Uso Rápido

```powershell
# Ver status atual
.\scripts\setup-graphify-hook.ps1 status

# Instalar hook automático (RECOMENDADO)
.\scripts\setup-graphify-hook.ps1 install

# Desabilitar temporariamente (durante refatorações grandes)
.\scripts\setup-graphify-hook.ps1 disable

# Reativar
.\scripts\setup-graphify-hook.ps1 enable

# Remover completamente
.\scripts\setup-graphify-hook.ps1 uninstall
```

#### 📋 Comandos Detalhados

| Comando | Descrição | Quando usar |
|---------|-----------|-------------|
| `status` | Mostra se o hook está instalado/ativo | Verificar configuração atual |
| `install` | Instala o hook post-commit | Primeira configuração ou após clone do repo |
| `uninstall` | Remove o hook completamente | Deseja gerenciar Graphify manualmente |
| `enable` | Reativa um hook desabilitado | Após terminar refatoração grande |
| `disable` | Desabilita temporariamente | Durante muitos commits rápidos |

#### ⚙️ Como Funciona

1. **Detecção Inteligente**: Hook só roda se o commit modificou arquivos de código (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`)
2. **Execução Silenciosa**: Atualiza o grafo em background sem poluir output do commit
3. **Fail-Safe**: Se graphify não estiver instalado, apenas avisa mas não bloqueia o commit
4. **Mensagens Claras**: Mostra status da atualização com emojis e cores

#### 📊 Exemplo de Output

```
🔄 Detectadas mudanças em código, atualizando Graphify...
✅ Graphify atualizado com sucesso

[main 7a3f1c2] feat(vendas): add order tracking
 3 files changed, 145 insertions(+), 12 deletions(-)
```

#### 🎯 Quando Usar Cada Modo

**✅ Use `install` (recomendado):**
- Desenvolvimento normal do dia-a-dia
- Garante que o grafo está sempre atualizado
- Respostas do Kiro AI sempre precisas

**⏸️ Use `disable` temporariamente:**
- Refatoração grande com muitos commits pequenos
- Experimentos que você vai reverter
- Performance crítica (saving 5-15 segundos por commit)

**❌ Use `uninstall` se:**
- Prefere controle manual total
- Usa outro sistema de versionamento além de git
- Graphify não está instalado e não pretende instalar

#### 🔧 Requisitos

- **Git** instalado
- **Graphify** instalado (opcional - hook avisa se não encontrar)
- **PowerShell** 5.1+ (Windows)

#### 💡 Dicas

1. **Primeiro Setup**: Após clonar o repositório, rode `.\scripts\setup-graphify-hook.ps1 install`
2. **Durante Refatoração**: Desabilite com `disable` e reative com `enable` quando terminar
3. **Manual Override**: Sempre pode rodar `graphify update` manualmente quando quiser
4. **Verificação**: Use `status` para confirmar que o hook está ativo

#### 🐛 Troubleshooting

**Hook não está executando:**
```powershell
# Verificar status
.\scripts\setup-graphify-hook.ps1 status

# Reinstalar
.\scripts\setup-graphify-hook.ps1 uninstall
.\scripts\setup-graphify-hook.ps1 install
```

**Graphify não encontrado:**
```powershell
# Instalar graphify
pip install graphify

# Verificar instalação
graphify --version
```

**Performance lenta:**
```powershell
# Desabilitar temporariamente
.\scripts\setup-graphify-hook.ps1 disable

# Fazer seus commits...

# Reativar e atualizar manualmente
.\scripts\setup-graphify-hook.ps1 enable
graphify update
```

---

## 📚 Documentação Relacionada

- **Git Conventions**: `.kiro/steering/git-conventions.md` - Contém documentação sobre quando atualizar Graphify
- **Graphify Docs**: `graphify-out/GRAPH_REPORT.md` - Relatório do grafo atual
- **Project Docs**: `docs/` - Documentação geral do projeto

---

## 🤝 Contribuindo

Ao adicionar novos scripts:

1. Crie um arquivo `.ps1` com nome descritivo
2. Adicione header com descrição e exemplos de uso
3. Documente aqui no README com seção própria
4. Use convenções de commit: `chore(scripts): add new utility script`

---

**Última atualização**: 2026-06-24  
**Mantido por**: RunasERP Team
