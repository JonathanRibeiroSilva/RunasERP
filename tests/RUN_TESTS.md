# Como Rodar os Testes - Runas ERP MVP

## Pré-requisitos

1. Serviços rodando: `docker-compose -f docker-compose.dev.yml up -d`
2. Instalar dependências: `pip install -r tests/requirements.txt`

## Comandos

```bash
# Todos os testes
pytest

# Apenas integração
pytest tests/integration/

# Apenas E2E
pytest tests/e2e/

# Com cobertura
pytest --cov=api-gateway --cov=services --cov-report=html

# Teste específico
pytest tests/integration/test_auth.py::TestAuth::test_login_admin_success -v
```

## Testes Prioritários para MVP

1. **Autenticação**: `pytest tests/integration/test_auth.py -v`
2. **Loja Online**: `pytest tests/integration/test_loja_online.py -v`
3. **Fluxo Venda**: `pytest tests/e2e/test_fluxo_venda.py -v`
