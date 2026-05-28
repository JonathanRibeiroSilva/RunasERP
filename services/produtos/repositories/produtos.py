"""
Repositories para acesso aos dados de Produtos.
"""
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from models.categoria import Categoria
from models.produto import Produto
from models.variante import Variante, AtributoVariante
from models.catalogo import CatalogoConfig, CatalogoFoto
from models.fornecedor import Fornecedor, FornecedorProduto


class CategoriaRepository:
    """Repository para Categoria."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(self, nome: str, descricao: str | None = None) -> Categoria:
        """Cria uma nova categoria."""
        categoria = Categoria(nome=nome, descricao=descricao)
        self.session.add(categoria)
        await self.session.flush()
        return categoria

    async def obter_por_id(self, categoria_id: UUID) -> Categoria | None:
        """Obtém uma categoria por ID."""
        result = await self.session.execute(
            select(Categoria).where(Categoria.id == categoria_id)
        )
        return result.scalars().first()

    async def obter_por_nome(self, nome: str) -> Categoria | None:
        """Obtém uma categoria por nome."""
        result = await self.session.execute(
            select(Categoria).where(Categoria.nome == nome)
        )
        return result.scalars().first()

    async def listar_todas(self, skip: int = 0, limit: int = 10) -> tuple[list[Categoria], int]:
        """Lista todas as categorias com paginação."""
        # Contar total
        count_result = await self.session.execute(select(func.count(Categoria.id)))
        total = count_result.scalar()

        # Buscar com paginação
        result = await self.session.execute(
            select(Categoria).offset(skip).limit(limit)
        )
        return result.scalars().all(), total

    async def atualizar(
        self, categoria_id: UUID, nome: str | None = None, descricao: str | None = None
    ) -> Categoria | None:
        """Atualiza uma categoria."""
        categoria = await self.obter_por_id(categoria_id)
        if not categoria:
            return None

        if nome is not None:
            categoria.nome = nome
        if descricao is not None:
            categoria.descricao = descricao

        await self.session.flush()
        return categoria

    async def deletar(self, categoria_id: UUID) -> bool:
        """Deleta uma categoria."""
        categoria = await self.obter_por_id(categoria_id)
        if not categoria:
            return False

        await self.session.delete(categoria)
        await self.session.flush()
        return True


class ProdutoRepository:
    """Repository para Produto."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(self, categoria_id: UUID, nome: str, descricao: str | None = None) -> Produto:
        """Cria um novo produto."""
        produto = Produto(categoria_id=categoria_id, nome=nome, descricao=descricao)
        self.session.add(produto)
        await self.session.flush()
        return produto

    async def obter_por_id(self, produto_id: UUID) -> Produto | None:
        """Obtém um produto por ID."""
        result = await self.session.execute(
            select(Produto)
            .where(Produto.id == produto_id)
            .options(
                selectinload(Produto.categoria),
                selectinload(Produto.variantes).selectinload(Variante.atributos),
                selectinload(Produto.catalogo_config),
                selectinload(Produto.catalogo_fotos),
                selectinload(Produto.fornecedores)
            )
        )
        return result.scalars().first()

    async def obter_por_nome(self, nome: str) -> list[Produto]:
        """Obtém produtos por nome (busca parcial)."""
        result = await self.session.execute(
            select(Produto).where(Produto.nome.ilike(f"%{nome}%"))
        )
        return result.scalars().all()

    async def listar_por_categoria(
        self, categoria_id: UUID, skip: int = 0, limit: int = 10
    ) -> tuple[list[Produto], int]:
        """Lista produtos de uma categoria."""
        # Contar total
        count_result = await self.session.execute(
            select(func.count(Produto.id)).where(Produto.categoria_id == categoria_id)
        )
        total = count_result.scalar()

        # Buscar com paginação
        result = await self.session.execute(
            select(Produto)
            .where(Produto.categoria_id == categoria_id)
            .offset(skip)
            .limit(limit)
            .options(
                selectinload(Produto.variantes),
                selectinload(Produto.catalogo_config)
            )
        )
        return result.scalars().all(), total

    async def listar_todos(self, skip: int = 0, limit: int = 10, apenas_ativos: bool = True) -> tuple[list[Produto], int]:
        """Lista todos os produtos."""
        query = select(Produto)
        if apenas_ativos:
            query = query.where(Produto.ativo.is_(True))

        # Contar total
        count_result = await self.session.execute(select(func.count(Produto.id)))
        total = count_result.scalar()

        # Buscar com paginação
        result = await self.session.execute(
            query.offset(skip).limit(limit).options(
                selectinload(Produto.categoria),
                selectinload(Produto.variantes),
                selectinload(Produto.catalogo_config)
            )
        )
        return result.scalars().all(), total

    async def atualizar(
        self,
        produto_id: UUID,
        nome: str | None = None,
        categoria_id: UUID | None = None,
        descricao: str | None = None,
        ativo: bool | None = None,
    ) -> Produto | None:
        """Atualiza um produto."""
        produto = await self.obter_por_id(produto_id)
        if not produto:
            return None

        if nome is not None:
            produto.nome = nome
        if categoria_id is not None:
            produto.categoria_id = categoria_id
        if descricao is not None:
            produto.descricao = descricao
        if ativo is not None:
            produto.ativo = ativo

        await self.session.flush()
        return produto

    async def deletar(self, produto_id: UUID) -> bool:
        """Deleta um produto."""
        produto = await self.obter_por_id(produto_id)
        if not produto:
            return False

        await self.session.delete(produto)
        await self.session.flush()
        return True


