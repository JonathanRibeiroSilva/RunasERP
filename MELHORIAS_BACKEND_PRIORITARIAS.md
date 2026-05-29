# 🚀 Melhorias Prioritárias do Backend

> **Sugestões de melhorias para implementar ANTES de colocar em produção**
> 
> **Última atualização**: 27/05/2026
> **Status**: Sistema em desenvolvimento (44% completo, sem usuários reais)

---

## 🎯 Por que fazer AGORA?

✅ **Sem dados em produção**: Mudanças estruturais são fáceis  
✅ **Sem usuários**: Pode quebrar e testar à vontade  
✅ **Sem downtime**: Não precisa se preocupar com disponibilidade  
✅ **Arquitetura limpa**: Evita débito técnico futuro  

**Depois que entrar em produção, essas mudanças serão 10x mais difíceis!**

---

## 🔥 PRIORIDADE MÁXIMA (Próximas 2 semanas)

### 1. Multi-Tenant (Empresa ID)

**Por quê?**: Migrar depois é um pesadelo. Fazer agora é simples.

**Impacto**: 🔴 CRÍTICO - Afeta toda a arquitetura de dados

**Esforço**: 1-2 semanas

**O que fazer**:

1. Criar tabela `empresas`
2. Adicionar `empresa_id` em TODAS as tabelas
3. Criar middleware de isolamento
4. Atualizar todos os repositories para filtrar por `empresa_id`
5. Atualizar seeds e testes

**Benefícios**:
- ✅ Permite modelo SaaS
- ✅ Economia de 80% em hospedagem
- ✅ Manutenção centralizada
- ✅ Escalabilidade desde o início


---

### 2. Banco de Dados Unificado

**Por quê?**: 6 PostgreSQL containers = desperdício de recursos

**Impacto**: 🟡 ALTO - Economia de 400-500 MB RAM

**Esforço**: 4-6 horas

**O que fazer**:

1. Criar `init-schemas.sql` com 6 schemas
2. Atualizar `docker-compose.yml` para 1 PostgreSQL
3. Atualizar connection strings com `search_path`
4. Testar migrations em cada schema
5. Atualizar documentação

**Benefícios**:
- ✅ Economia de ~400 MB RAM
- ✅ Economia de ~15% CPU
- ✅ Backups mais simples
- ✅ Manutenção mais fácil

---

### 3. Auditoria e Logs Estruturados

**Por quê?**: Rastrear quem fez o quê é essencial para ERP

**Impacto**: 🟡 ALTO - Compliance e debugging

**Esforço**: 1 semana

**O que fazer**:

1. Criar tabela `audit_log`
2. Adicionar campos `criado_por`, `atualizado_por` em todas as tabelas
3. Implementar middleware de auditoria
4. Logar todas as operações de escrita (CREATE, UPDATE, DELETE)
5. Adicionar endpoint para consultar logs

**Estrutura sugerida**:

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[UUID] = ...
    empresa_id: Mapped[UUID] = ...  # Multi-tenant
    usuario_id: Mapped[UUID] = ...
    tabela: Mapped[str] = ...  # "clientes", "produtos", etc
    registro_id: Mapped[UUID] = ...  # ID do registro afetado
    acao: Mapped[str] = ...  # "CREATE", "UPDATE", "DELETE"
    dados_antes: Mapped[dict] = ...  # JSON com dados anteriores
    dados_depois: Mapped[dict] = ...  # JSON com dados novos
    ip_address: Mapped[str] = ...
    user_agent: Mapped[str] = ...
    criado_em: Mapped[datetime] = ...
