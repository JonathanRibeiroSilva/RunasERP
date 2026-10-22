"""O botão pausar/reativar segue `ativo`; a listagem tem de derivá-lo da suspensão real."""
import pytest

from routers.plataforma import _esta_suspenso


def _empresa(status="ATIVA", ativo=True, assinatura=None):
    return {"status": status, "ativo": ativo, "assinatura": assinatura}


@pytest.mark.parametrize(
    "empresa",
    [
        # Suspensa à mão antes de `ativo` ser gravado: o caso dos tenants em produção.
        _empresa(status="SUSPENSA", ativo=True),
        # Suspensa pela régua: a empresa não foi tocada, só a assinatura.
        _empresa(assinatura={"status": "SUSPENSA"}),
    ],
)
def test_suspenso_por_status_ou_por_assinatura(empresa):
    assert _esta_suspenso(empresa)


@pytest.mark.parametrize(
    "empresa",
    [
        _empresa(),
        _empresa(assinatura={"status": "INADIMPLENTE"}),
        # Inativa por outro motivo: não é suspensão, o rótulo do status não muda.
        _empresa(status="CANCELADA", ativo=False),
    ],
)
def test_nao_suspenso(empresa):
    assert not _esta_suspenso(empresa)
