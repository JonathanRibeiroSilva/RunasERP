"""
Router da Loja Online (E-commerce).
Endpoints públicos para carrinho, checkout e rastreamento.
"""
from typing import Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

log = structlog.get_logger()

from config import settings
from database import get_db
from schemas.loja import (
    ItemCarrinhoCreate,
    CarrinhoResponse,
    AtualizarQuantidadeRequest,
    CheckoutRequest,
    CheckoutResponse,
    PedidoClienteResumido,
    RastreamentoPedido
)
from services.carrinho_service import CarrinhoService
from services.loja_service import LojaService
from utils.tenant import get_empresa_id, get_empresa_id_from_slug, get_cliente_id, get_empresa_slug_by_id

router = APIRouter(prefix="/loja", tags=["loja-online"])

CART_COOKIE_MAX_AGE = 604800  # 7 dias


def definir_cookie_carrinho(response: Response, sessao_id: str) -> None:
    """Define o cookie cart_session_id; secure/samesite seguem o esquema do deploy (HTTPS vs HTTP local)."""
    is_https = settings.FRONTEND_URL.startswith("https://")
    response.set_cookie(
        key="cart_session_id",
        value=sessao_id,
        max_age=CART_COOKIE_MAX_AGE,
        httponly=True,
        secure=is_https,
        samesite="none" if is_https else "lax",
        path="/",
    )


# ==================== CARRINHO ====================

