"""Conferência visual de recebimento: valida e resume, nunca escreve."""
from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends

from schemas.conferencia_visual import (
    LIMIAR_CONFIANCA,
    ConferenciaVisualRequest,
    ConferenciaVisualResponse,
)
from utils.tenant import get_empresa_id

router = APIRouter(prefix="/estoque/conferencia-visual", tags=["Conferência visual"])


@router.post("", response_model=ConferenciaVisualResponse)
async def conferir(
    dados: ConferenciaVisualRequest,
    _empresa_id: Annotated[int, Depends(get_empresa_id)],
):
    """Resume o que o modelo do navegador detectou. Sem banco, sem efeito colateral."""
    aceitas = [d for d in dados.detecoes if d.confianca >= LIMIAR_CONFIANCA]
    return ConferenciaVisualResponse(
        total_detectado=len(dados.detecoes),
        total_aceito=len(aceitas),
        contagem_por_rotulo=dict(Counter(d.rotulo for d in aceitas)),
    )