```

**Benefícios**:
- ✅ Rastreabilidade completa
- ✅ Compliance (LGPD, auditoria fiscal)
- ✅ Debugging facilitado
- ✅ Histórico de alterações

---

### 4. Validação de CEP no Backend

**Por quê?**: Nunca confie apenas no frontend

**Impacto**: 🟢 MÉDIO - Segurança e integridade de dados

**Esforço**: 4-6 horas

**O que fazer**:

1. Criar serviço `ViaCepService`
2. Adicionar validação assíncrona no endpoint de endereços
3. Implementar fallback (se API cair, aceita mas loga warning)
4. Adicionar cache Redis para CEPs consultados
5. Adicionar testes


**Exemplo**:

```python
class ViaCepService:
    async def validar_cep(self, cep: str) -> dict | None:
        # Verificar cache Redis primeiro
        cached = await redis.get(f"cep:{cep}")
        if cached:
            return json.loads(cached)
        
        try:
            # Consultar ViaCEP
            response = await httpx.get(f"https://viacep.com.br/ws/{cep}/json/")
            data = response.json()
            
            if "erro" not in data:
                # Cachear por 30 dias
                await redis.setex(f"cep:{cep}", 2592000, json.dumps(data))
                return data
        except Exception as e:
            log.warning("viacep_falhou", cep=cep, error=str(e))
            # Fallback: aceita o CEP mas loga
            return None
```

**Benefícios**:
- ✅ Segurança (valida no backend)
- ✅ Integridade de dados
- ✅ Cache reduz chamadas à API
- ✅ Fallback evita bloqueios

---

## 🔥 PRIORIDADE ALTA (Próximas 4 semanas)

### 5. Soft Delete Consistente + Reativação Automática ⭐

> **📄 Documentação completa**: Ver `REGRA_SOFT_DELETE_REATIVACAO.md` na raiz do projeto

**Por quê?**: Alguns serviços têm, outros não. E falta lógica de reativação.

**Impacto**: 🟡 ALTO - Recuperação de dados e UX

**Esforço**: 1-2 dias

**Problema Atual**: 
- Se um cliente foi desativado (soft delete) e tentam cadastrar novamente com o mesmo CPF, o sistema retorna erro "CPF já cadastrado"
- O correto seria **reativar automaticamente** o cliente existente

**O que fazer**:

1. Adicionar campos `ativo` e `deletado_em` em TODAS as tabelas
2. Criar mixin `SoftDeleteMixin`
3. Atualizar todos os repositories
4. Adicionar filtro automático em queries
5. **Implementar lógica de reativação automática**
6. Criar endpoints para "restaurar" registros manualmente


**Exemplo**:

```python
class SoftDeleteMixin:
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    deletado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deletado_por: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

class Cliente(Base, SoftDeleteMixin):
    # ... campos do cliente
```

**Regra de Negócio Detalhada**:

### Consultas (GET) - Apenas Ativos
```python
# Todas as consultas retornam APENAS registros ativos
GET /clientes?nome=João          → Só clientes ativos
GET /clientes?cpf=12345678900    → Só clientes ativos
GET /clientes/:id                → Só se estiver ativo

# Clientes inativos ficam "invisíveis" no sistema
```

### Cadastro (POST) - Reativação Inteligente
```python
POST /clientes { cpf, nome, telefone, email }

