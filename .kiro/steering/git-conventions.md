---
inclusion: always
---

# Language Conventions

## Chat
Always respond to the user in **Brazilian Portuguese (PT-BR)**.

## Code
- Identifiers, variable names, function names, class names: **keep as-is in the existing codebase** (project uses PT-BR identifiers — do not change them)
- Code comments: **PT-BR**
- Commit messages: **English** (see below)
- Documentation files (`.md`): follow the existing file's language

---

# Testing and Debugging Conventions

## Terminal Commands (Windows PowerShell)

**ALWAYS use `Invoke-WebRequest` instead of `curl` for HTTP requests:**

```powershell
# ❌ NEVER use (wastes tokens, causes errors)
curl http://localhost:8000/api/health

# ✅ ALWAYS use
Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing
```

**Reason:** PowerShell alias `curl` → `Invoke-WebRequest` causes confusion and token waste with error handling.

## API Testing Routes

**ALWAYS test APIs through the Cloudflare tunnel, never direct to services:**

```powershell
# ❌ NEVER test directly to services
Invoke-WebRequest -Uri "http://localhost:8000/api/produtos"
Invoke-WebRequest -Uri "http://localhost:8002/produtos"

# ✅ ALWAYS test through Cloudflare tunnel (simulates production)
Invoke-WebRequest -Uri "https://www.runaserp.com.br/api/produtos" -UseBasicParsing

# ✅ Alternative with domain variable
$domain = "https://www.runaserp.com.br"
Invoke-WebRequest -Uri "$domain/api/produtos" -UseBasicParsing
```

**Reasons:**
1. ✅ Tests OAuth2 flows (Google/Microsoft require HTTPS)
2. ✅ Tests CORS configuration
3. ✅ Tests Nginx reverse proxy
4. ✅ Tests Mercado Pago webhooks
5. ✅ Simulates real production environment
6. ✅ Validates SSL/HTTPS behavior
7. ✅ Uses production domain (Cloudflare tunnel)

## Exception: Local Service Debugging

Direct service access is ONLY acceptable for debugging specific service issues:

```powershell
# Only when debugging a specific service
docker logs erp-api-gateway-dev -f
Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
```

---

# Engineering Standards

All code written must follow software engineering best practices. These are non-negotiable.

## Clean Code

