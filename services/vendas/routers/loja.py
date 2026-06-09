"""
Router da Loja Online (E-commerce).
Endpoints públicos para carrinho, checkout e rastreamento.
"""
from typing import Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Cookie, Response
from sqlalchemy.ext.asyncio import AsyncSession

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
from utils.tenant import get_empresa_id

router = APIRouter(prefix="/loja", tags=["loja-online"])


# ==================== CARRINHO ====================

@router.get(
    "/carrinho",
    response_model=CarrinhoResponse,
    summary="Obter Carrinho",
    description="Obtém carrinho atual da sessão ou cria novo"
)
async def obter_carrinho(
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    sessao_id: Annotated[str | None, Cookie(alias="cart_session_id")] = None,
    response: Response = None
):
    """
    Obtém carrinho existente ou cria novo.
    
    O sessao_id é armazenado em cookie (cart_session_id).
    Se não existir, gera novo e retorna no header Set-Cookie.
    """
    try:
        # Gerar sessao_id se não existir
        if not sessao_id:
            sessao_id = await CarrinhoService.gerar_sessao_id()
            # Definir cookie (7 dias = 604800 segundos)
            response.set_cookie(
                key="cart_session_id",
                value=sessao_id,
                max_age=604800,
                httponly=True,
                samesite="lax"
            )
        
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
    empresa_id: Annotated[int, Depends(get_empresa_id)],
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
            response.set_cookie(
                key="cart_session_id",
                value=sessao_id,
                max_age=604800,
                httponly=True,
                samesite="lax"
            )
        
        carrinho = await CarrinhoService.adicionar_item(
            sessao_id,
            empresa_id,
            data
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
    empresa_id: Annotated[int, Depends(get_empresa_id)],
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
    empresa_id: Annotated[int, Depends(get_empresa_id)],
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
    empresa_id: Annotated[int, Depends(get_empresa_id)],
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

@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Processar Checkout",
    description="Converte carrinho em pedido de venda"
)
async def processar_checkout(
    data: CheckoutRequest,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
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
    try:
        resultado = await LojaService.processar_checkout(
            db,
            sessao_id,
            empresa_id,
            data
        )
        
        return resultado
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar checkout: {str(e)}")


# ==================== ÁREA DO CLIENTE ====================

@router.get(
    "/meus-pedidos",
    response_model=list[PedidoClienteResumido],
    summary="Listar Meus Pedidos",
    description="Lista pedidos do cliente autenticado (requer autenticação futura)"
)
async def listar_meus_pedidos(
    cliente_id: UUID,  # TODO: Obter de token JWT quando auth estiver integrado
    empresa_id: Annotated[int, Depends(get_empresa_id)],
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Lista pedidos do cliente.
    
    **TODO**: Integrar com autenticação (JWT) para obter cliente_id automaticamente.
    Por enquanto, requer cliente_id como query param.
    """
    try:
        pedidos = await LojaService.listar_pedidos_cliente(
            db,
            empresa_id,
            cliente_id,
            skip,
            limit
        )
        
        return pedidos
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar pedidos: {str(e)}")


# ==================== RASTREAMENTO ====================

@router.get(
    "/rastrear/{numero_venda}",
    response_model=RastreamentoPedido,
    summary="Rastrear Pedido",
    description="Rastreia status do pedido pelo número da venda (público)"
)
async def rastrear_pedido(
    numero_venda: str,
    empresa_id: Annotated[int, Depends(get_empresa_id)],
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
