# Transações de Banco de Dados

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Conceitos ACID](#conceitos-acid)
- [Modelo de Banco e Migrations](#modelo-de-banco-e-migrations)
- [Auditoria em Banco](#auditoria-em-banco)
- [Implementação no Projeto](#implementação-no-projeto)
- [Padrões de Uso](#padrões-de-uso)
- [Exemplos Práticos](#exemplos-práticos)
- [Boas Práticas](#boas-práticas)
- [Troubleshooting](#troubleshooting)

---

## Visão Geral

O sistema Runas ERP implementa **transações atômicas** em todas as operações de banco de dados para garantir a integridade e consistência dos dados. Utilizamos SQLAlchemy com suporte assíncrono para gerenciar transações de forma eficiente.

### Por que Transações são Importantes?

Em um sistema ERP, operações como:
- **Entrada de estoque** (criar movimentação + atualizar quantidade + criar lote)
- **Venda de produto** (criar venda + baixar estoque + gerar financeiro)
- **Ajuste de inventário** (registrar movimentação + atualizar quantidade)

Precisam ser **atômicas**: ou todas as operações são concluídas com sucesso, ou nenhuma é aplicada.

---

## Conceitos ACID

Nossas transações seguem os princípios ACID:

### 🔹 Atomicidade
Todas as operações dentro de uma transação são executadas como uma unidade indivisível.

```python
# ✅ Correto: Tudo ou nada
async with db.begin_nested():
    movimentacao = await criar_movimentacao(...)
    estoque = await atualizar_estoque(...)
    lote = await criar_lote(...)
# Se qualquer operação falhar, TODAS são revertidas
```

### 🔹 Consistência
O banco de dados passa de um estado válido para outro estado válido.

```python
# Antes: estoque.quantidade = 100
# Operação: saída de 30 unidades
# Depois: estoque.quantidade = 70
# ✅ Estado sempre consistente
```

### 🔹 Isolamento
Transações concorrentes não interferem entre si.

```python
# SQLAlchemy gerencia locks automaticamente
# Duas vendas simultâneas do mesmo produto não causam inconsistência
```

### 🔹 Durabilidade
Uma vez confirmada (commit), a transação persiste mesmo em caso de falha do sistema.

```python
await db.commit()  # Dados persistidos permanentemente
```

---

## Modelo de Banco e Migrations

### Um Postgres, um schema por aplicação

Não existe um banco por serviço: existe **um único Postgres** com **um schema
por aplicação**. Os schemas são criados por `postgres/init-schemas.sql`:

```sql
CREATE SCHEMA IF NOT EXISTS gateway;
CREATE SCHEMA IF NOT EXISTS empresas;
CREATE SCHEMA IF NOT EXISTS clientes;
CREATE SCHEMA IF NOT EXISTS produtos;
CREATE SCHEMA IF NOT EXISTS estoque;
CREATE SCHEMA IF NOT EXISTS vendas;
CREATE SCHEMA IF NOT EXISTS financeiro;
CREATE SCHEMA IF NOT EXISTS notificacoes;
CREATE SCHEMA IF NOT EXISTS evolution;
```

São nove schemas para oito aplicações: os sete serviços, o `api-gateway`
(schema `gateway`) e o `evolution`, que é a Evolution API e não um serviço
deste repositório. O mesmo script concede `GRANT ALL` e `ALTER DEFAULT
PRIVILEGES` (tabelas e sequences) ao usuário `erp` em cada schema.

O isolamento é garantido no engine: cada aplicação fixa o `search_path` para o
schema dela na criação da conexão.

```python
# services/estoque/database.py:19 (idêntico nos outros, trocando o schema)
engine = create_async_engine(
    settings.DATABASE_URL,
    ...
    connect_args={"server_settings": {"search_path": "estoque,public"}}
)
```

| Aplicação | Arquivo | `search_path` |
|-----------|---------|---------------|
| api-gateway | `api-gateway/database.py:20` | `gateway,public` |
| empresas | `services/empresas/database.py:19` | `empresas,public` |
| clientes | `services/clientes/database.py:19` | `clientes,public` |
| produtos | `services/produtos/database.py:19` | `produtos,public` |
| estoque | `services/estoque/database.py:19` | `estoque,public` |
| vendas | `services/vendas/database.py:19` | `vendas,public` |
| financeiro | `services/financeiro/database.py:19` | `financeiro,public` |
| notificacoes | `services/notificacoes/database.py:19` | `notificacoes,public` |

### Oito Alembics independentes

Cada uma das 8 aplicações tem o seu próprio diretório `alembic/` e a sua
própria tabela de versão, gravada **dentro do schema da aplicação** via
`version_table_schema`. Não há histórico de migration compartilhado e não há
ordem de boot garantida entre os serviços.

```python
# services/empresas/alembic/env.py:57 e :69
context.configure(
    ...
    version_table_schema="empresas",
    include_schemas=False,  # Apenas schema empresas
)
```

O mesmo padrão aparece em `api-gateway/alembic/env.py:57` (`gateway`) e nos
`services/<serviço>/alembic/env.py` (linhas 33 e 53) de clientes, estoque,
financeiro, notificacoes, produtos e vendas.

### As migrations rodam no boot, como subprocesso

O `init_db()` de cada aplicação executa `alembic upgrade head` **antes de a
aplicação atender tráfego**. É subprocesso, não a API Python do Alembic, porque
`alembic/env.py` chama `fileConfig()` e substituiria a configuração de logging
do app em execução.

```python
# services/empresas/database.py — init_db()
if not [p for p in Path("alembic/versions").glob("*.py") if p.name != "__init__.py"]:
    raise RuntimeError(
        "alembic/versions/ sem revisions: a imagem foi construída sem as "
        "migrations (verifique o .dockerignore deste serviço)"
    )
await asyncio.to_thread(
    subprocess.run, ["alembic", "upgrade", "head"], check=True
)
```

O guard existe porque `alembic upgrade head` **sai com código 0 quando não
encontra revision nenhuma** — indistinguível de "já está no head". Uma linha no
`.dockerignore` excluiu `alembic/versions/*.py` da imagem e o serviço subiu
saudável, com `/health` em 200 e zero tabelas, até o login falhar com 403 três
camadas adiante. Com o guard, esse caso derruba o processo no boot em vez de
servir um banco vazio.

Esse par (guard + `alembic upgrade head` em subprocesso) está presente nos 8
`database.py`: os 7 serviços e o `api-gateway`.

> **Consequência prática:** uma revision nova roda no boot do container. Uma
> migration que falha — uma constraint que não passa nos dados existentes, por
> exemplo — significa crashloop, não deploy degradado.

---

## Auditoria em Banco

A auditoria vive no schema `gateway` e tem dois níveis:

| Objeto | O que guarda |
|--------|--------------|
| `gateway.auditoria` | Trilha de intenção, gravada pelo middleware do gateway: `usuario_id`, `empresa_id`, `metodo`, `rota`, `payload`, `status_resposta`, `criado_em` |
| `gateway.auditoria_registros` | Snapshot de estado: `schema_origem`, `tabela`, `registro_id`, `empresa_id`, `operacao`, `dados_antes`, `dados_depois`, `revertido_em`, `criado_em` |
| `gateway.auditar_registro()` | Função de trigger `plpgsql` que preenche `auditoria_registros` a partir de `OLD`/`NEW` |

A trilha diz quem e quando; só o snapshot diz o quê — é ele que torna o
rollback possível.

As duas tabelas, seus índices e a função de trigger **não** nascem de uma
migration de serviço. A função é compartilhada, e sete Alembics independentes
não têm ordem de boot garantida entre si. Ela é criada em dois lugares, que
**precisam andar juntos**:

1. `postgres/init-schemas.sql` — roda na primeira inicialização do container do
   Postgres.
2. O `db-init` inline em `docker-compose.prod.yml:168-237` — idempotente, roda a
   cada deploy.

As duas cópias são o mesmo SQL, e cada uma carrega o comentário "Mantenha em
sincronia com o db-init do docker-compose.prod.yml". Alterar uma sem a outra
produz um ambiente onde o trigger existe e a função não.

As migrations por serviço só fazem `CREATE TRIGGER` apontando para a função já
existente — arquivo `alembic/versions/20260828_120000_auditoria.py` em
api-gateway, clientes, empresas, estoque, produtos e vendas. Financeiro e
notificacoes não têm essa migration.

---

## Implementação no Projeto

### Configuração Base

Todos os serviços utilizam a mesma configuração de sessão:

```python
# database.py
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Objetos permanecem acessíveis após commit
    autocommit=False,        # Transações manuais
    autoflush=False          # Controle manual de flush
)
```

### Estrutura de Camadas

```
┌─────────────────────────────────────────┐
│           ROUTER (FastAPI)              │
│  - Recebe requisição                    │
│  - Injeta sessão DB                     │
│  - Trata exceções HTTP                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            SERVICE LAYER                │
│  - Lógica de negócio                    │
│  - Gerencia transações (begin/commit)   │
│  - Trata exceções de negócio            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         REPOSITORY LAYER                │
│  - Operações de banco de dados          │
│  - Queries SQL                          │
│  - Não gerencia transações              │
└─────────────────────────────────────────┘
```

### Responsabilidades

| Camada | Responsabilidade | Transações |
|--------|------------------|------------|
| **Router** | Validação HTTP, injeção de dependências | ❌ Não gerencia |
| **Service** | Lógica de negócio, validações, transações | ✅ **Gerencia aqui** |
| **Repository** | Operações CRUD, queries | ❌ Não gerencia |

---

## Padrões de Uso

### Padrão 1: Transação Simples (Operação Única)

Para operações que envolvem apenas uma ação no banco:

```python
async def criar_categoria(self, dados: CategoriaCreate):
    """Cria uma nova categoria com transação atômica."""
    try:
        async with self.session.begin_nested():
            # Validações
            existente = await self.repo.obter_por_nome(dados.nome)
            if existente:
                raise ValueError(f"Categoria '{dados.nome}' já existe")
            
            # Operação
            categoria = await self.repo.criar(
                nome=dados.nome, 
                descricao=dados.descricao
            )
        
        # Commit da transação principal
        await self.session.commit()
        return categoria
        
    except ValueError:
        await self.session.rollback()
        raise
    except Exception:
        await self.session.rollback()
        raise
```

### Padrão 2: Transação Complexa (Múltiplas Operações)

Para operações que envolvem múltiplas ações que devem ser atômicas:

```python
async def entrada_estoque(
    db: AsyncSession,
    data: EntradaEstoqueRequest,
    usuario_id: Optional[UUID] = None
) -> Tuple[EstoqueResponse, Optional[UUID]]:
    """Registra entrada de estoque com transação atômica."""
    try:
        async with db.begin_nested():
            # 1. Buscar ou criar estoque
            estoque = await EstoqueRepository.buscar_por_produto(
                db, data.produto_id, data.variante_id
            )
            
            if not estoque:
                estoque = await EstoqueRepository.criar(
                    db,
                    produto_id=data.produto_id,
                    variante_id=data.variante_id,
                    quantidade=0.0,
                    estoque_minimo=0.0
                )
            
            # 2. Registrar movimentação
            quantidade_anterior = estoque.quantidade
            quantidade_posterior = quantidade_anterior + data.quantidade
            
            movimentacao = await MovimentacaoRepository.criar(
                db,
                estoque_id=estoque.id,
                tipo=TipoMovimentacao.ENTRADA.value,
                quantidade=data.quantidade,
                quantidade_anterior=quantidade_anterior,
                quantidade_posterior=quantidade_posterior,
                motivo=data.motivo,
                observacao=data.observacao,
                documento=data.documento,
                custo_unitario=data.custo_unitario,
                usuario_id=usuario_id
            )
            
            # 3. Atualizar quantidade
            estoque = await EstoqueRepository.atualizar_quantidade(
                db, estoque.id, quantidade_posterior
            )
            
            # 4. Criar lote se solicitado
            lote_id = None
            if data.criar_lote and data.codigo_lote:
                lote = await LoteRepository.criar(
                    db,
                    estoque_id=estoque.id,
                    codigo=data.codigo_lote,
                    quantidade=data.quantidade,
                    data_fabricacao=data.data_fabricacao,
                    data_validade=data.data_validade,
                    fornecedor=data.fornecedor,
                    nota_fiscal=data.nota_fiscal,
                    custo_unitario=data.custo_unitario
                )
                lote_id = lote.id
                
                # 5. Atualizar movimentação com lote
                movimentacao.lote_id = lote_id
        
        # Commit da transação principal
        await db.commit()
        
        log.info(
            "entrada_estoque",
            estoque_id=estoque.id,
            quantidade=data.quantidade,
            lote_id=lote_id
        )
        
        return EstoqueResponse.model_validate(estoque), lote_id
        
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        log.error("erro_entrada_estoque", error=str(e))
        raise
```

### Padrão 3: Router Simplificado

Os routers não gerenciam transações, apenas chamam os serviços:

```python
@router.post("/entrada", response_model=EstoqueResponse, status_code=201)
async def entrada_estoque(
    data: EntradaEstoqueRequest,
    db: AsyncSession = Depends(get_db)
):
    """Registra entrada de estoque."""
    try:
        estoque, lote_id = await EstoqueService.entrada_estoque(db, data)
        return estoque
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Exemplos Práticos

### Exemplo 1: Saída de Estoque com Validação

```python
@staticmethod
async def saida_estoque(
    db: AsyncSession,
    data: SaidaEstoqueRequest,
    usuario_id: Optional[UUID] = None
) -> EstoqueResponse:
    """Registra saída de estoque com transação atômica."""
    try:
        async with db.begin_nested():
            # Buscar estoque
            estoque = await EstoqueRepository.buscar_por_produto(
                db, data.produto_id, data.variante_id
            )
            if not estoque:
                raise ValueError("Estoque não encontrado")
            
            # Verificar disponibilidade
            if estoque.quantidade_disponivel < data.quantidade:
                raise ValueError(
                    f"Quantidade disponível insuficiente. "
                    f"Disponível: {estoque.quantidade_disponivel}, "
                    f"Solicitado: {data.quantidade}"
                )
            
            # Se especificou lote, verificar e atualizar
            if data.lote_id:
                lote = await LoteRepository.buscar_por_id(db, data.lote_id)
                if not lote or lote.estoque_id != estoque.id:
                    raise ValueError("Lote não encontrado")
                
                if lote.quantidade < data.quantidade:
                    raise ValueError(
                        f"Quantidade insuficiente no lote. "
                        f"Disponível: {lote.quantidade}"
                    )
                
                # Atualizar quantidade do lote
                await LoteRepository.atualizar_quantidade(
                    db, lote.id, lote.quantidade - data.quantidade
                )
            
            # Registrar movimentação
            quantidade_anterior = estoque.quantidade
            quantidade_posterior = quantidade_anterior - data.quantidade
            
            await MovimentacaoRepository.criar(
                db,
                estoque_id=estoque.id,
                lote_id=data.lote_id,
                tipo=TipoMovimentacao.SAIDA.value,
                quantidade=data.quantidade,
                quantidade_anterior=quantidade_anterior,
                quantidade_posterior=quantidade_posterior,
                motivo=data.motivo,
                observacao=data.observacao,
                documento=data.documento,
                usuario_id=usuario_id
            )
            
            # Atualizar quantidade
            estoque = await EstoqueRepository.atualizar_quantidade(
                db, estoque.id, quantidade_posterior
            )
        
        # Commit da transação principal
        await db.commit()
        
        log.info(
            "saida_estoque",
            estoque_id=estoque.id,
            quantidade=data.quantidade,
            lote_id=data.lote_id
        )
        
        return EstoqueResponse.model_validate(estoque)
        
    except ValueError:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        log.error("erro_saida_estoque", error=str(e))
        raise
```

### Exemplo 2: Criação de Variante com Atributos

```python
async def criar_variante(self, dados: VarianteCreate):
    """Cria uma nova variante com transação atômica."""
    try:
        async with self.session.begin_nested():
            # Validar produto
            produto = await self.produto_repo.obter_por_id(dados.produto_id)
            if not produto:
                raise ValueError(f"Produto não encontrado")

            # Verificar SKU único
            existente = await self.variante_repo.obter_por_sku(dados.sku)
            if existente:
                raise ValueError(f"SKU '{dados.sku}' já existe")

            # Validar preço
            if dados.preco_venda < dados.preco_custo:
                raise ValueError(
                    "Preço de venda não pode ser menor que preço de custo"
                )

            # Criar variante
            variante = await self.variante_repo.criar(
                produto_id=dados.produto_id,
                sku=dados.sku,
                preco_custo=dados.preco_custo,
                markup_pct=dados.markup_pct,
                preco_venda=dados.preco_venda,
            )

            # Criar atributos (cor, tamanho, etc.)
            for atributo in dados.atributos:
                await self.atributo_repo.criar(
                    variante_id=variante.id,
                    chave=atributo.chave,
                    valor=atributo.valor,
                )

            await self.session.flush()
        
        await self.session.commit()
        return variante
        
    except ValueError:
        await self.session.rollback()
        raise
    except Exception:
        await self.session.rollback()
        raise
```

---

## Boas Práticas

### ✅ DO (Faça)

1. **Sempre use `begin_nested()` para operações complexas**
   ```python
   async with db.begin_nested():
       # Múltiplas operações aqui
   ```

2. **Faça commit no service, não no router**
   ```python
   # Service
   await db.commit()
   
   # Router apenas chama o service
   return await service.criar_produto(dados)
   ```

3. **Trate exceções específicas primeiro**
   ```python
   except ValueError:
       await db.rollback()
       raise
   except Exception as e:
       await db.rollback()
       log.error("erro", error=str(e))
       raise
   ```

4. **Valide antes de modificar dados**
   ```python
   # Primeiro valida
   if estoque.quantidade < quantidade_solicitada:
       raise ValueError("Estoque insuficiente")
   
   # Depois modifica
   await atualizar_estoque(...)
   ```

5. **Use logging para rastreabilidade**
   ```python
   log.info("operacao_sucesso", estoque_id=estoque.id)
   log.error("operacao_falhou", error=str(e))
   ```

### ❌ DON'T (Não Faça)

1. **Não faça commit no repository**
   ```python
   # ❌ Errado
   async def criar(self, **kwargs):
       obj = Model(**kwargs)
       self.session.add(obj)
       await self.session.commit()  # ❌ Não!
   ```

2. **Não ignore exceções**
   ```python
   # ❌ Errado
   try:
       await operacao()
   except:
       pass  # ❌ Nunca ignore erros!
   ```

3. **Não misture lógica de negócio no repository**
   ```python
   # ❌ Errado - validação no repository
   async def criar_produto(self, dados):
       if dados.preco < 0:  # ❌ Validação deve estar no service
           raise ValueError("Preço inválido")
   ```

4. **Não use autocommit=True**
   ```python
   # ❌ Errado
   AsyncSessionLocal = async_sessionmaker(
       engine,
       autocommit=True  # ❌ Perde controle de transações
   )
   ```

5. **Não deixe transações abertas por muito tempo**
   ```python
   # ❌ Errado
   async with db.begin_nested():
       await operacao_rapida()
       await sleep(60)  # ❌ Não bloqueie a transação
       await outra_operacao()
   ```

---

## Troubleshooting

### Problema: Deadlock

**Sintoma:** Operações ficam travadas esperando umas pelas outras.

**Causa:** Duas transações tentando acessar os mesmos recursos em ordem diferente.

**Solução:**
```python
# Sempre acesse recursos na mesma ordem
# ✅ Correto: sempre produto → estoque → lote
async with db.begin_nested():
    produto = await buscar_produto(...)
    estoque = await buscar_estoque(...)
    lote = await buscar_lote(...)
```

### Problema: Dados não Persistidos

**Sintoma:** Operação parece funcionar mas dados não aparecem no banco.

**Causa:** Falta de `commit()` ou exceção silenciosa.

**Solução:**
```python
# Sempre faça commit explícito
async with db.begin_nested():
    await operacao()

await db.commit()  # ✅ Não esqueça!

# E sempre logue exceções
except Exception as e:
    log.error("erro", error=str(e))  # ✅ Rastreie erros
    raise
```

### Problema: Objetos Expirados

**Sintoma:** `DetachedInstanceError` ao acessar objetos após commit.

**Causa:** `expire_on_commit=True` (padrão do SQLAlchemy).

**Solução:**
```python
# Já configurado no projeto
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False  # ✅ Objetos permanecem acessíveis
)
```

### Problema: Transação Muito Longa

**Sintoma:** Timeouts ou locks prolongados.

**Causa:** Operações lentas dentro da transação.

**Solução:**
```python
# ❌ Errado
async with db.begin_nested():
    await operacao_db()
    await chamar_api_externa()  # ❌ Lento!
    await outra_operacao_db()

# ✅ Correto
# Primeiro faz chamadas externas
resultado_api = await chamar_api_externa()

# Depois abre transação rápida
async with db.begin_nested():
    await operacao_db()
    await usar_resultado(resultado_api)
    await outra_operacao_db()
```

---

## Serviços Implementados

Estado por serviço:

### ✅ Estoque
- `criar_estoque()`
- `entrada_estoque()`
- `saida_estoque()`
- `ajustar_estoque()`
- `reservar_estoque()`
- `liberar_reserva()`
- `atualizar_estoque()`

### ✅ Produtos
- `criar_categoria()`
- `atualizar_categoria()`
- `deletar_categoria()`
- `criar_produto()`
- `atualizar_produto()`
- `deletar_produto()`
- `criar_variante()`
- `atualizar_variante()`
- `deletar_variante()`

### ✅ Clientes
- `criar_cliente()`
- `atualizar_cliente()`
- `desativar_cliente()`
- `definir_credito()`
- `ajustar_credito()`
- `bloquear_cliente()`
- `desbloquear_cliente()`
- `adicionar_endereco()`
- `atualizar_endereco()`
- `remover_endereco()`

### ✅ Vendas

Implementado. `services/vendas/routers/` expõe 6 routers, todos registrados em
`services/vendas/main.py:94-99`: `vendas.py`, `loja.py` (loja online),
`webhook.py` (Mercado Pago), `admin_entrega.py`, `admin_pagamento.py` e
`admin_integracao.py`.

As transações atômicas ficam em `services/vendas/services/venda_service.py`, que
usa `async with db.begin_nested()` em:
- `criar_venda()`
- `atualizar_venda()`
- `separar_venda()`
- `entregar_venda()`
- `finalizar_venda()`
- `cancelar_venda()`

Outros serviços da pasta (`reserva_temporaria_service.py`, `loja_service.py`,
`mercadopago_service.py`, `entrega_service.py`, os de configuração) fazem
`await db.commit()` direto, sem `begin_nested()`.

### ⚪ Financeiro

Ainda não implementado. `services/financeiro/main.py` não tem nenhuma chamada a
`include_router`: só health check, CORS, o middleware `validar_token_interno` e
o handler global de exceções. `routers/`, `services/`, `models/`,
`repositories/` e `schemas/` contêm apenas `__init__.py`. Existe o Alembic do
serviço, com uma única revision de baseline
(`alembic/versions/20260919_baseline.py`).

---

## Referências

- [SQLAlchemy Async Transactions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncio-scoped-session)
- [FastAPI Database Dependencies](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [PostgreSQL Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)

---

**Última atualização:** 2026-09-26  
**Versão:** 1.1.0