Lógica:
1. Busca CPF (incluindo inativos)
2. Se NÃO existe → Cria novo cliente
3. Se existe e está ATIVO → Erro 409 "CPF já cadastrado"
4. Se existe e está INATIVO → Reativa + Atualiza APENAS dados cadastrais
```

### Campos que Atualizam vs Mantêm

**✅ ATUALIZAM (dados cadastrais podem ter mudado)**:
- Nome
- Telefone
- Email
- Data de nascimento
- Endereços

**❌ MANTÊM (dados financeiros/operacionais são históricos)**:
- Limite de crédito
- Crédito disponível
- Saldo devedor
- Dia de vencimento
- Status de bloqueio

**Por quê?**: Preserva histórico financeiro e relacionamentos (compras, pagamentos).

---

**Implementação**:

```python
# services/clientes/services/cliente_service.py
async def criar_cliente(self, data: ClienteCreate) -> Cliente:
    """
    Cria um novo cliente ou reativa um existente.
    
    Regras:
    - Se CPF não existe: cria novo cliente
    - Se CPF existe e está ATIVO: retorna erro "CPF já cadastrado"
    - Se CPF existe e está INATIVO: reativa e atualiza APENAS dados cadastrais
    """
    try:
        async with self.db.begin_nested():
            # Buscar cliente por CPF (incluindo inativos)
            cliente_existente = await self.cliente_repo.buscar_por_cpf(
                data.cpf, 
                incluir_inativos=True  # ← IMPORTANTE
            )
            
            if cliente_existente:
                # Se está ativo, retorna erro
                if cliente_existente.ativo:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="CPF já cadastrado"
                    )
                
                # Se está inativo, reativa e atualiza APENAS dados cadastrais
                log.info(
                    "cliente.reativando", 
                    cliente_id=str(cliente_existente.id),
                    cpf=data.cpf
                )
                
                cliente = await self.cliente_repo.reativar(
                    cliente_existente.id,
                    nome=data.nome,
                    telefone=data.telefone,
                    email=data.email,
                    data_nasc=data.data_nasc
                    # NÃO atualiza: limite_credito, credito_disponivel, etc
                )
                
                return cliente
            
            # CPF não existe, cria novo
            cliente = await self.cliente_repo.criar(data)
        
        await self.db.commit()
        log.info("cliente.criado", cliente_id=str(cliente.id), cpf=data.cpf)
        return cliente
        
    except HTTPException:
        await self.db.rollback()
        raise
    except Exception as e:
        await self.db.rollback()
        log.error("erro_criar_cliente", error=str(e))
        raise
```

```python
# repositories/cliente_repository.py
async def buscar_por_cpf(
    self, 
    cpf: str, 
    incluir_inativos: bool = False
) -> Cliente | None:
    """
    Busca cliente por CPF.
    
    Args:
        cpf: CPF do cliente
        incluir_inativos: Se True, busca também inativos
                         Se False, busca apenas ativos (padrão)
    """
    query = select(Cliente).where(Cliente.cpf == cpf)
    
    if not incluir_inativos:
        query = query.where(Cliente.ativo == True)
    
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

async def reativar(
    self, 
    cliente_id: UUID,
    nome: str,
    telefone: str,
    email: str | None,
    data_nasc: date | None
) -> Cliente:
    """
    Reativa cliente e atualiza APENAS dados cadastrais.
    Mantém dados financeiros intactos (limite_credito, credito_disponivel, etc).
    """
    cliente = await self.buscar_por_id(cliente_id)
    
    # Atualizar APENAS dados cadastrais
    cliente.nome = nome
    cliente.telefone = telefone
    cliente.email = email
    cliente.data_nasc = data_nasc
    
    # Reativar
    cliente.ativo = True
    cliente.deletado_em = None
    cliente.deletado_por = None
    
    # NÃO toca em dados financeiros:
    # - limite_credito (mantém)
    # - credito_disponivel (mantém)
    # - dia_vencimento (mantém)
    # - bloqueado (mantém)
    
    await self.db.flush()
    await self.db.refresh(cliente)
    
    return cliente
```

**Exemplo de Cenário**:

```python
# 1. Cliente foi desativado anteriormente
Estado anterior (inativo):
- cpf: "12345678900"
- nome: "João Silva"
- telefone: "(11) 11111-1111"
- limite_credito: 5000.00
- credito_disponivel: 2000.00
- ativo: false

# 2. Tentam cadastrar novamente com dados atualizados
POST /clientes {
  "cpf": "12345678900",
  "nome": "João Santos",  ← mudou (casou)
  "telefone": "(11) 99999-9999"  ← mudou
}

