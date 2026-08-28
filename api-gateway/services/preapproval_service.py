"""
Assinatura da plataforma via Mercado Pago Preapproval.

ATENÇÃO — dois Mercado Pagos no mesmo sistema:
  - PLATAFORMA_MP_ACCESS_TOKEN (aqui): conta do dono da plataforma, cobra os
    lojistas pela mensalidade.
  - vendas.configuracoes_pagamento: conta de cada lojista, cobra os clientes
    finais dele.
Nunca os misture. Este módulo só conhece o primeiro.
"""
from datetime import date, timedelta

import httpx
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings

log = structlog.get_logger()

MP_API = "https://api.mercadopago.com"

# Da carência ao corte de escrita, e do corte à suspensão. A régua inteira em
# dois números: avisa, depois trava a escrita, e só então suspende.
DIAS_CARENCIA = 5
DIAS_SOMENTE_LEITURA = 7


def _headers() -> dict:
    token = settings.PLATAFORMA_MP_ACCESS_TOKEN
    if not token:
        raise RuntimeError("PLATAFORMA_MP_ACCESS_TOKEN não configurado")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def criar_assinatura(
    db: AsyncSession, empresa_id: int, plano: str, valor: float, email_pagador: str
) -> dict:
    """Cria o preapproval no MP e devolve o link para o lojista assinar."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{MP_API}/preapproval",
            headers=_headers(),
            json={
                "reason": f"Runas ERP — plano {plano}",
                "payer_email": email_pagador,
                "back_url": f"{settings.FRONTEND_URL}/plataforma",
                "auto_recurring": {
                    "frequency": 1,
                    "frequency_type": "months",
                    "transaction_amount": float(valor),
                    "currency_id": "BRL",
                },
            },
        )
    resp.raise_for_status()
    dados = resp.json()

    vence = date.today() + timedelta(days=30)
    await db.execute(
        text(
            "INSERT INTO gateway.assinaturas "
            "(empresa_id, plano, valor, mp_preapproval_id, status, vence_em, carencia_ate) "
            "VALUES (:e, :p, :v, :mp, 'PENDENTE', :vence, :carencia) "
            "ON CONFLICT (empresa_id) DO UPDATE SET plano = :p, valor = :v, "
            "mp_preapproval_id = :mp, status = 'PENDENTE', vence_em = :vence, "
            "carencia_ate = :carencia, atualizado_em = now()"
        ),
        {
            "e": empresa_id, "p": plano, "v": valor, "mp": dados.get("id"),
            "vence": vence, "carencia": vence + timedelta(days=DIAS_CARENCIA),
        },
    )
    await db.commit()

    log.info("plataforma.assinatura_criada", empresa_id=empresa_id, preapproval=dados.get("id"))
    return {"preapproval_id": dados.get("id"), "init_point": dados.get("init_point")}


async def cancelar_assinatura(db: AsyncSession, empresa_id: int) -> bool:
    """Cancela no MP e marca localmente. Sem assinatura, devolve False."""
    mp_id = await db.scalar(
        text("SELECT mp_preapproval_id FROM gateway.assinaturas WHERE empresa_id = :e"),
        {"e": empresa_id},
    )
    if not mp_id:
        return False

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{MP_API}/preapproval/{mp_id}", headers=_headers(), json={"status": "cancelled"}
        )
    resp.raise_for_status()

    await db.execute(
        text(
            "UPDATE gateway.assinaturas SET status = 'CANCELADA', atualizado_em = now() "
            "WHERE empresa_id = :e"
        ),
        {"e": empresa_id},
    )
    await db.commit()
    log.info("plataforma.assinatura_cancelada", empresa_id=empresa_id)
    return True


async def registrar_pagamento(db: AsyncSession, mp_preapproval_id: str) -> int | None:
    """
    Pagamento confirmado: empurra o vencimento e devolve o tenant ao normal.

    Vale em qualquer estágio da régua, inclusive suspenso — quem pagou volta a
    operar no request seguinte, e é a reativação que o suporte não deveria
    precisar fazer à mão.
    """
    vence = date.today() + timedelta(days=30)
    empresa_id = await db.scalar(
        text(
            "UPDATE gateway.assinaturas SET status = 'ATIVA', vence_em = :vence, "
            "carencia_ate = :carencia, somente_leitura_desde = NULL, "
            "atualizado_em = now() WHERE mp_preapproval_id = :mp RETURNING empresa_id"
        ),
        {"mp": mp_preapproval_id, "vence": vence,
         "carencia": vence + timedelta(days=DIAS_CARENCIA)},
    )
    if empresa_id:
        # Suspensão corta pelos usuários (ver _definir_acesso); pagar devolve.
        await db.execute(
            text("UPDATE gateway.usuarios SET ativo = TRUE WHERE empresa_id = :e"),
            {"e": empresa_id},
        )
    await db.commit()
    log.info("plataforma.pagamento_confirmado", empresa_id=empresa_id, preapproval=mp_preapproval_id)
    return empresa_id


async def aplicar_regua(db: AsyncSession) -> dict:
    """
    Varredura diária de vencimentos. Uma query em assinaturas, nenhum dado de
    tenant percorrido — cabe de sobra numa VPS de 1 vCPU.

    Passou a carência: somente leitura. Sete dias assim: suspensão.
    """
    hoje = date.today()

    somente_leitura = (await db.execute(
        text(
            "UPDATE gateway.assinaturas SET somente_leitura_desde = :hoje, "
            "status = 'INADIMPLENTE', atualizado_em = now() "
            "WHERE carencia_ate < :hoje AND somente_leitura_desde IS NULL "
            "AND status <> 'CANCELADA' RETURNING empresa_id"
        ),
        {"hoje": hoje},
    )).scalars().all()

    suspender = (await db.execute(
        text(
            "UPDATE gateway.assinaturas SET status = 'SUSPENSA', atualizado_em = now() "
            "WHERE somente_leitura_desde <= :limite AND status = 'INADIMPLENTE' "
            "RETURNING empresa_id"
        ),
        {"limite": hoje - timedelta(days=DIAS_SOMENTE_LEITURA)},
    )).scalars().all()

    for empresa_id in suspender:
        await db.execute(
            text("UPDATE gateway.usuarios SET ativo = FALSE WHERE empresa_id = :e"),
            {"e": empresa_id},
        )

    # Poda: sem retenção, a auditoria enche o disco de 50GB antes dos dados.
    podados = (await db.execute(
        text(
            "DELETE FROM gateway.auditoria_registros "
            "WHERE criado_em < now() - INTERVAL '180 days'"
        )
    )).rowcount
    podados += (await db.execute(
        text("DELETE FROM gateway.auditoria WHERE criado_em < now() - INTERVAL '180 days'")
    )).rowcount

    await db.commit()
    log.info(
        "plataforma.regua_aplicada",
        somente_leitura=len(somente_leitura), suspensos=len(suspender), podados=podados,
    )
    return {
        "somente_leitura": list(somente_leitura),
        "suspensos": list(suspender),
        "auditoria_podada": podados,
    }
