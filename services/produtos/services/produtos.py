"""
Services com lógica de negócio para Produtos.
"""
from decimal import Decimal
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
    LojaOnlineConfigCreate,
    LojaOnlineConfigUpdate,
    LojaOnlinePublicarRequest,
    ProdutoLojaOnlineStatusRead,
    LojaOnlineFotoCreate,
    LojaOnlineFotoUpdate,
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
    LojaOnlineConfigRepository,
    LojaOnlineFotoRepository,
    FornecedorRepository,
    FornecedorProdutoRepository,
)


def _exigir_preco_cobrindo_fornecedor(preco_venda: Decimal, preco_fornecedor: Decimal) -> None:
    """
    Recusa vender por menos do que se paga ao fornecedor.

    Mesma regra que `preco < custo` já barra no cadastro do produto, só que
    olhando para o preço que se paga de verdade: `Produto.custo` é digitado à
    mão e nada o sincroniza com o vínculo do fornecedor, então a guarda de lá
    não cobria esta. Vale nas duas direções — cadastrar fornecedor caro demais
    e baixar o preço de venda abaixo do fornecedor dão o mesmo prejuízo por
    unidade vendida.
    """
    if preco_fornecedor > preco_venda:
        raise ValueError(
            f"Preço do fornecedor (R$ {preco_fornecedor}) não pode ser maior que "
            f"o preço de venda (R$ {preco_venda})"
        )


def _exigir_promocao_nao_maior_que_preco(preco: Decimal, preco_promocional: Decimal | None) -> None:
    """
    Recusa promoção que cobra mais caro que o preço normal.

    Igual ao preço normal passa: é o lojista decidindo não dar desconto neste
    item, e nenhuma tela mente por isso — o card da loja só risca o preço antigo
    quando a promoção é estritamente menor. Acima é que não existe: o campo se
    chama "promocional", a vitrine exibe esse número no lugar do preço, e o
    cliente lê como desconto o que é aumento.
    """
    if preco_promocional is not None and preco_promocional > preco:
        raise ValueError(
            f"Preço promocional (R$ {preco_promocional}) não pode ser maior que "
            f"o preço de venda (R$ {preco})"
        )


