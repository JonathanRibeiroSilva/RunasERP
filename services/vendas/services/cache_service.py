"""
Service de Cache de Produtos para Loja Online.
Usa Redis para cache de produtos com TTL de 5 minutos.
"""
from typing import Optional, Dict, Any
from uuid import UUID
import json
from decimal import Decimal
import structlog
import httpx

from auth.redis_client import redis_client
from config import settings

log = structlog.get_logger()


class CacheService:
    """Service para cache de produtos em Redis."""
    
    # TTL de 5 minutos
    CACHE_TTL = 300
    
    @staticmethod
    def _get_cache_key(produto_id: UUID, variante_id: Optional[UUID] = None) -> str:
        """
        Gera chave do cache.
        
        Args:
            produto_id: ID do produto
            variante_id: ID da variante (opcional)
        
        Returns:
            str: Chave do Redis
        """
        if variante_id:
            return f"loja:produto:{produto_id}:variante:{variante_id}"
        return f"loja:produto:{produto_id}"
    
    @staticmethod
    async def obter_produto(
        produto_id: UUID,
        variante_id: Optional[UUID] = None,
        empresa_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém produto do cache ou busca no serviço.
        
        Args:
            produto_id: ID do produto
            variante_id: ID da variante (opcional)
            empresa_id: ID da empresa (para busca no serviço)
        
        Returns:
            Optional[Dict[str, Any]]: Dados do produto ou None
        """
        try:
            cache_key = CacheService._get_cache_key(produto_id, variante_id)
            
            # Tentar obter do cache
            cached = await redis_client.get(cache_key)
            if cached:
                log.debug("produto_cache_hit", produto_id=str(produto_id))
                return json.loads(cached)
            
            # Cache miss - buscar no serviço
            log.debug("produto_cache_miss", produto_id=str(produto_id))
            produto = await CacheService._buscar_produto_servico(
                produto_id,
                variante_id,
                empresa_id
            )
            
            if produto:
                # Salvar no cache
                await CacheService._salvar_cache(cache_key, produto)
            
            return produto
            
        except Exception as e:
            log.error(
                "erro_cache_produto",
                produto_id=str(produto_id),
                error=str(e)
            )
            # Em caso de erro, retornar None (não bloquear)
            return None
    
    @staticmethod
    async def _buscar_produto_servico(
        produto_id: UUID,
        variante_id: Optional[UUID] = None,
        empresa_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca produto no serviço de produtos.
        
        Args:
            produto_id: ID do produto
            variante_id: ID da variante (opcional)
            empresa_id: ID da empresa
        
        Returns:
            Optional[Dict[str, Any]]: Dados do produto ou None
        """
        try:
            async with httpx.AsyncClient() as client:
                if variante_id:
                    url = f"{settings.PRODUTOS_URL}/produtos/{produto_id}/variantes/{variante_id}"
                else:
                    url = f"{settings.PRODUTOS_URL}/produtos/{produto_id}"
                
                headers = {}
                if empresa_id:
                    headers["X-Empresa-Id"] = str(empresa_id)
                
                response = await client.get(url, headers=headers, timeout=5.0)
                
                if response.status_code == 200:
                    return response.json()
                
                return None
                
        except Exception as e:
            log.error(
                "erro_buscar_produto_servico",
                produto_id=str(produto_id),
                error=str(e)
            )
            return None
    
    @staticmethod
    async def _salvar_cache(cache_key: str, produto: Dict[str, Any]) -> None:
        """
        Salva produto no cache.
        
        Args:
            cache_key: Chave do Redis
            produto: Dados do produto
        """
        try:
            # Converter Decimal para string (JSON serialization)
            produto_str = json.dumps(produto, default=str)
            await redis_client.setex(
                cache_key,
                CacheService.CACHE_TTL,
                produto_str
            )
            
            log.debug("produto_salvo_cache", cache_key=cache_key)
            
        except Exception as e:
            log.error("erro_salvar_cache", cache_key=cache_key, error=str(e))
    
    @staticmethod
    async def invalidar_produto(
        produto_id: UUID,
        variante_id: Optional[UUID] = None
    ) -> None:
        """
        Invalida cache de um produto.
        
        Args:
            produto_id: ID do produto
            variante_id: ID da variante (opcional)
        """
        try:
            cache_key = CacheService._get_cache_key(produto_id, variante_id)
            await redis_client.delete(cache_key)
            
            log.info("produto_cache_invalidado", produto_id=str(produto_id))
            
        except Exception as e:
            log.error(
                "erro_invalidar_cache",
                produto_id=str(produto_id),
                error=str(e)
            )
    
    @staticmethod
    async def limpar_cache_empresa(empresa_id: int) -> None:
        """
        Limpa todo cache de produtos de uma empresa.
        
        Args:
            empresa_id: ID da empresa
        """
        try:
            # Buscar todas as chaves com padrão loja:produto:*
            pattern = "loja:produto:*"
            cursor = "0"
            
            while cursor != 0:
                cursor, keys = await redis_client.scan(
                    cursor=int(cursor),
                    match=pattern,
                    count=100
                )
                
                if keys:
                    await redis_client.delete(*keys)
            
            log.info("cache_empresa_limpo", empresa_id=empresa_id)
            
        except Exception as e:
            log.error(
                "erro_limpar_cache_empresa",
                empresa_id=empresa_id,
                error=str(e)
            )
