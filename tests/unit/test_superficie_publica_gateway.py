"""A superfície do gateway é o que a internet alcança — nada morto pode ficar lá.

/auth/register (deprecated, sem dependência de auth) criava operador do ERP para
qualquer um, e /auth/cliente/registrar-interno aceita senha já hasheada — quem
chama define a senha da conta. Ambos respondiam na borda. Os testes guardam a
classe: rota deprecada não fica publicada, e o endpoint interno fica fechado.
"""
import re
from pathlib import Path

GATEWAY = Path(__file__).resolve().parents[2] / "api-gateway"


def test_nenhuma_rota_deprecada_publicada():
    """Rota deprecada é rota morta: apaga, não deixa respondendo na borda."""
    ofensores = [
        f"{path.relative_to(GATEWAY.parent)}:{n}"
        for path in GATEWAY.rglob("routers/*.py")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if "deprecated=True" in line
    ]
    assert not ofensores, f"rotas deprecadas ainda publicadas: {ofensores}"


def test_registrar_interno_recusa_chamada_vinda_da_internet():
    """O nginx carimba X-Forwarded-For; a chamada interna do vendas não tem."""
    fonte = (GATEWAY / "routers" / "auth_cliente.py").read_text(encoding="utf-8")
    corpo = fonte[fonte.index('@router.post("/registrar-interno"'):]
    corpo = corpo[: corpo.index("\n@router.")] if "\n@router." in corpo else corpo

    assert "x_forwarded_for" in corpo, "guarda de origem sumiu do registrar-interno"
    assert re.search(r"if x_forwarded_for is not None:", corpo), "guarda não bloqueia mais"
