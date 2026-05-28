"""
Proxy HTTP para rotear requisições aos microsserviços.
"""
import httpx
from typing import Any
from fastapi import Request, Response, HTTPException, status
import structlog
from config import settings

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
        "/estoque": settings.ESTOQUE_URL,
        "/carrinho": settings.VENDAS_URL,
        "/pedidos": settings.VENDAS_URL,
        "/pagamentos": settings.VENDAS_URL,
        "/contas": settings.FINANCEIRO_URL,
        "/notificacoes": settings.NOTIFICACOES_URL,
    }
    
    @classmethod
    async def proxy_request(
        cls,
        request: Request,
        path: str
    ) -> Response:
        """
        Faz proxy da requisição para o microsserviço apropriado.
        
        Args:
            request: Requisição FastAPI
            path: Caminho completo da requisição
            
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
        
        # Ler body se existir
        body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None
        
        log.info(
            "proxy.request",
            method=request.method,
            path=path,
            target=target_url
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
