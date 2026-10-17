"""
A lista de /plataforma quebrava inteira (500) com um único tenant sem limite de
produtos: o model e o banco aceitam max_produtos NULL (= ilimitado), mas o
EmpresaListItem o declarava `int` e a validação estourava ao serializar.
"""
from datetime import datetime, timezone

from models.empresa import StatusEmpresa, TipoEmpresa
from schemas.empresa import EmpresaListItem


def _item(max_produtos):
    return {
        "id": 1, "slug": "loja", "razao_social": "Loja LTDA", "nome_fantasia": "Loja",
        "cnpj": "11222333000181", "tipo": TipoEmpresa.MATRIZ, "status": StatusEmpresa.ATIVA,
        "cidade": "São Paulo", "uf": "SP", "catalogo_ativo": False, "plano": "BASICO",
        "max_usuarios": 5, "max_produtos": max_produtos, "ativo": True,
        "criado_em": datetime.now(timezone.utc),
    }


def test_lista_aceita_tenant_sem_limite_de_produtos():
    assert EmpresaListItem(**_item(None)).max_produtos is None


def test_lista_mantem_limite_numerico():
    assert EmpresaListItem(**_item(500)).max_produtos == 500
