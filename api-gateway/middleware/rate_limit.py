"""
Middleware de rate limiting.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address


# 300/min por IP: teto generoso pra não travar um escritório inteiro atrás de
# um único IP de NAT. Login/registro/reset de senha levam limite bem mais
# apertado via @limiter.limit direto na rota (ver routers/auth*.py).
limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