# 3. Sistema reativa e atualiza
Resultado:
- cpf: "12345678900"
- nome: "João Santos"  ← ATUALIZADO
- telefone: "(11) 99999-9999"  ← ATUALIZADO
- limite_credito: 5000.00  ← MANTIDO
- credito_disponivel: 2000.00  ← MANTIDO
- ativo: true  ← REATIVADO
- mesmo ID, mesmos relacionamentos preservados
```

**Benefícios**:
- ✅ Recuperação de dados deletados acidentalmente
- ✅ Auditoria (quem deletou e quando)
- ✅ Compliance (LGPD - direito ao esquecimento)
- ✅ **Melhor UX**: Reativa automaticamente ao invés de dar erro
- ✅ **Evita duplicação**: Não cria novo registro, reutiliza o existente
- ✅ **Mantém histórico**: Preserva ID e relacionamentos antigos
- ✅ **Preserva dados financeiros**: Limite de crédito, saldo devedor, etc.
- ✅ **Atualiza dados pessoais**: Telefone e email podem ter mudado

**Aplicar em**:
- ✅ Clientes (CPF único)
- ✅ Produtos (SKU único)
- ✅ Fornecedores (CNPJ único)
- ✅ Categorias (Nome único)
- ✅ Todos os cadastros principais

---

### 6. Índices de Banco de Dados

**Por quê?**: Performance vai degradar com volume de dados

**Impacto**: 🟡 ALTO - Performance

**Esforço**: 1 dia

**O que fazer**:

1. Analisar queries mais frequentes
2. Adicionar índices compostos estratégicos
3. Adicionar índices em foreign keys
4. Adicionar índices em campos de busca/filtro
5. Testar com dados de volume (seed com 10k+ registros)

**Índices sugeridos**:

```sql
-- Clientes
CREATE INDEX idx_clientes_empresa_ativo ON clientes(empresa_id, ativo);
CREATE INDEX idx_clientes_cpf ON clientes(cpf);
CREATE INDEX idx_clientes_nome ON clientes(nome);

-- Produtos
CREATE INDEX idx_produtos_empresa_ativo ON produtos(empresa_id, ativo);
CREATE INDEX idx_produtos_categoria ON produtos(categoria_id);
CREATE INDEX idx_produtos_nome ON produtos(nome);

-- Vendas (quando implementar)
CREATE INDEX idx_vendas_empresa_data ON vendas(empresa_id, data_venda);
CREATE INDEX idx_vendas_cliente ON vendas(cliente_id);
CREATE INDEX idx_vendas_status ON vendas(status);
```


**Benefícios**:
- ✅ Queries 10-100x mais rápidas
- ✅ Escalabilidade com volume
- ✅ Melhor experiência do usuário

---

### 7. Rate Limiting por Usuário/Empresa

**Por quê?**: Prevenir abuso e ataques

**Impacto**: 🟢 MÉDIO - Segurança

**Esforço**: 1 dia

**O que fazer**:

1. Implementar rate limiting por `usuario_id` e `empresa_id`
2. Usar Redis para contadores
3. Diferentes limites por tipo de operação
4. Retornar headers com limite restante
5. Adicionar whitelist para IPs confiáveis

**Exemplo**:

```python
# Limites sugeridos
RATE_LIMITS = {
    "default": "100/minute",
    "login": "5/minute",
    "cadastro": "10/minute",
    "consulta": "200/minute",
    "relatorio": "10/minute",
}
```

**Benefícios**:
- ✅ Proteção contra abuso
- ✅ Proteção contra DDoS
- ✅ Controle de custos (API externa)

---

### 8. Error Handlers Padronizados ⭐

> **📄 Documentação completa**: Ver `ERROR_HANDLING_GUIDE.md` na raiz do projeto

**Por quê?**: Retornar códigos HTTP corretos e mensagens claras

**Impacto**: 🟡 ALTO - Developer Experience e Debugging

**Esforço**: 1-2 dias

**O que fazer**:

1. Adicionar handlers específicos para cada exceção customizada
2. Adicionar handler para HTTPException do FastAPI
3. Melhorar handler global com request_id
4. Padronizar formato de resposta de erro
5. Adicionar logs estruturados por nível
6. Implementar em todos os microsserviços

**Benefícios**:
- ✅ Códigos HTTP corretos (400, 404, 409, 500)
- ✅ Mensagens claras para o frontend
- ✅ Código limpo (sem try/except em todo lugar)
- ✅ Rastreabilidade com request_id
- ✅ Segurança (não expõe stack traces)
- ✅ Debugging facilitado

---

### 9. Validações de Negócio Centralizadas

**Por quê?**: Evitar duplicação de lógica

**Impacto**: 🟢 MÉDIO - Manutenibilidade

**Esforço**: 2-3 dias

**O que fazer**:

1. Criar camada de `validators/` em cada serviço
2. Mover validações complexas dos endpoints para validators
3. Reutilizar validators em múltiplos lugares
4. Adicionar testes unitários para validators


**Exemplo**:

```python
# validators/cliente_validator.py
class ClienteValidator:
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        # Lógica de validação de CPF
        pass
    
    @staticmethod
    async def validar_credito_disponivel(
        cliente: Cliente, 
        valor_compra: Decimal
    ) -> bool:
        if cliente.bloqueado:
            raise ValidationError("Cliente bloqueado")
        
        if cliente.credito_disponivel < valor_compra:
            raise ValidationError("Crédito insuficiente")
        
        return True
