"""
Router da plataforma — administração dos tenants, exclusivo do SUPER_ADMIN.

Substitui scripts/provisionar-lojista.ps1, que batia direto nos containers em
dois endpoints sem autenticação. Nenhuma rota aqui lê dado de negócio de um
tenant: só metadados de empresa e contagem de usuários.
"""
import json
from typing import Annotated

import httpx
import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from auth.oauth2 import require_super_admin
from config import settings
from database import get_db
from interno import auth_interno
from models.usuario import Usuario, RoleEnum
from repositories.usuario_repository import UsuarioRepository
from services import preapproval_service
from schemas.usuario import UsuarioCreate

router = APIRouter(
    prefix="/plataforma",
    tags=["Plataforma"],
    dependencies=[Depends(require_super_admin)],
)
log = structlog.get_logger()

# O serviço empresas não tem noção de papel. Este header é o portão dele para as
# rotas de plataforma — mesmo contrato do X-Empresa-Id: só o gateway injeta.
HEADERS_PLATAFORMA = {"X-Plataforma": "1"}


async def _empresas(method: str, path: str, tenant_id: int | None = None, **kwargs) -> httpx.Response:
    """
    Chamada ao serviço empresas com o header de plataforma.

    `tenant_id` é para as rotas que também exigem X-Empresa-Id (as guardadas por
    exigir_tenant, como o DELETE usado na compensação): o serviço é fail closed
    e responde 400 sem ele, o que silenciava o rollback e deixava tenant órfão.
    """
    # X-Plataforma era identidade pura: quem alcançasse o serviço direto virava
    # plataforma. Dois carimbos fecham isso (achado G1b):
    #   - auth_interno: veio de dentro da malha (o mesmo nos 8 containers);
    #   - X-Plataforma-Token: veio DESTE router, que roda depois do
    #     require_super_admin. As rotas de plataforma apagam tenant, então
    #     "veio de algum dos 8" não é prova suficiente.
    headers = auth_interno(HEADERS_PLATAFORMA)
    if settings.PLATAFORMA_INTERNO_TOKEN:
        headers["X-Plataforma-Token"] = settings.PLATAFORMA_INTERNO_TOKEN
    if tenant_id is not None:
        headers["X-Empresa-Id"] = str(tenant_id)
    async with httpx.AsyncClient(timeout=30.0) as client:
        return await client.request(
            method, f"{settings.EMPRESAS_URL}{path}", headers=headers, **kwargs
        )


def _repassar(resp: httpx.Response) -> dict:
    """Erro do serviço empresas chega ao super admin como erro, não como 200."""
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", resp.text))
    return resp.json()


@router.get("/tenants", summary="Listar todos os tenants")
async def listar_tenants(db: Annotated[AsyncSession, Depends(get_db)]):
    """Empresas da plataforma + quantos usuários ativos cada uma tem."""
    empresas = _repassar(await _empresas("GET", "/empresas/plataforma/todas"))

    contagem = dict(
        (await db.execute(
            select(Usuario.empresa_id, func.count())
            .where(Usuario.ativo.is_(True), Usuario.empresa_id.is_not(None))
            .group_by(Usuario.empresa_id)
        )).all()
    )
    # Assinatura mora no banco do gateway: uma query local, sem cross-serviço.
    assinaturas = {
        r["empresa_id"]: dict(r)
        for r in (await db.execute(text(
            "SELECT empresa_id, plano, valor, status, vence_em, "
            "somente_leitura_desde IS NOT NULL AS somente_leitura "
            "FROM gateway.assinaturas"
        ))).mappings().all()
    }
    for e in empresas["items"]:
        e["usuarios_ativos"] = contagem.get(e["id"], 0)
        e["assinatura"] = assinaturas.get(e["id"])
    return empresas


