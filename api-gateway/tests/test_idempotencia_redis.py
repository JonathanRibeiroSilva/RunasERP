"""
Idempotência contra Redis de verdade.

Cobre o que o dublê não consegue provar: concorrência real (o SET NX decidindo
entre duas corotinas), expiração do EX e round-trip de corpo binário através do
`decode_responses=True` de auth/redis_client.py.

Pula sozinho quando não há Redis local — test_idempotencia.py segue hermético.

Cada teste roda num único asyncio.run() com um cliente próprio: o pool do
redis-py prende conexões ao loop que as criou, e reaproveitar o cliente entre
loops dá "Event loop is closed".
"""
import asyncio

import pytest
from redis.asyncio import from_url

from proxy import idempotency, service_proxy
from tests.test_idempotencia import ServicoFake, UsuarioFake, montar_request


# Mesmas opções de auth/redis_client.py; só o índice do banco muda, para não
# encostar no db 0 que a aplicação usa.
REDIS_URL = "redis://localhost:6379/15"


def rodar(corpo):
    """Executa `corpo(redis)` num loop novo, com Redis limpo e cliente próprio."""
    async def principal():
        cliente = from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
        try:
            await cliente.ping()
        except Exception as erro:  # noqa: BLE001 — sem Redis local, pula
            await cliente.aclose()
            pytest.skip(f"Redis indisponível em {REDIS_URL}: {erro}")
        try:
            await cliente.flushdb()
            return await corpo(cliente)
        finally:
            await cliente.flushdb()
            await cliente.aclose()

    return asyncio.run(principal())


def montar_servico(monkeypatch):
    servico = ServicoFake()
    monkeypatch.setattr(service_proxy.httpx, "AsyncClient", servico.como_client())
    return servico


def ligar_redis(monkeypatch, redis):
    async def get_redis_fake():
        return redis

    monkeypatch.setattr(service_proxy, "get_redis", get_redis_fake)


def proxy_coro(metodo="POST", path="/pagamentos", chave="abc-123"):
    return service_proxy.ServiceProxy.proxy_request(
        montar_request(metodo, path, {"Idempotency-Key": chave}),
        path,
        current_user=UsuarioFake(1),
    )


def test_concorrencia_apenas_uma_atravessa(monkeypatch):
    """Duas requisições simultâneas: uma passa, a outra leva 409. Nunca duas."""
    servico = montar_servico(monkeypatch)
    servico.atraso = 0.05  # garante sobreposição real das duas corotinas

    async def corpo(redis):
        ligar_redis(monkeypatch, redis)
        return await asyncio.gather(
            proxy_coro(), proxy_coro(), return_exceptions=True
        )

    resultados = rodar(corpo)

    oks = [r for r in resultados if not isinstance(r, BaseException)]
    conflitos = [
        r for r in resultados
        if isinstance(r, service_proxy.HTTPException) and r.status_code == 409
    ]
    assert servico.chamadas == 1, f"{servico.chamadas} escritas — duplicou"
    assert len(oks) == 1 and len(conflitos) == 1, resultados


def test_ex_expira_e_a_chave_volta_a_ser_reservavel():
    """O TTL do SET NX EX é real: depois dele a mesma chave reserva de novo."""
    chave = idempotency.montar_chave(1, "POST", "/pagamentos", "expira")

    async def corpo(redis):
        primeira = await idempotency.reservar(redis, chave, 1)
        presa = await idempotency.reservar(redis, chave, 1)
        await asyncio.sleep(1.5)
        return primeira, presa, await idempotency.reservar(redis, chave, 60)

    primeira, presa, depois = rodar(corpo)

    assert primeira is None
    assert presa == idempotency.EM_VOO
    assert depois is None, "a chave não expirou — EX não foi aplicado"


def test_replay_devolve_corpo_binario_identico(monkeypatch):
    """Bytes não-utf8 sobrevivem ao decode_responses=True do cliente Redis."""
    servico = montar_servico(monkeypatch)
    servico.body = b"\xff\xfe\x00\x01PK\x03\x04binario"

    async def corpo(redis):
        ligar_redis(monkeypatch, redis)
        return await proxy_coro(), await proxy_coro()

    primeira, segunda = rodar(corpo)

    assert servico.chamadas == 1
    assert segunda.body == primeira.body == servico.body
    assert segunda.headers["x-idempotent-replay"] == "true"


def test_marcador_em_voo_sobrevive_ao_round_trip():
    """O \x00 do marcador volta idêntico do Redis — senão o 409 viraria replay."""
    async def corpo(redis):
        await redis.set("idem:1:marcador", idempotency.EM_VOO, nx=True, ex=60)
        return await redis.get("idem:1:marcador")

    assert rodar(corpo) == idempotency.EM_VOO