```

**Benefícios**:
- ✅ Código mais limpo
- ✅ Reutilização de lógica
- ✅ Testes mais fáceis
- ✅ Manutenção centralizada

---

## 🟡 PRIORIDADE MÉDIA (Próximas 6-8 semanas)

### 10. Cache Estratégico com Redis

**Por quê?**: Reduzir carga no banco de dados

**Impacto**: 🟢 MÉDIO - Performance

**Esforço**: 1 semana

**O que fazer**:

1. Identificar dados que mudam pouco (categorias, configurações)
2. Implementar cache com TTL adequado
3. Invalidar cache em updates
4. Adicionar métricas de hit/miss

**Dados para cachear**:

```python
# Cache de longa duração (1 hora - 1 dia)
- Categorias de produtos
- Configurações do sistema
- Dados de empresas
- CEPs consultados

# Cache de curta duração (5-15 minutos)
- Lista de produtos ativos
- Estoque disponível
- Crédito disponível de clientes
```


**Benefícios**:
- ✅ Reduz 50-80% de queries ao banco
- ✅ Respostas mais rápidas
- ✅ Menor carga no PostgreSQL

---

### 11. Testes Automatizados

**Por quê?**: Confiança para fazer mudanças

**Impacto**: 🟡 ALTO - Qualidade

**Esforço**: 2-3 semanas (contínuo)

**O que fazer**:

1. Configurar pytest com fixtures
2. Testes unitários para services e validators
3. Testes de integração para endpoints
4. Testes de carga com Locust
5. CI/CD com GitHub Actions

**Meta de cobertura**:
- Services: 80%+
- Validators: 90%+
- Endpoints: 70%+

**Benefícios**:
- ✅ Confiança para refatorar
- ✅ Detecta bugs antes de produção
- ✅ Documentação viva do código
- ✅ Onboarding mais fácil

---

### 12. Documentação Swagger/OpenAPI

**Por quê?**: Frontend precisa saber como usar a API

**Impacto**: 🟢 MÉDIO - Developer Experience

**Esforço**: 1 semana

**O que fazer**:

1. Adicionar docstrings em todos os endpoints
2. Documentar schemas com exemplos
3. Documentar códigos de erro
4. Adicionar exemplos de requisições
5. Configurar Swagger UI

**Benefícios**:
- ✅ Frontend sabe exatamente o que esperar
- ✅ Testes manuais mais fáceis
- ✅ Onboarding de desenvolvedores
- ✅ Geração de clientes automática


---

### 13. Backup Automatizado

**Por quê?**: Dados são o ativo mais importante

**Impacto**: 🔴 CRÍTICO - Disaster Recovery

**Esforço**: 2-3 dias

**O que fazer**:

1. Script de backup diário do PostgreSQL
2. Upload para S3/Google Cloud Storage
3. Retenção: 7 dias diários, 4 semanais, 12 mensais
4. Testar restore regularmente
5. Alertas se backup falhar

**Exemplo**:

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h postgres -U runas runas_erp | gzip > backup_$DATE.sql.gz
aws s3 cp backup_$DATE.sql.gz s3://runas-backups/
```

**Benefícios**:
- ✅ Proteção contra perda de dados
- ✅ Recuperação de desastres
- ✅ Compliance

---

## 🟢 PRIORIDADE BAIXA (Futuro)

### 14. Event Sourcing para Auditoria

