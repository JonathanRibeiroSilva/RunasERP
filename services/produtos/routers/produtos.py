"""
Routers FastAPI para Produtos.
"""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from utils.tenant import get_empresa_id
from schemas.produtos import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
    ProdutoCreate,
    ProdutoRead,
    ProdutoReadSimples,
    ProdutoLojaOnlineRead,
    ProdutoUpdate,
    VarianteCreate,
    VarianteRead,
    VarianteUpdate,
    AtributoVarianteBase,
    LojaOnlineConfigCreate,
    LojaOnlineConfigRead,
    LojaOnlineConfigUpdate,
    LojaOnlineFotoCreate,
    LojaOnlineFotoRead,
    LojaOnlineFotoUpdate,
    FornecedorCreate,
    FornecedorRead,
    FornecedorUpdate,
    FornecedorProdutoCreate,
    FornecedorProdutoRead,
    FornecedorProdutoUpdate,
)
from services.produtos import (
    CategoriaService,
    ProdutoService,
    VarianteService,
    LojaOnlineService,
    FornecedorService,
    FornecedorProdutoService,
)


# ======================== ROUTER CATEGORIAS ========================

router_categorias = APIRouter(prefix="/categorias", tags=["categorias"])


@router_categorias.post("", response_model=CategoriaRead, status_code=201)
async def criar_categoria(
    dados: CategoriaCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Cria uma nova categoria."""
    # Validar que empresa_id do body corresponde ao header
    if dados.empresa_id != empresa_id:
        raise HTTPException(status_code=403, detail="empresa_id do body não corresponde ao header X-Empresa-Id")
    
    try:
        service = CategoriaService(session)
        categoria = await service.criar_categoria(empresa_id, dados)
        return categoria
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar categoria")


@router_categorias.get("/{categoria_id}", response_model=CategoriaRead)
async def obter_categoria(
    categoria_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Obtém uma categoria por ID."""
    try:
        service = CategoriaService(session)
        return await service.obter_categoria(empresa_id, categoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_categorias.get("", response_model=dict)
async def listar_categorias(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    """Lista todas as categorias."""
    service = CategoriaService(session)
    categorias, total = await service.listar_categorias(empresa_id=empresa_id, skip=skip, limit=limit)
    # Converter modelos SQLAlchemy para schemas Pydantic
    categorias_response = [CategoriaRead.model_validate(cat) for cat in categorias]
    return {"total": total, "skip": skip, "limit": limit, "items": categorias_response}


@router_categorias.put("/{categoria_id}", response_model=CategoriaRead)
async def atualizar_categoria(
    categoria_id: UUID,
    dados: CategoriaUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Atualiza uma categoria."""
    try:
        service = CategoriaService(session)
        categoria = await service.atualizar_categoria(empresa_id, categoria_id, dados)
        return categoria
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar categoria")


@router_categorias.delete("/{categoria_id}", status_code=204)
async def deletar_categoria(
    categoria_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Deleta uma categoria."""
    try:
        service = CategoriaService(session)
        await service.deletar_categoria(empresa_id, categoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar categoria")


# ======================== ROUTER PRODUTOS ========================

router_produtos = APIRouter(prefix="/produtos", tags=["produtos"])


@router_produtos.post("", response_model=ProdutoRead, status_code=201)
async def criar_produto(
    dados: ProdutoCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Cria um novo produto."""
    # Validar que empresa_id do body corresponde ao header
    if dados.empresa_id != empresa_id:
        raise HTTPException(status_code=403, detail="empresa_id do body não corresponde ao header X-Empresa-Id")
    
    try:
        service = ProdutoService(session)
        produto = await service.criar_produto(empresa_id, dados)
        # Recarregar para incluir relacionamentos
        return await service.obter_produto(empresa_id, produto.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar produto")


@router_produtos.get("/{produto_id}", response_model=ProdutoRead)
async def obter_produto(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Obtém um produto por ID."""
    try:
        service = ProdutoService(session)
        return await service.obter_produto(empresa_id, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_produtos.get("", response_model=dict)
async def listar_produtos(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    apenas_deletados: bool = Query(False),
    session: AsyncSession = Depends(get_db),
):
    """
    Lista produtos.
    
    Args:
        apenas_deletados: False = todos não deletados, True = apenas deletados
    """
    service = ProdutoService(session)
    produtos, total = await service.listar_produtos(
        empresa_id=empresa_id,
        skip=skip, 
        limit=limit, 
        apenas_deletados=apenas_deletados
    )
    # Converter modelos SQLAlchemy para schemas Pydantic (usando schema simplificado)
    produtos_response = [ProdutoReadSimples.model_validate(prod) for prod in produtos]
    return {"total": total, "skip": skip, "limit": limit, "items": produtos_response}


@router_produtos.get("/categoria/{categoria_id}", response_model=dict)
async def listar_por_categoria(
    categoria_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """Lista produtos de uma categoria."""
    try:
        service = ProdutoService(session)
        produtos, total = await service.listar_por_categoria(empresa_id, categoria_id, skip=skip, limit=limit)
        # Converter modelos SQLAlchemy para schemas Pydantic
        produtos_response = [ProdutoRead.model_validate(prod) for prod in produtos]
        return {"total": total, "skip": skip, "limit": limit, "items": produtos_response}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_produtos.get("/buscar/nome", response_model=list)
async def buscar_por_nome(
    nome: str = Query(..., min_length=3),
    empresa_id: Annotated[int, Depends(get_empresa_id)] = None,
    session: AsyncSession = Depends(get_db)
):
    """Busca produtos por nome."""
    try:
        service = ProdutoService(session)
        produtos = await service.buscar_por_nome(empresa_id, nome)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [ProdutoReadSimples.model_validate(prod) for prod in produtos]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_produtos.put("/{produto_id}", response_model=ProdutoRead)
async def atualizar_produto(
    produto_id: UUID,
    dados: ProdutoUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Atualiza um produto."""
    try:
        service = ProdutoService(session)
        produto = await service.atualizar_produto(empresa_id, produto_id, dados)
        return await service.obter_produto(empresa_id, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar produto")


@router_produtos.delete("/{produto_id}", status_code=204)
async def deletar_produto(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Soft delete de um produto."""
    try:
        service = ProdutoService(session)
        await service.deletar_produto(empresa_id, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar produto")


@router_produtos.patch("/{produto_id}/restaurar", status_code=204)
async def restaurar_produto(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Restaura um produto deletado."""
    try:
        service = ProdutoService(session)
        await service.restaurar_produto(empresa_id, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao restaurar produto")


# ======================== ROUTER VARIANTES ========================

router_variantes = APIRouter(prefix="/variantes", tags=["variantes"])


@router_variantes.post("", response_model=VarianteRead, status_code=201)
async def criar_variante(
    dados: VarianteCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Cria uma nova variante."""
    # Validar que empresa_id do body corresponde ao header
    if dados.empresa_id != empresa_id:
        raise HTTPException(status_code=403, detail="empresa_id do body não corresponde ao header X-Empresa-Id")
    
    try:
        service = VarianteService(session)
        variante = await service.criar_variante(empresa_id, dados)
        return await service.obter_variante(empresa_id, variante.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar variante")


@router_variantes.get("/{variante_id}", response_model=VarianteRead)
async def obter_variante(
    variante_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Obtém uma variante por ID."""
    try:
        service = VarianteService(session)
        return await service.obter_variante(empresa_id, variante_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_variantes.get("/produto/{produto_id}", response_model=list)
async def listar_variantes_produto(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Lista variantes de um produto."""
    try:
        service = VarianteService(session)
        variantes = await service.listar_por_produto(empresa_id, produto_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [VarianteRead.model_validate(var) for var in variantes]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_variantes.put("/{variante_id}", response_model=VarianteRead)
async def atualizar_variante(
    variante_id: UUID,
    dados: VarianteUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Atualiza uma variante."""
    try:
        service = VarianteService(session)
        variante = await service.atualizar_variante(empresa_id, variante_id, dados)
        return await service.obter_variante(empresa_id, variante_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar variante")


@router_variantes.delete("/{variante_id}", status_code=204)
async def deletar_variante(
    variante_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Deleta uma variante."""
    try:
        service = VarianteService(session)
        await service.deletar_variante(empresa_id, variante_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar variante")


# ======================== ROUTER LOJA ONLINE PÚBLICA ========================

router_loja_online_publico = APIRouter(prefix="/loja-online/publico", tags=["loja-online-publico"])


async def get_empresa_id_from_slug(
    slug: str = Query(..., description="Slug da empresa (ex: distribuidora-central)"),
    session: AsyncSession = Depends(get_db)
) -> int:
    """
    Resolve o empresa_id a partir do slug da empresa.
    
    Consulta direto no banco de dados o schema empresas.
    """
    from sqlalchemy import text
    
    try:
        # Query direto no schema empresas (cross-schema query)
        query = text("""
            SELECT id 
            FROM empresas.empresas 
            WHERE slug = :slug AND status = 'ATIVA'
            LIMIT 1
        """)
        
        result = await session.execute(query, {"slug": slug})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=404, 
                detail=f"Empresa com slug '{slug}' não encontrada"
            )
        
        return row[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Erro ao consultar empresa"
        )


@router_loja_online_publico.get("/produtos", response_model=dict)
async def listar_produtos_loja_online_publico(
    empresaSlug: str = Query(..., description="Slug da empresa"),
    categoria_id: UUID | None = Query(None),
    busca: str | None = Query(None, min_length=2),
    ordenar: str = Query("nome", regex="^(nome|preco_asc|preco_desc|recentes)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """
    Lista produtos visíveis na loja online pública.
    
    Retorna apenas produtos com:
    - ativo = True
    - loja_online_config.visivel = True
    
    Query params:
    - empresaSlug: slug da empresa (obrigatório)
    - categoria_id: filtrar por categoria (opcional)
    - busca: buscar por nome (opcional)
    - ordenar: nome|preco_asc|preco_desc|recentes (padrão: nome)
    - skip/limit: paginação
    """
    try:
        # Resolver empresa_id a partir do slug
        empresa_id = await get_empresa_id_from_slug(empresaSlug, session)
        
        service = ProdutoService(session)
        
        # TODO: Filtrar apenas produtos com loja_online_config.visivel = True
        # Por enquanto, retorna todos os produtos ativos
        produtos, total = await service.listar_produtos(
            empresa_id=empresa_id,
            skip=skip, 
            limit=limit, 
            apenas_ativos=True
        )
        
        # Filtrar por categoria se fornecido
        if categoria_id:
            produtos = [p for p in produtos if p.categoria_id == categoria_id]
            total = len(produtos)
        
        # Buscar por nome se fornecido
        if busca:
            produtos = [p for p in produtos if busca.lower() in p.nome.lower()]
            total = len(produtos)
        
        # Converter para schema simplificado
        produtos_response = [ProdutoReadSimples.model_validate(prod) for prod in produtos]
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": produtos_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao listar produtos da loja online")


@router_loja_online_publico.get("/categorias", response_model=dict)
async def listar_categorias_loja_online_publico(
    empresaSlug: str = Query(..., description="Slug da empresa"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    """Lista categorias da loja online pública."""
    try:
        empresa_id = await get_empresa_id_from_slug(empresaSlug, session)
        service = CategoriaService(session)
        categorias, total = await service.listar_categorias(
            empresa_id=empresa_id,
            skip=skip,
            limit=limit
        )
        categorias_response = [CategoriaRead.model_validate(cat) for cat in categorias]
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": categorias_response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar categorias: {str(e)}")


@router_loja_online_publico.get("/produto/{produto_id}", response_model=ProdutoLojaOnlineRead)
async def obter_produto_loja_online_publico(
    produto_id: UUID,
    empresaSlug: str = Query(..., description="Slug da empresa"),
    session: AsyncSession = Depends(get_db),
):
    """Obtém detalhes de um produto na loja online pública."""
    try:
        empresa_id = await get_empresa_id_from_slug(empresaSlug, session)
        service = ProdutoService(session)
        produto = await service.obter_produto(empresa_id, produto_id)
        
        if not produto.ativo:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        
        return ProdutoLojaOnlineRead.model_validate(produto)
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter produto: {str(e)}")


# ======================== ROUTER LOJA ONLINE ========================

router_loja_online = APIRouter(prefix="/loja-online", tags=["loja-online"])


@router_loja_online.post("/config", response_model=LojaOnlineConfigRead, status_code=201)
async def criar_config_loja_online(
    dados: LojaOnlineConfigCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Cria configuração de loja online."""
    try:
        service = LojaOnlineService(session)
        config = await service.criar_config(empresa_id, dados)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar config de loja online")


@router_loja_online.get("/config/{produto_id}", response_model=LojaOnlineConfigRead)
async def obter_config_loja_online(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Obtém configuração de loja online."""
    try:
        service = LojaOnlineService(session)
        return await service.obter_config(empresa_id, produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_loja_online.put("/config/{config_id}", response_model=LojaOnlineConfigRead)
async def atualizar_config_loja_online(
    config_id: UUID,
    dados: LojaOnlineConfigUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Atualiza configuração de loja online."""
    try:
        service = LojaOnlineService(session)
        config = await service.atualizar_config(empresa_id, config_id, dados)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar config de loja online")


@router_loja_online.post("/fotos", response_model=LojaOnlineFotoRead, status_code=201)
async def adicionar_foto_loja_online(
    dados: LojaOnlineFotoCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Adiciona foto à loja online."""
    try:
        service = LojaOnlineService(session)
        foto = await service.adicionar_foto(empresa_id, dados)
        return foto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao adicionar foto")


@router_loja_online.get("/fotos/{produto_id}", response_model=list)
async def listar_fotos_loja_online(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Lista fotos de um produto."""
    try:
        service = LojaOnlineService(session)
        fotos = await service.listar_fotos(empresa_id, produto_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [LojaOnlineFotoRead.model_validate(foto) for foto in fotos]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_loja_online.put("/fotos/{foto_id}", response_model=LojaOnlineFotoRead)
async def atualizar_foto_loja_online(
    foto_id: UUID,
    dados: LojaOnlineFotoUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Atualiza uma foto."""
    try:
        service = LojaOnlineService(session)
        foto = await service.atualizar_foto(empresa_id, foto_id, dados)
        return foto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar foto")


@router_loja_online.delete("/fotos/{foto_id}", status_code=204)
async def deletar_foto_loja_online(
    foto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Deleta uma foto."""
    try:
        service = LojaOnlineService(session)
        await service.deletar_foto(empresa_id, foto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar foto")


# ======================== ROUTER FORNECEDORES ========================

router_fornecedores = APIRouter(prefix="/fornecedores", tags=["fornecedores"])


@router_fornecedores.post("", response_model=FornecedorRead, status_code=201)
async def criar_fornecedor(
    dados: FornecedorCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Cria um novo fornecedor."""
    # Validar que empresa_id do body corresponde ao header
    if dados.empresa_id != empresa_id:
        raise HTTPException(status_code=403, detail="empresa_id do body não corresponde ao header X-Empresa-Id")
    
    try:
        service = FornecedorService(session)
        fornecedor = await service.criar_fornecedor(empresa_id, dados)
        return fornecedor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar fornecedor")


@router_fornecedores.get("/{fornecedor_id}", response_model=FornecedorRead)
async def obter_fornecedor(
    fornecedor_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Obtém um fornecedor por ID."""
    try:
        service = FornecedorService(session)
        return await service.obter_fornecedor(empresa_id, fornecedor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedores.get("", response_model=dict)
async def listar_fornecedores(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    apenas_ativos: bool = Query(True),
    session: AsyncSession = Depends(get_db),
):
    """Lista todos os fornecedores."""
    service = FornecedorService(session)
    fornecedores, total = await service.listar_fornecedores(empresa_id=empresa_id, skip=skip, limit=limit, apenas_ativos=apenas_ativos)
    # Converter modelos SQLAlchemy para schemas Pydantic
    fornecedores_response = [FornecedorRead.model_validate(forn) for forn in fornecedores]
    return {"total": total, "skip": skip, "limit": limit, "items": fornecedores_response}


@router_fornecedores.put("/{fornecedor_id}", response_model=FornecedorRead)
async def atualizar_fornecedor(
    fornecedor_id: UUID,
    dados: FornecedorUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Atualiza um fornecedor."""
    try:
        service = FornecedorService(session)
        fornecedor = await service.atualizar_fornecedor(empresa_id, fornecedor_id, dados)
        return fornecedor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar fornecedor")


@router_fornecedores.delete("/{fornecedor_id}", status_code=204)
async def deletar_fornecedor(
    fornecedor_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Deleta um fornecedor."""
    try:
        service = FornecedorService(session)
        await service.deletar_fornecedor(empresa_id, fornecedor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar fornecedor")


# ======================== ROUTER FORNECEDOR PRODUTOS ========================

router_fornecedor_produtos = APIRouter(prefix="/fornecedor-produtos", tags=["fornecedor-produtos"])


@router_fornecedor_produtos.post("", response_model=FornecedorProdutoRead, status_code=201)
async def vincular_fornecedor_produto(
    dados: FornecedorProdutoCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Vincula um fornecedor a um produto."""
    try:
        service = FornecedorProdutoService(session)
        vinculo = await service.vincular_fornecedor(empresa_id, dados)
        return vinculo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao vincular fornecedor")


@router_fornecedor_produtos.get("/{vinculo_id}", response_model=FornecedorProdutoRead)
async def obter_vinculo(
    vinculo_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Obtém um vínculo fornecedor-produto."""
    try:
        service = FornecedorProdutoService(session)
        return await service.obter_vinculo(empresa_id, vinculo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedor_produtos.get("/produto/{produto_id}", response_model=list)
async def listar_fornecedores_produto(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Lista fornecedores de um produto."""
    try:
        service = FornecedorProdutoService(session)
        vinculos = await service.listar_fornecedores_produto(empresa_id, produto_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [FornecedorProdutoRead.model_validate(vinc) for vinc in vinculos]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedor_produtos.get("/fornecedor/{fornecedor_id}", response_model=list)
async def listar_produtos_fornecedor(
    fornecedor_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Lista produtos de um fornecedor."""
    try:
        service = FornecedorProdutoService(session)
        vinculos = await service.listar_produtos_fornecedor(empresa_id, fornecedor_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [FornecedorProdutoRead.model_validate(vinc) for vinc in vinculos]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedor_produtos.put("/{vinculo_id}", response_model=FornecedorProdutoRead)
async def atualizar_vinculo(
    vinculo_id: UUID,
    dados: FornecedorProdutoUpdate,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Atualiza um vínculo fornecedor-produto."""
    try:
        service = FornecedorProdutoService(session)
        vinculo = await service.atualizar_vinculo(empresa_id, vinculo_id, dados)
        return vinculo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar vínculo")


@router_fornecedor_produtos.delete("/{vinculo_id}", status_code=204)
async def deletar_vinculo(
    vinculo_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    session: AsyncSession = Depends(get_db)
):
    """Deleta um vínculo fornecedor-produto."""
    try:
        service = FornecedorProdutoService(session)
        await service.deletar_vinculo(empresa_id, vinculo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar vínculo")
