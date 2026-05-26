"""
Services com lógica de negócio para Produtos.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.produtos import (
    CategoriaCreate,
    CategoriaUpdate,
    ProdutoCreate,
    ProdutoUpdate,
    VarianteCreate,
    VarianteUpdate,
    AtributoVarianteBase,
    CatalogoConfigCreate,
    CatalogoConfigUpdate,
    CatalogoFotoCreate,
    CatalogoFotoUpdate,
    FornecedorCreate,
    FornecedorUpdate,
    FornecedorProdutoCreate,
    FornecedorProdutoUpdate,
)
from repositories.produtos import (
    CategoriaRepository,
    ProdutoRepository,
    VarianteRepository,
    AtributoVarianteRepository,
    CatalogoConfigRepository,
    CatalogoFotoRepository,
    FornecedorRepository,
    FornecedorProdutoRepository,
)


class CategoriaService:
    """Service para Categoria."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CategoriaRepository(session)

    async def criar_categoria(self, dados: CategoriaCreate):
        """Cria uma nova categoria com transação atômica."""
        try:
            async with self.session.begin_nested():
                # Validar se categoria já existe
                existente = await self.repo.obter_por_nome(dados.nome)
                if existente:
                    raise ValueError(f"Categoria '{dados.nome}' já existe")

                categoria = await self.repo.criar(nome=dados.nome, descricao=dados.descricao)
            
            await self.session.commit()
            return categoria
        except ValueError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise

    async def obter_categoria(self, categoria_id: UUID):
        """Obtém uma categoria por ID."""
        categoria = await self.repo.obter_por_id(categoria_id)
        if not categoria:
            raise ValueError(f"Categoria com ID {categoria_id} não encontrada")
        return categoria

    async def listar_categorias(self, skip: int = 0, limit: int = 10):
        """Lista todas as categorias."""
        return await self.repo.listar_todas(skip=skip, limit=limit)

    async def atualizar_categoria(self, categoria_id: UUID, dados: CategoriaUpdate):
        """Atualiza uma categoria com transação atômica."""
        try:
            async with self.session.begin_nested():
                categoria = await self.repo.obter_por_id(categoria_id)
                if not categoria:
                    raise ValueError(f"Categoria com ID {categoria_id} não encontrada")

                # Validar nome único se mudou
                if dados.nome and dados.nome != categoria.nome:
                    existente = await self.repo.obter_por_nome(dados.nome)
                    if existente:
                        raise ValueError(f"Categoria '{dados.nome}' já existe")

                categoria_atualizada = await self.repo.atualizar(
                    categoria_id,
                    nome=dados.nome,
                    descricao=dados.descricao,
                )
            
            await self.session.commit()
            return categoria_atualizada
        except ValueError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise

    async def deletar_categoria(self, categoria_id: UUID):
        """Deleta uma categoria com transação atômica."""
        try:
            async with self.session.begin_nested():
                categoria = await self.repo.obter_por_id(categoria_id)
                if not categoria:
                    raise ValueError(f"Categoria com ID {categoria_id} não encontrada")

                resultado = await self.repo.deletar(categoria_id)
            
            await self.session.commit()
            return resultado
        except ValueError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise


class ProdutoService:
    """Service para Produto."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.produto_repo = ProdutoRepository(session)
        self.categoria_repo = CategoriaRepository(session)

    async def criar_produto(self, dados: ProdutoCreate):
        """Cria um novo produto com transação atômica."""
        try:
            async with self.session.begin_nested():
                # Validar categoria
                categoria = await self.categoria_repo.obter_por_id(dados.categoria_id)
                if not categoria:
                    raise ValueError(f"Categoria com ID {dados.categoria_id} não encontrada")

                produto = await self.produto_repo.criar(
                    categoria_id=dados.categoria_id,
                    nome=dados.nome,
                    descricao=dados.descricao,
                )
            
            await self.session.commit()
            return produto
        except ValueError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise

    async def obter_produto(self, produto_id: UUID):
        """Obtém um produto por ID."""
        produto = await self.produto_repo.obter_por_id(produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrada")
        return produto

    async def listar_produtos(self, skip: int = 0, limit: int = 10, apenas_ativos: bool = True):
        """Lista todos os produtos."""
        return await self.produto_repo.listar_todos(
            skip=skip, limit=limit, apenas_ativos=apenas_ativos
        )

    async def listar_por_categoria(self, categoria_id: UUID, skip: int = 0, limit: int = 10):
        """Lista produtos de uma categoria."""
        # Validar categoria
        categoria = await self.categoria_repo.obter_por_id(categoria_id)
        if not categoria:
            raise ValueError(f"Categoria com ID {categoria_id} não encontrada")

        return await self.produto_repo.listar_por_categoria(categoria_id, skip=skip, limit=limit)

    async def buscar_por_nome(self, nome: str):
        """Busca produtos por nome."""
        if not nome or len(nome) < 3:
            raise ValueError("Nome deve ter no mínimo 3 caracteres")
        return await self.produto_repo.obter_por_nome(nome)

    async def atualizar_produto(self, produto_id: UUID, dados: ProdutoUpdate):
        """Atualiza um produto com transação atômica."""
        try:
            async with self.session.begin_nested():
                produto = await self.produto_repo.obter_por_id(produto_id)
                if not produto:
                    raise ValueError(f"Produto com ID {produto_id} não encontrada")

                # Validar nova categoria se foi mudada
                if dados.categoria_id and dados.categoria_id != produto.categoria_id:
                    categoria = await self.categoria_repo.obter_por_id(dados.categoria_id)
                    if not categoria:
                        raise ValueError(f"Categoria com ID {dados.categoria_id} não encontrada")

                produto_atualizado = await self.produto_repo.atualizar(
                    produto_id,
                    nome=dados.nome,
                    categoria_id=dados.categoria_id,
                    descricao=dados.descricao,
                    ativo=dados.ativo,
                )
            
            await self.session.commit()
            return produto_atualizado
        except ValueError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise

    async def deletar_produto(self, produto_id: UUID):
        """Deleta um produto com transação atômica."""
        try:
            async with self.session.begin_nested():
                produto = await self.produto_repo.obter_por_id(produto_id)
                if not produto:
                    raise ValueError(f"Produto com ID {produto_id} não encontrada")

                resultado = await self.produto_repo.deletar(produto_id)
            
            await self.session.commit()
            return resultado
        except ValueError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise


class VarianteService:
    """Service para Variante."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.variante_repo = VarianteRepository(session)
        self.atributo_repo = AtributoVarianteRepository(session)
        self.produto_repo = ProdutoRepository(session)

    async def criar_variante(self, dados: VarianteCreate):
        """Cria uma nova variante com transação atômica."""
        try:
            async with self.session.begin_nested():
                # Validar produto
                produto = await self.produto_repo.obter_por_id(dados.produto_id)
                if not produto:
                    raise ValueError(f"Produto com ID {dados.produto_id} não encontrada")

                # Verificar SKU único
                existente = await self.variante_repo.obter_por_sku(dados.sku)
                if existente:
                    raise ValueError(f"SKU '{dados.sku}' já existe")

                # Validar preço
                if dados.preco_venda < dados.preco_custo:
                    raise ValueError("Preço de venda não pode ser menor que preço de custo")

                # Criar variante
                variante = await self.variante_repo.criar(
                    produto_id=dados.produto_id,
                    sku=dados.sku,
                    preco_custo=dados.preco_custo,
                    markup_pct=dados.markup_pct,
                    preco_venda=dados.preco_venda,
                )

                # Criar atributos se fornecidos
                for atributo in dados.atributos:
                    await self.atributo_repo.criar(
                        variante_id=variante.id,
                        chave=atributo.chave,
                        valor=atributo.valor,
                    )

                await self.session.flush()
            
            await self.session.commit()
            return variante
        except ValueError:
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise

    async def obter_variante(self, variante_id: UUID):
        """Obtém uma variante por ID."""
        variante = await self.variante_repo.obter_por_id(variante_id)
        if not variante:
            raise ValueError(f"Variante com ID {variante_id} não encontrada")
        return variante

    async def listar_por_produto(self, produto_id: UUID):
        """Lista variantes de um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrada")

        return await self.variante_repo.listar_por_produto(produto_id)

    async def atualizar_variante(self, variante_id: UUID, dados: VarianteUpdate):
        """Atualiza uma variante."""
        variante = await self.variante_repo.obter_por_id(variante_id)
        if not variante:
            raise ValueError(f"Variante com ID {variante_id} não encontrada")

        # Validar SKU se mudou
        if dados.sku and dados.sku != variante.sku:
            existente = await self.variante_repo.obter_por_sku(dados.sku)
            if existente:
                raise ValueError(f"SKU '{dados.sku}' já existe")

        # Validar preço
        preco_custo = dados.preco_custo or variante.preco_custo
        preco_venda = dados.preco_venda or variante.preco_venda
        if preco_venda < preco_custo:
            raise ValueError("Preço de venda não pode ser menor que preço de custo")

        return await self.variante_repo.atualizar(
            variante_id,
            sku=dados.sku,
            preco_custo=dados.preco_custo,
            markup_pct=dados.markup_pct,
            preco_venda=dados.preco_venda,
            ativo=dados.ativo,
        )

    async def deletar_variante(self, variante_id: UUID):
        """Deleta uma variante."""
        variante = await self.variante_repo.obter_por_id(variante_id)
        if not variante:
            raise ValueError(f"Variante com ID {variante_id} não encontrada")

        return await self.variante_repo.deletar(variante_id)


class CatalogoService:
    """Service para Catálogo (Config e Fotos)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.catalogo_config_repo = CatalogoConfigRepository(session)
        self.catalogo_foto_repo = CatalogoFotoRepository(session)
        self.produto_repo = ProdutoRepository(session)

    async def criar_config(self, dados: CatalogoConfigCreate):
        """Cria configuração de catálogo para um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(dados.produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {dados.produto_id} não encontrada")

        # Verificar se já existe config
        existente = await self.catalogo_config_repo.obter_por_produto(dados.produto_id)
        if existente:
            raise ValueError(f"Configuração de catálogo já existe para este produto")

        return await self.catalogo_config_repo.criar(
            produto_id=dados.produto_id,
            visivel=dados.visivel,
            destaque=dados.destaque,
            ordem_exibicao=dados.ordem_exibicao,
            descricao_publica=dados.descricao_publica,
        )

    async def obter_config(self, produto_id: UUID):
        """Obtém configuração de catálogo de um produto."""
        config = await self.catalogo_config_repo.obter_por_produto(produto_id)
        if not config:
            raise ValueError(f"Configuração não encontrada para produto {produto_id}")
        return config

    async def atualizar_config(self, catalogo_id: UUID, dados: CatalogoConfigUpdate):
        """Atualiza configuração de catálogo."""
        config = await self.catalogo_config_repo.atualizar(
            catalogo_id,
            visivel=dados.visivel,
            destaque=dados.destaque,
            ordem_exibicao=dados.ordem_exibicao,
            descricao_publica=dados.descricao_publica,
        )
        if not config:
            raise ValueError(f"Configuração com ID {catalogo_id} não encontrada")
        return config

    async def adicionar_foto(self, dados: CatalogoFotoCreate):
        """Adiciona foto ao catálogo."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(dados.produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {dados.produto_id} não encontrada")

        return await self.catalogo_foto_repo.criar(
            produto_id=dados.produto_id,
            url=dados.url,
            ordem=dados.ordem,
        )

    async def listar_fotos(self, produto_id: UUID):
        """Lista fotos de um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrada")

        return await self.catalogo_foto_repo.listar_por_produto(produto_id)

    async def atualizar_foto(self, foto_id: UUID, dados: CatalogoFotoUpdate):
        """Atualiza uma foto."""
        foto = await self.catalogo_foto_repo.atualizar(
            foto_id,
            url=dados.url,
            ordem=dados.ordem,
        )
        if not foto:
            raise ValueError(f"Foto com ID {foto_id} não encontrada")
        return foto

    async def deletar_foto(self, foto_id: UUID):
        """Deleta uma foto."""
        return await self.catalogo_foto_repo.deletar(foto_id)


class FornecedorService:
    """Service para Fornecedor."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FornecedorRepository(session)

    async def criar_fornecedor(self, dados: FornecedorCreate):
        """Cria um novo fornecedor."""
        # Validar CNPJ único se fornecido
        if dados.cnpj:
            existente = await self.repo.obter_por_cnpj(dados.cnpj)
            if existente:
                raise ValueError(f"CNPJ '{dados.cnpj}' já cadastrado")

        return await self.repo.criar(
            nome=dados.nome,
            cnpj=dados.cnpj,
            email=dados.email,
            telefone=dados.telefone,
            endereco=dados.endereco,
            cidade=dados.cidade,
            uf=dados.uf,
        )

    async def obter_fornecedor(self, fornecedor_id: UUID):
        """Obtém um fornecedor por ID."""
        fornecedor = await self.repo.obter_por_id(fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")
        return fornecedor

    async def listar_fornecedores(self, skip: int = 0, limit: int = 10, apenas_ativos: bool = True):
        """Lista fornecedores."""
        return await self.repo.listar_todos(skip=skip, limit=limit, apenas_ativos=apenas_ativos)

    async def atualizar_fornecedor(self, fornecedor_id: UUID, dados: FornecedorUpdate):
        """Atualiza um fornecedor."""
        fornecedor = await self.repo.obter_por_id(fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")

        # Validar CNPJ se mudou
        if dados.cnpj and dados.cnpj != fornecedor.cnpj:
            existente = await self.repo.obter_por_cnpj(dados.cnpj)
            if existente:
                raise ValueError(f"CNPJ '{dados.cnpj}' já cadastrado")

        return await self.repo.atualizar(
            fornecedor_id,
            nome=dados.nome,
            cnpj=dados.cnpj,
            email=dados.email,
            telefone=dados.telefone,
            endereco=dados.endereco,
            cidade=dados.cidade,
            uf=dados.uf,
            ativo=dados.ativo,
        )

    async def deletar_fornecedor(self, fornecedor_id: UUID):
        """Deleta um fornecedor."""
        fornecedor = await self.repo.obter_por_id(fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")

        return await self.repo.deletar(fornecedor_id)


class FornecedorProdutoService:
    """Service para Associação Fornecedor-Produto."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FornecedorProdutoRepository(session)
        self.fornecedor_repo = FornecedorRepository(session)
        self.produto_repo = ProdutoRepository(session)

    async def vincular_fornecedor(self, dados: FornecedorProdutoCreate):
        """Vincula um fornecedor a um produto."""
        # Validar fornecedor
        fornecedor = await self.fornecedor_repo.obter_por_id(dados.fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {dados.fornecedor_id} não encontrada")

        # Validar produto
        produto = await self.produto_repo.obter_por_id(dados.produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {dados.produto_id} não encontrada")

        # Validar preço
        if dados.preco_fornecedor <= 0:
            raise ValueError("Preço do fornecedor deve ser maior que zero")

        return await self.repo.criar(
            fornecedor_id=dados.fornecedor_id,
            produto_id=dados.produto_id,
            codigo_fornecedor=dados.codigo_fornecedor,
            preco_fornecedor=dados.preco_fornecedor,
            prazo_entrega_dias=dados.prazo_entrega_dias,
            quantidade_minima=dados.quantidade_minima,
        )

    async def obter_vinculo(self, vinculo_id: UUID):
        """Obtém um vínculo fornecedor-produto."""
        vinculo = await self.repo.obter_por_id(vinculo_id)
        if not vinculo:
            raise ValueError(f"Vínculo com ID {vinculo_id} não encontrada")
        return vinculo

    async def listar_fornecedores_produto(self, produto_id: UUID):
        """Lista fornecedores de um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrada")

        return await self.repo.listar_fornecedores_produto(produto_id)

    async def listar_produtos_fornecedor(self, fornecedor_id: UUID):
        """Lista produtos de um fornecedor."""
        # Validar fornecedor
        fornecedor = await self.fornecedor_repo.obter_por_id(fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")

        return await self.repo.listar_produtos_fornecedor(fornecedor_id)

    async def atualizar_vinculo(self, vinculo_id: UUID, dados: FornecedorProdutoUpdate):
        """Atualiza um vínculo fornecedor-produto."""
        vinculo = await self.repo.obter_por_id(vinculo_id)
        if not vinculo:
            raise ValueError(f"Vínculo com ID {vinculo_id} não encontrada")

        # Validar preço
        preco = dados.preco_fornecedor or vinculo.preco_fornecedor
        if preco <= 0:
            raise ValueError("Preço do fornecedor deve ser maior que zero")

        return await self.repo.atualizar(
            vinculo_id,
            codigo_fornecedor=dados.codigo_fornecedor,
            preco_fornecedor=dados.preco_fornecedor,
            prazo_entrega_dias=dados.prazo_entrega_dias,
            quantidade_minima=dados.quantidade_minima,
            ativo=dados.ativo,
        )

    async def deletar_vinculo(self, vinculo_id: UUID):
        """Deleta um vínculo fornecedor-produto."""
        vinculo = await self.repo.obter_por_id(vinculo_id)
        if not vinculo:
            raise ValueError(f"Vínculo com ID {vinculo_id} não encontrada")

        return await self.repo.deletar(vinculo_id)
