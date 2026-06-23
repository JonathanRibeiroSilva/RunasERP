# 🧪 Guia de Teste - Interface de Categorias

> **Objetivo**: Validar todas as funcionalidades da interface de categorias
> **Tempo estimado**: 10-15 minutos
> **Pré-requisitos**: Sistema rodando localmente

---

## 🚀 Preparação

### 1. Iniciar o Sistema
```bash
# Na raiz do projeto
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Aguardar todos os serviços ficarem healthy
docker ps
```

### 2. Acessar o Sistema
1. Abrir navegador em: `http://localhost:3000`
2. Fazer login com usuário de teste
3. Navegar para: **Produtos → Categorias**

---

## ✅ Checklist de Testes

### Teste 1: Visualização Inicial
- [ ] Página carrega sem erros
- [ ] Título "Categorias" está visível
- [ ] Subtítulo "Gerencie as categorias de produtos" está visível
- [ ] Botão "Nova Categoria" está visível
- [ ] Se houver categorias, elas aparecem em grid
- [ ] Se não houver categorias, mensagem "Nenhuma categoria cadastrada" aparece

**Resultado esperado**: ✅ Página carrega corretamente

---

### Teste 2: Criar Nova Categoria

#### 2.1 - Criar categoria válida
1. Clicar em "Nova Categoria"
2. Preencher:
   - Nome: `Eletrônicos`
   - Descrição: `Produtos eletrônicos em geral`
3. Clicar em "Criar"

**Checklist**:
- [ ] Formulário abre inline
- [ ] Campos estão vazios
- [ ] Toast de sucesso aparece
- [ ] Categoria aparece no grid
- [ ] Formulário fecha automaticamente
- [ ] Card da categoria mostra ícone de pasta
- [ ] Nome e descrição estão corretos
- [ ] Badge "Ativo" está verde

**Resultado esperado**: ✅ Categoria criada com sucesso

#### 2.2 - Validação de campo obrigatório
1. Clicar em "Nova Categoria"
2. Deixar nome vazio
3. Tentar clicar em "Criar"

**Checklist**:
- [ ] Navegador mostra mensagem de validação HTML5
- [ ] Formulário não é enviado

**Resultado esperado**: ✅ Validação funciona

#### 2.3 - Criar categoria duplicada
1. Clicar em "Nova Categoria"
2. Preencher nome: `Eletrônicos` (mesmo nome do teste 2.1)
3. Clicar em "Criar"

**Checklist**:
- [ ] Toast de erro aparece
- [ ] Mensagem: "Categoria 'Eletrônicos' já existe" ou similar
- [ ] Categoria não é criada

**Resultado esperado**: ✅ Backend impede duplicação

#### 2.4 - Cancelar criação
1. Clicar em "Nova Categoria"
2. Preencher alguns campos
3. Clicar em "Cancelar"

**Checklist**:
- [ ] Formulário fecha
- [ ] Dados não são salvos
- [ ] Grid permanece inalterado

**Resultado esperado**: ✅ Cancelamento funciona

---

### Teste 3: Editar Categoria

#### 3.1 - Editar categoria existente
1. Localizar categoria "Eletrônicos"
2. Clicar no ícone de lápis (✏️)
3. Alterar:
   - Nome: `Eletrônicos Premium`
   - Descrição: `Produtos eletrônicos de alta qualidade`
4. Clicar em "Atualizar"

**Checklist**:
- [ ] Formulário abre com dados pré-preenchidos
- [ ] Título muda para "Editar Categoria"
- [ ] Botão muda para "Atualizar"
- [ ] Toast de sucesso aparece
- [ ] Card atualiza com novos dados
- [ ] Formulário fecha automaticamente

**Resultado esperado**: ✅ Categoria atualizada com sucesso

#### 3.2 - Cancelar edição
1. Clicar no ícone de lápis de alguma categoria
2. Alterar alguns campos
3. Clicar em "Cancelar"

**Checklist**:
- [ ] Formulário fecha
- [ ] Alterações não são salvas
- [ ] Card permanece com dados originais

**Resultado esperado**: ✅ Cancelamento funciona

---

### Teste 4: Excluir Categoria

#### 4.1 - Criar categoria para teste
1. Criar categoria: `Teste Exclusão`
2. Confirmar que foi criada

