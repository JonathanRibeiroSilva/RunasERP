---
paths:
  - "tests/**"
  - "**/tests/**/*.py"
  - "**/test_*.py"
  - ".github/workflows/ci.yml"
---

# Testes de backend — as duas pernas do CI

O CI (`.github/workflows/ci.yml`) roda exatamente duas pernas. Rode essas duas; o resto não é o que o gate checa.

```bash
# Perna 1 — suíte unitária, a partir da raiz do repo. Nenhum serviço precisa estar de pé.
pip install -r tests/requirements.txt
pytest -c tests/pytest.ini tests/unit
pytest -c tests/pytest.ini tests/unit/test_tenant_guards.py -v   # um arquivo

# Perna 2 — por serviço, a partir do diretório do próprio serviço (matriz de 8 no CI:
# api-gateway + os 7 serviços). Cada serviço importa "plano" (`from main import app`),
# então dois serviços no mesmo processo do pytest brigam por sys.path.
cd services/<nome>            # ou cd api-gateway
# O caminho de tests/requirements.txt é relativo a onde você está: ../../tests a partir de
# services/<nome>, ../tests a partir de api-gateway. O CI contorna com
# $GITHUB_WORKSPACE/tests/requirements.txt.
pip install -r requirements.txt -r ../../tests/requirements.txt
pytest tests
```

**Nunca rode `pytest` puro na raiz.** `tests/pytest.ini` tem `testpaths = tests`, e os arquivos soltos direto em `tests/` são scripts manuais, fora do gate: `test_produtos_api.py` chama um `localhost:8002` real (falha com nada de pé); `test_produtos_local.py` e `test_estrutura_simples.py` executam código no nível do módulo contra `services/produtos` (importam os models e dão `sys.exit(1)` na falha), então a coleta quebra.

## As duas pernas têm capacidades opostas — leia antes de escrever um teste

Não são o mesmo ambiente, e um teste escrito para uma quase sempre quebra na outra:

| | Perna 1 — `tests/unit` | Perna 2 — `<serviço>/tests` |
|---|---|---|
| config do pytest | `tests/pytest.ini`, `asyncio_mode = auto` | **nenhuma**: sem `pytest.ini`, `pyproject.toml` nem `setup.cfg` em serviço algum |
| testes async | `async def` simples funciona | modo strict: precisa de `@pytest.mark.asyncio` explícito |
| fastapi / sqlalchemy | **ausentes**: `tests/requirements.txt` não tem nenhum dos dois | presentes, vindos do `requirements.txt` do serviço |

Consequências:

- Um arquivo em `tests/unit` que importa o `main.py` de um serviço (ou qualquer coisa que puxe FastAPI/SQLAlchemy) **quebra a coleta da perna inteira**, não só ele. Os testes unitários de lá leem código-fonte, interpretam compose/YAML e afirmam sobre estrutura; não importam os apps.
- Um arquivo em `<serviço>/tests` com `async def test_...` sem marcador **não roda** no modo strict. Todo teste async existente nesses diretórios leva o `@pytest.mark.asyncio`; copie isso, não confie no modo auto.