@router.get(
    "/carrinho",
    response_model=CarrinhoResponse,
    summary="Obter Carrinho",
    description="Obtém carrinho atual da sessão ou cria novo"
)
async def obter_carrinho(
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    sessao_id: Annotated[str | None, Cookie(alias="cart_session_id")] = None,
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtém carrinho existente ou cria novo.
    
    O sessao_id é armazenado em cookie (cart_session_id).
    Se não existir, gera novo e retorna no header Set-Cookie.
    
    🔐 SEGURANÇA: Se sessao_id foi usado em checkout mas carrinho foi limpo pelo webhook,
    gera novo sessao_id para evitar reutilização.
    """
    try:
        # Verificar se sessao_id já foi usado em alguma venda
        if sessao_id:
            from repositories.venda_repository import VendaRepository
            
            # Buscar venda com este sessao_carrinho_id
            venda_vinculada = await VendaRepository.buscar_por_sessao_carrinho(
                db, empresa_id, sessao_id
            )
            
            if venda_vinculada:
                # ✅ Esta sessão foi usada em checkout - verificar se carrinho ainda existe
                carrinho_existe = await CarrinhoService.carrinho_existe(sessao_id, empresa_id)
                
                if not carrinho_existe:
                    # Carrinho foi limpo pelo webhook → gerar novo sessao_id
                    log.info(
                        "carrinho_processado_gerando_novo",
                        sessao_antiga=sessao_id,
                        venda_id=str(venda_vinculada.id),
                        numero_venda=venda_vinculada.numero_venda
                    )
                    
                    sessao_id = await CarrinhoService.gerar_sessao_id()
                    definir_cookie_carrinho(response, sessao_id)
        
        # Gerar sessao_id se não existir
        if not sessao_id:
            sessao_id = await CarrinhoService.gerar_sessao_id()
            definir_cookie_carrinho(response, sessao_id)

        carrinho = await CarrinhoService.obter_ou_criar_carrinho(
            sessao_id,
            empresa_id
        )
        
        return carrinho
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter carrinho: {str(e)}")


@router.post(
    "/carrinho/itens",
    response_model=CarrinhoResponse,
    summary="Adicionar Item ao Carrinho",
    description="Adiciona produto ao carrinho ou incrementa quantidade se já existir"
)
async def adicionar_item_carrinho(
    data: ItemCarrinhoCreate,
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    db: AsyncSession = Depends(get_db),
    sessao_id: Annotated[str | None, Cookie(alias="cart_session_id")] = None,
    response: Response = None
):
    """
    Adiciona item ao carrinho.
    Se item já existe, incrementa quantidade.
    """
    try:
        # Gerar sessao_id se não existir
        if not sessao_id:
            sessao_id = await CarrinhoService.gerar_sessao_id()
            definir_cookie_carrinho(response, sessao_id)
        
        carrinho = await CarrinhoService.adicionar_item(
            sessao_id,
            empresa_id,
            data,
            db
        )
        
        return carrinho
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao adicionar item: {str(e)}")


@router.put(
    "/carrinho/itens/{produto_id}",
    response_model=CarrinhoResponse,
    summary="Atualizar Quantidade do Item",
    description="Atualiza quantidade de um item específico no carrinho"
)
async def atualizar_quantidade_item(
    produto_id: UUID,
    data: AtualizarQuantidadeRequest,
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    sessao_id: Annotated[str, Cookie(alias="cart_session_id")],
    variante_id: Optional[UUID] = None
):
    """
    Atualiza quantidade de item específico.
    """
    try:
        carrinho = await CarrinhoService.atualizar_quantidade_item(
            sessao_id,
            empresa_id,
            produto_id,
            variante_id,
            data
        )
        
        return carrinho
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar item: {str(e)}")


@router.delete(
    "/carrinho/itens/{produto_id}",
    response_model=CarrinhoResponse,
    summary="Remover Item do Carrinho",
    description="Remove item específico do carrinho"
)
async def remover_item_carrinho(
    produto_id: UUID,
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    sessao_id: Annotated[str, Cookie(alias="cart_session_id")],
    variante_id: Optional[UUID] = None
):
    """
    Remove item do carrinho.
    """
    try:
        carrinho = await CarrinhoService.remover_item(
            sessao_id,
            empresa_id,
            produto_id,
            variante_id
        )
        
        return carrinho
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover item: {str(e)}")


@router.delete(
    "/carrinho",
    summary="Limpar Carrinho",
    description="Remove todos os itens do carrinho"
)
async def limpar_carrinho(
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    sessao_id: Annotated[str, Cookie(alias="cart_session_id")]
):
    """
    Limpa carrinho completamente.
    """
    try:
        await CarrinhoService.limpar_carrinho(sessao_id, empresa_id)
        return {"message": "Carrinho limpo com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar carrinho: {str(e)}")


# ==================== CHECKOUT ====================

@router.post("/checkout/debug")
async def debug_checkout(request: dict):
    """Endpoint de debug para ver o payload recebido"""
    log.info("debug_payload", payload=request)
    return {"received": request}


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Processar Checkout",
    description="Converte carrinho em pedido de venda"
)
async def processar_checkout(
    data: CheckoutRequest,
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    sessao_id: Annotated[str, Cookie(alias="cart_session_id")],
    db: AsyncSession = Depends(get_db)
):
    """
    Processa checkout:
    1. Valida carrinho
    2. Cria venda com status PEDIDO
    3. Reserva estoque
    4. Limpa carrinho
    5. Retorna dados do pedido
    
    **Nota**: O pagamento deve ser confirmado posteriormente para prosseguir.
    """
    import structlog
    log = structlog.get_logger()
    
    # 🔍 DEBUG: Log do cookie recebido
    log.info(
        "🔍 DEBUG: Checkout - Cookie recebido no router",
        sessao_id=sessao_id,
        sessao_id_exists=bool(sessao_id),
        sessao_id_length=len(sessao_id) if sessao_id else 0,
        empresa_id=empresa_id,
        cliente_nome=data.cliente_novo.nome if data.cliente_novo else None
    )
    
    log.info("checkout_recebido", 
             cliente_nome=data.cliente_novo.nome if data.cliente_novo else None,
             tem_endereco=bool(data.endereco_entrega))
    
    try:
        resultado = await LojaService.processar_checkout(
            db,
            sessao_id,
            empresa_id,
            data
        )
        
        return resultado
        
    except ValueError as e:
        log.error("checkout_valor_error", erro=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error("checkout_exception", erro=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao processar checkout: {str(e)}")


# ==================== ÁREA DO CLIENTE ====================

@router.get(
    "/meus-pedidos",
    response_model=list[PedidoClienteResumido],
    summary="Listar Meus Pedidos",
    description="Lista pedidos do cliente autenticado (requer autenticação JWT)"
)
async def listar_meus_pedidos(
    cliente_id: Annotated[str, Depends(get_cliente_id)],
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista pedidos do cliente autenticado.
    
    O cliente_id é extraído automaticamente do header X-Cliente-Id,
    que é injetado pelo API Gateway quando o cliente faz login via JWT.
    
    **Autenticação**: Requer token JWT válido com tipo de usuário CLIENTE.
    """
    try:
        # Converter string UUID para UUID object
        from uuid import UUID
        cliente_uuid = UUID(cliente_id)
        
        pedidos = await LojaService.listar_pedidos_cliente(
            db,
            empresa_id,
            cliente_uuid,
            skip,
            limit
        )
        
        return pedidos
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"cliente_id inválido: {str(e)}"
        )
    except Exception as e:
        log.error("erro_listar_meus_pedidos", error=str(e), cliente_id=cliente_id)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar pedidos: {str(e)}"
        )


