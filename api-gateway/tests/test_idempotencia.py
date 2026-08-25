"""
Idempotência de escritas no gateway.

Guarda o caminho do dinheiro: um POST /pagamentos reenviado com a mesma
Idempotency-Key não pode virar dois pagamentos. Sem Redis e sem serviço real —
o proxy é exercitado com dublês para o teste rodar em qualquer máquina.
"""
import asyncio
import os

import pytest

# As settings do gateway exigem estas variáveis no import.
os.environ.setdefault("SECRET_KEY", "test-secret-key-super-secure-min-32-chars")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
for _servico in ("EMPRESAS", "CLIENTES", "PRODUTOS", "ESTOQUE", "VENDAS",
                 "FINANCEIRO", "NOTIFICACOES"):
    os.environ.setdefault(f"{_servico}_URL", f"http://{_servico.lower()}:8000")

from starlette.requests import Request  # noqa: E402

from proxy import idempotency, service_proxy  # noqa: E402


class RedisFake:
    """Dicionário com a semântica de SET NX / GET / DELETE. TTL é ignorado."""

    def __init__(self):
        self.dados = {}

    async def set(self, chave, valor, nx=False, ex=None):
        if nx and chave in self.dados:
            return None
        self.dados[chave] = valor
        return True

    async def get(self, chave):
        return self.dados.get(chave)

    async def delete(self, chave):
        self.dados.pop(chave, None)


class RespostaFake:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.content = body
        self.headers = {"content-type": "application/json"}


class ServicoFake:
    """Conta quantas vezes o microsserviço foi realmente chamado."""

    def __init__(self, status_code=201, body=b'{"id": 7}'):
        self.status_code = status_code
        self.body = body
        self.chamadas = 0
        self.atraso = 0  # segundos: usado para sobrepor requisições concorrentes

    def como_client(self):
        servico = self

        class ClientFake:
            def __init__(self, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def request(self, **kwargs):
                servico.chamadas += 1
                if servico.atraso:
                    await asyncio.sleep(servico.atraso)
                return RespostaFake(servico.status_code, servico.body)

        return ClientFake


class UsuarioFake:
    def __init__(self, empresa_id):
        self.empresa_id = empresa_id
        self.cliente_id = None


def montar_request(metodo, path, headers):
    scope = {
        "type": "http",
        "method": metodo,
        "path": path,
        "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }

    async def receive():
        return {"type": "http.request", "body": b"{}", "more_body": False}

    return Request(scope, receive)


@pytest.fixture
def ambiente(monkeypatch):
    """Troca Redis e httpx por dublês e devolve (redis, servico)."""
    redis = RedisFake()
    servico = ServicoFake()

    async def get_redis_fake():
        return redis

    monkeypatch.setattr(service_proxy, "get_redis", get_redis_fake)
    monkeypatch.setattr(service_proxy.httpx, "AsyncClient", servico.como_client())
    return redis, servico


def proxy(metodo, path, headers, empresa_id=1):
    return asyncio.run(
        service_proxy.ServiceProxy.proxy_request(
            montar_request(metodo, path, headers),
            path,
            current_user=UsuarioFake(empresa_id),
        )
    )


def test_sem_header_nada_muda(ambiente):
    """Sem Idempotency-Key o proxy encaminha toda vez — comportamento atual."""
    redis, servico = ambiente

    proxy("POST", "/pagamentos", {})
    proxy("POST", "/pagamentos", {})

    assert servico.chamadas == 2
    assert redis.dados == {}


def test_mesma_chave_devolve_resposta_salva_sem_rechamar(ambiente):
    """Retry com a mesma chave: resposta idêntica, serviço chamado uma só vez."""
    redis, servico = ambiente
    # Grafia canônica; montar_request normaliza para minúsculas como o servidor
    # ASGI faz na vida real, e o proxy lê via request.headers (case-insensitive).
    headers = {"Idempotency-Key": "abc-123"}

    primeira = proxy("POST", "/pagamentos", headers)
    segunda = proxy("POST", "/pagamentos", headers)

    assert servico.chamadas == 1, "o serviço foi chamado de novo — venda duplicada"
    assert segunda.status_code == primeira.status_code == 201
    assert segunda.body == primeira.body == b'{"id": 7}'
    assert segunda.headers["x-idempotent-replay"] == "true"
    assert "x-idempotent-replay" not in primeira.headers


def test_erro_5xx_libera_a_chave(ambiente):
    """5xx não é resposta final: a chave some e o cliente consegue reenviar."""
    redis, servico = ambiente
    servico.status_code = 500
    headers = {"idempotency-key": "abc-123"}

    proxy("POST", "/pagamentos", headers)
    assert redis.dados == {}, "5xx guardado — a chave ficaria travada pelo TTL"

    servico.status_code = 201
    resposta = proxy("POST", "/pagamentos", headers)

    assert servico.chamadas == 2
    assert resposta.status_code == 201


def test_falha_de_conexao_libera_a_chave(ambiente, monkeypatch):
    """Timeout/conexão também liberam: erro transitório não pode travar a chave."""
    redis, servico = ambiente

    class ClientQuebrado(servico.como_client()):
        async def request(self, **kwargs):
            raise service_proxy.httpx.ConnectError("sem rota")

    monkeypatch.setattr(service_proxy.httpx, "AsyncClient", ClientQuebrado)
    with pytest.raises(service_proxy.HTTPException) as erro:
        proxy("POST", "/pagamentos", {"idempotency-key": "abc-123"})

    assert erro.value.status_code == 503
    assert redis.dados == {}


def test_requisicao_em_voo_responde_409(ambiente):
    """Reserva feita e resposta ainda não gravada: 409, nunca uma segunda escrita."""
    redis, _ = ambiente
    chave = idempotency.montar_chave(1, "POST", "/pagamentos", "abc-123")

    assert asyncio.run(idempotency.reservar(redis, chave, 60)) is None
    guardado = asyncio.run(idempotency.reservar(redis, chave, 60))

    assert guardado == idempotency.EM_VOO
    with pytest.raises(service_proxy.HTTPException) as erro:
        idempotency.responder_guardado(guardado)
    assert erro.value.status_code == 409


def test_chave_e_escopada_por_tenant_metodo_e_path(ambiente):
    """Mesma chave de empresas/métodos/paths diferentes não pode colidir."""
    _, servico = ambiente

    proxy("POST", "/pagamentos", {"idempotency-key": "abc-123"}, empresa_id=1)
    proxy("POST", "/pagamentos", {"idempotency-key": "abc-123"}, empresa_id=2)
    proxy("PUT", "/pagamentos", {"idempotency-key": "abc-123"}, empresa_id=1)
    proxy("POST", "/contas", {"idempotency-key": "abc-123"}, empresa_id=1)

    assert servico.chamadas == 4


def test_corpo_acima_do_teto_nao_e_guardado(ambiente):
    """Resposta gigante: libera a reserva em vez de encher o Redis."""
    redis, servico = ambiente
    servico.body = b"x" * (idempotency.MAX_BODY + 1)

    proxy("POST", "/pagamentos", {"idempotency-key": "abc-123"})

    assert redis.dados == {}
