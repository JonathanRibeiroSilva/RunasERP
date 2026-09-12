"""
Cifra de credenciais de integração por tenant.

Fernet vem do `cryptography`, dependência transitiva de python-jose[cryptography]
(requirements.txt:21) — nenhum pacote novo.

Sem INTEGRACOES_SECRET_KEY configurada a escrita FALHA. Cair para texto plano
seria pior que falhar: o admin salvaria a senha do SMTP achando que está
protegida, e o incidente só apareceria depois do vazamento.
"""
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from config import settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    chave = getattr(settings, "INTEGRACOES_SECRET_KEY", "") or ""
    if not chave:
        raise RuntimeError(
            "INTEGRACOES_SECRET_KEY não configurada: credenciais de integração "
            "não podem ser gravadas. Gere com Fernet.generate_key()."
        )
    return Fernet(chave.encode() if isinstance(chave, str) else chave)


def encrypt(valor: str) -> str:
    """Cifra um segredo para gravação."""
    return _fernet().encrypt(valor.encode()).decode()


def decrypt(valor: str) -> str:
    """Decifra um segredo lido do banco.

    InvalidToken normalmente significa chave trocada: o valor antigo é
    irrecuperável, e devolver string vazia disfarçaria isso de "não configurado".
    """
    try:
        return _fernet().decrypt(valor.encode()).decode()
    except InvalidToken as e:
        raise RuntimeError(
            "Credencial não decifrável — INTEGRACOES_SECRET_KEY mudou? "
            "O tenant precisa reconfigurar a integração."
        ) from e


def demo() -> None:
    """Autoteste: ida e volta, e ciphertexts distintos para o mesmo segredo."""
    import os
    os.environ.setdefault("INTEGRACOES_SECRET_KEY", Fernet.generate_key().decode())
    _fernet.cache_clear()
    settings.INTEGRACOES_SECRET_KEY = os.environ["INTEGRACOES_SECRET_KEY"]

    segredo = "APP_USR-1234567890-abcdef"
    cifrado = encrypt(segredo)
    assert cifrado != segredo, "gravou em texto plano"
    assert decrypt(cifrado) == segredo, "ida e volta quebrou"
    assert encrypt(segredo) != cifrado, "Fernet deve usar IV novo a cada cifra"
    print("crypto ok")


if __name__ == "__main__":
    demo()
