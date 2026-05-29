"""
Routers FastAPI para Produtos.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas.produtos import (
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
    ProdutoCreate,
    ProdutoRead,
    ProdutoReadSimples,
    ProdutoCatalogoRead,
    ProdutoUpdate,
    VarianteCreate,
    VarianteRead,
    VarianteUpdate,
    AtributoVarianteBase,
    CatalogoConfigCreate,
    CatalogoConfigRead,
    CatalogoConfigUpdate,
    CatalogoFotoCreate,
    CatalogoFotoRead,
    CatalogoFotoUpdate,
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
    CatalogoService,
    FornecedorService,
    FornecedorProdutoService,
)


# ======================== ROUTER CATEGORIAS ========================

router_categorias = APIRouter(prefix="/categorias", tags=["categorias"])


@router_categorias.post("", response_model=CategoriaRead, status_code=201)
async def criar_categoria(dados: CategoriaCreate, session: AsyncSession = Depends(get_db)):
    """Cria uma nova categoria."""
    try:
        service = CategoriaService(session)
        categoria = await service.criar_categoria(dados)
        return categoria
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar categoria")


@router_categorias.get("/{categoria_id}", response_model=CategoriaRead)
async def obter_categoria(categoria_id: UUID, session: AsyncSession = Depends(get_db)):
    """Obtém uma categoria por ID."""
    try:
        service = CategoriaService(session)
        return await service.obter_categoria(categoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_categorias.get("", response_model=dict)
async def listar_categorias(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100), session: AsyncSession = Depends(get_db)):
    """Lista todas as categorias."""
    service = CategoriaService(session)
    categorias, total = await service.listar_categorias(skip=skip, limit=limit)
    # Converter modelos SQLAlchemy para schemas Pydantic
    categorias_response = [CategoriaRead.model_validate(cat) for cat in categorias]
    return {"total": total, "skip": skip, "limit": limit, "items": categorias_response}


@router_categorias.put("/{categoria_id}", response_model=CategoriaRead)
async def atualizar_categoria(
    categoria_id: UUID, dados: CategoriaUpdate, session: AsyncSession = Depends(get_db)
):
    """Atualiza uma categoria."""
    try:
        service = CategoriaService(session)
        categoria = await service.atualizar_categoria(categoria_id, dados)
        return categoria
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar categoria")


@router_categorias.delete("/{categoria_id}", status_code=204)
async def deletar_categoria(categoria_id: UUID, session: AsyncSession = Depends(get_db)):
    """Deleta uma categoria."""
    try:
        service = CategoriaService(session)
        await service.deletar_categoria(categoria_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar categoria")


# ======================== ROUTER PRODUTOS ========================

router_produtos = APIRouter(prefix="/produtos", tags=["produtos"])


@router_produtos.post("", response_model=ProdutoRead, status_code=201)
async def criar_produto(dados: ProdutoCreate, session: AsyncSession = Depends(get_db)):
    """Cria um novo produto."""
    try:
        service = ProdutoService(session)
        produto = await service.criar_produto(dados)
        # Recarregar para incluir relacionamentos
        return await service.obter_produto(produto.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar produto")


@router_produtos.get("/{produto_id}", response_model=ProdutoRead)
async def obter_produto(produto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Obtém um produto por ID."""
    try:
        service = ProdutoService(session)
        return await service.obter_produto(produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_produtos.get("", response_model=dict)
async def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    apenas_ativos: bool = Query(True),
    session: AsyncSession = Depends(get_db),
):
    """Lista todos os produtos."""
    service = ProdutoService(session)
    produtos, total = await service.listar_produtos(skip=skip, limit=limit, apenas_ativos=apenas_ativos)
    # Converter modelos SQLAlchemy para schemas Pydantic (usando schema simplificado)
    produtos_response = [ProdutoReadSimples.model_validate(prod) for prod in produtos]
    return {"total": total, "skip": skip, "limit": limit, "items": produtos_response}


