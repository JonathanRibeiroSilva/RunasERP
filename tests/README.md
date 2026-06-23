# Test Strategy - Runas ERP MVP

## Objetivo
Garantir cobertura de testes para os fluxos críticos do MVP, focando em:
- Autenticação e autorização
- CRUD de entidades principais
- Fluxos de negócio end-to-end
- Integração entre microsserviços

---

## Estrutura de Testes

```
tests/
├── README.md                          # Este arquivo
├── conftest.py                        # Fixtures compartilhadas (pytest)
├── pytest.ini                         # Configuração do pytest
├── requirements.txt                   # Dependências de teste
│
├── unit/                              # Testes unitários (sem dependências externas)
│   ├── test_validators.py
│   ├── test_schemas.py
│   └── test_utils.py
│
├── integration/                       # Testes de integração (com banco)
│   ├── test_auth.py                   # Autenticação (login, OAuth, tokens)
│   ├── test_empresas.py               # CRUD empresas
│   ├── test_clientes.py               # CRUD clientes
│   ├── test_produtos.py               # CRUD produtos + categorias
│   ├── test_estoque.py                # Movimentações de estoque
│   ├── test_vendas.py                 # Pedidos e pagamentos
│   └── test_loja_online.py            # Loja pública
│
├── e2e/                               # Testes end-to-end (fluxos completos)
│   ├── test_cadastro_empresa.py       # Criar empresa → usuário → seed
│   ├── test_fluxo_venda.py            # Produto → Estoque → Venda → Pagamento
│   └── test_fluxo_loja_online.py     # Vitrine → Carrinho → Checkout
│
└── performance/                       # Testes de carga (opcional para MVP)
    └── locustfile.py
```

---

## Prioridades para MVP

### ✅ Prioridade ALTA (Crítico para apresentação)

1. **Autenticação** (`test_auth.py`)
   - Login com email/senha
   - OAuth (Google/Microsoft)
   - Refresh tokens
   - Permissões (admin vs operador)

2. **Fluxo de Venda Completo** (`test_fluxo_venda.py`)
   - Criar produto
   - Adicionar ao estoque
   - Criar pedido
   - Processar pagamento (Mercado Pago sandbox)
   - Baixa no estoque
   - Geração de nota fiscal

3. **Loja Online Pública** (`test_loja_online.py`)
   - Listar produtos sem autenticação
   - Filtrar por categoria
   - Buscar por nome
   - Visualizar detalhes do produto

4. **Multi-tenancy** (em todos os testes)
   - Garantir isolamento de dados por empresa_id
   - Validar X-Empresa-Id header

### 🟡 Prioridade MÉDIA (Importante)

5. **CRUD Clientes** (`test_clientes.py`)
6. **CRUD Produtos** (`test_produtos.py`)
7. **Movimentações de Estoque** (`test_estoque.py`)
8. **CRUD Empresas** (`test_empresas.py`)

### 🟢 Prioridade BAIXA (Nice to have)

9. **Validadores** (`test_validators.py`)
10. **Performance** (`locustfile.py`)

---

## Comandos

```bash
# Rodar todos os testes
pytest

# Rodar testes com cobertura
pytest --cov=api-gateway --cov=services --cov-report=html

# Rodar apenas teste específico
pytest tests/integration/test_auth.py::test_login_success -v
```
