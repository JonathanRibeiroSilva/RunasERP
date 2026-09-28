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
from interno import auth_interno
from auth.redis_client import get_redis
from proxy import idempotency

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
        "/loja-online": settings.PRODUTOS_URL,
        "/estoque": settings.ESTOQUE_URL,
        "/loja": settings.VENDAS_URL,
        "/carrinho": settings.VENDAS_URL,
        "/pagamentos": settings.VENDAS_URL,
        "/integracoes": settings.VENDAS_URL,
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

        None significa "não existe empresa com esse slug" e nada mais. Erros de
        banco sobem: um `except Exception` aqui transformava
        `relation "empresas.empresas" does not exist` em um 404 comum, e o stack
        rodava semanas parecendo saudável com a tabela de tenants ausente.
        """
        async for db in get_db():
            result = await db.execute(
                text("SELECT id FROM empresas.empresas WHERE slug = :slug"),
                {"slug": slug}
            )
            row = result.first()
            return row[0] if row else None

    @classmethod
    async def get_empresa_slug_from_id(cls, empresa_id: int) -> str | None:
        """
        Resolve o slug da empresa a partir do empresa_id.

        Args:
            empresa_id: ID da empresa

        Returns:
            str: Slug da empresa ou None se não encontrado

        Mesma regra do método acima: erro de banco sobe. Engolir a exceção fazia
        o /auth/login responder 200 com `empresa_slug: null`, o frontend seguir
        sem tenant e as chamadas seguintes baterem em 403 no validar_tenant —
        um login quebrado disfarçado de login bem-sucedido.
        """
        async for db in get_db():
            result = await db.execute(
                text("SELECT slug FROM empresas.empresas WHERE id = :empresa_id"),
                {"empresa_id": empresa_id}
            )
            row = result.first()
            return row[0] if row else None

    @classmethod
    async def _inject_context_headers(
        cls,
        headers: dict,
        current_user: Optional[Usuario],
        empresa_slug: Optional[str]
    ) -> int | None:
        """
        Pipeline único de injeção de contexto multi-tenancy.

        Resolve o empresa_id (slug público → usuário/cliente autenticado) e injeta os
        headers X-Empresa-Id e X-Cliente-Id. Toda rota proxied passa por aqui — sem
        injeção manual por rota. Retorna o empresa_id resolvido (para logging).
        """
        empresa_id = None

        # 1. Rotas públicas de loja: resolver empresa_id pelo slug
        if empresa_slug:
            empresa_id = await cls.get_empresa_id_from_slug(empresa_slug)
            if not empresa_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empresa com slug '{empresa_slug}' não encontrada"
                )
        # 2. Usuário/cliente autenticado
        elif current_user and hasattr(current_user, "empresa_id"):
            empresa_id = current_user.empresa_id

        if empresa_id:
            headers["X-Empresa-Id"] = str(empresa_id)

        # X-Cliente-Id quando o portador é um cliente autenticado
        if current_user and getattr(current_user, "cliente_id", None):
            headers["X-Cliente-Id"] = str(current_user.cliente_id)

        return empresa_id

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

        # Headers de contexto sao contrato do gateway: os servicos confiam neles
        # como identidade. O cliente nao pode fornece-los -- X-Plataforma nem era
        # sobrescrito abaixo, e chaves de request.headers vem minusculas, entao um
        # x-empresa-id do cliente sobreviveria ao lado do X-Empresa-Id injetado.
        for interno in ("x-empresa-id", "x-cliente-id", "x-plataforma",
                        "x-servico-interno-token", "x-plataforma-token"):
            headers.pop(interno, None)

        # E o gateway que prova a origem interna dos headers acima. Um unico
        # carimbo aqui cobre toda escrita e leitura de todos os servicos --
        # e' por aqui que passa praticamente todo o trafego da malha.
        headers = auth_interno(headers)

        # Injeção centralizada de contexto multi-tenancy (empresa_id / cliente_id)
        empresa_id = await cls._inject_context_headers(headers, current_user, empresa_slug)

        # Idempotência de escritas: reserva a chave ANTES de encaminhar, para que
        # um retry do cliente devolva a resposta salva em vez de duplicar a venda.
        # Sem o header Idempotency-Key nada muda — o caminho segue como antes.
        chave_idem = None
        valor_idem = request.headers.get("idempotency-key")
        if valor_idem and request.method in idempotency.METODOS:
            redis = await get_redis()
            chave_idem = idempotency.montar_chave(
                empresa_id, request.method, path, valor_idem
            )
            guardado = await idempotency.reservar(
                redis, chave_idem, settings.IDEMPOTENCY_TTL_SECONDS
            )
            if guardado is not None:
                log.info("proxy.idempotent_hit", path=path, empresa_id=empresa_id)
                return idempotency.responder_guardado(guardado)

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

                if chave_idem:
                    await idempotency.concluir(
                        redis,
                        chave_idem,
                        response.status_code,
                        response.content,
                        response.headers.get("content-type"),
                        settings.IDEMPOTENCY_TTL_SECONDS
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
            if chave_idem:
                await idempotency.liberar(redis, chave_idem)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Serviço não respondeu a tempo"
            )
        except httpx.ConnectError:
            log.error("proxy.connection_error", path=path, target=target_url)
            if chave_idem:
                await idempotency.liberar(redis, chave_idem)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Serviço indisponível"
            )
        except Exception as e:
            log.error("proxy.error", error=str(e), path=path)
            if chave_idem:
                await idempotency.liberar(redis, chave_idem)
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