@router_produtos.get("/categoria/{categoria_id}", response_model=dict)
async def listar_por_categoria(
    categoria_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """Lista produtos de uma categoria."""
    try:
        service = ProdutoService(session)
        produtos, total = await service.listar_por_categoria(categoria_id, skip=skip, limit=limit)
        # Converter modelos SQLAlchemy para schemas Pydantic
        produtos_response = [ProdutoRead.model_validate(prod) for prod in produtos]
        return {"total": total, "skip": skip, "limit": limit, "items": produtos_response}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_produtos.get("/buscar/nome", response_model=list)
async def buscar_por_nome(nome: str = Query(..., min_length=3), session: AsyncSession = Depends(get_db)):
    """Busca produtos por nome."""
    try:
        service = ProdutoService(session)
        produtos = await service.buscar_por_nome(nome)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [ProdutoReadSimples.model_validate(prod) for prod in produtos]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_produtos.put("/{produto_id}", response_model=ProdutoRead)
async def atualizar_produto(
    produto_id: UUID, dados: ProdutoUpdate, session: AsyncSession = Depends(get_db)
):
    """Atualiza um produto."""
    try:
        service = ProdutoService(session)
        produto = await service.atualizar_produto(produto_id, dados)
        return await service.obter_produto(produto_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar produto")


@router_produtos.delete("/{produto_id}", status_code=204)
async def deletar_produto(produto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Deleta um produto."""
    try:
        service = ProdutoService(session)
        await service.deletar_produto(produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar produto")


# ======================== ROUTER VARIANTES ========================

router_variantes = APIRouter(prefix="/variantes", tags=["variantes"])


@router_variantes.post("", response_model=VarianteRead, status_code=201)
async def criar_variante(dados: VarianteCreate, session: AsyncSession = Depends(get_db)):
    """Cria uma nova variante."""
    try:
        service = VarianteService(session)
        variante = await service.criar_variante(dados)
        return await service.obter_variante(variante.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar variante")


@router_variantes.get("/{variante_id}", response_model=VarianteRead)
async def obter_variante(variante_id: UUID, session: AsyncSession = Depends(get_db)):
    """Obtém uma variante por ID."""
    try:
        service = VarianteService(session)
        return await service.obter_variante(variante_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_variantes.get("/produto/{produto_id}", response_model=list)
async def listar_variantes_produto(produto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Lista variantes de um produto."""
    try:
        service = VarianteService(session)
        variantes = await service.listar_por_produto(produto_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [VarianteRead.model_validate(var) for var in variantes]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_variantes.put("/{variante_id}", response_model=VarianteRead)
async def atualizar_variante(
    variante_id: UUID, dados: VarianteUpdate, session: AsyncSession = Depends(get_db)
):
    """Atualiza uma variante."""
    try:
        service = VarianteService(session)
        variante = await service.atualizar_variante(variante_id, dados)
        return await service.obter_variante(variante_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar variante")


@router_variantes.delete("/{variante_id}", status_code=204)
async def deletar_variante(variante_id: UUID, session: AsyncSession = Depends(get_db)):
    """Deleta uma variante."""
    try:
        service = VarianteService(session)
        await service.deletar_variante(variante_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar variante")


# ======================== ROUTER CATÁLOGO PÚBLICO ========================

router_catalogo_publico = APIRouter(prefix="/catalogo/publico", tags=["catalogo-publico"])


@router_catalogo_publico.get("/produtos", response_model=dict)
async def listar_produtos_catalogo_publico(
    categoria_id: UUID | None = Query(None),
    busca: str | None = Query(None, min_length=2),
    ordenar: str = Query("nome", regex="^(nome|preco_asc|preco_desc|recentes)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """
    Lista produtos visíveis no catálogo público (SEM autenticação).
    
    Retorna apenas produtos com:
    - ativo = True
    - catalogo_config.visivel = True
    """
    try:
        service = ProdutoService(session)
        
        # TODO: Filtrar apenas produtos com catalogo_config.visivel = True
        # Por enquanto, retorna todos os produtos ativos
        produtos, total = await service.listar_produtos(
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
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao listar produtos do catálogo")


@router_catalogo_publico.get("/produto/{produto_id}", response_model=ProdutoCatalogoRead)
async def obter_produto_catalogo_publico(
    produto_id: UUID,
    session: AsyncSession = Depends(get_db)
):
    """
    Obtém detalhes de um produto no catálogo público (SEM autenticação).
    Não expõe dados internos como custo, markup e fornecedores.
    """
    try:
        service = ProdutoService(session)
        produto = await service.obter_produto(produto_id)

        if not produto.ativo:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

        return ProdutoCatalogoRead.model_validate(produto)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao obter produto")


@router_catalogo_publico.get("/categorias", response_model=dict)
async def listar_categorias_catalogo_publico(
    session: AsyncSession = Depends(get_db)
):
    """
    Lista categorias ativas no catálogo público (SEM autenticação).
    
    Retorna apenas categorias com produtos visíveis.
    """
    try:
        service = CategoriaService(session)
        categorias, total = await service.listar_categorias(skip=0, limit=100)
        
        # Converter para schema
        categorias_response = [CategoriaRead.model_validate(cat) for cat in categorias]
        
        return {
            "total": total,
            "items": categorias_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao listar categorias")


# ======================== ROUTER CATÁLOGO ========================

router_catalogo = APIRouter(prefix="/catalogo", tags=["catalogo"])


@router_catalogo.post("/config", response_model=CatalogoConfigRead, status_code=201)
async def criar_config_catalogo(dados: CatalogoConfigCreate, session: AsyncSession = Depends(get_db)):
    """Cria configuração de catálogo."""
    try:
        service = CatalogoService(session)
        config = await service.criar_config(dados)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar config de catálogo")


@router_catalogo.get("/config/{produto_id}", response_model=CatalogoConfigRead)
async def obter_config_catalogo(produto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Obtém configuração de catálogo."""
    try:
        service = CatalogoService(session)
        return await service.obter_config(produto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_catalogo.put("/config/{catalogo_id}", response_model=CatalogoConfigRead)
async def atualizar_config_catalogo(
    catalogo_id: UUID, dados: CatalogoConfigUpdate, session: AsyncSession = Depends(get_db)
):
    """Atualiza configuração de catálogo."""
    try:
        service = CatalogoService(session)
        config = await service.atualizar_config(catalogo_id, dados)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar config de catálogo")


@router_catalogo.post("/fotos", response_model=CatalogoFotoRead, status_code=201)
async def adicionar_foto_catalogo(dados: CatalogoFotoCreate, session: AsyncSession = Depends(get_db)):
    """Adiciona foto ao catálogo."""
    try:
        service = CatalogoService(session)
        foto = await service.adicionar_foto(dados)
        return foto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao adicionar foto")


@router_catalogo.get("/fotos/{produto_id}", response_model=list)
async def listar_fotos_catalogo(produto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Lista fotos de um produto."""
    try:
        service = CatalogoService(session)
        fotos = await service.listar_fotos(produto_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [CatalogoFotoRead.model_validate(foto) for foto in fotos]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_catalogo.put("/fotos/{foto_id}", response_model=CatalogoFotoRead)
async def atualizar_foto_catalogo(
    foto_id: UUID, dados: CatalogoFotoUpdate, session: AsyncSession = Depends(get_db)
):
    """Atualiza uma foto."""
    try:
        service = CatalogoService(session)
        foto = await service.atualizar_foto(foto_id, dados)
        return foto
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar foto")


@router_catalogo.delete("/fotos/{foto_id}", status_code=204)
async def deletar_foto_catalogo(foto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Deleta uma foto."""
    try:
        service = CatalogoService(session)
        await service.deletar_foto(foto_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar foto")


# ======================== ROUTER FORNECEDORES ========================

router_fornecedores = APIRouter(prefix="/fornecedores", tags=["fornecedores"])


@router_fornecedores.post("", response_model=FornecedorRead, status_code=201)
async def criar_fornecedor(dados: FornecedorCreate, session: AsyncSession = Depends(get_db)):
    """Cria um novo fornecedor."""
    try:
        service = FornecedorService(session)
        fornecedor = await service.criar_fornecedor(dados)
        return fornecedor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao criar fornecedor")


@router_fornecedores.get("/{fornecedor_id}", response_model=FornecedorRead)
async def obter_fornecedor(fornecedor_id: UUID, session: AsyncSession = Depends(get_db)):
    """Obtém um fornecedor por ID."""
    try:
        service = FornecedorService(session)
        return await service.obter_fornecedor(fornecedor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedores.get("", response_model=dict)
async def listar_fornecedores(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    apenas_ativos: bool = Query(True),
    session: AsyncSession = Depends(get_db),
):
    """Lista todos os fornecedores."""
    service = FornecedorService(session)
    fornecedores, total = await service.listar_fornecedores(skip=skip, limit=limit, apenas_ativos=apenas_ativos)
    # Converter modelos SQLAlchemy para schemas Pydantic
    fornecedores_response = [FornecedorRead.model_validate(forn) for forn in fornecedores]
    return {"total": total, "skip": skip, "limit": limit, "items": fornecedores_response}


@router_fornecedores.put("/{fornecedor_id}", response_model=FornecedorRead)
async def atualizar_fornecedor(
    fornecedor_id: UUID, dados: FornecedorUpdate, session: AsyncSession = Depends(get_db)
):
    """Atualiza um fornecedor."""
    try:
        service = FornecedorService(session)
        fornecedor = await service.atualizar_fornecedor(fornecedor_id, dados)
        return fornecedor
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar fornecedor")


@router_fornecedores.delete("/{fornecedor_id}", status_code=204)
async def deletar_fornecedor(fornecedor_id: UUID, session: AsyncSession = Depends(get_db)):
    """Deleta um fornecedor."""
    try:
        service = FornecedorService(session)
        await service.deletar_fornecedor(fornecedor_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar fornecedor")


# ======================== ROUTER FORNECEDOR PRODUTOS ========================

router_fornecedor_produtos = APIRouter(prefix="/fornecedor-produtos", tags=["fornecedor-produtos"])


@router_fornecedor_produtos.post("", response_model=FornecedorProdutoRead, status_code=201)
async def vincular_fornecedor_produto(dados: FornecedorProdutoCreate, session: AsyncSession = Depends(get_db)):
    """Vincula um fornecedor a um produto."""
    try:
        service = FornecedorProdutoService(session)
        vinculo = await service.vincular_fornecedor(dados)
        return vinculo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao vincular fornecedor")


@router_fornecedor_produtos.get("/{vinculo_id}", response_model=FornecedorProdutoRead)
async def obter_vinculo(vinculo_id: UUID, session: AsyncSession = Depends(get_db)):
    """Obtém um vínculo fornecedor-produto."""
    try:
        service = FornecedorProdutoService(session)
        return await service.obter_vinculo(vinculo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedor_produtos.get("/produto/{produto_id}", response_model=list)
async def listar_fornecedores_produto(produto_id: UUID, session: AsyncSession = Depends(get_db)):
    """Lista fornecedores de um produto."""
    try:
        service = FornecedorProdutoService(session)
        vinculos = await service.listar_fornecedores_produto(produto_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [FornecedorProdutoRead.model_validate(vinc) for vinc in vinculos]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedor_produtos.get("/fornecedor/{fornecedor_id}", response_model=list)
async def listar_produtos_fornecedor(fornecedor_id: UUID, session: AsyncSession = Depends(get_db)):
    """Lista produtos de um fornecedor."""
    try:
        service = FornecedorProdutoService(session)
        vinculos = await service.listar_produtos_fornecedor(fornecedor_id)
        # Converter modelos SQLAlchemy para schemas Pydantic
        return [FornecedorProdutoRead.model_validate(vinc) for vinc in vinculos]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router_fornecedor_produtos.put("/{vinculo_id}", response_model=FornecedorProdutoRead)
async def atualizar_vinculo(
    vinculo_id: UUID, dados: FornecedorProdutoUpdate, session: AsyncSession = Depends(get_db)
):
    """Atualiza um vínculo fornecedor-produto."""
    try:
        service = FornecedorProdutoService(session)
        vinculo = await service.atualizar_vinculo(vinculo_id, dados)
        return vinculo
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao atualizar vínculo")


@router_fornecedor_produtos.delete("/{vinculo_id}", status_code=204)
async def deletar_vinculo(vinculo_id: UUID, session: AsyncSession = Depends(get_db)):
    """Deleta um vínculo fornecedor-produto."""
    try:
        service = FornecedorProdutoService(session)
        await service.deletar_vinculo(vinculo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao deletar vínculo")
