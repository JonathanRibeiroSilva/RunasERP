"""Serviço interno não publica porta em todas as interfaces, nem em dev.

Nenhum dos serviços de `services/` valida JWT: todos tratam `X-Empresa-Id` como
identidade confiável, e quem descarta o header vindo do cliente é o gateway
(`api-gateway/proxy/service_proxy.py`, guardado por
test_headers_internos_nao_vem_do_cliente.py). Com a porta publicada em 0.0.0.0,
falar direto com o serviço pula o gateway inteiro: qualquer máquina que alcance
a porta escolhe o próprio tenant, e no 8007 do empresas o header X-Plataforma
ainda abre as rotas de super-admin (criar tenant, listar CNPJ de todos, alterar
plano).

Prod nunca publicou essas portas — o compose de produção só expõe o cloudflared.
Era só o dev que ficava aberto na rede local, que é onde a máquina do dev senta
numa rede que ela não controla.

Guarda a classe: um serviço novo em services/ entra na regra sozinho.
"""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]

# O gateway é o ponto de entrada e precisa ser alcançável pelo navegador; os
# serviços internos são falados por ele, pela rede do compose, onde `ports:` não
# tem efeito nenhum.
PUBLICOS = {"api-gateway", "frontend-dev"}


def _servicos_internos() -> set:
    """Todo diretório de services/ é um serviço interno, por definição."""
    return {p.name for p in (REPO / "services").iterdir() if p.is_dir()} - PUBLICOS


def test_servico_interno_publica_porta_so_em_localhost():
    compose = yaml.safe_load((REPO / "docker-compose.dev.yml").read_text(encoding="utf-8"))

    abertos = [
        f"{nome}: {porta}"
        for nome in sorted(_servicos_internos())
        for porta in compose["services"].get(nome, {}).get("ports", [])
        if not str(porta).startswith("127.0.0.1:")
    ]

    assert not abertos, (
        "serviço interno publicado fora de 127.0.0.1 — quem alcança a porta "
        f"escolhe o próprio X-Empresa-Id: {abertos}"
    )


def test_prod_nao_publica_porta_de_servico_interno():
    """Em prod o nome do serviço tem sufixo -prod; a regra é a mesma."""
    compose = yaml.safe_load((REPO / "docker-compose.prod.yml").read_text(encoding="utf-8"))

    abertos = [
        f"{nome}-prod: {porta}"
        for nome in sorted(_servicos_internos())
        for porta in compose["services"].get(f"{nome}-prod", {}).get("ports", [])
    ]

    assert not abertos, f"serviço interno exposto em produção: {abertos}"