class VarianteRepository:
    """Repository para Variante."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(
        self,
        produto_id: UUID,
        sku: str,
        preco_custo: float,
        markup_pct: float,
        preco_venda: float,
    ) -> Variante:
        """Cria uma nova variante."""
        variante = Variante(
            produto_id=produto_id,
            sku=sku,
            preco_custo=preco_custo,
            markup_pct=markup_pct,
            preco_venda=preco_venda,
        )
        self.session.add(variante)
        await self.session.flush()
        return variante

    async def obter_por_id(self, variante_id: UUID) -> Variante | None:
        """Obtém uma variante por ID."""
        result = await self.session.execute(
            select(Variante)
            .where(Variante.id == variante_id)
            .options(selectinload(Variante.atributos))
        )
        return result.scalars().first()

    async def obter_por_sku(self, sku: str) -> Variante | None:
        """Obtém uma variante por SKU."""
        result = await self.session.execute(
            select(Variante).where(Variante.sku == sku).options(selectinload(Variante.atributos))
        )
        return result.scalars().first()

    async def listar_por_produto(self, produto_id: UUID) -> list[Variante]:
        """Lista variantes de um produto."""
        result = await self.session.execute(
            select(Variante)
            .where(Variante.produto_id == produto_id)
            .options(selectinload(Variante.atributos))
        )
        return result.scalars().all()

    async def atualizar(
        self,
        variante_id: UUID,
        sku: str | None = None,
        preco_custo: float | None = None,
        markup_pct: float | None = None,
        preco_venda: float | None = None,
        ativo: bool | None = None,
    ) -> Variante | None:
        """Atualiza uma variante."""
        variante = await self.obter_por_id(variante_id)
        if not variante:
            return None

        if sku is not None:
            variante.sku = sku
        if preco_custo is not None:
            variante.preco_custo = preco_custo
        if markup_pct is not None:
            variante.markup_pct = markup_pct
        if preco_venda is not None:
            variante.preco_venda = preco_venda
        if ativo is not None:
            variante.ativo = ativo

        await self.session.flush()
        return variante

    async def deletar(self, variante_id: UUID) -> bool:
        """Deleta uma variante."""
        variante = await self.obter_por_id(variante_id)
        if not variante:
            return False

        await self.session.delete(variante)
        await self.session.flush()
        return True


class AtributoVarianteRepository:
    """Repository para AtributoVariante."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(self, variante_id: UUID, chave: str, valor: str) -> AtributoVariante:
        """Cria um novo atributo de variante."""
        atributo = AtributoVariante(variante_id=variante_id, chave=chave, valor=valor)
        self.session.add(atributo)
        await self.session.flush()
        return atributo

    async def obter_por_id(self, atributo_id: UUID) -> AtributoVariante | None:
        """Obtém um atributo por ID."""
        result = await self.session.execute(
            select(AtributoVariante).where(AtributoVariante.id == atributo_id)
        )
        return result.scalars().first()

    async def listar_por_variante(self, variante_id: UUID) -> list[AtributoVariante]:
        """Lista atributos de uma variante."""
        result = await self.session.execute(
            select(AtributoVariante).where(AtributoVariante.variante_id == variante_id)
        )
        return result.scalars().all()

    async def deletar(self, atributo_id: UUID) -> bool:
        """Deleta um atributo."""
        atributo = await self.obter_por_id(atributo_id)
        if not atributo:
            return False

        await self.session.delete(atributo)
        await self.session.flush()
        return True


