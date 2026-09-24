"""
Router de autenticação ADMIN - para criar usuários operadores.
Requer permissão de ADMIN.
"""
from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from sqlalchemy import func, select

from config import settings
from interno import auth_interno
from database import get_db
from repositories.usuario_repository import UsuarioRepository
from auth.oauth2 import require_admin
from schemas.usuario import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from models.usuario import Usuario, RoleEnum


router = APIRouter(prefix="/auth/admin", tags=["Autenticação Admin"])
log = structlog.get_logger()


async def _carregar_do_tenant(repo: UsuarioRepository, user_id: UUID, admin: Usuario) -> Usuario:
    """
    Carrega o usuário alvo garantindo que ele é do mesmo tenant do admin.

    404 e não 403 de propósito: um 403 confirmaria que o id existe em outro
    tenant, e a existência de um usuário já é informação sobre o outro lojista.
    """
    alvo = await repo.buscar_por_id(user_id)
    if not alvo or alvo.empresa_id != admin.empresa_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
    return alvo


async def _garantir_invariantes(db, admin: Usuario, alvo: Usuario, data: UsuarioUpdate) -> None:
    """
    As duas formas de um tenant se trancar para fora, barradas num lugar só.

    Chamada pelo PUT e pelo DELETE porque desativar é um caso particular de
    editar: proteger só o PUT deixaria o DELETE apagando o último admin.
    """
    if data.role is not None and data.role == RoleEnum.SUPER_ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "SUPER_ADMIN não é um papel de tenant")

    virou_inativo = data.ativo is False
    perdeu_admin = data.role is not None and data.role != RoleEnum.ADMIN

    if alvo.id == admin.id and (virou_inativo or perdeu_admin):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Você não pode desativar nem rebaixar a própria conta"
        )

    if alvo.role == RoleEnum.ADMIN and (virou_inativo or perdeu_admin):
        restantes = await db.scalar(
            select(func.count()).select_from(Usuario).where(
                Usuario.empresa_id == admin.empresa_id,
                Usuario.role == RoleEnum.ADMIN,
                Usuario.ativo.is_(True),
                Usuario.id != alvo.id,
            )
        )
        if not restantes:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "A empresa ficaria sem nenhum administrador ativo"
            )


async def _limite_de_usuarios(empresa_id: int) -> int | None:
    """Limite do plano, lido no serviço empresas. None = sem limite conhecido."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{settings.EMPRESAS_URL}/empresas/{empresa_id}",
            headers=auth_interno({"X-Empresa-Id": str(empresa_id)}),
        )
    if resp.status_code != 200:
        return None
    return resp.json().get("max_usuarios")


@router.get("/usuarios", summary="Listar usuários da empresa")
async def listar_usuarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Usuario, Depends(require_admin)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Usuários do próprio tenant. O filtro mora no repositório, não aqui."""
    usuarios, total = await UsuarioRepository(db).listar(
        empresa_id=admin.empresa_id, skip=skip, limit=limit
    )
    # O limite do plano conta ATIVOS (ver o POST): devolver só `total` fazia a
    # tela travar o botão antes do backend, contando usuários desativados.
    ativos = await db.scalar(
        select(func.count()).select_from(Usuario).where(
            Usuario.empresa_id == admin.empresa_id,
            Usuario.ativo.is_(True),
        )
    )
    return {
        "items": [UsuarioResponse.model_validate(u) for u in usuarios],
        "total": total,
        "ativos": ativos,
        "skip": skip,
        "limit": limit,
        "max_usuarios": await _limite_de_usuarios(admin.empresa_id),
    }


@router.put("/usuarios/{user_id}", response_model=UsuarioResponse)
async def atualizar_usuario(
    user_id: UUID,
    data: UsuarioUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Usuario, Depends(require_admin)],
):
    """Atualiza um usuário do próprio tenant."""
    repo = UsuarioRepository(db)
    alvo = await _carregar_do_tenant(repo, user_id, admin)
    await _garantir_invariantes(db, admin, alvo, data)

    if data.email and data.email != alvo.email:
        if await repo.buscar_por_email(data.email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email já cadastrado")

    usuario = await repo.atualizar(user_id, data)
    log.info("admin.atualizar_usuario", user_id=str(user_id), by=str(admin.id))
    return usuario


@router.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desativar_usuario(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Usuario, Depends(require_admin)],
):
    """Soft delete: o usuário perde o acesso no request seguinte, o histórico fica."""
    repo = UsuarioRepository(db)
    alvo = await _carregar_do_tenant(repo, user_id, admin)
    await _garantir_invariantes(db, admin, alvo, UsuarioUpdate(ativo=False))
    await repo.deletar(user_id)
    log.info("admin.desativar_usuario", user_id=str(user_id), by=str(admin.id))


@router.post("/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario_operador(
    data: UsuarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[Usuario, Depends(require_admin)]
):
    """
    Cria um novo usuário operador (ADMIN ou OPERADOR).
    
    Apenas usuários ADMIN podem criar novos operadores.
    O novo usuário será vinculado à mesma empresa do ADMIN.
    """
    if data.role == RoleEnum.SUPER_ADMIN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "SUPER_ADMIN não é um papel de tenant")

    limite = await _limite_de_usuarios(admin.empresa_id)
    if limite is not None:
        ativos = await db.scalar(
            select(func.count()).select_from(Usuario).where(
                Usuario.empresa_id == admin.empresa_id,
                Usuario.ativo.is_(True),
            )
        )
        if ativos >= limite:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Limite do plano atingido: {ativos} de {limite} usuários"
            )

    repo = UsuarioRepository(db)
    
    # Verificar se email já existe
    existing = await repo.buscar_por_email(data.email)
    if existing:
        log.warning("admin.criar_usuario.email_exists", 
                   email=data.email, 
                   admin_id=str(admin.id))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Forçar empresa_id do admin (não confiar no body)
    data.empresa_id = admin.empresa_id
    
    # Criar usuário
    usuario = await repo.criar(data)
    
    log.info("admin.criar_usuario.success", 
             user_id=str(usuario.id), 
             email=usuario.email, 
             role=usuario.role.value,
             empresa_id=usuario.empresa_id,
             created_by=str(admin.id))
    
    return usuario
