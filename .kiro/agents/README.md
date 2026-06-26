# 🤖 Agentes Customizados do Kiro

Esta pasta contém agentes especializados do Kiro para tarefas específicas do projeto.

## 📚 Documentation Agent

**Arquivo**: `documentation-agent.json`

### Propósito

Agente especializado em criar e revisar documentação com **validação de segurança automática** integrada. Previne a exposição acidental de credenciais em arquivos de documentação.

### Quando Usar

Use este agente para:
- ✅ Criar CHANGELOGs de features
- ✅ Documentar APIs e endpoints
- ✅ Escrever guias técnicos
- ✅ Atualizar README e documentação do projeto
- ✅ Criar exemplos de configuração

### Validações de Segurança Automáticas

O agente **bloqueia** automaticamente se detectar:
- Mercado Pago Token
- Stripe Keys
- AWS Keys
- GitHub Tokens
- Senhas em texto claro

### Fluxo de Trabalho

1. Solicitação de Documentação
2. Agente Cria Draft
3. Security Scan Automático
4. Se limpo: Salva
5. Se sensível: BLOQUEIA e solicita placeholder

### Exemplo de Uso Seguro

Solicitação:
```
Crie um CHANGELOG para a integração do Mercado Pago
```

O agente automaticamente usa placeholders seguros.

## 📊 Comparação: Agente vs Hook

| Aspecto | Hook | Agente |
|---------|------|--------|
| **Quando** | Antes de operações | Durante execução |
| **Controle** | Bloqueia/permite | Guia comportamento |
| **Escopo** | Geral | Específico |
| **Propósito** | Segurança | Qualidade |

### Defesa em Profundidade

Camada 1: Agente de Documentação (prevenção proativa)
Camada 2: Kiro Hook (verificação durante operação)
Camada 3: Git Pre-commit Hook (última defesa)

---

**Mantido por**: Equipe Runas ERP  
**Última atualização**: 23/06/2026