# ==================== RASTREAMENTO ====================

@router.get(
    "/rastrear/{numero_venda}",
    response_model=RastreamentoPedido,
    summary="Rastrear Pedido",
    description="Rastreia status do pedido pelo número da venda (público)"
)
async def rastrear_pedido(
    numero_venda: str,
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    db: AsyncSession = Depends(get_db)
):
    """
    Rastreia pedido pelo número da venda.
    
    Retorna:
    - Status atual
    - Histórico de mudanças
    - Próxima etapa esperada
    - Previsão de entrega (se aplicável)
    
    **Público**: Não requer autenticação (apenas número do pedido).
    """
    try:
        rastreamento = await LojaService.rastrear_pedido(
            db,
            empresa_id,
            numero_venda
        )
        
        if not rastreamento:
            raise HTTPException(
                status_code=404,
                detail=f"Pedido {numero_venda} não encontrado"
            )
        
        return rastreamento
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao rastrear pedido: {str(e)}")


# ==================== RETRY PAYMENT ====================

@router.post(
    "/pedidos/{numero_venda}/retry-payment",
    summary="Gerar Novo Link de Pagamento",
    description="Gera novo link do Mercado Pago para pedido com pagamento pendente"
)
async def retry_payment(
    numero_venda: str,
    cliente_id: Annotated[str, Depends(get_cliente_id)],
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    db: AsyncSession = Depends(get_db)
):
    """
    Gera novo link de pagamento do Mercado Pago para pedido com pagamento pendente.
    
    **Autenticação**: Requer cliente autenticado (JWT).
    
    **Regras**:
    - Pedido deve pertencer ao cliente autenticado
    - Status deve ser PEDIDO ou PENDENTE_PAGAMENTO
    - Gera nova preferência no Mercado Pago
    - Retorna novo link de pagamento
    
    **Uso**: Quando cliente desiste do pagamento ou link expira
    """
    try:
        from uuid import UUID
        from repositories.venda_repository import VendaRepository
        from services.mercadopago_service import MercadoPagoService
        from models.venda import StatusVenda
        
        # Converter cliente_id string para UUID
        cliente_uuid = UUID(cliente_id)
        
        # 1. Buscar venda pelo número
        venda = await VendaRepository.buscar_por_numero(
            db,
            empresa_id,
            numero_venda
        )
        
        if not venda:
            raise HTTPException(
                status_code=404,
                detail=f"Pedido {numero_venda} não encontrado"
            )
        
        # 2. Validar que venda pertence ao cliente autenticado
        if venda.cliente_id != cliente_uuid:
            log.warning(
                "retry_payment_cliente_nao_autorizado",
                venda_id=str(venda.id),
                venda_cliente_id=str(venda.cliente_id),
                cliente_autenticado_id=cliente_id
            )
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar este pedido"
            )
        
        # 3. Validar status (apenas PEDIDO ou PENDENTE_PAGAMENTO podem tentar pagamento)
        if venda.status not in [StatusVenda.PEDIDO.value, StatusVenda.PENDENTE_PAGAMENTO.value]:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível gerar link de pagamento para pedido com status {venda.status}"
            )
        
        # 4. Buscar venda completa com itens (necessário para criar preferência)
        venda_completa = await VendaRepository.buscar_por_id(
            db,
            empresa_id,
            venda.id,
            com_relacionamentos=True
        )
        
        if not venda_completa or not venda_completa.itens:
            raise HTTPException(
                status_code=500,
                detail="Erro ao buscar detalhes do pedido"
            )
        
        # 5. Resolver empresa_slug dinamicamente a partir do empresa_id (multi-tenant).
        # Sem fallback fixo: um slug de outra loja geraria back_urls/webhook do tenant errado.
        empresa_slug = await get_empresa_slug_by_id(db, empresa_id)
        if not empresa_slug:
            raise HTTPException(
                status_code=502,
                detail="Não foi possível resolver a loja para gerar o link de pagamento"
            )
        
        # 6. Criar nova preferência no Mercado Pago
        preferencia_id, init_point, sandbox_init_point, erro = await MercadoPagoService.criar_preferencia(
            db=db,
            venda=venda_completa,
            empresa_id=empresa_id,
            empresa_slug=empresa_slug
        )
        
        if erro:
            log.error(
                "retry_payment_erro_mercadopago",
                venda_id=str(venda.id),
                erro=erro
            )
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao gerar link de pagamento: {erro}"
            )
        
        if not init_point:
            raise HTTPException(
                status_code=500,
                detail="Mercado Pago não retornou link de pagamento"
            )

        # 7. Checkout Pro always uses init_point. With a Mercado Pago test user the
        # preference is already a TEST transaction, so the regular checkout accepts
        # test cards; the legacy sandbox_init_point is deprecated and never creates
        # card payments. APP_USR uses the same init_point for sandbox and production.
        mercadopago_url = init_point
        
        # 8. Atualizar venda com novo preference_id
        await VendaRepository.atualizar(
            db,
            empresa_id,
            venda.id,
            mercadopago_preference_id=preferencia_id,
            status=StatusVenda.PENDENTE_PAGAMENTO.value  # Garantir que status é PENDENTE_PAGAMENTO
        )
        
        log.info(
            "retry_payment_sucesso",
            venda_id=str(venda.id),
            numero_venda=numero_venda,
            cliente_id=cliente_id,
            preference_id=preferencia_id
        )
        
        return {
            "success": True,
            "venda_id": str(venda.id),
            "numero_venda": numero_venda,
            "mercadopago_url": mercadopago_url,
            "mensagem": "Novo link de pagamento gerado com sucesso"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(
            "retry_payment_erro",
            numero_venda=numero_venda,
            cliente_id=cliente_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar novo link de pagamento: {str(e)}"
        )


# ==================== RECUPERAR CARRINHO ====================

@router.post(
    "/pedidos/{numero_venda}/recuperar-carrinho",
    summary="Recuperar Carrinho de Pedido Não Pago",
    description="Reconstrói o carrinho a partir dos itens de um pedido com pagamento pendente"
)
async def recuperar_carrinho(
    numero_venda: str,
    cliente_id: Annotated[str, Depends(get_cliente_id)],
    empresa_id: Annotated[int, Depends(get_empresa_id_from_slug)],
    response: Response = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Recupera carrinho a partir de pedido com pagamento pendente.
    
    **Autenticação**: Requer cliente autenticado (JWT).
    
    **Regras**:
    - Pedido deve pertencer ao cliente autenticado
    - Status deve ser PEDIDO ou PENDENTE_PAGAMENTO
    - Reconstrói carrinho com itens do pedido
    - Valida estoque disponível
    - Gera nova sessão (não reutiliza a antiga)
    - Atualiza venda com nova sessão_carrinho_id
    - Retorna novo cookie cart_session_id
    
    **Uso**: Quando cliente deseja modificar pedido antes de pagar
    """
    try:
        from uuid import UUID
        from repositories.venda_repository import VendaRepository
        from services.carrinho_service import CarrinhoService
        from models.venda import StatusVenda
        from schemas.loja import ItemCarrinhoCreate
        
        # Converter cliente_id string para UUID
        cliente_uuid = UUID(cliente_id)
        
        # 1. Buscar venda pelo número (com itens)
        venda = await VendaRepository.buscar_por_numero(
            db,
            empresa_id,
            numero_venda
        )
        
        if not venda:
            raise HTTPException(
                status_code=404,
                detail=f"Pedido {numero_venda} não encontrado"
            )
        
        # Buscar venda completa com itens
        venda_completa = await VendaRepository.buscar_por_id(
            db,
            empresa_id,
            venda.id,
            com_relacionamentos=True
        )
        
        if not venda_completa or not venda_completa.itens:
            raise HTTPException(
                status_code=500,
                detail="Erro ao buscar itens do pedido"
            )
        
        # 2. Validar que venda pertence ao cliente autenticado
        if venda.cliente_id != cliente_uuid:
            log.warning(
                "recuperar_carrinho_cliente_nao_autorizado",
                venda_id=str(venda.id),
                venda_cliente_id=str(venda.cliente_id),
                cliente_autenticado_id=cliente_id
            )
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar este pedido"
            )
        
        # 3. Validar status (apenas PEDIDO ou PENDENTE_PAGAMENTO podem recuperar carrinho)
        if venda.status not in [StatusVenda.PEDIDO.value, StatusVenda.PENDENTE_PAGAMENTO.value]:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível recuperar carrinho de pedido com status {venda.status}"
            )
        
        # 4. Gerar nova sessão de carrinho
        nova_sessao_id = await CarrinhoService.gerar_sessao_id()
        
        log.info(
            "recuperar_carrinho_iniciado",
            venda_id=str(venda.id),
            numero_venda=numero_venda,
            sessao_antiga=venda.sessao_carrinho_id,
            sessao_nova=nova_sessao_id,
            quantidade_itens=len(venda_completa.itens)
        )
        
        # 5. Adicionar itens ao novo carrinho (validando estoque)
        itens_adicionados = 0
        itens_sem_estoque = []
        
        for item in venda_completa.itens:
            try:
                # Criar ItemCarrinhoCreate a partir do item da venda
                item_create = ItemCarrinhoCreate(
                    produto_id=item.produto_id,
                    variante_id=item.variante_id,
                    quantidade=item.quantidade
                )
                
                # Adicionar ao carrinho (valida estoque automaticamente)
                await CarrinhoService.adicionar_item(
                    nova_sessao_id,
                    empresa_id,
                    item_create,
                    db
                )
                
                itens_adicionados += 1
                
                log.info(
                    "recuperar_carrinho_item_adicionado",
                    produto_id=str(item.produto_id),
                    descricao=item.descricao_produto,
                    quantidade=float(item.quantidade)
                )
                
            except ValueError as e:
                # Item sem estoque - adicionar à lista de avisos
                itens_sem_estoque.append({
                    "descricao": item.descricao_produto,
                    "quantidade_pedido": float(item.quantidade),
                    "erro": str(e)
                })
                
                log.warning(
                    "recuperar_carrinho_item_sem_estoque",
                    produto_id=str(item.produto_id),
                    descricao=item.descricao_produto,
                    erro=str(e)
                )
        
        # 6. Verificar se pelo menos um item foi adicionado
        if itens_adicionados == 0:
            raise HTTPException(
                status_code=400,
                detail="Nenhum item do pedido está disponível em estoque"
            )
        
        # 7. Atualizar venda com nova sessao_carrinho_id
        await VendaRepository.atualizar(
            db,
            empresa_id,
            venda.id,
            sessao_carrinho_id=nova_sessao_id
        )
        
        # 8. Definir novo cookie cart_session_id
        definir_cookie_carrinho(response, nova_sessao_id)
        
        # 9. Obter carrinho reconstruído
        carrinho = await CarrinhoService.obter_ou_criar_carrinho(nova_sessao_id, empresa_id)
        
        log.info(
            "recuperar_carrinho_sucesso",
            venda_id=str(venda.id),
            numero_venda=numero_venda,
            nova_sessao_id=nova_sessao_id,
            itens_adicionados=itens_adicionados,
            itens_sem_estoque=len(itens_sem_estoque)
        )
        
        # 10. Montar resposta
        mensagem = f"Carrinho recuperado com sucesso! {itens_adicionados} item(ns) adicionado(s)."
        
        if itens_sem_estoque:
            mensagem += f" ATENÇÃO: {len(itens_sem_estoque)} item(ns) não foram adicionados por falta de estoque."
        
        return {
            "success": True,
            "venda_id": str(venda.id),
            "numero_venda": numero_venda,
            "nova_sessao_id": nova_sessao_id,
            "carrinho": carrinho.model_dump(),
            "itens_adicionados": itens_adicionados,
            "itens_sem_estoque": itens_sem_estoque,
            "mensagem": mensagem
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(
            "recuperar_carrinho_erro",
            numero_venda=numero_venda,
            cliente_id=cliente_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao recuperar carrinho: {str(e)}"
        )