class CategoriaService:
    """Service para Categoria."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = CategoriaRepository(session)

    async def criar_categoria(self, empresa_id: int, dados: CategoriaCreate):
        """Cria uma nova categoria com transação atômica."""
        existente = await self.repo.obter_por_nome(empresa_id, dados.nome)
        if existente:
            raise ValueError(f"Categoria '{dados.nome}' já existe")
        return await self.repo.criar(empresa_id=empresa_id, nome=dados.nome, descricao=dados.descricao)

    async def obter_categoria(self, empresa_id: int, categoria_id: UUID):
        """Obtém uma categoria por ID."""
        categoria = await self.repo.obter_por_id(empresa_id, categoria_id)
        if not categoria:
            raise ValueError(f"Categoria com ID {categoria_id} não encontrada")
        return categoria

    async def listar_categorias(self, empresa_id: int, skip: int = 0, limit: int = 10):
        """Lista todas as categorias."""
        return await self.repo.listar_todas(empresa_id=empresa_id, skip=skip, limit=limit)

    async def atualizar_categoria(self, empresa_id: int, categoria_id: UUID, dados: CategoriaUpdate):
        """Atualiza uma categoria."""
        categoria = await self.repo.obter_por_id(empresa_id, categoria_id)
        if not categoria:
            raise ValueError(f"Categoria com ID {categoria_id} não encontrada")

        if dados.nome and dados.nome != categoria.nome:
            existente = await self.repo.obter_por_nome(empresa_id, dados.nome)
            if existente:
                raise ValueError(f"Categoria '{dados.nome}' já existe")

        return await self.repo.atualizar(empresa_id, categoria_id, nome=dados.nome, descricao=dados.descricao)

    async def deletar_categoria(self, empresa_id: int, categoria_id: UUID):
        """Deleta uma categoria."""
        categoria = await self.repo.obter_por_id(empresa_id, categoria_id)
        if not categoria:
            raise ValueError(f"Categoria com ID {categoria_id} não encontrada")
        return await self.repo.deletar(empresa_id, categoria_id)


class ProdutoService:
    """Service para Produto."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.produto_repo = ProdutoRepository(session)
        self.categoria_repo = CategoriaRepository(session)
        self.fornecedor_produto_repo = FornecedorProdutoRepository(session)

    async def criar_produto(self, empresa_id: int, dados: ProdutoCreate):
        """Cria um novo produto."""
        categoria = await self.categoria_repo.obter_por_id(empresa_id, dados.categoria_id)
        if not categoria:
            raise ValueError(f"Categoria com ID {dados.categoria_id} não encontrada")

        if dados.preco < dados.custo:
            raise ValueError("Preço de venda não pode ser menor que o custo")

        _exigir_promocao_nao_maior_que_preco(dados.preco, dados.preco_promocional)

        return await self.produto_repo.criar(
            empresa_id=empresa_id,
            categoria_id=dados.categoria_id,
            nome=dados.nome,
            descricao=dados.descricao,
            ativo=dados.ativo,
            preco=dados.preco,
            custo=dados.custo,
            preco_promocional=dados.preco_promocional,
            unidade_medida=dados.unidade_medida,
        )

    async def obter_produto(self, empresa_id: int, produto_id: UUID):
        """Obtém um produto por ID."""
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")
        return produto

    async def listar_produtos(
        self,
        empresa_id: int,
        skip: int = 0,
        limit: int = 10,
        apenas_deletados: bool = False,
        apenas_ativos: bool | None = None,
        busca: str | None = None,
        categoria_id: UUID | None = None
    ):
        """
        Lista produtos.

        Args:
            empresa_id: ID da empresa (multi-tenancy)
            skip: Offset para paginação
            limit: Limite de resultados
            apenas_deletados: True = só deletados, False = todos não deletados
            apenas_ativos: True = só ativos, False = só inativos, None = todos
            busca: Filtra por nome (parcial, case-insensitive)
            categoria_id: Filtra por categoria
        """
        return await self.produto_repo.listar_todos(
            empresa_id=empresa_id,
            skip=skip,
            limit=limit,
            apenas_ativos=apenas_ativos,
            apenas_deletados=apenas_deletados,
            busca=busca,
            categoria_id=categoria_id
        )

    async def listar_por_categoria(self, empresa_id: int, categoria_id: UUID, skip: int = 0, limit: int = 10):
        """Lista produtos de uma categoria."""
        categoria = await self.categoria_repo.obter_por_id(empresa_id, categoria_id)
        if not categoria:
            raise ValueError(f"Categoria com ID {categoria_id} não encontrada")
        return await self.produto_repo.listar_por_categoria(empresa_id, categoria_id, skip=skip, limit=limit)

    async def buscar_por_nome(self, empresa_id: int, nome: str):
        """Busca produtos por nome."""
        if not nome or len(nome) < 3:
            raise ValueError("Nome deve ter no mínimo 3 caracteres")
        return await self.produto_repo.obter_por_nome(empresa_id, nome)

    async def listar_publicados_loja_online(
        self,
        empresa_id: int,
        skip: int = 0,
        limit: int = 20,
        categoria_id: UUID | None = None,
        busca: str | None = None,
        ordenar: str = "nome",
    ):
        """Lista produtos publicados (ativo + visivel na loja online) para o catálogo público."""
        return await self.produto_repo.listar_publicados_loja_online(
            empresa_id=empresa_id,
            skip=skip,
            limit=limit,
            categoria_id=categoria_id,
            busca=busca,
            ordenar=ordenar,
        )

    async def atualizar_produto(self, empresa_id: int, produto_id: UUID, dados: ProdutoUpdate):
        """Atualiza um produto."""
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")

        if dados.categoria_id and dados.categoria_id != produto.categoria_id:
            categoria = await self.categoria_repo.obter_por_id(empresa_id, dados.categoria_id)
            if not categoria:
                raise ValueError(f"Categoria com ID {dados.categoria_id} não encontrada")

        preco_efetivo = dados.preco if dados.preco is not None else produto.preco
        custo_efetivo = dados.custo if dados.custo is not None else produto.custo
        if preco_efetivo < custo_efetivo:
            raise ValueError("Preço de venda não pode ser menor que o custo")

        # Valores mesclados como os de cima, e pelo mesmo motivo: o PATCH só
        # enxerga o que veio. As duas direções levam ao mesmo absurdo — subir a
        # promoção acima do preço, ou baixar o preço abaixo de uma promoção já
        # gravada — e olhar só o que o request trouxe fecharia uma e deixaria a
        # outra aberta.
        promocional_efetivo = (
            dados.preco_promocional if dados.preco_promocional is not None
            else produto.preco_promocional
        )
        _exigir_promocao_nao_maior_que_preco(preco_efetivo, promocional_efetivo)

        # A outra direção do mesmo prejuízo: guardar o vínculo do fornecedor não
        # adianta se depois dá para baixar o preço de venda abaixo dele. Só
        # consulta quando o preço está mudando — não é para pesar num PATCH de nome.
        if dados.preco is not None:
            for vinculo in await self.fornecedor_produto_repo.listar_fornecedores_produto(produto_id):
                _exigir_preco_cobrindo_fornecedor(preco_efetivo, vinculo.preco_fornecedor)

        return await self.produto_repo.atualizar(
            empresa_id,
            produto_id,
            nome=dados.nome,
            categoria_id=dados.categoria_id,
            descricao=dados.descricao,
            ativo=dados.ativo,
            preco=dados.preco,
            custo=dados.custo,
            preco_promocional=dados.preco_promocional,
            unidade_medida=dados.unidade_medida,
        )

    async def deletar_produto(self, empresa_id: int, produto_id: UUID):
        """Soft delete de um produto."""
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")
        if produto.deletado_em is not None:
            raise ValueError("Produto já está deletado")
        return await self.produto_repo.deletar(empresa_id, produto_id)
    
    async def restaurar_produto(self, empresa_id: int, produto_id: UUID):
        """Restaura um produto deletado."""
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")
        if produto.deletado_em is None:
            raise ValueError("Produto não está deletado")
        return await self.produto_repo.restaurar(empresa_id, produto_id)