- **Nomes descritivos**: variáveis, funções e classes devem revelar intenção. Sem abreviações obscuras (`cli`, `tmp`, `x`)
- **Funções pequenas**: uma função faz uma coisa só. Se precisar de comentário para explicar o que ela faz, ela deve ser dividida
- **Sem números mágicos**: usar constantes nomeadas
- **Sem código morto**: não deixar código comentado ou funções não utilizadas
- **DRY** (Don't Repeat Yourself): lógica duplicada deve ser extraída
- **Sem side effects ocultos**: funções não devem alterar estado externo sem que o nome deixe claro

## SOLID Principles

- **S** — Single Responsibility: cada classe/módulo tem uma única razão para mudar
- **O** — Open/Closed: aberto para extensão, fechado para modificação
- **L** — Liskov Substitution: subclasses devem ser substituíveis pelas suas bases
- **I** — Interface Segregation: interfaces específicas são melhores que uma genérica
- **D** — Dependency Inversion: depender de abstrações, não de implementações concretas

## Design Patterns (em uso no projeto)

- **Repository Pattern**: toda query ao banco passa pelo repository — nunca direto no service ou router
- **Service Layer**: regras de negócio ficam no service — nunca no router
- **Dependency Injection**: usar `Depends()` do FastAPI para injetar sessão, usuário, etc.
- **DTO / Schema**: usar Pydantic schemas para entrada e saída — nunca expor o model ORM diretamente

## Error Handling

- **Nunca usar `except Exception` genérico** nos services — capturar exceções específicas
- **Exceções de negócio**: usar as exceções customizadas de `shared/exceptions.py` (`ValidationError`, `NotFoundError`, `ConflictError`, etc.)
- **Handlers globais**: os routers não devem ter try/except — os exception handlers do `main.py` cuidam disso
- **Nunca expor stack trace** ao cliente — retornar `request_id` em erros 500
- **Logs estruturados**: usar `structlog` com contexto (`usuario_id`, `path`, `method`)

## Security

- **Nunca confiar só no frontend**: validar todos os dados no backend
- **Nunca logar dados sensíveis**: senhas, tokens, CPF completo
- **Queries parametrizadas**: nunca concatenar strings SQL — usar SQLAlchemy ORM
- **Princípio do menor privilégio**: cada serviço acessa apenas seu próprio schema

### 🔒 Regras de Segurança Obrigatórias (NÃO NEGOCIÁVEIS)

Estas regras **NUNCA** devem ser violadas. Se o agente sugerir qualquer uma das práticas proibidas abaixo, é um erro crítico que deve ser rejeitado.

#### ❌ NUNCA Usar (Proibido)

1. **localStorage / sessionStorage para tokens**
   - ❌ `localStorage.setItem('token', jwt)`
   - ❌ `sessionStorage.setItem('access_token', token)`
   - **Por quê?**: Vulnerável a XSS (Cross-Site Scripting)

2. **Tokens em query parameters**
   - ❌ `https://api.com/dados?token=abc123`
   - **Por quê?**: Exposto em logs, histórico do navegador, referrers

3. **Senhas em plain text**
   - ❌ Armazenar senhas sem hash
   - ❌ Logar senhas (mesmo em dev)
   - ❌ Enviar senhas em GET requests

4. **CORS com wildcard em produção**
   - ❌ `Access-Control-Allow-Origin: *`
   - **Por quê?**: Permite qualquer origem acessar a API

5. **Dados sensíveis no frontend**
   - ❌ Lógica de negócio crítica em JavaScript
   - ❌ Validação apenas no frontend
   - ❌ Secrets/API keys em código frontend

6. **SQL Injection vulnerabilities**
   - ❌ `f"SELECT * FROM users WHERE id = {user_id}"`
   - ❌ String concatenation em queries
   - **Por quê?**: Permite execução de SQL arbitrário

#### ✅ SEMPRE Usar (Obrigatório)

1. **HttpOnly Cookies para tokens**
   ```python
   # Backend: FastAPI
   response.set_cookie(
       key="access_token",
       value=token,
       httponly=True,      # ← Não acessível via JavaScript
       secure=True,        # ← Apenas HTTPS
       samesite="lax",     # ← Proteção CSRF
       max_age=1800        # ← 30 minutos
   )
   ```
   ```typescript
   // Frontend: NÃO precisa manipular o token
   // O navegador envia automaticamente o cookie
   fetch('https://api.com/dados', {
     credentials: 'include'  // ← Envia cookies automaticamente
   })
   ```

2. **Bcrypt/Argon2 para senhas**
   ```python
   from passlib.context import CryptContext
   
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   hashed = pwd_context.hash(senha)  # ← Sempre hash
   ```

3. **CORS restritivo**
   ```python
   # Apenas origins específicas
   origins = [
       "https://www.runaserp.com.br",
       "http://localhost:3000"  # Apenas em dev
   ]
   ```

4. **Validação backend obrigatória**
   ```python
   # SEMPRE validar no backend, mesmo se validado no frontend
   def criar_cliente(dados: ClienteCreate) -> Cliente:
       if not validar_cpf(dados.cpf):
           raise ValidationError("CPF inválido")
       # ... resto da lógica
   ```

5. **Rate limiting**
   ```python
   # Proteger endpoints críticos
   @limiter.limit("5 per minute")  # Login
   @limiter.limit("10 per minute") # Cadastro
   ```

6. **Content Security Policy (CSP)**
   ```python
   # Headers de segurança
   response.headers["Content-Security-Policy"] = "default-src 'self'"
   response.headers["X-Content-Type-Options"] = "nosniff"
   response.headers["X-Frame-Options"] = "DENY"
   ```

#### 🎯 Padrão de Autenticação do Projeto

**Fluxo OAuth2 + HttpOnly Cookies**:

1. **Login** → Backend gera JWT → Armazena em HttpOnly Cookie
2. **Requests** → Frontend envia cookie automaticamente (credentials: 'include')
3. **Refresh** → Backend valida refresh token → Gera novo access token → Atualiza cookie
4. **Logout** → Backend invalida token + limpa cookie

**Arquivos de referência**:
- `api-gateway/auth/jwt.py` - Geração de tokens
- `api-gateway/routers/auth.py` - Endpoints de autenticação
- `frontend/src/contexts/AuthContext.tsx` - Client-side auth (sem manipular tokens)

#### 🚨 Red Flags - Rejeitar Imediatamente

Se o agente sugerir qualquer um destes padrões, **interrompa e corrija**:

- "Vamos guardar o token no localStorage..."
- "Adiciona o token na URL..."
- "Envia a senha em base64..." (não é criptografia!)
- "Valida o CPF só no frontend..."
- "Usa CORS * para simplificar..."
- "Deixa sem rate limit por enquanto..."

**Resposta correta**: "Essa abordagem viola as regras de segurança. Vou usar [solução segura] em vez disso."

---

## Code Structure (FastAPI + SQLAlchemy)

```
router      → valida entrada (Pydantic), chama service, retorna resposta
service     → regras de negócio, orquestra repositories, lança exceções de negócio
repository  → queries ao banco, sem lógica de negócio
validator   → validações complexas reutilizáveis (CPF, crédito, etc.)
schema      → Pydantic models de entrada/saída
model       → SQLAlchemy ORM models
```

## Testing

- Todo código novo deve ter testes unitários para o service layer
- Validators devem ter 90%+ de cobertura
- Usar `pytest` com fixtures para sessão de banco
- Nomear testes descritivamente: `test_criar_cliente_com_cpf_duplicado_retorna_409`

## Documentation

- Docstrings em PT-BR em todos os métodos públicos de service e repository
- Endpoints FastAPI devem ter `summary` e `description` no decorator
- Parâmetros e retornos documentados quando não óbvios

## KISS (Keep It Simple, Stupid)

O princípio KISS defende que a simplicidade deve ser um objetivo fundamental no design de software. Código complexo é mais difícil de entender, manter e debugar.

### Regras KISS

- **Prefira soluções simples**: se há duas formas de resolver um problema, escolha a mais simples
- **Evite over-engineering**: não adicionar abstrações, padrões ou funcionalidades "para o futuro"
- **Código auto-explicativo**: se precisar de muitos comentários, o código provavelmente está complexo demais
- **Uma coisa por vez**: não misturar múltiplas responsabilidades em uma função/classe
- **Evite cleverness**: código "esperto" que usa truques obscuros é difícil de manter

### Exemplos

❌ **Complexo (over-engineered)**:
```python
class AbstractClienteFactory:
    @abstractmethod
    def create_cliente(self) -> BaseCliente:
        pass

class PessoaFisicaFactory(AbstractClienteFactory):
    def create_cliente(self) -> PessoaFisica:
        return PessoaFisica()

# ... quando só há um tipo de cliente
```

✅ **Simples (KISS)**:
```python
def criar_cliente(nome: str, cpf: str, email: str) -> Cliente:
    return Cliente(nome=nome, cpf=cpf, email=email)
```

❌ **Complexo (clever)**:
```python
def calcular_desconto(valor: float) -> float:
    return valor * (1 - (0.1 if valor > 100 else 0.05 if valor > 50 else 0))
```

✅ **Simples (legível)**:
```python
def calcular_desconto(valor: float) -> float:
    if valor > 100:
        return valor * 0.9
    elif valor > 50:
        return valor * 0.95
    else:
        return valor
```

## IAGINI Code Calisthenics

IAGINI é um acrônimo mnemônico para lembrar dos **9 exercícios de Object Calisthenics** que promovem código limpo e manutenível.

### I - Indentação (One Level of Indentation per Method)

**Regra**: Máximo **1 nível de indentação** por método.

❌ **Ruim** (3 níveis):
```python
def processar_pedido(pedido: Pedido) -> None:
    if pedido.ativo:
        if pedido.valor > 0:
            for item in pedido.itens:
                if item.quantidade > 0:
                    item.processar()
```

✅ **Bom** (1 nível):
```python
def processar_pedido(pedido: Pedido) -> None:
    if not pedido.pode_ser_processado():
        return
    processar_itens(pedido.itens)

def processar_itens(itens: list[Item]) -> None:
    for item in itens:
        processar_item(item)

def processar_item(item: Item) -> None:
    if item.quantidade > 0:
        item.processar()
```

### A - Avoid else (Don't Use the ELSE Keyword)

**Regra**: Evitar `else` usando **early returns**, **polimorfismo** ou **estratégias**.

❌ **Ruim** (com else):
```python
def calcular_frete(tipo: str, peso: float) -> float:
    if tipo == "expresso":
        return peso * 5.0
    else:
        return peso * 2.0
```

✅ **Bom** (early return):
```python
def calcular_frete(tipo: str, peso: float) -> float:
    if tipo == "expresso":
        return peso * 5.0
    return peso * 2.0
```

✅ **Melhor** (polimorfismo):
```python
class FreteExpresso:
    def calcular(self, peso: float) -> float:
        return peso * 5.0

class FreteNormal:
    def calcular(self, peso: float) -> float:
        return peso * 2.0
```

### G - Getters/Setters (Wrap All Primitives and Strings)

**Regra**: Encapsular tipos primitivos em **Value Objects** quando representam conceitos de domínio.

❌ **Ruim** (primitivo exposto):
```python
cliente.cpf = "123.456.789-00"  # string qualquer
```

✅ **Bom** (Value Object):
```python
class CPF:
    def __init__(self, valor: str):
        if not self._validar(valor):
            raise ValueError("CPF inválido")
        self._valor = valor
    
    def _validar(self, valor: str) -> bool:
        # validação de CPF
        return True
    
    @property
    def valor(self) -> str:
        return self._valor

cliente.cpf = CPF("123.456.789-00")
```

### I - Immutability (First Class Collections)

**Regra**: Coleções não devem ser mutadas diretamente. Encapsulá-las em classes.

❌ **Ruim** (coleção exposta):
```python
pedido.itens.append(Item())  # qualquer código pode modificar
```

✅ **Bom** (coleção encapsulada):
```python
class Pedido:
    def __init__(self):
        self._itens: list[Item] = []
    
    def adicionar_item(self, item: Item) -> None:
        if self._pode_adicionar(item):
            self._itens.append(item)
    
    @property
    def itens(self) -> tuple[Item, ...]:
        return tuple(self._itens)  # imutável
```

### N - No abbreviations (One Dot per Line)

**Regra**: Evitar **encadeamento excessivo** (Lei de Deméter). Máximo 1 ponto por linha.

❌ **Ruim** (muitos pontos):
```python
cliente.endereco.cidade.estado.pais.nome
```

✅ **Bom** (delegação):
```python
cliente.obter_pais()  # delega internamente
```

### I - Interfaces (Keep All Entities Small)

**Regra**: Classes pequenas (< 200 linhas). Métodos pequenos (< 15 linhas).

❌ **Ruim** (classe gigante):
```python
class PedidoService:
    def criar_pedido(...): pass  # 50 linhas
    def atualizar_pedido(...): pass  # 40 linhas
    def cancelar_pedido(...): pass  # 30 linhas
    def calcular_frete(...): pass  # 25 linhas
    def aplicar_desconto(...): pass  # 20 linhas
    def enviar_email(...): pass  # 30 linhas
    # ... 500 linhas no total
```

✅ **Bom** (classes focadas):
```python
class PedidoService:
    def criar_pedido(...): pass

class FreteService:
    def calcular_frete(...): pass

class DescontoService:
    def aplicar_desconto(...): pass

class EmailService:
    def enviar_email(...): pass
```

### Aplicação no Projeto

- **I (Indentação)**: Extrair loops e condicionais aninhados em métodos auxiliares
- **A (Avoid else)**: Usar early returns nos services e validators
- **G (Getters/Setters)**: Já usamos: `CPF`, `Email`, `Telefone`, `Dinheiro` são Value Objects
- **I (Immutability)**: Pydantic schemas são imutáveis por padrão (frozen=True quando necessário)
- **N (No abbreviations)**: Lei de Deméter: evitar `pedido.cliente.endereco.cep`, criar `pedido.obter_cep()`
- **I (Interfaces)**: Services com < 200 linhas, métodos com < 15 linhas

---

# Eficiência e Economia de Tokens

O objetivo é **executar tarefas rapidamente**, sem desperdício de tempo ou tokens. Evite criar artefatos desnecessários.

## ❌ NÃO Criar Automaticamente

A menos que **explicitamente solicitado** pelo usuário, **NÃO crie**:

### 1. Documentação Redundante
- ❌ Arquivos `.md` resumindo mudanças já documentadas no commit
- ❌ Changelogs manuais (use `git log` ou ferramentas automáticas)
- ❌ Documentos de "análise" antes de fazer mudanças simples
- ❌ README para features triviais
- ❌ Documentos temporários com sufixos: `_TEMP.md`, `_WIP.md`, `_DRAFT.md`
- ❌ Documentos de bugfix: `BUGFIX_*.md`, `FIX_*.md`
- ❌ Documentos de auditoria temporários: `AUDITORIA_*.md`
- ❌ Documentos de resumo: `RESUMO_*.md`, `FINAL_*.md`
- ❌ Documentos de teste: `TESTAR_*.md`, `COMO_TESTAR_*.md`

**Exceções**: Documentação de APIs públicas, guias de setup, arquitetura complexa.

### ⚠️ POLÍTICA DE LIMPEZA IMPLEMENTADA (Jun/2026)

O projeto adota **política de documentação limpa**:

1. **Zero Changelogs**: `git log` é a fonte da verdade
2. **Zero Temporários**: Docs temporários são deletados após uso
3. **Zero Archives**: Docs obsoletos são deletados, não arquivados
4. **Graphify Otimizado**: Apenas código e docs essenciais são indexados

### 2. Scripts Desnecessários
- ❌ Scripts bash/PowerShell para tarefas de uma linha
- ❌ Wrappers ao redor de comandos Docker já simples
- ❌ Scripts de "deploy" que só rodam `docker-compose up`

**Exceções**: Automação de processos multi-step, CI/CD pipelines.

### 3. Arquivos de Configuração Excessivos
- ❌ Configs separados para cada ambiente quando `.env` basta
- ❌ JSON/YAML com valores default óbvios
- ❌ Arquivos de "exemplo" quando a doc inline já explica

**Exceções**: Configs de CI/CD, Docker, Kubernetes, ferramentas de build.

### 4. Código Boilerplate
- ❌ Classes abstratas "para futuras extensões" sem uso concreto
- ❌ Interfaces genéricas sem múltiplas implementações
- ❌ Logs excessivos em todas as linhas
- ❌ Try/catch genéricos "por precaução"

**Exceções**: Padrões já estabelecidos no projeto (Repository, Service, etc.).

## ✅ Priorize Ação Direta

### Fluxo Recomendado

1. **Entenda o pedido** → clarifica apenas se realmente ambíguo
2. **Execute a mudança** → faça diretamente, sem "propor" se o pedido é claro
3. **Verifique** → rode builds, testes, linters
4. **Commit** → mensagem descritiva, sem criar `.md` explicativo

### Exemplos

❌ **Fluxo ineficiente** (desperdiça tokens):
```
User: "Adiciona validação de CPF no cadastro de cliente"

AI:
1. Cria arquivo: docs/VALIDACAO_CPF_ANALISE.md
2. Cria arquivo: docs/VALIDACAO_CPF_IMPLEMENTACAO.md
3. Cria script: scripts/validate_cpf.sh
4. Implementa a validação
5. Cria arquivo: docs/VALIDACAO_CPF_CHANGELOG.md
6. Pergunta: "Quer que eu crie testes?"
```

✅ **Fluxo eficiente** (direto ao ponto):
```
User: "Adiciona validação de CPF no cadastro de cliente"

AI:
1. Implementa validator em shared/validators/cpf.py
2. Integra no schema de cliente
3. Testa manualmente com Invoke-WebRequest
4. Responde: "Validação de CPF implementada e testada. Rodando no endpoint POST /clientes.
   
   Sugestão de commit: feat(clientes): add CPF validation"
```

## 📋 Quando Documentar

**Crie documentação apenas quando**:

1. **Arquitetura complexa**: Microserviços, fluxos OAuth, webhooks
2. **APIs externas**: Integrações com Mercado Pago, Google, Microsoft
3. **Setup não-trivial**: Docker multi-stage, túneis Cloudflare, migrações
4. **Decisões de design**: Por que escolhemos X em vez de Y (quando não óbvio)
5. **Solicitação explícita**: "Documenta isso em um .md"

**Formato recomendado**: markdown conciso, com exemplos práticos.

## 🚀 Princípio de Ação

**Default**: Implementar → Verificar → Responder

**Não pergunte** se pode fazer algo que foi claramente pedido.

**Não proponha** múltiplas opções se a melhor prática é óbvia.

**Não documente** se o código já é auto-explicativo.

**Não faça commits** automaticamente - deixe o controle do Git com o desenvolvedor. Apenas sugira a mensagem de commit apropriada na resposta.

---

# Git Commit Conventions

All commits must follow the **Conventional Commits** specification in **English**.

## Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

## Types

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes only |
| `style` | Formatting, missing semicolons, etc (no logic change) |
| `refactor` | Code change that is neither a fix nor a feature |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Build process, dependency updates, tooling |
| `ci` | CI/CD configuration changes |
| `revert` | Reverts a previous commit |

## Rules

- Subject line: max 72 characters, imperative mood, no period at the end
- Use English for type, scope, description, and body
- Scope is optional but recommended (e.g. `feat(auth)`, `fix(estoque)`, `docs(checklist)`)
- Body: explain *what* and *why*, not *how*

## Examples

```
feat(auth): add Google OAuth2 login support

fix(estoque): prevent negative stock on concurrent sales

docs(checklist): add backend quality and security section

refactor(clientes): extract CPF validation to shared validator

chore(docker): consolidate 8 postgres containers into one

perf(produtos): add composite indexes on empresa_id and ativo
```

---

# Graphify Knowledge Graph Management

## What is Graphify?

Graphify mantém um **grafo de conhecimento** do projeto em `graphify-out/`, mapeando:
- **Componentes**: arquivos, classes, funções, rotas
- **Relacionamentos**: imports, chamadas, dependências
- **Comunidades**: clusters de código relacionado

## 🎯 Uso Obrigatório do Graphify (ECONOMIZA TOKENS!)

**REGRA**: Antes de ler arquivos ou fazer `grep_search` para entender o código, **SEMPRE consulte o Graphify primeiro**.

### ❌ Fluxo ERRADO (desperdiça tokens):

```
User: "Como funciona o módulo de vendas?"

AI:
1. read_file('services/vendas/main.py')           # 500 linhas
2. read_file('services/vendas/routers/venda.py')  # 300 linhas
3. read_file('services/vendas/services/venda_service.py')  # 400 linhas
4. grep_search('class Venda')                     # 50 matches
5. read_file('services/vendas/models/venda.py')   # 200 linhas
6. ... consome 10k+ tokens lendo arquivos
```

### ✅ Fluxo CORRETO (economiza 90% dos tokens):

```
User: "Como funciona o módulo de vendas?"

AI:
1. graphify query "módulo de vendas"
   # Retorna: subgrafo focado com ~500 tokens
   # - Classes principais: Venda, VendaService, VendaRepository
   # - Relacionamentos: VendaService → VendaRepository → Venda
   # - Dependências: depends on Produto, Cliente, Estoque
   
2. Se precisar de detalhes específicos, lê APENAS os arquivos relevantes identificados
3. Responde ao usuário
```

**Economia**: ~9.500 tokens (95% de redução)

## 📋 Comandos do Graphify

### 1. `graphify query "<pergunta>"`
**Uso**: Perguntas gerais sobre arquitetura, componentes, funcionalidades

```bash
# Exemplos de queries eficientes
graphify query "como funciona a autenticação?"
graphify query "quais serviços dependem do banco de dados?"
graphify query "estrutura do módulo de vendas"
graphify query "fluxo de criação de pedido"
graphify query "onde é usado o CPF?"
```

**Retorno**: Subgrafo focado com nós e relacionamentos relevantes (~200-800 tokens)

### 2. `graphify path "<Componente A>" "<Componente B>"`
**Uso**: Entender como dois componentes se conectam

```bash
# Exemplos
graphify path "VendaService" "EstoqueService"
graphify path "AuthRouter" "Usuario"
graphify path "ProdutoRepository" "database"
```

**Retorno**: Caminho(s) de dependência entre componentes (~100-300 tokens)

### 3. `graphify explain "<conceito>"`
**Uso**: Explicação detalhada de um componente específico

```bash
# Exemplos
graphify explain "VendaService"
graphify explain "oauth2_scheme"
graphify explain "calculate_frete"
```

**Retorno**: Detalhes do componente (métodos, dependências, uso) (~200-500 tokens)

## 🚦 Quando Usar Cada Abordagem

### Situação 1: Pergunta Arquitetural
```
User: "Quais serviços temos no projeto?"
User: "Como está organizado o backend?"
User: "Qual a estrutura de microserviços?"

✅ Ação: graphify query "<pergunta>"
❌ NÃO: ler múltiplos arquivos aleatoriamente
```

### Situação 2: Entender Fluxo/Feature
```
User: "Como funciona o checkout?"
User: "Explica o fluxo de autenticação"
User: "Como é processado um pedido?"

✅ Ação: 
1. graphify query "fluxo de <feature>"
2. Se necessário detalhes de implementação: read_code dos arquivos específicos
❌ NÃO: ler todos os arquivos relacionados sem filtro
```

### Situação 3: Dependências entre Componentes
```
User: "O que depende do EstoqueService?"
User: "Quais rotas usam autenticação?"
User: "Onde o ValidadorCPF é usado?"

✅ Ação: graphify query "dependências de <componente>"
❌ NÃO: grep_search seguido de leitura de todos os matches
```

### Situação 4: Implementação Específica
```
User: "Muda a validação do campo email no ClienteService"
User: "Corrige o bug na linha 45 do venda_service.py"
User: "Adiciona log no método create_pedido"

✅ Ação: read_code/read_file direto (você já sabe o arquivo exato)
❌ NÃO: usar Graphify para mudanças pontuais em arquivo conhecido
```

### Situação 5: Primeira vez no Projeto
```
User: "Adiciona uma feature X no módulo Y que eu não conheço"

✅ Ação:
1. graphify query "módulo Y"  # Entende estrutura
2. graphify explain "ComponentePrincipalY"  # Detalhes
3. read_code apenas dos arquivos que você vai modificar
❌ NÃO: ler toda a pasta do módulo Y
```

## 🎯 Decisão Rápida: Graphify ou Read?

| Pergunta para si mesmo | Resposta | Ação |
|------------------------|----------|------|
| "Preciso entender a arquitetura/estrutura?" | Sim | `graphify query` |
| "Preciso saber como componentes se conectam?" | Sim | `graphify path` |
| "Preciso de visão geral de um componente?" | Sim | `graphify explain` |
| "Já sei exatamente qual arquivo modificar?" | Sim | `read_code/read_file` |
| "É uma mudança pontual (1-2 arquivos)?" | Sim | `read_code/read_file` |
| "Preciso debugar código linha por linha?" | Sim | `read_file` com line ranges |

## 📊 Métricas de Economia

**Exemplo real do projeto RunasERP**:

| Abordagem | Tokens Gastos | Tempo |
|-----------|---------------|-------|
| ❌ Ler 10 arquivos do módulo vendas | ~8.000 tokens | Alto |
| ✅ `graphify query "módulo de vendas"` | ~500 tokens | Baixo |
| **Economia** | **93.75%** | **10x mais rápido** |

---

| Abordagem | Tokens Gastos | Tempo |
|-----------|---------------|-------|
| ❌ `grep_search "VendaService"` + ler todos matches | ~5.000 tokens | Alto |
| ✅ `graphify explain "VendaService"` | ~300 tokens | Baixo |
| **Economia** | **94%** | **8x mais rápido** |

## 🚨 Red Flags - Use Graphify!

Se você estiver fazendo isso, **PARE e use Graphify**:

- ❌ Lendo 5+ arquivos para "entender o contexto"
- ❌ Fazendo `grep_search` seguido de múltiplos `read_file`
- ❌ Lendo `main.py`, `__init__.py`, routers, services sequencialmente
- ❌ "Explorando" uma pasta nova lendo arquivo por arquivo
- ❌ Tentando mapear dependências manualmente

**Resposta correta**: "Vou consultar o Graphify primeiro para economizar tokens."

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

### ❌ NÃO precisa rodar manualmente

```powershell
# ❌ NÃO FAÇA ISSO (o GitHub Actions já faz)
git commit -m "feat(vendas): add order tracking"
graphify update  # ← Desnecessário!
git add graphify-out/
git commit -m "chore(graphify): update"
```

## 🔍 Quando Rodar Manualmente

Apenas em casos especiais:

### 1. Desenvolvimento Local (antes de commitar)
```powershell
# Para testar queries antes do commit
graphify update
graphify query "como funciona o módulo de vendas?"
```

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

**Workflow**: `.github/workflows/graphify-update.yml`

**Gatilhos**:
- Push para `main`, `master`, ou `Developer`
- Mudanças em arquivos: `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.vue`

**Proteções**:
- ❌ Não roda se o commit contém `[skip graphify]` (evita loops)
- ❌ Não roda se não houver mudanças em código
- ✅ Commit automático feito por `github-actions[bot]`

**Processo**:
1. Detecta mudanças em código
2. Roda `graphify update`
3. Commita: `chore(graphify): auto-update knowledge graph [skip graphify]`
4. Faz push automático

## 🎯 Quando o GitHub Actions NÃO atualiza

- ❌ Commits apenas de documentação (`.md` files)
- ❌ Commits de configuração (`.env`, `docker-compose.yml`)
- ❌ Commits de assets (imagens, fontes)
- ❌ Commits de dados (seeds, migrations)

Nesses casos, o workflow não é disparado (por design).

## 💡 AI Assistant Usage

O Kiro AI usa o Graphify para responder perguntas sobre o código:

```
# Exemplos de queries que usam o Graphify
"Quais componentes dependem do módulo de vendas?"
"Mostre o fluxo de autenticação"
"Qual a estrutura do serviço de produtos?"
```

**⚠️ IMPORTANTE**: Se o grafo estiver desatualizado localmente, aguarde o GitHub Actions completar ou rode `graphify update` manualmente.

## 📈 Status do Grafo Atual

- **Nós**: ~9.432 componentes
- **Edges**: ~12.236 relacionamentos
- **Comunidades**: ~706 clusters
- **Última atualização**: Verificar `graphify-out/.graphify_root`
- **Atualização**: Automática via GitHub Actions