**Por quê?**: Rastreabilidade completa de mudanças

**Esforço**: 2-3 semanas

### 15. GraphQL como alternativa ao REST

**Por quê?**: Frontend pode pedir exatamente o que precisa

**Esforço**: 2-3 semanas

### 16. WebSockets para Notificações em Tempo Real

**Por quê?**: Melhor UX (notificações instantâneas)

**Esforço**: 1 semana

### 17. Filas de Processamento (Celery/RabbitMQ)

**Por quê?**: Processos longos não bloqueiam requisições

**Esforço**: 1-2 semanas

---

## 📋 Plano de Ação Sugerido

### Semana 1-2: Fundação
- [ ] Multi-Tenant (empresa_id)
- [ ] Banco de Dados Unificado
- [ ] Auditoria básica

### Semana 3-4: Segurança e Qualidade
- [ ] Validação de CEP no backend
- [ ] Soft Delete consistente + Reativação automática
- [ ] Índices de banco de dados
- [ ] Rate Limiting
- [ ] Error Handlers padronizados


### Semana 5-6: Performance e Manutenibilidade
- [ ] Validações centralizadas
- [ ] Cache estratégico
- [ ] Documentação Swagger
- [ ] Backup automatizado

### Semana 7-8: Testes e Refinamento
- [ ] Testes unitários (80% cobertura)
- [ ] Testes de integração
- [ ] Testes de carga
- [ ] CI/CD

---

## 💰 Custo vs Benefício

| Melhoria | Esforço | Impacto | ROI | Prioridade |
|----------|---------|---------|-----|------------|
| Multi-Tenant | 2 semanas | 🔴 Crítico | ⭐⭐⭐⭐⭐ | MÁXIMA |
| Banco Unificado | 6 horas | 🟡 Alto | ⭐⭐⭐⭐⭐ | MÁXIMA |
| Auditoria | 1 semana | 🟡 Alto | ⭐⭐⭐⭐ | MÁXIMA |
| Validação CEP | 6 horas | 🟢 Médio | ⭐⭐⭐⭐ | MÁXIMA |
| Soft Delete + Reativação | 2 dias | 🟡 Alto | ⭐⭐⭐⭐ | ALTA |
| Índices | 1 dia | 🟡 Alto | ⭐⭐⭐⭐⭐ | ALTA |
| Rate Limiting | 1 dia | 🟢 Médio | ⭐⭐⭐ | ALTA |
| Error Handlers | 2 dias | 🟡 Alto | ⭐⭐⭐⭐ | ALTA |
| Validators | 3 dias | 🟢 Médio | ⭐⭐⭐ | ALTA |
| Cache | 1 semana | 🟢 Médio | ⭐⭐⭐ | MÉDIA |
| Testes | 3 semanas | 🟡 Alto | ⭐⭐⭐⭐ | MÉDIA |
| Swagger | 1 semana | 🟢 Médio | ⭐⭐⭐ | MÉDIA |
| Backup | 3 dias | 🔴 Crítico | ⭐⭐⭐⭐⭐ | MÉDIA |

---

## 🎯 Recomendação Final

**Foque nas 4 primeiras melhorias (Prioridade MÁXIMA):**

1. ✅ **Multi-Tenant** - Fundamental para o futuro
2. ✅ **Banco Unificado** - Economia imediata de recursos
3. ✅ **Auditoria** - Compliance e rastreabilidade
4. ✅ **Validação CEP** - Segurança e integridade

**Total: ~3 semanas de trabalho**

Isso vai te dar:
- ✅ Sistema preparado para escalar
- ✅ Economia de 80% em hospedagem
- ✅ Compliance e auditoria
- ✅ Dados íntegros e seguros

**Depois disso, implemente as melhorias de Prioridade ALTA conforme necessidade.**

---

## 📞 Dúvidas?

Se precisar de ajuda para implementar qualquer uma dessas melhorias, é só pedir!

---

**Documento criado em**: 27/05/2026  
**Responsável**: Equipe de Backend  
**Próxima revisão**: Após implementação das melhorias prioritárias