class VarianteService:
    """Service para Variante."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.variante_repo = VarianteRepository(session)
        self.atributo_repo = AtributoVarianteRepository(session)
        self.produto_repo = ProdutoRepository(session)

    async def criar_variante(self, empresa_id: int, dados: VarianteCreate):
        """Cria uma nova variante."""
        produto = await self.produto_repo.obter_por_id(empresa_id, dados.produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {dados.produto_id} não encontrado")

        existente = await self.variante_repo.obter_por_sku(empresa_id, dados.sku)
        if existente:
            raise ValueError(f"SKU '{dados.sku}' já existe")

        # `preco_venda` do corpo é ignorado: quem calcula é o repositório, com
        # `Variante.calcular_preco_venda()`. A checagem que existia aqui
        # (`preco_venda < preco_custo`) saiu porque virou impossível de falhar —
        # `markup_pct` é `ge=0`, então custo * (1 + markup/100) nunca fica abaixo
        # do custo. Guarda que não pode disparar mente sobre o que protege.
        variante = await self.variante_repo.criar(
            empresa_id=empresa_id,
            produto_id=dados.produto_id,
            sku=dados.sku,
            preco_custo=dados.preco_custo,
            markup_pct=dados.markup_pct,
        )

        for atributo in dados.atributos:
            await self.atributo_repo.criar(
                variante_id=variante.id,
                chave=atributo.chave,
                valor=atributo.valor,
            )

        return variante

    async def obter_variante(self, empresa_id: int, variante_id: UUID):
        """Obtém uma variante por ID."""
        variante = await self.variante_repo.obter_por_id(empresa_id, variante_id)
        if not variante:
            raise ValueError(f"Variante com ID {variante_id} não encontrada")
        return variante

    async def listar_por_produto(self, empresa_id: int, produto_id: UUID):
        """Lista variantes de um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrada")

        return await self.variante_repo.listar_por_produto(empresa_id, produto_id)

    async def atualizar_variante(self, empresa_id: int, variante_id: UUID, dados: VarianteUpdate):
        """Atualiza uma variante."""
        variante = await self.variante_repo.obter_por_id(empresa_id, variante_id)
        if not variante:
            raise ValueError(f"Variante com ID {variante_id} não encontrada")

        # Validar SKU se mudou
        if dados.sku and dados.sku != variante.sku:
            existente = await self.variante_repo.obter_por_sku(empresa_id, dados.sku)
            if existente:
                raise ValueError(f"SKU '{dados.sku}' já existe")

        # Nada de mesclar preço à mão aqui: o repositório recalcula em cima da
        # instância, que já tem o que o PATCH não trouxe. O merge que existia
        # usava `or`, e `markup_pct` é `ge=0` — um markup de 0 é falsy e cairia
        # no valor antigo sem ninguém ver.
        return await self.variante_repo.atualizar(
            empresa_id,
            variante_id,
            sku=dados.sku,
            preco_custo=dados.preco_custo,
            markup_pct=dados.markup_pct,
            ativo=dados.ativo,
        )

    async def deletar_variante(self, empresa_id: int, variante_id: UUID):
        """Deleta uma variante."""
        variante = await self.variante_repo.obter_por_id(empresa_id, variante_id)
        if not variante:
            raise ValueError(f"Variante com ID {variante_id} não encontrada")

        return await self.variante_repo.deletar(empresa_id, variante_id)