class CatalogoConfigRepository:
    """Repository para CatalogoConfig."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(
        self,
        produto_id: UUID,
        visivel: bool = False,
        destaque: bool = False,
        ordem_exibicao: int = 0,
        descricao_publica: str | None = None,
    ) -> CatalogoConfig:
        """Cria uma nova configuração de catálogo."""
        catalogo = CatalogoConfig(
            produto_id=produto_id,
            visivel=visivel,
            destaque=destaque,
            ordem_exibicao=ordem_exibicao,
            descricao_publica=descricao_publica,
        )
        self.session.add(catalogo)
        await self.session.flush()
        return catalogo

    async def obter_por_produto(self, produto_id: UUID) -> CatalogoConfig | None:
        """Obtém configuração de catálogo de um produto."""
        result = await self.session.execute(
            select(CatalogoConfig).where(CatalogoConfig.produto_id == produto_id)
        )
        return result.scalars().first()

    async def atualizar(
        self,
        catalogo_id: UUID,
        visivel: bool | None = None,
        destaque: bool | None = None,
        ordem_exibicao: int | None = None,
        descricao_publica: str | None = None,
    ) -> CatalogoConfig | None:
        """Atualiza uma configuração de catálogo."""
        result = await self.session.execute(
            select(CatalogoConfig).where(CatalogoConfig.id == catalogo_id)
        )
        catalogo = result.scalars().first()
        if not catalogo:
            return None

        if visivel is not None:
            catalogo.visivel = visivel
        if destaque is not None:
            catalogo.destaque = destaque
        if ordem_exibicao is not None:
            catalogo.ordem_exibicao = ordem_exibicao
        if descricao_publica is not None:
            catalogo.descricao_publica = descricao_publica

        await self.session.flush()
        return catalogo

    async def deletar(self, catalogo_id: UUID) -> bool:
        """Deleta uma configuração de catálogo."""
        result = await self.session.execute(
            select(CatalogoConfig).where(CatalogoConfig.id == catalogo_id)
        )
        catalogo = result.scalars().first()
        if not catalogo:
            return False

        await self.session.delete(catalogo)
        await self.session.flush()
        return True


class CatalogoFotoRepository:
    """Repository para CatalogoFoto."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(self, produto_id: UUID, url: str, ordem: int = 0) -> CatalogoFoto:
        """Cria uma nova foto de catálogo."""
        foto = CatalogoFoto(produto_id=produto_id, url=url, ordem=ordem)
        self.session.add(foto)
        await self.session.flush()
        return foto

    async def obter_por_id(self, foto_id: UUID) -> CatalogoFoto | None:
        """Obtém uma foto por ID."""
        result = await self.session.execute(
            select(CatalogoFoto).where(CatalogoFoto.id == foto_id)
        )
        return result.scalars().first()

    async def listar_por_produto(self, produto_id: UUID) -> list[CatalogoFoto]:
        """Lista fotos de um produto ordenadas."""
        result = await self.session.execute(
            select(CatalogoFoto)
            .where(CatalogoFoto.produto_id == produto_id)
            .order_by(CatalogoFoto.ordem)
        )
        return result.scalars().all()

    async def atualizar(
        self, foto_id: UUID, url: str | None = None, ordem: int | None = None
    ) -> CatalogoFoto | None:
        """Atualiza uma foto."""
        foto = await self.obter_por_id(foto_id)
        if not foto:
            return None

        if url is not None:
            foto.url = url
        if ordem is not None:
            foto.ordem = ordem

        await self.session.flush()
        return foto

    async def deletar(self, foto_id: UUID) -> bool:
        """Deleta uma foto."""
        foto = await self.obter_por_id(foto_id)
        if not foto:
            return False

        await self.session.delete(foto)
        await self.session.flush()
        return True


