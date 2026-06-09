"""
Repository para Empresas.
Responsável por todas as queries ao banco de dados.
"""
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.empresa import Empresa, StatusEmpresa
from schemas.empresa import EmpresaCreate, EmpresaUpdate


class EmpresaRepository:
    """Repository para operações de banco de dados de Empresas."""
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa o repository com a sessão do banco.
        
        Args:
            session: Sessão assíncrona do SQLAlchemy
        """
        self.session = session
    
    async def criar(self, empresa_data: EmpresaCreate, criado_por: Optional[int] = None) -> Empresa:
        """
        Cria uma nova empresa.
        
        Args:
            empresa_data: Dados da empresa
            criado_por: ID do usuário que criou
            
        Returns:
            Empresa criada
        """
        empresa = Empresa(**empresa_data.model_dump(), criado_por=criado_por)
        self.session.add(empresa)
        await self.session.flush()
        await self.session.refresh(empresa)
        return empresa
    
    async def buscar_por_id(self, empresa_id: int) -> Optional[Empresa]:
        """
        Busca empresa por ID (apenas ativas).
        
        Args:
            empresa_id: ID da empresa
            
        Returns:
            Empresa encontrada ou None
        """
        stmt = select(Empresa).where(
            Empresa.id == empresa_id,
            Empresa.ativo == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def buscar_por_slug(self, slug: str) -> Optional[Empresa]:
        """
        Busca empresa por slug (apenas ativas).
        
        Args:
            slug: Slug da empresa
            
        Returns:
            Empresa encontrada ou None
        """
        stmt = select(Empresa).where(
            Empresa.slug == slug.lower(),
            Empresa.ativo == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def buscar_por_cnpj(self, cnpj: str, incluir_inativas: bool = False) -> Optional[Empresa]:
        """
        Busca empresa por CNPJ.
        
        Args:
            cnpj: CNPJ da empresa
            incluir_inativas: Se deve incluir empresas inativas
            
        Returns:
            Empresa encontrada ou None
        """
        stmt = select(Empresa).where(Empresa.cnpj == cnpj)
        
        if not incluir_inativas:
            stmt = stmt.where(Empresa.ativo == True)
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def listar(
        self,
        skip: int = 0,
        limit: int = 100,
        busca: Optional[str] = None,
        tipo: Optional[str] = None,
        status: Optional[StatusEmpresa] = None,
        uf: Optional[str] = None,
    ) -> tuple[List[Empresa], int]:
        """
        Lista empresas com filtros e paginação.
        
        Args:
            skip: Número de registros a pular
            limit: Número máximo de registros
            busca: Termo de busca (razão social, nome fantasia, CNPJ)
            tipo: Filtro por tipo de empresa
            status: Filtro por status
            uf: Filtro por UF
            
        Returns:
            Tupla com (lista de empresas, total de registros)
        """
        # Query base - apenas empresas ativas
        stmt = select(Empresa).where(Empresa.ativo == True)
        
        # Aplicar filtros
        if busca:
            busca_like = f"%{busca}%"
            stmt = stmt.where(
                or_(
                    Empresa.razao_social.ilike(busca_like),
                    Empresa.nome_fantasia.ilike(busca_like),
                    Empresa.cnpj.like(busca_like)
                )
            )
        
        if tipo:
            stmt = stmt.where(Empresa.tipo == tipo)
        
        if status:
            stmt = stmt.where(Empresa.status == status)
        
        if uf:
            stmt = stmt.where(Empresa.uf == uf.upper())
        
        # Contar total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()
        
        # Aplicar paginação e ordenação
        stmt = stmt.order_by(Empresa.nome_fantasia).offset(skip).limit(limit)
        
        # Executar query
        result = await self.session.execute(stmt)
        empresas = list(result.scalars().all())
        
        return empresas, total
    
    async def atualizar(
        self,
        empresa: Empresa,
        empresa_data: EmpresaUpdate,
        atualizado_por: Optional[int] = None
    ) -> Empresa:
        """
        Atualiza uma empresa.
        
        Args:
            empresa: Empresa a ser atualizada
            empresa_data: Novos dados
            atualizado_por: ID do usuário que atualizou
            
        Returns:
            Empresa atualizada
        """
        # Atualizar apenas campos fornecidos (não None)
        for field, value in empresa_data.model_dump(exclude_unset=True).items():
            setattr(empresa, field, value)
        
        if atualizado_por:
            empresa.atualizado_por = atualizado_por
        
        await self.session.flush()
        await self.session.refresh(empresa)
        return empresa
    
    async def desativar(self, empresa: Empresa, atualizado_por: Optional[int] = None) -> Empresa:
        """
        Desativa uma empresa (soft delete).
        
        Args:
            empresa: Empresa a ser desativada
            atualizado_por: ID do usuário que desativou
            
        Returns:
            Empresa desativada
        """
        empresa.ativo = False
        empresa.status = StatusEmpresa.INATIVA
        
        if atualizado_por:
            empresa.atualizado_por = atualizado_por
        
        await self.session.flush()
        await self.session.refresh(empresa)
        return empresa
    
    async def reativar(self, empresa: Empresa, atualizado_por: Optional[int] = None) -> Empresa:
        """
        Reativa uma empresa.
        
        Args:
            empresa: Empresa a ser reativada
            atualizado_por: ID do usuário que reativou
            
        Returns:
            Empresa reativada
        """
        empresa.ativo = True
        empresa.status = StatusEmpresa.ATIVA
        
        if atualizado_por:
            empresa.atualizado_por = atualizado_por
        
        await self.session.flush()
        await self.session.refresh(empresa)
        return empresa
    
    async def listar_filiais(self, empresa_matriz_id: int) -> List[Empresa]:
        """
        Lista todas as filiais de uma matriz.
        
        Args:
            empresa_matriz_id: ID da empresa matriz
            
        Returns:
            Lista de filiais
        """
        stmt = select(Empresa).where(
            Empresa.empresa_matriz_id == empresa_matriz_id,
            Empresa.ativo == True
        ).order_by(Empresa.nome_fantasia)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def contar_filiais(self, empresa_matriz_id: int) -> int:
        """
        Conta o número de filiais ativas de uma matriz.
        
        Args:
            empresa_matriz_id: ID da empresa matriz
            
        Returns:
            Número de filiais
        """
        stmt = select(func.count()).select_from(Empresa).where(
            Empresa.empresa_matriz_id == empresa_matriz_id,
            Empresa.ativo == True
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def buscar_info_publica_por_slug(self, slug: str) -> Optional[Empresa]:
        """
        Busca informações públicas da empresa por slug (para catálogo).
        
        Args:
            slug: Slug da empresa
            
        Returns:
            Empresa com dados públicos ou None
        """
        stmt = select(Empresa).where(
            Empresa.slug == slug.lower(),
            Empresa.ativo == True,
            Empresa.status == StatusEmpresa.ATIVA,
            Empresa.catalogo_ativo == True
        )
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
