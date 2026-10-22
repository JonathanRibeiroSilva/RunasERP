"""
Suspender não pode esconder o tenant do painel da plataforma.

`ativo=false` é o soft delete deste serviço: a listagem e as buscas filtram por
ele. Uma suspensão gravada com ativo=false fazia o lojista sumir da tela — e,
sem aparecer lá, ninguém clicava em reativar. A rota de reativar também dava
404, porque atualizar_plano buscava só empresas ativas.
"""
import pytest

from models.empresa import Empresa, StatusEmpresa, TipoEmpresa
from repositories.empresa_repository import EmpresaRepository
from schemas.empresa import EmpresaPlanoUpdate
from services.empresa_service import EmpresaService


async def _empresa(db, slug, cnpj, status, ativo):
    empresa = Empresa(
        slug=slug,
        razao_social="Empresa de Teste LTDA",
        nome_fantasia=slug,
        tipo=TipoEmpresa.MATRIZ,
        status=status,
        ativo=ativo,
        cnpj=cnpj,
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
async def test_suspensa_com_ativo_falso_continua_na_listagem(db):
    suspensa = await _empresa(db, "susp-escondida", "11.111.111/0001-11",
                              StatusEmpresa.SUSPENSA, ativo=False)

    ids = [e.id for e in await EmpresaRepository(db).listar_todas()]

    assert suspensa.id in ids


@pytest.mark.asyncio
async def test_inativa_por_soft_delete_continua_fora_da_listagem(db):
    """O filtro não pode ter virado 'mostra tudo': soft delete segue escondido."""
    apagada = await _empresa(db, "apagada", "22.222.222/0001-22",
                             StatusEmpresa.INATIVA, ativo=False)

    ids = [e.id for e in await EmpresaRepository(db).listar_todas()]

    assert apagada.id not in ids


@pytest.mark.asyncio
async def test_reativar_alcanca_empresa_escondida_e_a_devolve(db):
    escondida = await _empresa(db, "susp-para-voltar", "33.333.333/0001-33",
                               StatusEmpresa.SUSPENSA, ativo=False)

    resposta = await EmpresaService(db).atualizar_plano(
        escondida.id, EmpresaPlanoUpdate(status=StatusEmpresa.ATIVA, ativo=True)
    )

    assert resposta.ativo is True
    assert resposta.status == StatusEmpresa.ATIVA.value
    ids = [e.id for e in await EmpresaRepository(db).listar_todas()]
    assert escondida.id in ids
