"""
G5 (Onda 6): desativar_empresa tinha um TODO no lugar da checagem de
dependentes — "por enquanto, permite desativar". Qualquer empresa com
clientes, produtos ou vendas cadastrados podia ser desativada sem aviso.

A checagem cruza três serviços por HTTP (`_tem_dados_dependentes`); aqui ela
é substituída por monkeypatch — mesmo padrão das fixtures `estoque`/`credito`
nos testes de vendas — porque o que está sob teste é o comportamento de
`desativar_empresa` perante o resultado, não a plumbing HTTP em si.
"""
import pytest

from exceptions import ConflictError
from models.empresa import Empresa, StatusEmpresa, TipoEmpresa
from services.empresa_service import EmpresaService

EMPRESA_ID_INEXISTENTE = 1


async def _empresa(db, slug):
    empresa = Empresa(
        slug=slug,
        razao_social="Empresa de Teste LTDA",
        nome_fantasia="Empresa de Teste",
        tipo=TipoEmpresa.MATRIZ,
        status=StatusEmpresa.ATIVA,
        cnpj=f"12.345.678/000{len(slug) % 10}-90",
        cep="01310-100",
        logradouro="Rua de Teste",
        numero="100",
        bairro="Centro",
        cidade="São Paulo",
        uf="SP",
    )
    db.add(empresa)
    await db.commit()
    await db.refresh(empresa)
    return empresa


@pytest.mark.asyncio
async def test_desativar_empresa_sem_dependentes(db, monkeypatch):
    async def sem_dependentes(empresa_id):
        return []

    monkeypatch.setattr(
        EmpresaService, "_tem_dados_dependentes", staticmethod(sem_dependentes)
    )
    empresa = await _empresa(db, "empresa-sem-dependentes")
    service = EmpresaService(db)

    resultado = await service.desativar_empresa(empresa.id)

    assert resultado.status == StatusEmpresa.INATIVA.value


@pytest.mark.asyncio
async def test_desativar_empresa_com_dependentes_e_bloqueada(db, monkeypatch):
    async def com_dependentes(empresa_id):
        return ["vendas", "clientes"]

    monkeypatch.setattr(
        EmpresaService, "_tem_dados_dependentes", staticmethod(com_dependentes)
    )
    empresa = await _empresa(db, "empresa-com-dependentes")
    service = EmpresaService(db)

    with pytest.raises(ConflictError) as excinfo:
        await service.desativar_empresa(empresa.id)

    assert excinfo.value.details["dependentes"] == ["vendas", "clientes"]

    await db.refresh(empresa)
    assert empresa.status == StatusEmpresa.ATIVA, (
        "bloquear a desativação não pode deixar a empresa mudada mesmo assim"
    )
