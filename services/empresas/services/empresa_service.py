"""
Service para Empresas.
Contém toda a lógica de negócio relacionada a empresas (multi-tenancy).
"""
from typing import Optional, List
import re
import unicodedata
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from interno import auth_interno
from exceptions import ValidationError, NotFoundError, ConflictError
from models.empresa import Empresa, TipoEmpresa, StatusEmpresa
from schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaPlanoUpdate,
    EmpresaResponse,
    EmpresaListItem,
    EmpresaPublicInfo,
)
from repositories.empresa_repository import EmpresaRepository
from utils.validators import validar_cnpj


class EmpresaService:
    """Service para regras de negócio de Empresas."""
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa o service com a sessão do banco.
        
        Args:
            session: Sessão assíncrona do SQLAlchemy
        """
        self.session = session
        self.repository = EmpresaRepository(session)
    
    async def criar_empresa(
        self,
        empresa_data: EmpresaCreate,
        criado_por: Optional[int] = None
    ) -> EmpresaResponse:
        """
        Cria uma nova empresa com validações de negócio.
        
        Regras:
        - CNPJ deve ser válido
        - CNPJ não pode estar cadastrado
        - Slug não pode estar em uso
        - Se for filial, matriz deve existir
        
        Args:
            empresa_data: Dados da empresa
            criado_por: ID do usuário que está criando
            
        Returns:
            Empresa criada
            
        Raises:
            ValidationError: Se dados inválidos
            ConflictError: Se CNPJ ou slug já existe
        """
        # Validar CNPJ
        cnpj_limpo = empresa_data.cnpj.replace(".", "").replace("/", "").replace("-", "")
        if not validar_cnpj(cnpj_limpo):
            raise ValidationError("CNPJ inválido", {"campo": "cnpj"})
        
        # Verificar se CNPJ já existe (incluindo inativas)
        empresa_existente = await self.repository.buscar_por_cnpj(
            empresa_data.cnpj,
            incluir_inativas=True
        )
        
        if empresa_existente:
            if empresa_existente.ativo:
                raise ConflictError(
                    "Já existe uma empresa cadastrada com este CNPJ",
                    {"campo": "cnpj", "empresa_id": empresa_existente.id}
                )
            else:
                # Reativar empresa existente
                return await self._reativar_empresa_existente(
                    empresa_existente,
                    empresa_data,
                    criado_por
                )
        
        # Slug omitido: gerar automaticamente a partir do nome fantasia (URL pública da loja)
        if not empresa_data.slug:
            empresa_data.slug = await self._gerar_slug_unico(empresa_data.nome_fantasia)
        else:
            # Verificar se slug já existe
            slug_existente = await self.repository.buscar_por_slug(empresa_data.slug)
            if slug_existente:
                raise ConflictError(
                    "Já existe uma empresa com este slug",
                    {"campo": "slug", "empresa_id": slug_existente.id}
                )
        
        # Se for filial, validar que a matriz existe
        if empresa_data.tipo == TipoEmpresa.FILIAL:
            if not empresa_data.empresa_matriz_id:
                raise ValidationError(
                    "Filiais devem informar a empresa matriz",
                    {"campo": "empresa_matriz_id"}
                )
            
            matriz = await self.repository.buscar_por_id(empresa_data.empresa_matriz_id)
            if not matriz:
                raise NotFoundError(
                    "Empresa matriz não encontrada",
                    {"empresa_matriz_id": empresa_data.empresa_matriz_id}
                )
            
            if matriz.tipo != TipoEmpresa.MATRIZ:
                raise ValidationError(
                    "A empresa informada não é uma matriz",
                    {"empresa_matriz_id": empresa_data.empresa_matriz_id}
                )
            
            # Verificar limite de filiais do plano da matriz
            num_filiais = await self.repository.contar_filiais(matriz.id)
            if num_filiais >= matriz.max_lojas:
                raise ConflictError(
                    f"Limite de {matriz.max_lojas} filiais atingido para o plano {matriz.plano}",
                    {"max_lojas": matriz.max_lojas, "atual": num_filiais}
                )
        
        # Criar empresa
        try:
            empresa = await self.repository.criar(empresa_data, criado_por)
            await self.session.commit()
            return EmpresaResponse.model_validate(empresa)
        except Exception as e:
            await self.session.rollback()
            raise ValidationError(f"Erro ao criar empresa: {str(e)}")
    
    async def _gerar_slug_unico(self, nome: str, excluir_empresa_id: Optional[int] = None) -> str:
        """
        Gera um slug único a partir de um nome (loja-2, loja-3... em caso de conflito).

        excluir_empresa_id: em renomeações, o slug atual da própria empresa não conta
        como conflito (renomear "Loja X" para "loja x" mantém o slug, sem sufixo).
        """
        base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
        base = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:90]
        if len(base) < 3:
            base = "loja"

        slug = base
        sufixo = 2
        while True:
            existente = await self.repository.buscar_por_slug(slug)
            if not existente or existente.id == excluir_empresa_id:
                return slug
            slug = f"{base}-{sufixo}"
            sufixo += 1

    async def _reativar_empresa_existente(
        self,
        empresa_existente: Empresa,
        empresa_data: EmpresaCreate,
        criado_por: Optional[int]
    ) -> EmpresaResponse:
        """
        Reativa uma empresa existente e atualiza apenas dados cadastrais.
        
        Mantém: Configurações, limites, plano
        Atualiza: Dados cadastrais, endereço, contato
        """
        # Criar objeto de atualização apenas com dados cadastrais
        update_data = EmpresaUpdate(
            slug=empresa_data.slug,
            razao_social=empresa_data.razao_social,
            nome_fantasia=empresa_data.nome_fantasia,
            inscricao_estadual=empresa_data.inscricao_estadual,
            inscricao_municipal=empresa_data.inscricao_municipal,
            regime_tributario=empresa_data.regime_tributario,
            cep=empresa_data.cep,
            logradouro=empresa_data.logradouro,
            numero=empresa_data.numero,
            complemento=empresa_data.complemento,
            bairro=empresa_data.bairro,
            cidade=empresa_data.cidade,
            uf=empresa_data.uf,
            telefone=empresa_data.telefone,
            celular=empresa_data.celular,
            email=empresa_data.email,
            site=empresa_data.site,
        )
        
        # Reativar
        empresa_reativada = await self.repository.reativar(empresa_existente, criado_por)
        
        # Atualizar dados cadastrais
        empresa_atualizada = await self.repository.atualizar(
            empresa_reativada,
            update_data,
            criado_por
        )
        
        await self.session.commit()
        return EmpresaResponse.model_validate(empresa_atualizada)
    
    async def buscar_empresa(self, empresa_id: int) -> EmpresaResponse:
        """
        Busca uma empresa por ID.
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            Empresa encontrada
            
        Raises:
            NotFoundError: Se empresa não existe
        """
        empresa = await self.repository.buscar_por_id(empresa_id)
        if not empresa:
            raise NotFoundError(
                "Empresa não encontrada",
                {"empresa_id": empresa_id}
            )
        
        return EmpresaResponse.model_validate(empresa)
    
    async def buscar_empresa_por_slug(self, slug: str) -> EmpresaResponse:
        """
        Busca uma empresa por slug.
        
        Args:
            slug: Slug da empresa
            
        Returns:
            Empresa encontrada
            
        Raises:
            NotFoundError: Se empresa não existe
        """
        empresa = await self.repository.buscar_por_slug(slug)
        if not empresa:
            raise NotFoundError(
                "Empresa não encontrada",
                {"slug": slug}
            )
        
        return EmpresaResponse.model_validate(empresa)
    
    async def buscar_info_publica(self, slug: str) -> EmpresaPublicInfo:
        """
        Busca informações públicas da empresa (para catálogo).
        
        Args:
            slug: Slug da empresa
            
        Returns:
            Informações públicas da empresa
            
        Raises:
            NotFoundError: Se empresa não existe ou catálogo não está ativo
        """
        empresa = await self.repository.buscar_info_publica_por_slug(slug)
        if not empresa:
            raise NotFoundError(
                "Empresa não encontrada ou catálogo não está ativo",
                {"slug": slug}
            )
        
        return EmpresaPublicInfo.model_validate(empresa)
    
    async def listar_empresas(
        self,
        tenant_id: int,
        skip: int = 0,
        limit: int = 100,
        busca: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[str] = None,
        uf: Optional[str] = None,
    ) -> tuple[List[EmpresaListItem], int]:
        """
        Lista empresas com filtros e paginação.
        
        Args:
            tenant_id: Empresa do chamador — a listagem nunca sai do próprio tenant
            skip: Número de registros a pular
            limit: Número máximo de registros
            busca: Termo de busca
            tipo: Filtro por tipo
            status: Filtro por status
            uf: Filtro por UF
            
        Returns:
            Tupla com (lista de empresas, total)
        """
        # Validar status se fornecido
        status_enum = None
        if status:
            try:
                status_enum = StatusEmpresa(status)
            except ValueError:
                raise ValidationError(
                    f"Status inválido. Use: {', '.join([s.value for s in StatusEmpresa])}",
                    {"campo": "status"}
                )
        
        empresas, total = await self.repository.listar(
            tenant_id=tenant_id,
            skip=skip,
            limit=limit,
            busca=busca,
            tipo=tipo,
            status=status_enum,
            uf=uf
        )
        
        empresas_response = [
            EmpresaListItem.model_validate(empresa)
            for empresa in empresas
        ]
        
        return empresas_response, total
    
    async def atualizar_empresa(
        self,
        empresa_id: int,
        empresa_data: EmpresaUpdate,
        atualizado_por: Optional[int] = None
    ) -> EmpresaResponse:
        """
        Atualiza uma empresa.
        
        Args:
            empresa_id: ID da empresa
            empresa_data: Novos dados
            atualizado_por: ID do usuário que está atualizando
            
        Returns:
            Empresa atualizada
            
        Raises:
            NotFoundError: Se empresa não existe
            ConflictError: Se slug ou CNPJ conflita com outra empresa
        """
        empresa = await self.repository.buscar_por_id(empresa_id)
        if not empresa:
            raise NotFoundError(
                "Empresa não encontrada",
                {"empresa_id": empresa_id}
            )
        
        # Validar CNPJ se estiver sendo alterado
        if empresa_data.cnpj and empresa_data.cnpj != empresa.cnpj:
            cnpj_limpo = empresa_data.cnpj.replace(".", "").replace("/", "").replace("-", "")
            if not validar_cnpj(cnpj_limpo):
                raise ValidationError("CNPJ inválido", {"campo": "cnpj"})
            
            cnpj_existente = await self.repository.buscar_por_cnpj(empresa_data.cnpj)
            if cnpj_existente and cnpj_existente.id != empresa_id:
                raise ConflictError(
                    "Já existe uma empresa com este CNPJ",
                    {"campo": "cnpj", "empresa_id": cnpj_existente.id}
                )
        
        # Validar slug se estiver sendo alterado
        if empresa_data.slug and empresa_data.slug != empresa.slug:
            slug_existente = await self.repository.buscar_por_slug(empresa_data.slug)
            if slug_existente and slug_existente.id != empresa_id:
                raise ConflictError(
                    "Já existe uma empresa com este slug",
                    {"campo": "slug", "empresa_id": slug_existente.id}
                )

        # Nome da loja alterado sem slug explícito: o endereço público (/c/{slug})
        # acompanha o novo nome automaticamente. Links antigos deixam de funcionar —
        # o frontend avisa o lojista antes de salvar.
        if (
            empresa_data.slug is None
            and empresa_data.catalogo_titulo
            and empresa_data.catalogo_titulo != empresa.catalogo_titulo
        ):
            novo_slug = await self._gerar_slug_unico(
                empresa_data.catalogo_titulo, excluir_empresa_id=empresa_id
            )
            if novo_slug != empresa.slug:
                empresa_data.slug = novo_slug

        # Atualizar
        try:
            empresa_atualizada = await self.repository.atualizar(
                empresa,
                empresa_data,
                atualizado_por
            )
            await self.session.commit()
            return EmpresaResponse.model_validate(empresa_atualizada)
        except Exception as e:
            await self.session.rollback()
            raise ValidationError(f"Erro ao atualizar empresa: {str(e)}")
    
    async def listar_todas_plataforma(self) -> List[EmpresaListItem]:
        """Todos os tenants, para o painel da plataforma."""
        return [
            EmpresaListItem.model_validate(e)
            for e in await self.repository.listar_todas()
        ]

    async def atualizar_plano(
        self,
        empresa_id: int,
        plano_data: "EmpresaPlanoUpdate",
    ) -> EmpresaResponse:
        """
        Atualiza plano, limites e status — campos de billing da plataforma.

        Separado de atualizar_empresa de propósito: os dois schemas são
        disjuntos, e é essa separação que impede o lojista de se auto-promover.
        """
        empresa = await self.repository.buscar_por_id(empresa_id)
        if not empresa:
            raise NotFoundError(
                "Empresa não encontrada",
                {"empresa_id": empresa_id}
            )

        for campo, valor in plano_data.model_dump(exclude_unset=True).items():
            setattr(empresa, campo, valor)

        await self.session.commit()
        await self.session.refresh(empresa)
        return EmpresaResponse.model_validate(empresa)

    @staticmethod
    async def _tem_dados_dependentes(empresa_id: int) -> List[str]:
        """
        Verifica se a empresa tem clientes, produtos ou vendas cadastrados (G5).

        Conservador de propósito: resposta inesperada, timeout ou erro de rede
        em qualquer uma das três checagens entra na lista de volta igual um
        dependente de verdade teria — presumir que há dado e bloquear a
        desativação é mais seguro do que desativar sem saber ao certo.
        """
        alvos = {
            "clientes": f"{settings.CLIENTES_URL}/clientes",
            "produtos": f"{settings.PRODUTOS_URL}/produtos",
            "vendas": f"{settings.VENDAS_URL}/vendas",
        }
        headers = auth_interno({"X-Empresa-Id": str(empresa_id)})

        encontrados = []
        async with httpx.AsyncClient() as client:
            for nome, url in alvos.items():
                try:
                    response = await client.get(
                        url, params={"limit": 1}, headers=headers, timeout=5.0
                    )
                    if response.status_code != 200 or response.json().get("total", 0) > 0:
                        encontrados.append(nome)
                except Exception:
                    encontrados.append(nome)
        return encontrados

    async def desativar_empresa(
        self,
        empresa_id: int,
        atualizado_por: Optional[int] = None
    ) -> EmpresaResponse:
        """
        Desativa uma empresa (soft delete).
        
        Args:
            empresa_id: ID da empresa
            atualizado_por: ID do usuário que está desativando
            
        Returns:
            Empresa desativada
            
        Raises:
            NotFoundError: Se empresa não existe
        """
        empresa = await self.repository.buscar_por_id(empresa_id)
        if not empresa:
            raise NotFoundError(
                "Empresa não encontrada",
                {"empresa_id": empresa_id}
            )

        dependentes = await self._tem_dados_dependentes(empresa_id)
        if dependentes:
            raise ConflictError(
                "Empresa tem dados dependentes e não pode ser desativada",
                {"empresa_id": empresa_id, "dependentes": dependentes}
            )

        try:
            empresa_desativada = await self.repository.desativar(empresa, atualizado_por)
            await self.session.commit()
            return EmpresaResponse.model_validate(empresa_desativada)
        except Exception as e:
            await self.session.rollback()
            raise ValidationError(f"Erro ao desativar empresa: {str(e)}")
    
    async def listar_filiais(self, empresa_matriz_id: int) -> List[EmpresaListItem]:
        """
        Lista todas as filiais de uma matriz.
        
        Args:
            empresa_matriz_id: ID da empresa matriz
            
        Returns:
            Lista de filiais
            
        Raises:
            NotFoundError: Se matriz não existe
        """
        matriz = await self.repository.buscar_por_id(empresa_matriz_id)
        if not matriz:
            raise NotFoundError(
                "Empresa matriz não encontrada",
                {"empresa_matriz_id": empresa_matriz_id}
            )
        
        if matriz.tipo != TipoEmpresa.MATRIZ:
            raise ValidationError(
                "A empresa informada não é uma matriz",
                {"empresa_id": empresa_matriz_id}
            )
        
        filiais = await self.repository.listar_filiais(empresa_matriz_id)
        
        return [EmpresaListItem.model_validate(filial) for filial in filiais]
