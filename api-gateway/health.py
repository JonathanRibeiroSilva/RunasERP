"""Agregação do readiness check.

Módulo à parte e sem imports pesados de propósito: o gate do CI roda
`pytest -c tests/pytest.ini tests/unit` com apenas pytest+httpx+yaml instalados,
e importar main.py de lá puxaria fastapi e sqlalchemy, que não existem naquele
ambiente. Aqui fica só a decisão; as sondas ficam em main.py.
"""

SERVICE_NAMES = (
    "empresas",
    "clientes",
    "produtos",
    "estoque",
    "vendas",
    "financeiro",
    "notificacoes",
)


def summarize(checks):
    """Traduz a lista de sondas em (status HTTP, corpo).

    503 nomeando quem caiu, não 200 com um campo dizendo que caiu: a sonda
    externa só olha o código de status, e um 200 degradado não dispara alarme
    nenhum — que é exatamente como /health passou meses verde com o backend
    inteiro invisível.
    """
    down = sorted(c["name"] for c in checks if c["status"] != "up")
    return (
        503 if down else 200,
        {
            "status": "degraded" if down else "healthy",
            "down": down,
            "checks": list(checks),
        },
    )
