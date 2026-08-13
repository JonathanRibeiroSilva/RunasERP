"""
Helpers de concorrência para baixa de estoque.

Sem dependências de banco/ORM (apenas stdlib) — facilita testes unitários da política
de retry de deadlock e da ordenação determinística de locks.
"""
from typing import Any, Optional, Tuple

# SQLSTATE do PostgreSQL para falhas transitórias de concorrência (recuperáveis por retry).
PG_DEADLOCK_DETECTED = "40P01"
PG_SERIALIZATION_FAILURE = "40001"
SQLSTATES_TRANSITORIOS = frozenset({PG_DEADLOCK_DETECTED, PG_SERIALIZATION_FAILURE})

# Política de retry para deadlocks.
MAX_TENTATIVAS_DEADLOCK = 3
BACKOFF_BASE_SEGUNDOS = 0.05


def extrair_sqlstate(exc: BaseException) -> Optional[str]:
    """Extrai o SQLSTATE de uma exceção do driver (asyncpg) ou do wrapper SQLAlchemy."""
    for candidato in (exc, getattr(exc, "orig", None)):
        if candidato is None:
            continue
        codigo = getattr(candidato, "sqlstate", None) or getattr(candidato, "pgcode", None)
        if codigo:
            return str(codigo)
    return None


def eh_erro_transitorio(exc: BaseException) -> bool:
    """True se a exceção é um deadlock/serialization failure recuperável por retry."""
    return extrair_sqlstate(exc) in SQLSTATES_TRANSITORIOS


def chave_ordenacao_item(produto_id: Any, variante_id: Any) -> Tuple[str, str]:
    """
    Chave determinística para travar linhas de estoque sempre na mesma ordem.

    Adquirir locks em uma ordem global consistente entre transações concorrentes evita
    deadlocks: cada transação pega os locks na mesma sequência.
    """
    return (str(produto_id), str(variante_id) if variante_id is not None else "")


def backoff_segundos(tentativa: int) -> float:
    """Backoff exponencial por número da tentativa (0-based)."""
    return BACKOFF_BASE_SEGUNDOS * (2 ** tentativa)
