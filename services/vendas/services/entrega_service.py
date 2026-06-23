"""
Service de Entrega e Frete.
Gerencia validação de CEP, cálculo de taxa de entrega por bairro.
"""
from typing import Optional, Dict, Any
from decimal import Decimal
import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.venda import FaixaEntrega, ConfiguracaoLoja

log = structlog.get_logger()


class EntregaService:
    """
    Service para gerenciar entrega e cálculo de frete.
    
    Funcionalidades:
    - Validar CEP via ViaCEP
    - Calcular taxa de entrega (híbrida: padrão + exceções por bairro)
    - Gerenciar faixas de entrega por empresa
    """
    
    VIACEP_API_URL = "https://viacep.com.br/ws"
    
    @staticmethod
    async def validar_cep(cep: str) -> tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Valida CEP via ViaCEP.
        
        Args:
            cep: CEP sem formatação (8 dígitos)
        
        Returns:
            tuple: (valido, dados, erro)
                - valido: True se CEP existe
                - dados: Dict com logradouro, bairro, cidade, estado
                - erro: mensagem de erro se falhou
        """
        if not cep or len(cep) != 8:
            return (False, None, "CEP deve ter 8 dígitos")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{EntregaService.VIACEP_API_URL}/{cep}/json/",
                    timeout=5.0
                )
                
                if response.status_code != 200:
                    return (False, None, f"ViaCEP retornou status {response.status_code}")
                
                data = response.json()
                
                # ViaCEP retorna {"erro": true} para CEP inválido
                if data.get("erro"):
                    return (False, None, "CEP não encontrado")
                
                # Extrair dados relevantes
                dados = {
                    "logradouro": data.get("logradouro", ""),
                    "complemento": data.get("complemento", ""),
                    "bairro": data.get("bairro", ""),
                    "cidade": data.get("localidade", ""),
                    "estado": data.get("uf", ""),
                    "cep": cep
                }
                
                log.info(
                    "cep_validado",
                    cep=cep,
                    bairro=dados["bairro"],
                    cidade=dados["cidade"]
                )
                
                return (True, dados, None)
                
        except httpx.TimeoutException:
            log.warning("viacep_timeout", cep=cep)
            # Permite continuar mesmo se ViaCEP falhar
            return (False, None, "Timeout ao validar CEP - prossiga manualmente")
        
        except Exception as e:
            log.error("viacep_erro", error=str(e), cep=cep)
            # Permite continuar mesmo se ViaCEP falhar
            return (False, None, f"Erro ao validar CEP: {str(e)}")
    
    @staticmethod
    async def obter_config_loja(
        db: AsyncSession,
        empresa_id: int
    ) -> ConfiguracaoLoja:
        """
        Obtém configuração da loja (taxa padrão de entrega).
        Se não existir, cria com valores padrão.
        
        Returns:
            ConfiguracaoLoja: Configuração da loja
        """
        from repositories.venda_repository import ConfiguracaoLojaRepository
        
        # Buscar config existente
        config = await ConfiguracaoLojaRepository.buscar_por_empresa(db, empresa_id)
        
        if config:
            return config
        
        # Criar config padrão
        config = await ConfiguracaoLojaRepository.criar(
            db,
            empresa_id=empresa_id,
            taxa_entrega_padrao=Decimal('0.0'),
            cobrar_taxa_entrega=True
        )
        
        await db.flush()
        
        log.info(
            "config_loja_criada",
            empresa_id=empresa_id,
            taxa_padrao=float(config.taxa_entrega_padrao)
        )
        
        return config
    
    @staticmethod
    async def obter_faixa_por_bairro(
        db: AsyncSession,
        empresa_id: int,
        bairro: str
    ) -> Optional[FaixaEntrega]:
        """
        Busca faixa de entrega específica para um bairro.
        
        Returns:
            FaixaEntrega ou None se não tem exceção para este bairro
        """
        from repositories.venda_repository import FaixaEntregaRepository
        
        return await FaixaEntregaRepository.buscar_por_bairro(db, empresa_id, bairro)
    
    @staticmethod
    async def calcular_taxa_entrega(
        db: AsyncSession,
        empresa_id: int,
        cep: str,
        bairro: Optional[str] = None
    ) -> Decimal:
        """
        Calcula taxa de entrega (híbrida: padrão + exceções por bairro).
        
        Lógica:
        1. Se bairro fornecido, usa diretamente; senão extrai do CEP via ViaCEP
        2. Busca faixa específica para o bairro
        3. Se não encontrar, usa taxa padrão
        
        Args:
            empresa_id: ID da empresa
            cep: CEP sem formatação (8 dígitos)
            bairro: Nome do bairro (opcional, se não fornecido extrai do CEP)
        
        Returns:
            Decimal: Valor da taxa de entrega
        """
        # 1. Obter configuração da loja (taxa padrão)
        config = await EntregaService.obter_config_loja(db, empresa_id)
        
        # Se não cobra taxa, retorna 0
        if not config.cobrar_taxa_entrega:
            return Decimal('0.0')
        
        # 2. Obter bairro (se não fornecido, extrai do CEP)
        if not bairro:
            valido, dados, erro = await EntregaService.validar_cep(cep)
            
            if valido and dados:
                bairro = dados.get("bairro", "")
        
        # 3. Buscar faixa específica para o bairro
        if bairro:
            faixa = await EntregaService.obter_faixa_por_bairro(
                db, empresa_id, bairro
            )
            
            if faixa:
                log.info(
                    "taxa_entrega_calculada_faixa",
                    empresa_id=empresa_id,
                    bairro=bairro,
                    taxa=float(faixa.taxa)
                )
                return faixa.taxa
        
        # 4. Usar taxa padrão se não encontrou faixa específica
        log.info(
            "taxa_entrega_calculada_padrao",
            empresa_id=empresa_id,
            bairro=bairro,
            taxa=float(config.taxa_entrega_padrao)
        )
        
        return config.taxa_entrega_padrao
    
    @staticmethod
    async def criar_ou_atualizar_config_loja(
        db: AsyncSession,
        empresa_id: int,
        taxa_entrega_padrao: Decimal,
        cobrar_taxa_entrega: bool = True
    ) -> ConfiguracaoLoja:
        """
        Cria ou atualiza configuração da loja.
        
        Returns:
            ConfiguracaoLoja: Configuração criada/atualizada
        """
        config = await EntregaService.obter_config_loja(db, empresa_id)
        
        if config:
            config.taxa_entrega_padrao = taxa_entrega_padrao
            config.cobrar_taxa_entrega = cobrar_taxa_entrega
            
            log.info(
                "config_loja_atualizada",
                empresa_id=empresa_id,
                taxa=float(taxa_entrega_padrao)
            )
        else:
            config = ConfiguracaoLoja(
                empresa_id=empresa_id,
                taxa_entrega_padrao=taxa_entrega_padrao,
                cobrar_taxa_entrega=cobrar_taxa_entrega
            )
            db.add(config)
            
            log.info(
                "config_loja_criada",
                empresa_id=empresa_id,
                taxa=float(taxa_entrega_padrao)
            )
        
        await db.commit()
        await db.refresh(config)
        
        return config
    
    @staticmethod
    async def criar_faixa_entrega(
        db: AsyncSession,
        empresa_id: int,
        bairro: str,
        taxa: Decimal
    ) -> FaixaEntrega:
        """
        Cria faixa de entrega específica para um bairro.
        
        Returns:
            FaixaEntrega: Faixa criada
        """
        faixa = FaixaEntrega(
            empresa_id=empresa_id,
            bairro=bairro,
            taxa=taxa,
            ativo=True
        )
        
        db.add(faixa)
        await db.commit()
        await db.refresh(faixa)
        
        log.info(
            "faixa_entrega_criada",
            empresa_id=empresa_id,
            bairro=bairro,
            taxa=float(taxa)
        )
        
        return faixa
    
    @staticmethod
    async def atualizar_faixa_entrega(
        db: AsyncSession,
        faixa_id: str,
        taxa: Optional[Decimal] = None,
        ativo: Optional[bool] = None
    ) -> Optional[FaixaEntrega]:
        """
        Atualiza faixa de entrega existente.
        
        Returns:
            FaixaEntrega ou None se não encontrou
        """
        from uuid import UUID
        
        stmt = select(FaixaEntrega).where(FaixaEntrega.id == UUID(faixa_id))
        result = await db.execute(stmt)
        faixa = result.scalar_one_or_none()
        
        if not faixa:
            return None
        
        if taxa is not None:
            faixa.taxa = taxa
        
        if ativo is not None:
            faixa.ativo = ativo
        
        await db.commit()
        await db.refresh(faixa)
        
        log.info(
            "faixa_entrega_atualizada",
            faixa_id=faixa_id,
            taxa=float(faixa.taxa) if taxa else None,
            ativo=ativo
        )
        
        return faixa
    
    @staticmethod
    async def listar_faixas_entrega(
        db: AsyncSession,
        empresa_id: int,
        apenas_ativas: bool = True
    ) -> list[FaixaEntrega]:
        """
        Lista faixas de entrega da empresa.
        
        Returns:
            list[FaixaEntrega]: Lista de faixas
        """
        stmt = select(FaixaEntrega).where(
            FaixaEntrega.empresa_id == empresa_id
        )
        
        if apenas_ativas:
            stmt = stmt.where(FaixaEntrega.ativo == True)
        
        stmt = stmt.order_by(FaixaEntrega.bairro)
        
        result = await db.execute(stmt)
        return result.scalars().all()
