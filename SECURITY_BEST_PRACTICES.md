# 🔒 Boas Práticas de Segurança - Runas ERP

## ⚠️ NUNCA Commite Segredos

### ❌ O que NUNCA fazer:
- Commitar arquivos `.env` com credenciais reais
- Incluir chaves de API em código ou documentação
- Deixar senhas em arquivos de configuração
- Expor tokens de acesso em logs ou changelogs
- Hardcodar credenciais em código

### ✅ O que fazer:
- **Use variáveis de ambiente** para todas as credenciais
- **Use `.env.example`** como modelo (sem valores reais)
- **Use placeholders** em documentação: `<sua-chave-aqui>`, `xxxx...xxxx`
- **Revise SEMPRE** antes de commitar: `git diff --staged`
- **Regenere chaves** se forem expostas acidentalmente

## 🛡️ Proteções Implementadas

### 1. `.gitignore`
Garante que arquivos `.env` nunca sejam commitados.

### 2. Pre-commit Hook
Hook do Git que verifica automaticamente padrões sensíveis.
Localização: `.git/hooks/pre-commit`

### 3. Kiro Hook
Hook do Kiro Agent que bloqueia operações de escrita com segredos.
Localização: `.kiro/hooks/prevent-secrets-commit.json`

## 📝 Checklist Antes de Commitar

- [ ] Revisei `git diff --staged`
- [ ] Não há arquivos `.env` (exceto `.env.example`)
- [ ] Não há chaves de API visíveis
- [ ] Não há senhas em texto claro
- [ ] Usei placeholders em exemplos de documentação

## 🚨 Se Você Expôs uma Chave

1. **Regenere a chave IMEDIATAMENTE** no painel do provedor
2. **Revogue a chave antiga**
3. **Atualize o `.env` local** com a nova chave
4. **Notifique a equipe** se for ambiente compartilhado

---

**Lembre-se**: Uma chave exposta é uma chave comprometida.
