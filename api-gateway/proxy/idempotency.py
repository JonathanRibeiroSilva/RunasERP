"""
Idempotência de escritas: uma reserva no Redis por Idempotency-Key.

Mora no gateway porque toda requisição do frontend passa por
ServiceProxy.proxy_request() — uma implementação cobre todos os serviços.
Esta camada é defesa contra retry de cliente (mesma chave devolve a mesma
resposta, nunca uma segunda venda). A garantia final continua sendo o ledger
UNIQUE no banco de cada serviço; as duas se somam, nenhuma substitui a outra.
"""
import base64
import hashlib
import json

from fastapi import HTTPException, Response, status
from redis.asyncio import Redis


# Só escritas: um GET repetido não duplica nada.
METODOS = {"POST", "PUT", "PATCH", "DELETE"}

# Marcador de reserva: requisição encaminhada, resposta final ainda não chegou.
EM_VOO = "\x00em-voo"

# Status que o cliente deve poder reenviar: a reserva é liberada em vez de
# guardada, senão um pico de tráfego (429) ou um timeout de upstream (408)
# tranca a chave pelo TTL inteiro e o cliente nunca consegue completar a venda.
TRANSITORIOS = {408, 425, 429}

# ponytail: teto de 256 KB por resposta guardada. Acima disso a reserva é
# liberada e aquela chave perde o replay — é o preço de não encher o Redis com
# export/relatório. Se alguma resposta grande precisar de replay, mova o corpo
# para outro storage em vez de subir este número.
MAX_BODY = 256 * 1024


def montar_chave(empresa_id: int | None, metodo: str, path: str, valor: str) -> str:
    """
    Monta a chave Redis escopada por tenant.

    empresa_id fica fora do hash para a chave continuar legível no redis-cli.
    Método e path entram no digest junto com o valor do header: a mesma chave
    reenviada para outro endpoint é outra operação, não um replay.
    """
    digest = hashlib.sha256(f"{metodo}|{path}|{valor}".encode()).hexdigest()
    return f"idem:{empresa_id or 0}:{digest}"


async def reservar(redis: Redis, chave: str, ttl: int) -> str | None:
    """
    Reserva a chave antes de encaminhar.

    Returns:
        None se a reserva foi feita (siga em frente); caso contrário o valor já
        guardado — o marcador EM_VOO ou a resposta serializada.
    """
    if await redis.set(chave, EM_VOO, nx=True, ex=ttl):
        return None

    # Corrida rara: a chave expirou entre o SET e o GET. Tratar como em voo
    # devolve 409 e o cliente reenvia — duplicar a escrita seria pior.
    return await redis.get(chave) or EM_VOO


def responder_guardado(guardado: str) -> Response:
    """
    Devolve o que está guardado: 409 se ainda em voo, senão a resposta salva.

    Raises:
        HTTPException: 409 quando uma requisição idêntica ainda está em voo.
    """
    if guardado == EM_VOO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requisição com esta Idempotency-Key ainda está em processamento"
        )

    salvo = json.loads(guardado)
    return Response(
        content=base64.b64decode(salvo["body"]),
        status_code=salvo["status"],
        media_type=salvo["content_type"],
        headers={"X-Idempotent-Replay": "true"}
    )


async def concluir(
    redis: Redis,
    chave: str,
    status_code: int,
    content: bytes,
    content_type: str | None,
    ttl: int
) -> None:
    """
    Fecha a reserva com a resposta final do serviço.

    Guarda apenas resposta final (2xx e 4xx de negócio). 5xx, status transitório
    ou corpo acima do teto liberam a reserva para o cliente poder reenviar.
    """
    if status_code >= 500 or status_code in TRANSITORIOS or len(content) > MAX_BODY:
        await liberar(redis, chave)
        return

    await redis.set(
        chave,
        json.dumps({
            "status": status_code,
            "body": base64.b64encode(content).decode(),
            "content_type": content_type
        }),
        ex=ttl
    )


async def liberar(redis: Redis, chave: str) -> None:
    """Apaga a reserva — usado quando a resposta não é final (erro transitório)."""
    await redis.delete(chave)
