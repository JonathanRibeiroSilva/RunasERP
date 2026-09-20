"""Quem manda a senha já hasheada define a senha da conta do comprador.

POST /auth/cliente/registrar-interno aceita `senha_hash` pronto. A única porta
era a ausência do X-Forwarded-For — o nginx carimba esse header no que vem da
internet, então a chamada interna do vendas não tem. Funciona hoje e depende de
o nginx continuar configurado assim para sempre, e de nenhum caminho interno
novo passar por ele.

A porta agora é o segredo compartilhado REGISTRO_INTERNO_TOKEN. O que estes
testes prendem é a FIAÇÃO: um segredo carimbado de um lado e conferido com
outro nome do outro não protege nada e não falha em lugar nenhum — o checkout
simplesmente para de criar conta, em silêncio, em produção.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HEADER = "X-Registro-Interno-Token"
ENV = "REGISTRO_INTERNO_TOKEN"

GATEWAY_ROTA = REPO / "api-gateway" / "routers" / "auth_cliente.py"
VENDAS_CHAMADOR = REPO / "services" / "vendas" / "services" / "loja_service.py"


def _corpo_do_registrar_interno() -> str:
    """A janela da rota, não o arquivo: o resto de auth_cliente.py não é a regra."""
    fonte = GATEWAY_ROTA.read_text(encoding="utf-8")
    corpo = fonte[fonte.index('@router.post("/registrar-interno"'):]
    return corpo[: corpo.index("\n@router.")] if "\n@router." in corpo else corpo


def test_rota_confere_o_segredo_em_tempo_constante():
    corpo = _corpo_do_registrar_interno()

    assert f'alias="{HEADER}"' in corpo, "a rota não lê mais o header do segredo"
    assert f"settings.{ENV}" in corpo, "a rota não compara mais com a env"
    # compare_digest e não ==: comparação de segredo que sai no primeiro byte
    # diferente conta o segredo pelo tempo de resposta.
    assert "secrets.compare_digest" in corpo, "comparação de segredo sem tempo constante"


def test_vendas_carimba_o_mesmo_header_com_a_mesma_env():
    """O outro lado do par. Sem isto, fechar a janela derruba o checkout."""
    chamador = VENDAS_CHAMADOR.read_text(encoding="utf-8")
    trecho = chamador[chamador.index("/auth/cliente/registrar-interno") - 400:]
    trecho = trecho[: trecho.index("timeout=10.0")]

    assert HEADER in trecho, "o vendas não carimba mais o header do segredo"
    assert f"settings.{ENV}" in trecho, "o vendas carimba um valor que não é a env do par"


def test_os_dois_servicos_declaram_a_env():
    faltando = [
        str(cfg.relative_to(REPO))
        for cfg in (REPO / "api-gateway" / "config.py",
                    REPO / "services" / "vendas" / "config.py")
        if f"{ENV}:" not in cfg.read_text(encoding="utf-8")
    ]
    assert not faltando, f"config.py sem a env do segredo: {faltando}"


def _bloco_do_servico(compose: str, servico: str) -> str:
    """Do `  <servico>:` até o próximo serviço no mesmo nível de indentação."""
    inicio = compose.index(f"\n  {servico}:\n") + 1
    resto = compose[inicio:]
    fim = re.search(r"\n  [a-z0-9_-]+:\n", resto)
    return resto[: fim.start()] if fim else resto


def test_as_duas_pontas_recebem_a_env_nos_dois_composes():
    """Uma ponta sem a env = segredo que nunca bate. Tem que chegar nas duas."""
    faltando = []
    for arquivo, gateway, vendas in (
        ("docker-compose.dev.yml", "api-gateway", "vendas"),
        ("docker-compose.prod.yml", "api-gateway-prod", "vendas-prod"),
    ):
        compose = (REPO / arquivo).read_text(encoding="utf-8")
        for servico in (gateway, vendas):
            if f"{ENV}: ${{{ENV}}}" not in _bloco_do_servico(compose, servico):
                faltando.append(f"{arquivo}:{servico}")

    assert not faltando, f"serviço sem a env do segredo: {faltando}"


def test_a_janela_fail_open_esta_nomeada_enquanto_estiver_aberta():
    """Este teste existe para ser apagado.

    Enquanto o segredo não estiver carimbado em prod, chamada sem segredo passa
    e vira um warning nomeado — é o que se mede antes de fechar. Fechar a janela
    é trocar esse log.warning por um raise; aí este teste fica vermelho, e é
    exatamente assim que se descobre que a decisão foi tomada de propósito.
    """
    corpo = _corpo_do_registrar_interno()

    assert "cliente.internal_register.sem_segredo" in corpo, (
        "a janela fail-open sumiu: se foi de propósito, apague este teste junto"
    )
    # Enquanto ela estiver aberta, a guarda antiga é o que protege.
    assert re.search(r"if x_forwarded_for is not None:", corpo), (
        "a guarda do X-Forwarded-For saiu antes de a janela fechar"
    )
