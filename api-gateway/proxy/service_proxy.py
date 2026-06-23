"""
Proxy HTTP para rotear requisições aos microsserviços.
"""
import httpx
from typing import Any, Optional
from fastapi import Request, Response, HTTPException, status
import structlog
from sqlalchemy import text
from config import settings
from models.usuario import Usuario
from database import get_db

log = structlog.get_logger()


class ServiceProxy:
    """Proxy para comunicação com microsserviços."""
    
    # Mapeamento de prefixos para URLs dos serviços
    SERVICE_URLS = {
        "/clientes": settings.CLIENTES_URL,
        "/produtos": settings.PRODUTOS_URL,
        "/categorias": settings.PRODUTOS_URL,
        "/variantes": settings.PRODUTOS_URL,
        "/fornecedores": settings.PRODUTOS_URL,
        "/catalogo": settings.PRODUTOS_URL,
        "/loja-online": settings.PRODUTOS_URL,
        "/estoque": settings.ESTOQUE_URL,
        "/loja": settings.VENDAS_URL,
        "/carrinho": settings.VENDAS_URL,
        "/pedidos": settings.VENDAS_URL,
        "/pagamentos": settings.VENDAS_URL,
        "/contas": settings.FINANCEIRO_URL,
        "/notificacoes": settings.NOTIFICACOES_URL,
        "/empresas": settings.EMPRESAS_URL,
    }
    
    @classmethod
    async def get_empresa_id_from_slug(cls, slug: str) -> int | None:
        """
        Resolve empresa_id a partir do slug.
        
        Args:
            slug: Slug da empresa (ex: 'distribuidora-central')
            
        Returns:
            int: ID da empresa ou None se não encontrado
        """
        try:
            async for db in get_db():
                result = await db.execute(
                    text("SELECT id FROM empresas.empresas WHERE slug = :slug"),
                    {"slug": slug}
                )
                row = result.first()
                return row[0] if row else None
        except Exception as e:
            log.error("erro ao resolver empresa_id", slug=slug, error=str(e))
            return None
    
    @classmethod
    async def proxy_request(
        cls,
        request: Request,
        path: str,
        current_user: Optional[Usuario] = None,
        empresa_slug: Optional[str] = None
    ) -> Response:
        """
        Faz proxy da requisição para o microsserviço apropriado.
        
        Args:
            request: Requisição FastAPI
            path: Caminho completo da requisição
            current_user: Usuário autenticado (opcional)
            empresa_slug: Slug da empresa para resolver empresa_id (opcional)
            
        Returns:
            Response do microsserviço
        """
        # Determinar qual serviço deve receber a requisição
        service_url = cls._get_service_url(path)
        
        if not service_url:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Serviço não encontrado"
            )
        
        # Construir URL completa
        target_url = f"{service_url}{path}"
        
        # Copiar query params
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"
        
        # Copiar headers (exceto host)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Adicionar header X-Empresa-Id
        empresa_id = None
        
        # 1. Tentar obter de empresa_slug (rotas públicas de loja)
        if empresa_slug:
            empresa_id = await cls.get_empresa_id_from_slug(empresa_slug)
            if not empresa_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empresa com slug '{empresa_slug}' não encontrada"
                )
        
        # 2. Se usuário autenticado e empresa_id não foi definido ainda
        elif current_user and hasattr(current_user, "empresa_id"):
            empresa_id = current_user.empresa_id
        
        # Adicionar header se empresa_id foi resolvido
        if empresa_id:
            headers["X-Empresa-Id"] = str(empresa_id)
        
        # Ler body se existir
        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
        
        log.info(
            "proxy.request",
            method=request.method,
            path=path,
            target=target_url,
            empresa_id=empresa_id
        )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body
                )
                
                log.info(
                    "proxy.response",
                    status_code=response.status_code,
                    path=path
                )
                
                # Retornar resposta do microsserviço
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
                
        except httpx.TimeoutException:
            log.error("proxy.timeout", path=path, target=target_url)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Serviço não respondeu a tempo"
            )
        except httpx.ConnectError:
            log.error("proxy.connection_error", path=path, target=target_url)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço indisponível"
            )
        except Exception as e:
            log.error("proxy.error", error=str(e), path=path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao comunicar com o serviço"
            )
    
    @classmethod
    def _get_service_url(cls, path: str) -> str | None:
        """
        Determina a URL do serviço baseado no caminho.
        
        Args:
            path: Caminho da requisição
            
        Returns:
            URL do serviço ou None
        """
        for prefix, url in cls.SERVICE_URLS.items():
            if path.startswith(prefix):
                return url
        return None