class LojaOnlineService:
    """Service para Loja Online (Config e Fotos)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.loja_online_config_repo = LojaOnlineConfigRepository(session)
        self.loja_online_foto_repo = LojaOnlineFotoRepository(session)
        self.produto_repo = ProdutoRepository(session)

    async def criar_config(self, empresa_id: int, dados: LojaOnlineConfigCreate):
        """Cria configuração de loja online para um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(empresa_id, dados.produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {dados.produto_id} não encontrada")

        # Verificar se já existe config
        existente = await self.loja_online_config_repo.obter_por_produto(dados.produto_id)
        if existente:
            raise ValueError(f"Configuração de loja online já existe para este produto")

        return await self.loja_online_config_repo.criar(
            produto_id=dados.produto_id,
            visivel=dados.visivel,
            destaque=dados.destaque,
            ordem_exibicao=dados.ordem_exibicao,
            descricao_publica=dados.descricao_publica,
        )

    async def obter_config(self, empresa_id: int, produto_id: UUID):
        """Obtém configuração de loja online de um produto."""
        # Validar produto pertence à empresa
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")
        
        config = await self.loja_online_config_repo.obter_por_produto(produto_id)
        if not config:
            raise ValueError(f"Configuração não encontrada para produto {produto_id}")
        return config

    async def atualizar_config(self, empresa_id: int, loja_online_id: UUID, dados: LojaOnlineConfigUpdate):
        """Atualiza configuração de loja online."""
        config = await self.loja_online_config_repo.atualizar(
            empresa_id,
            loja_online_id,
            visivel=dados.visivel,
            destaque=dados.destaque,
            ordem_exibicao=dados.ordem_exibicao,
            descricao_publica=dados.descricao_publica,
        )
        if not config:
            raise ValueError(f"Configuração com ID {loja_online_id} não encontrada")
        return config

    async def listar_status_produtos(self, empresa_id: int, skip: int = 0, limit: int = 20):
        """Lista produtos ativos da empresa com seu status de publicação na loja online."""
        produtos, total = await self.loja_online_config_repo.listar_status_produtos(
            empresa_id=empresa_id, skip=skip, limit=limit
        )
        items = [
            ProdutoLojaOnlineStatusRead(
                id=produto.id,
                nome=produto.nome,
                preco=produto.preco,
                categoria_id=produto.categoria_id,
                ativo=produto.ativo,
                visivel=produto.loja_online_config.visivel if produto.loja_online_config else False,
                destaque=produto.loja_online_config.destaque if produto.loja_online_config else False,
                ordem_exibicao=produto.loja_online_config.ordem_exibicao if produto.loja_online_config else 0,
            )
            for produto in produtos
        ]
        return items, total

    async def publicar_produto(self, empresa_id: int, produto_id: UUID, dados: LojaOnlinePublicarRequest):
        """
        Publica ou despublica um produto na loja online (upsert de LojaOnlineConfig).

        Diferente de `criar_config`/`atualizar_config` (que exigem saber se a config
        já existe), este método faz get-or-create — usado pelo toggle de publicação
        da tela de administração da loja.
        """
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrado")

        config = await self.loja_online_config_repo.obter_por_produto(produto_id)
        if config:
            return await self.loja_online_config_repo.atualizar(
                empresa_id, config.id, visivel=dados.visivel, destaque=dados.destaque
            )
        return await self.loja_online_config_repo.criar(
            produto_id=produto_id, visivel=dados.visivel, destaque=dados.destaque
        )

    async def adicionar_foto(self, empresa_id: int, dados: LojaOnlineFotoCreate):
        """Adiciona foto à loja online."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(empresa_id, dados.produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {dados.produto_id} não encontrada")

        return await self.loja_online_foto_repo.criar(
            produto_id=dados.produto_id,
            url=dados.url,
            ordem=dados.ordem,
        )

    async def listar_fotos(self, empresa_id: int, produto_id: UUID):
        """Lista fotos de um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrada")

        return await self.loja_online_foto_repo.listar_por_produto(produto_id)

    async def atualizar_foto(self, empresa_id: int, foto_id: UUID, dados: LojaOnlineFotoUpdate):
        """Atualiza uma foto."""
        foto = await self.loja_online_foto_repo.atualizar(
            empresa_id,
            foto_id,
            url=dados.url,
            ordem=dados.ordem,
        )
        if not foto:
            raise ValueError(f"Foto com ID {foto_id} não encontrada")
        return foto

    async def deletar_foto(self, empresa_id: int, foto_id: UUID):
        """Deleta uma foto."""
        return await self.loja_online_foto_repo.deletar(empresa_id, foto_id)


class FornecedorService:
    """Service para Fornecedor."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FornecedorRepository(session)

    async def criar_fornecedor(self, empresa_id: int, dados: FornecedorCreate):
        """Cria um novo fornecedor."""
        # Validar CNPJ único se fornecido
        if dados.cnpj:
            existente = await self.repo.obter_por_cnpj(empresa_id, dados.cnpj)
            if existente:
                raise ValueError(f"CNPJ '{dados.cnpj}' já cadastrado")

        return await self.repo.criar(
            empresa_id=empresa_id,
            nome=dados.nome,
            cnpj=dados.cnpj,
            email=dados.email,
            telefone=dados.telefone,
            endereco=dados.endereco,
            cidade=dados.cidade,
            uf=dados.uf,
        )

    async def obter_fornecedor(self, empresa_id: int, fornecedor_id: UUID):
        """Obtém um fornecedor por ID."""
        fornecedor = await self.repo.obter_por_id(empresa_id, fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")
        return fornecedor

    async def listar_fornecedores(self, empresa_id: int, skip: int = 0, limit: int = 10, apenas_ativos: bool = True):
        """Lista fornecedores."""
        return await self.repo.listar_todos(empresa_id=empresa_id, skip=skip, limit=limit, apenas_ativos=apenas_ativos)

    async def atualizar_fornecedor(self, empresa_id: int, fornecedor_id: UUID, dados: FornecedorUpdate):
        """Atualiza um fornecedor."""
        fornecedor = await self.repo.obter_por_id(empresa_id, fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")

        # Validar CNPJ se mudou
        if dados.cnpj and dados.cnpj != fornecedor.cnpj:
            existente = await self.repo.obter_por_cnpj(empresa_id, dados.cnpj)
            if existente:
                raise ValueError(f"CNPJ '{dados.cnpj}' já cadastrado")

        return await self.repo.atualizar(
            empresa_id,
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

    async def deletar_fornecedor(self, empresa_id: int, fornecedor_id: UUID):
        """Deleta um fornecedor."""
        fornecedor = await self.repo.obter_por_id(empresa_id, fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")

        return await self.repo.deletar(empresa_id, fornecedor_id)


class FornecedorProdutoService:
    """Service para Associação Fornecedor-Produto."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FornecedorProdutoRepository(session)
        self.fornecedor_repo = FornecedorRepository(session)
        self.produto_repo = ProdutoRepository(session)

    async def vincular_fornecedor(self, empresa_id: int, dados: FornecedorProdutoCreate):
        """Vincula um fornecedor a um produto."""
        # Validar fornecedor
        fornecedor = await self.fornecedor_repo.obter_por_id(empresa_id, dados.fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {dados.fornecedor_id} não encontrada")

        # Validar produto
        produto = await self.produto_repo.obter_por_id(empresa_id, dados.produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {dados.produto_id} não encontrada")

        # Validar preço
        if dados.preco_fornecedor <= 0:
            raise ValueError("Preço do fornecedor deve ser maior que zero")
        _exigir_preco_cobrindo_fornecedor(produto.preco, dados.preco_fornecedor)

        return await self.repo.criar(
            fornecedor_id=dados.fornecedor_id,
            produto_id=dados.produto_id,
            codigo_fornecedor=dados.codigo_fornecedor,
            preco_fornecedor=dados.preco_fornecedor,
            prazo_entrega_dias=dados.prazo_entrega_dias,
            quantidade_minima=dados.quantidade_minima,
        )

    async def obter_vinculo(self, empresa_id: int, vinculo_id: UUID):
        """Obtém um vínculo fornecedor-produto."""
        vinculo = await self.repo.obter_por_id(empresa_id, vinculo_id)
        if not vinculo:
            raise ValueError(f"Vínculo com ID {vinculo_id} não encontrada")
        return vinculo

    async def listar_fornecedores_produto(self, empresa_id: int, produto_id: UUID):
        """Lista fornecedores de um produto."""
        # Validar produto
        produto = await self.produto_repo.obter_por_id(empresa_id, produto_id)
        if not produto:
            raise ValueError(f"Produto com ID {produto_id} não encontrada")

        return await self.repo.listar_fornecedores_produto(produto_id)

    async def listar_produtos_fornecedor(self, empresa_id: int, fornecedor_id: UUID):
        """Lista produtos de um fornecedor."""
        # Validar fornecedor
        fornecedor = await self.fornecedor_repo.obter_por_id(empresa_id, fornecedor_id)
        if not fornecedor:
            raise ValueError(f"Fornecedor com ID {fornecedor_id} não encontrada")

        return await self.repo.listar_produtos_fornecedor(fornecedor_id)

    async def atualizar_vinculo(self, empresa_id: int, vinculo_id: UUID, dados: FornecedorProdutoUpdate):
        """Atualiza um vínculo fornecedor-produto."""
        vinculo = await self.repo.obter_por_id(empresa_id, vinculo_id)
        if not vinculo:
            raise ValueError(f"Vínculo com ID {vinculo_id} não encontrada")

        # Validar preço
        preco = dados.preco_fornecedor or vinculo.preco_fornecedor
        if preco <= 0:
            raise ValueError("Preço do fornecedor deve ser maior que zero")

        # O produto vem pelo vínculo já conferido acima, então continua sendo
        # da empresa — obter_por_id não devolveria produto de outro tenant.
        produto = await self.produto_repo.obter_por_id(empresa_id, vinculo.produto_id)
        if produto:
            _exigir_preco_cobrindo_fornecedor(produto.preco, preco)

        return await self.repo.atualizar(
            empresa_id,
            vinculo_id,
            codigo_fornecedor=dados.codigo_fornecedor,
            preco_fornecedor=dados.preco_fornecedor,
            prazo_entrega_dias=dados.prazo_entrega_dias,
            quantidade_minima=dados.quantidade_minima,
            ativo=dados.ativo,
        )

    async def deletar_vinculo(self, empresa_id: int, vinculo_id: UUID):
        """Deleta um vínculo fornecedor-produto."""
        vinculo = await self.repo.obter_por_id(empresa_id, vinculo_id)
        if not vinculo:
            raise ValueError(f"Vínculo com ID {vinculo_id} não encontrada")

        return await self.repo.deletar(empresa_id, vinculo_id)