@router.post("/tenants", status_code=status.HTTP_201_CREATED, summary="Provisionar tenant")
async def criar_tenant(
    payload: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Cria a empresa e o usuário ADMIN inicial dela.

    Não há transação distribuída entre gateway e empresas: se o admin falhar, a
    empresa recém-criada é apagada. Sem essa compensação o provisionamento deixa
    empresas órfãs que ninguém consegue acessar nem recriar (slug/CNPJ ocupados).
    """
    empresa_payload = dict(payload.get("empresa") or {})
    admin_payload = dict(payload.get("admin") or {})
    if not empresa_payload or not admin_payload:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Informe 'empresa' e 'admin'")

    # Loja nasce fechada: o lojista abre o catálogo quando terminar de configurar.
    empresa_payload.setdefault("catalogo_ativo", False)
    empresa = _repassar(await _empresas("POST", "/empresas", json=empresa_payload))

    repo = UsuarioRepository(db)
    if await repo.buscar_por_email(admin_payload.get("email", "")):
        await _empresas("DELETE", f"/empresas/{empresa['id']}", tenant_id=empresa["id"])
        raise HTTPException(status.HTTP_409_CONFLICT, "Email do admin já cadastrado")

    try:
        admin = await repo.criar(UsuarioCreate(
            **{**admin_payload, "role": RoleEnum.ADMIN, "empresa_id": empresa["id"]}
        ))
    except Exception:
        await _empresas("DELETE", f"/empresas/{empresa['id']}", tenant_id=empresa["id"])
        log.error("plataforma.provisionar.rollback", empresa_id=empresa["id"])
        raise

    log.info("plataforma.provisionar.success", empresa_id=empresa["id"], admin_id=str(admin.id))
    return {"empresa": empresa, "admin": {"id": str(admin.id), "email": admin.email}}


async def _definir_acesso(db: AsyncSession, empresa_id: int, ativo: bool, status_empresa: str) -> dict:
    """
    Corta (ou devolve) o acesso do tenant pelos usuários dele.

    get_current_user lê o Usuario do banco a cada request, então isso derruba a
    sessão no request seguinte — sem mexer no caminho de auth e sem o gateway
    consultar o serviço empresas a cada chamada. O status da empresa é a verdade
    de exibição; usuario.ativo é a que corta.
    """
    empresa = _repassar(await _empresas(
        "PATCH", f"/empresas/{empresa_id}/plano", json={"status": status_empresa}
    ))
    await db.execute(
        update(Usuario).where(Usuario.empresa_id == empresa_id).values(ativo=ativo)
    )
    await db.commit()
    log.info("plataforma.acesso", empresa_id=empresa_id, ativo=ativo, status=status_empresa)
    return empresa


@router.patch("/tenants/{empresa_id}/suspender", summary="Suspender tenant")
async def suspender_tenant(empresa_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await _definir_acesso(db, empresa_id, ativo=False, status_empresa="SUSPENSA")


@router.patch("/tenants/{empresa_id}/reativar", summary="Reativar tenant")
async def reativar_tenant(empresa_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    return await _definir_acesso(db, empresa_id, ativo=True, status_empresa="ATIVA")


class PlanoUpdate(BaseModel):
    """Espelha EmpresaPlanoUpdate do serviço empresas.

    `status` fica como str em vez de enum: quem é dono do domínio é o empresas,
    que valida contra StatusEmpresa e devolve 422 — duplicar a lista aqui só
    criaria drift. O que o schema acrescenta é recusar campo desconhecido antes
    de repassar, em vez de encaminhar dict arbitrário para uma rota de billing.
    """
    plano: str | None = None
    max_usuarios: int | None = None
    max_produtos: int | None = None
    status: str | None = None
    ativo: bool | None = None

    model_config = ConfigDict(extra="forbid")


@router.patch("/tenants/{empresa_id}/plano", summary="Alterar plano e limites")
async def alterar_plano(empresa_id: int, plano: PlanoUpdate):
    """Plano e limites — os campos que EmpresaUpdate deixou de aceitar."""
    # exclude_unset, não model_dump() puro: do outro lado, atualizar_plano faz
    # setattr de tudo que chega (empresa_service.py). Mandar os cinco campos com
    # null marcaria todos como informados e zeraria plano e limites de quem só
    # queria mudar o status.
    return _repassar(await _empresas(
        "PATCH", f"/empresas/{empresa_id}/plano", json=plano.model_dump(exclude_unset=True)
    ))


# ==================== AUDITORIA E REVERSÃO (Fase 3.3) ====================

@router.get("/tenants/{empresa_id}/auditoria", summary="Trilha de auditoria do tenant")
async def auditoria_do_tenant(
    empresa_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
):
    """
    Últimas escritas do tenant, unindo os dois níveis.

    A trilha do middleware dá o "quem e quando"; o snapshot da trigger dá o
    "o quê". Só as linhas com snapshot são reversíveis — por isso `reversivel`
    vem no payload em vez de a tela adivinhar.
    """
    trilha = (await db.execute(
        text(
            "SELECT id, usuario_id, metodo, rota, status_resposta, criado_em "
            "FROM gateway.auditoria WHERE empresa_id = :e "
            "ORDER BY criado_em DESC LIMIT :l"
        ),
        {"e": empresa_id, "l": limit},
    )).mappings().all()

    snapshots = (await db.execute(
        text(
            # dados_antes/dados_depois vao junto: reverter sobrescreve um
            # registro, e confirmar sem ver o que muda e assinar em branco.
            "SELECT id, schema_origem, tabela, registro_id, operacao, "
            "dados_antes, dados_depois, revertido_em, criado_em "
            "FROM gateway.auditoria_registros "
            "WHERE empresa_id = :e ORDER BY criado_em DESC LIMIT :l"
        ),
        {"e": empresa_id, "l": limit},
    )).mappings().all()

    return {
        "requisicoes": [dict(r) for r in trilha],
        "registros": [{**dict(r), "reversivel": r["revertido_em"] is None} for r in snapshots],
    }


@router.post("/auditoria/{registro_id}/reverter", summary="Reverter uma escrita")
async def reverter_registro(
    registro_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    super_admin: Annotated[Usuario, Depends(require_super_admin)],
):
    """
    Reaplica `dados_antes` no registro de origem.

    Duas recusas deliberadas: reverter duas vezes o mesmo snapshot, e reverter
    algo que já mudou depois. A segunda é a que importa — aplicar um estado
    antigo por cima de uma edição posterior apagaria silenciosamente o trabalho
    de outra pessoa, que é exatamente o que a reversão existe para evitar.
    """
    snap = (await db.execute(
        text("SELECT * FROM gateway.auditoria_registros WHERE id = :id"),
        {"id": registro_id},
    )).mappings().first()

    if not snap:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro de auditoria não encontrado")
    if snap["revertido_em"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Este registro já foi revertido")
    if not snap["dados_antes"]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Um INSERT não tem estado anterior: apague o registro em vez de reverter"
        )

    alvo = f'{snap["schema_origem"]}.{snap["tabela"]}'
    atual = (await db.execute(
        text(f"SELECT to_jsonb(t) AS d FROM {alvo} t WHERE t.id::text = :rid"),
        {"rid": snap["registro_id"]},
    )).scalar()

    if atual is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "O registro de origem não existe mais")
    if snap["dados_depois"] and atual != snap["dados_depois"]:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "O registro mudou depois desta operação — reverter descartaria a "
            "alteração mais recente. Reverta a operação mais nova primeiro."
        )

    antes = snap["dados_antes"]
    # jsonb_populate_record em vez de montar SET col = (:dados->>'col'): o ->>
    # devolve texto, e atribuir texto a coluna numeric/bool/timestamp falha. O
    # populate_record converte cada campo pelo tipo real da tabela de origem.
    # Os nomes de coluna vêm do to_jsonb da própria trigger, nunca do usuário;
    # os valores viajam por bind param.
    colunas = [c for c in antes if c != "id"]
    if not colunas:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Nada a reverter")
    lista = ", ".join(f'"{c}"' for c in colunas)
    await db.execute(
        text(
            f"UPDATE {alvo} t SET ({lista}) = "
            f"(SELECT {lista} FROM jsonb_populate_record(NULL::{alvo}, CAST(:dados AS JSONB))) "
            f"WHERE t.id::text = :rid"
        ),
        {"dados": json.dumps(antes), "rid": snap["registro_id"]},
    )
    await db.execute(
        text("UPDATE gateway.auditoria_registros SET revertido_em = now() WHERE id = :id"),
        {"id": registro_id},
    )
    # Reverter é uma escrita auditada, não um apagamento da história: a trigger
    # da tabela de origem grava o snapshot novo, e esta linha registra quem mandou.
    await db.execute(
        text(
            "INSERT INTO gateway.auditoria (usuario_id, empresa_id, metodo, rota, "
            "payload, status_resposta) VALUES (CAST(:u AS UUID), :e, 'POST', :rota, "
            "CAST(:p AS JSONB), 200)"
        ),
        {
            "u": str(super_admin.id),
            "e": snap["empresa_id"],
            "rota": f"/plataforma/auditoria/{registro_id}/reverter",
            "p": json.dumps({"alvo": alvo, "registro_id": snap["registro_id"]}),
        },
    )
    await db.commit()

    log.info("plataforma.reverter", registro_id=registro_id, alvo=alvo, by=str(super_admin.id))
    return {"revertido": True, "alvo": alvo, "registro_id": snap["registro_id"]}


# Serviço -> rota de listagem que compõe a exportação do tenant.
FONTES_EXPORTACAO = {
    "empresa": (settings.EMPRESAS_URL, "/empresas"),
    "clientes": (settings.CLIENTES_URL, "/clientes"),
    "produtos": (settings.PRODUTOS_URL, "/produtos"),
    "estoque": (settings.ESTOQUE_URL, "/estoque"),
    "vendas": (settings.VENDAS_URL, "/vendas"),
}


@router.get("/tenants/{empresa_id}/exportar", summary="Exportar dados do tenant")
async def exportar_tenant(
    empresa_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    super_admin: Annotated[Usuario, Depends(require_super_admin)],
):
    """
    Dados do tenant em JSON, atravessando os serviços com o X-Empresa-Id dele.

    É o único ponto do sistema em que o super admin toca dado de negócio, e por
    isso a exportação é auditada com quem exportou, quando e de quem. Resposta
    em streaming: a VPS tem ~1.1GB livres e montar o tenant inteiro em memória
    derrubaria o gateway junto.
    """
    await db.execute(
        text(
            "INSERT INTO gateway.auditoria (usuario_id, empresa_id, metodo, rota, "
            "status_resposta) VALUES (CAST(:u AS UUID), :e, 'GET', :rota, 200)"
        ),
        {
            "u": str(super_admin.id),
            "e": empresa_id,
            "rota": f"/plataforma/tenants/{empresa_id}/exportar",
        },
    )
    await db.commit()
    log.info("plataforma.exportar", empresa_id=empresa_id, by=str(super_admin.id))

    async def gerar():
        yield '{"empresa_id": %d, "dados": {' % empresa_id
        primeiro = True
        async with httpx.AsyncClient(timeout=60.0) as client:
            for nome, (base, path) in FONTES_EXPORTACAO.items():
                if not primeiro:
                    yield ","
                primeiro = False
                yield json.dumps(nome) + ":"
                resp = await client.get(
                    f"{base}{path}",
                    headers=auth_interno({"X-Empresa-Id": str(empresa_id)}),
                    params={"limit": 1000},
                )
                yield resp.text if resp.status_code == 200 else json.dumps(
                    {"erro": resp.status_code}
                )
        yield "}}"

    return StreamingResponse(
        gerar(),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="tenant-{empresa_id}.json"'},
    )


@router.get("/tenants/{empresa_id}/dumps", summary="Listar backups do tenant")
async def listar_dumps(empresa_id: int):
    """
    Backups disponíveis. Vazio até a Fase 4 existir.

    Não há rota de restaurar, e é deliberado: restaurar sobrescreve o tenant
    inteiro e descarta tudo posterior ao dump. Isso é operação de terminal com
    revisão humana; o caminho de suporte do dia a dia é a reversão pontual
    acima, que é cirúrgica e auditada. Esta rota existe agora só para a tela
    nascer completa e não precisar de refatoração quando o backup entrar.
    """
    return {
        "items": [],
        "restauracao": "manual",
        "detalhe": "scripts/restaurar-tenant.sh (Fase 4)",
    }


# ==================== COBRANÇA (Fase 3.1) ====================

@router.post("/tenants/{empresa_id}/assinatura", summary="Gerar link de assinatura")
async def gerar_assinatura(
    empresa_id: int,
    dados: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cria o preapproval na conta MP da plataforma e devolve o link de adesão."""
    email = dados.get("email_pagador")
    if not email:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Informe email_pagador")
    return await preapproval_service.criar_assinatura(
        db, empresa_id, dados.get("plano", "BASICO"), dados.get("valor", 0), email
    )


@router.delete("/tenants/{empresa_id}/assinatura", summary="Cancelar assinatura")
async def cancelar_assinatura(empresa_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    """Cancela no MP e marca localmente. Não suspende: a régua faz isso no prazo."""
    if not await preapproval_service.cancelar_assinatura(db, empresa_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant sem assinatura")
    return {"cancelada": True}


# ==================== ROTAS SEM SUPER_ADMIN ====================
# Router separado de propósito: o de cima tem require_super_admin no nível do
# router, e webhook e cron não têm sessão de usuário nenhuma. Registrar as duas
# no main.py, ambas antes do proxy.

router_publico = APIRouter(prefix="/plataforma", tags=["Plataforma"])


@router_publico.post("/webhook/mercadopago", summary="Webhook de assinatura (público)")
async def webhook_mercadopago(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Confirmação de pagamento da mensalidade.

    Idempotente pelo id do evento, no mesmo padrão de vendas/routers/webhook.py:
    o MP reenvia, e processar duas vezes empurraria o vencimento em dois meses.
    Responde 200 mesmo para evento repetido — 4xx faria o MP reenviar para sempre.
    """
    corpo = await request.json()
    evento_id = str(corpo.get("id") or corpo.get("data", {}).get("id") or "")
    if not evento_id:
        return {"ignorado": "evento sem id"}

    ja_visto = await db.scalar(
        text("SELECT 1 FROM gateway.webhooks_plataforma WHERE evento_id = :id"),
        {"id": evento_id},
    )
    if ja_visto:
        log.info("plataforma.webhook_repetido", evento_id=evento_id)
        return {"ja_processado": True}

    await db.execute(
        text(
            "INSERT INTO gateway.webhooks_plataforma (evento_id, tipo, payload) "
            "VALUES (:id, :tipo, :p)"
        ),
        {"id": evento_id, "tipo": corpo.get("type"), "p": json.dumps(corpo)},
    )
    await db.commit()

    preapproval_id = corpo.get("data", {}).get("id")
    if corpo.get("type") == "subscription_preapproval" and preapproval_id:
        empresa_id = await preapproval_service.registrar_pagamento(db, str(preapproval_id))
        return {"processado": True, "empresa_id": empresa_id}

    return {"processado": False, "tipo": corpo.get("type")}


@router_publico.post("/jobs/regua", summary="Varredura diária de vencimentos")
async def rodar_regua(
    db: Annotated[AsyncSession, Depends(get_db)],
    x_job_token: str | None = Header(None, alias="X-Job-Token"),
):
    """
    Aplica a régua de inadimplência e poda a auditoria vencida.

    Chamado pelo cron do host, não por um scheduler residente:
    # ponytail: cron do host batendo num endpoint, não Celery. O beat worker come
    # RAM 24h por dia para trabalhar 200ms. Trocar quando houver um segundo job.
    """
    if not settings.PLATAFORMA_JOB_TOKEN or x_job_token != settings.PLATAFORMA_JOB_TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Token de job inválido")
    return await preapproval_service.aplicar_regua(db)