class FornecedorRepository:
    """Repository para Fornecedor."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(
        self,
        nome: str,
        cnpj: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
        endereco: str | None = None,
        cidade: str | None = None,
        uf: str | None = None,
    ) -> Fornecedor:
        """Cria um novo fornecedor."""
        fornecedor = Fornecedor(
            nome=nome,
            cnpj=cnpj,
            email=email,
            telefone=telefone,
            endereco=endereco,
            cidade=cidade,
            uf=uf,
        )
        self.session.add(fornecedor)
        await self.session.flush()
        return fornecedor

    async def obter_por_id(self, fornecedor_id: UUID) -> Fornecedor | None:
        """Obtém um fornecedor por ID."""
        result = await self.session.execute(
            select(Fornecedor).where(Fornecedor.id == fornecedor_id)
        )
        return result.scalars().first()

    async def obter_por_cnpj(self, cnpj: str) -> Fornecedor | None:
        """Obtém um fornecedor por CNPJ."""
        result = await self.session.execute(
            select(Fornecedor).where(Fornecedor.cnpj == cnpj)
        )
        return result.scalars().first()

    async def listar_todos(
        self, skip: int = 0, limit: int = 10, apenas_ativos: bool = True
    ) -> tuple[list[Fornecedor], int]:
        """Lista todos os fornecedores."""
        query = select(Fornecedor)
        if apenas_ativos:
            query = query.where(Fornecedor.ativo.is_(True))

        # Contar total
        count_result = await self.session.execute(select(func.count(Fornecedor.id)))
        total = count_result.scalar()

        # Buscar com paginação
        result = await self.session.execute(query.offset(skip).limit(limit))
        return result.scalars().all(), total

    async def atualizar(
        self,
        fornecedor_id: UUID,
        nome: str | None = None,
        cnpj: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
        endereco: str | None = None,
        cidade: str | None = None,
        uf: str | None = None,
        ativo: bool | None = None,
    ) -> Fornecedor | None:
        """Atualiza um fornecedor."""
        fornecedor = await self.obter_por_id(fornecedor_id)
        if not fornecedor:
            return None

        if nome is not None:
            fornecedor.nome = nome
        if cnpj is not None:
            fornecedor.cnpj = cnpj
        if email is not None:
            fornecedor.email = email
        if telefone is not None:
            fornecedor.telefone = telefone
        if endereco is not None:
            fornecedor.endereco = endereco
        if cidade is not None:
            fornecedor.cidade = cidade
        if uf is not None:
            fornecedor.uf = uf
        if ativo is not None:
            fornecedor.ativo = ativo

        await self.session.flush()
        return fornecedor

    async def deletar(self, fornecedor_id: UUID) -> bool:
        """Deleta um fornecedor."""
        fornecedor = await self.obter_por_id(fornecedor_id)
        if not fornecedor:
            return False

        await self.session.delete(fornecedor)
        await self.session.flush()
        return True


class FornecedorProdutoRepository:
    """Repository para FornecedorProduto."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def criar(
        self,
        fornecedor_id: UUID,
        produto_id: UUID,
        preco_fornecedor: float,
        codigo_fornecedor: str | None = None,
        prazo_entrega_dias: int = 0,
        quantidade_minima: int = 1,
    ) -> FornecedorProduto:
        """Cria uma nova associação fornecedor-produto."""
        fornecedor_produto = FornecedorProduto(
            fornecedor_id=fornecedor_id,
            produto_id=produto_id,
            codigo_fornecedor=codigo_fornecedor,
            preco_fornecedor=preco_fornecedor,
            prazo_entrega_dias=prazo_entrega_dias,
            quantidade_minima=quantidade_minima,
        )
        self.session.add(fornecedor_produto)
        await self.session.flush()
        return fornecedor_produto

    async def obter_por_id(self, fornecedor_produto_id: UUID) -> FornecedorProduto | None:
        """Obtém uma associação por ID."""
        result = await self.session.execute(
            select(FornecedorProduto).where(FornecedorProduto.id == fornecedor_produto_id)
        )
        return result.scalars().first()

    async def listar_fornecedores_produto(self, produto_id: UUID) -> list[FornecedorProduto]:
        """Lista fornecedores de um produto."""
        result = await self.session.execute(
            select(FornecedorProduto)
            .where(FornecedorProduto.produto_id == produto_id)
            .where(FornecedorProduto.ativo.is_(True))
        )
        return result.scalars().all()

    async def listar_produtos_fornecedor(self, fornecedor_id: UUID) -> list[FornecedorProduto]:
        """Lista produtos de um fornecedor."""
        result = await self.session.execute(
            select(FornecedorProduto)
            .where(FornecedorProduto.fornecedor_id == fornecedor_id)
            .where(FornecedorProduto.ativo.is_(True))
        )
        return result.scalars().all()

    async def atualizar(
        self,
        fornecedor_produto_id: UUID,
        codigo_fornecedor: str | None = None,
        preco_fornecedor: float | None = None,
        prazo_entrega_dias: int | None = None,
        quantidade_minima: int | None = None,
        ativo: bool | None = None,
    ) -> FornecedorProduto | None:
        """Atualiza uma associação."""
        fp = await self.obter_por_id(fornecedor_produto_id)
        if not fp:
            return None

        if codigo_fornecedor is not None:
            fp.codigo_fornecedor = codigo_fornecedor
        if preco_fornecedor is not None:
            fp.preco_fornecedor = preco_fornecedor
        if prazo_entrega_dias is not None:
            fp.prazo_entrega_dias = prazo_entrega_dias
        if quantidade_minima is not None:
            fp.quantidade_minima = quantidade_minima
        if ativo is not None:
            fp.ativo = ativo

        await self.session.flush()
        return fp

    async def deletar(self, fornecedor_produto_id: UUID) -> bool:
        """Deleta uma associação."""
        fp = await self.obter_por_id(fornecedor_produto_id)
        if not fp:
            return False

        await self.session.delete(fp)
        await self.session.flush()
        return True
