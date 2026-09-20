"""
Wiring de segurança do gateway: rate limiting, CORS.

Regression test puro de configuração — não sobe app real (sem banco/Redis),
só confere o que ficou registrado no FastAPI/slowapi no import. O bug que isto
evita: o Limiter existia mas nunca era plugado em nada (sem middleware, sem
handler, sem decorator em rota nenhuma) — `rtk gain`/CI nunca teriam pego isso
porque a app "funcionava" normalmente, só que sem limite algum.
"""
import os

# As settings do gateway exigem estas variáveis no import.
os.environ.setdefault("SECRET_KEY", "test-secret-key-super-secure-min-32-chars")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
for _servico in ("EMPRESAS", "CLIENTES", "PRODUTOS", "ESTOQUE", "VENDAS",
                 "FINANCEIRO", "NOTIFICACOES"):
    os.environ.setdefault(f"{_servico}_URL", f"http://{_servico.lower()}:8000")
os.environ.setdefault("FRONTEND_URL", "https://app.runaserp.com.br")

from slowapi.errors import RateLimitExceeded  # noqa: E402

import main  # noqa: E402
from middleware.rate_limit import limiter  # noqa: E402


def test_rate_limit_tem_teto_global():
    """default_limits vazio == o bug original: Limiter existe, nada usa."""
    assert limiter._default_limits


def test_slowapi_middleware_e_handler_registrados():
    nomes = [m.cls.__name__ for m in main.app.user_middleware]
    assert "SlowAPIMiddleware" in nomes
    assert RateLimitExceeded in main.app.exception_handlers


def test_cors_middleware_sai_por_fora_do_slowapi():
    """CORS precisa embrulhar o SlowAPI, senão um 429 sai sem header de CORS."""
    nomes = [m.cls.__name__ for m in main.app.user_middleware]
    assert nomes.index("CORSMiddleware") < nomes.index("SlowAPIMiddleware")


def test_cors_nao_aceita_qualquer_origem():
    cors = next(m for m in main.app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert "*" not in cors.kwargs["allow_origins"]


def test_rotas_sensiveis_tem_limite_proprio():
    limitadas = set(limiter._route_limits)
    for rota in (
        "routers.auth.login",
        "routers.auth.forgot_password",
        "routers.auth.reset_password",
        "routers.auth_cliente.login_cliente",
        "routers.auth_cliente.register_cliente",
    ):
        assert rota in limitadas, f"{rota} sem @limiter.limit"


def test_healthcheck_isento_do_rate_limit():
    """Sonda externa/Docker não pode nunca receber 429 de saúde do gateway."""
    assert "main.health_check" in limiter._exempt_routes
    assert "main.readiness_check" in limiter._exempt_routes