#### 4.2 - Excluir categoria
1. Localizar categoria "Teste Exclusão"
2. Clicar no ícone de lixeira (🗑️)
3. Confirmar exclusão no diálogo

**Checklist**:
- [ ] Diálogo de confirmação aparece
- [ ] Mensagem mostra nome da categoria
- [ ] Toast de sucesso aparece após confirmar
- [ ] Categoria desaparece do grid
- [ ] Total de categorias diminui

**Resultado esperado**: ✅ Categoria excluída com sucesso

#### 4.3 - Cancelar exclusão
1. Clicar no ícone de lixeira de alguma categoria
2. Clicar em "Cancelar" no diálogo

**Checklist**:
- [ ] Diálogo fecha
- [ ] Categoria não é excluída
- [ ] Grid permanece inalterado

**Resultado esperado**: ✅ Cancelamento funciona

#### 4.4 - Tentar excluir categoria com produtos (se aplicável)
1. Criar um produto vinculado a uma categoria
2. Tentar excluir essa categoria

**Checklist**:
- [ ] Toast de erro aparece
- [ ] Mensagem indica que há produtos vinculados
- [ ] Categoria não é excluída

**Resultado esperado**: ✅ Backend impede exclusão

---

### Teste 5: Responsividade

#### 5.1 - Desktop (1920x1080)
- [ ] Grid mostra 3-4 cards por linha
- [ ] Cards têm tamanho adequado
- [ ] Espaçamento está correto

#### 5.2 - Tablet (768x1024)
- [ ] Grid mostra 2 cards por linha
- [ ] Layout se adapta corretamente
- [ ] Botões são clicáveis

#### 5.3 - Mobile (375x667)
- [ ] Grid mostra 1 card por linha
- [ ] Formulário ocupa largura total
- [ ] Botões são clicáveis
- [ ] Texto é legível

**Resultado esperado**: ✅ Interface responsiva

---

### Teste 6: Estados de Loading

#### 6.1 - Loading inicial
1. Recarregar página
2. Observar estado de loading

**Checklist**:
- [ ] Spinner aparece durante carregamento
- [ ] Mensagem "Carregando..." está visível
- [ ] Após carregar, spinner desaparece
- [ ] Categorias aparecem

**Resultado esperado**: ✅ Loading funciona

---

### Teste 7: Integração com Produtos

#### 7.1 - Cadastrar produto com categoria
1. Navegar para: **Produtos → Novo Produto**
2. Verificar campo "Categoria"
3. Selecionar uma categoria criada

**Checklist**:
- [ ] Campo categoria está disponível
- [ ] Categorias criadas aparecem no select
- [ ] É possível selecionar uma categoria
- [ ] Produto pode ser criado com categoria

**Resultado esperado**: ✅ Integração funciona

---

## 📊 Resumo dos Testes

### Funcionalidades Testadas
- ✅ Visualização inicial
- ✅ Criar categoria (válida, duplicada, validação)
- ✅ Editar categoria
- ✅ Excluir categoria
- ✅ Cancelar operações
- ✅ Responsividade
- ✅ Estados de loading
- ✅ Integração com produtos

### Critérios de Aceitação
- [ ] Todos os testes passaram
- [ ] Nenhum erro no console do navegador
- [ ] Nenhum erro no console do backend
- [ ] Performance aceitável (< 500ms por operação)
- [ ] UX fluida e intuitiva

---

## 🐛 Problemas Encontrados

### Template para Reportar Bugs

```markdown
**Teste**: [Nome do teste]
**Passo**: [Passo onde ocorreu o erro]
**Esperado**: [O que deveria acontecer]
**Obtido**: [O que realmente aconteceu]
**Console**: [Erros no console, se houver]
**Screenshot**: [Anexar se possível]
```

---

## 🎯 Próximos Passos

Após validar todos os testes:

1. ✅ Marcar Sprint 2 como concluída
2. ✅ Atualizar checklist de desenvolvimento
3. ✅ Documentar funcionalidade
4. 🔴 Iniciar Sprint 3 (Estoque Frontend)

---

**Documento criado em**: 28/05/2026  
**Última atualização**: 28/05/2026  
**Responsável**: QA / Equipe de Desenvolvimento
