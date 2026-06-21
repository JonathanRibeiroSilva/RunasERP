"""
Service de Carrinho (Redis).
Gerencia carrinho de compras temporário usando Redis para performance.
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal
import redis.asyncio as redis
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.loja import (
    ItemCarrinhoCreate,
    ItemCarrinhoResponse,
    CarrinhoResponse,
    AtualizarQuantidadeRequest
)
from services.venda_service import VendaService
from config import settings

log = structlog.get_logger()


class CarrinhoService:
    """
    Service para gerenciar carrinho de compras no Redis.
    
    Estrutura no Redis:
    - Key: carrinho:{sessao_id}:{empresa_id}
    - TTL: 7 dias (604800 segundos)
    - Value: JSON com dados do carrinho
    """
    
    CARRINHO_PREFIX = "carrinho"
    CARRINHO_TTL = 604800  # 7 dias em segundos
    
    @staticmethod
    def _get_redis_key(sessao_id: str, empresa_id: int) -> str:
        """Gera chave Redis para o carrinho."""
        return f"{CarrinhoService.CARRINHO_PREFIX}:{sessao_id}:{empresa_id}"
    
    @staticmethod
    async def _get_redis() -> redis.Redis:
        """Retorna conexão Redis."""
        return redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    @staticmethod
    async def obter_ou_criar_carrinho(
        sessao_id: str,
        empresa_id: int
    ) -> CarrinhoResponse:
        """
        Obtém carrinho existente ou cria novo.
        """
        r = await CarrinhoService._get_redis()
        key = CarrinhoService._get_redis_key(sessao_id, empresa_id)
        
        try:
            # Tentar obter carrinho existente
            data = await r.get(key)
            
            if data:
                carrinho_dict = json.loads(data)
                # Renovar TTL
                await r.expire(key, CarrinhoService.CARRINHO_TTL)
                return CarrinhoResponse(**carrinho_dict)
            
            # Criar novo carrinho
            now = datetime.utcnow()
            carrinho = CarrinhoResponse(
                sessao_id=sessao_id,
                empresa_id=empresa_id,
                itens=[],
                subtotal=Decimal('0.0'),
                quantidade_itens=0,
                criado_em=now,
                atualizado_em=now
            )
            
            # Salvar no Redis
            await r.setex(
                key,
                CarrinhoService.CARRINHO_TTL,
                carrinho.model_dump_json()
            )
            
            log.info(
                "carrinho_criado",
                sessao_id=sessao_id,
                empresa_id=empresa_id
            )
            
            return carrinho
            
        finally:
            await r.aclose()
    
    @staticmethod
    async def adicionar_item(
        sessao_id: str,
        empresa_id: int,
        data: ItemCarrinhoCreate,
        db: AsyncSession  # ← NOVO: sessão do banco
    ) -> CarrinhoResponse:
        """
        Adiciona ou atualiza item no carrinho COM RESERVA DE ESTOQUE.
        """
        from services.reserva_temporaria_service import ReservaTemporariaService
        
        r = await CarrinhoService._get_redis()
        key = CarrinhoService._get_redis_key(sessao_id, empresa_id)
        
        try:
            # Validar e buscar dados do produto/variante
            if data.variante_id:
                # Buscar variante
                variante = await VendaService.verificar_produto_existe(
                    data.produto_id,
                    data.variante_id,
                    empresa_id
                )
                if not variante:
                    raise ValueError(f"Variante {data.variante_id} não encontrada")
                
                # Buscar dados do produto principal para obter nome
                produto = await VendaService.verificar_produto_existe(data.produto_id, None, empresa_id)
                if not produto:
                    raise ValueError(f"Produto {data.produto_id} não encontrado")
                
                # Extrair dados combinados (variante + produto)
                codigo = variante.get('sku')
                descricao = produto.get('nome')
                preco = Decimal(str(variante.get('preco_venda', 0)))
            else:
                # Buscar apenas produto (sem variante)
                produto = await VendaService.verificar_produto_existe(data.produto_id, None, empresa_id)
                if not produto:
                    raise ValueError(f"Produto {data.produto_id} não encontrado")
                
                # Extrair dados do produto
                codigo = produto.get('codigo', produto.get('sku'))
                descricao = produto.get('nome')
                preco = Decimal(str(produto.get('preco', produto.get('preco_venda', 0))))
            
            if preco <= 0:
                raise ValueError("Produto sem preço de venda definido")
            
            # ========== RESERVAR ESTOQUE (NOVO) ==========
            sucesso, disponivel, erro = await ReservaTemporariaService.reservar(
                db=db,
                empresa_id=empresa_id,
                produto_id=data.produto_id,
                quantidade=data.quantidade,
                sessao_id=sessao_id,
                variante_id=data.variante_id
            )
            
            if not sucesso:
                # Retornar erro com quantidade disponível
                raise ValueError(
                    f"Estoque insuficiente. {erro if erro else f'Disponível: {disponivel}'}"
                )
            
            # Obter carrinho atual
            carrinho = await CarrinhoService.obter_ou_criar_carrinho(sessao_id, empresa_id)
            
            # Verificar se item já existe
            item_existente = None
            for item in carrinho.itens:
                if (str(item.produto_id) == str(data.produto_id) and 
                    str(item.variante_id) == str(data.variante_id)):
                    item_existente = item
                    break
            
            if item_existente:
                # Atualizar quantidade
                item_existente.quantidade += data.quantidade
                item_existente.subtotal = item_existente.quantidade * item_existente.preco_unitario
            else:
                # Adicionar novo item
                novo_item = ItemCarrinhoResponse(
                    produto_id=data.produto_id,
                    variante_id=data.variante_id,
                    codigo_produto=codigo,
                    descricao_produto=descricao,
                    preco_unitario=preco,
                    quantidade=data.quantidade,
                    subtotal=data.quantidade * preco,
                    estoque_disponivel=True
                )
                carrinho.itens.append(novo_item)
            
            # Recalcular totais
            carrinho.subtotal = sum(item.subtotal for item in carrinho.itens)
            carrinho.quantidade_itens = len(carrinho.itens)
            carrinho.atualizado_em = datetime.utcnow()
            
            # Salvar no Redis
            await r.setex(
                key,
                CarrinhoService.CARRINHO_TTL,
                carrinho.model_dump_json()
            )
            
            log.info(
                "item_adicionado_carrinho_com_reserva",
                sessao_id=sessao_id,
                empresa_id=empresa_id,
                produto_id=str(data.produto_id),
                quantidade=float(data.quantidade),
                disponivel=float(disponivel) if disponivel else None
            )
            
            return carrinho
            
        finally:
            await r.aclose()
    
    @staticmethod
    async def atualizar_quantidade_item(
        sessao_id: str,
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID],
        data: AtualizarQuantidadeRequest
    ) -> CarrinhoResponse:
        """
        Atualiza quantidade de um item específico.
        """
        r = await CarrinhoService._get_redis()
        key = CarrinhoService._get_redis_key(sessao_id, empresa_id)
        
        try:
            # Obter carrinho
            carrinho = await CarrinhoService.obter_ou_criar_carrinho(sessao_id, empresa_id)
            
            # Encontrar item
            item_encontrado = None
            for item in carrinho.itens:
                if (str(item.produto_id) == str(produto_id) and 
                    str(item.variante_id) == str(variante_id)):
                    item_encontrado = item
                    break
            
            if not item_encontrado:
                raise ValueError("Item não encontrado no carrinho")
            
            # Atualizar quantidade
            item_encontrado.quantidade = data.quantidade
            item_encontrado.subtotal = data.quantidade * item_encontrado.preco_unitario
            
            # Recalcular totais
            carrinho.subtotal = sum(item.subtotal for item in carrinho.itens)
            carrinho.atualizado_em = datetime.utcnow()
            
            # Salvar
            await r.setex(
                key,
                CarrinhoService.CARRINHO_TTL,
                carrinho.model_dump_json()
            )
            
            log.info(
                "quantidade_atualizada",
                sessao_id=sessao_id,
                produto_id=str(produto_id),
                nova_quantidade=float(data.quantidade)
            )
            
            return carrinho
            
        finally:
            await r.aclose()
    
    @staticmethod
    async def remover_item(
        sessao_id: str,
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID]
    ) -> CarrinhoResponse:
        """
        Remove item do carrinho.
        """
        r = await CarrinhoService._get_redis()
        key = CarrinhoService._get_redis_key(sessao_id, empresa_id)
        
        try:
            # Obter carrinho
            carrinho = await CarrinhoService.obter_ou_criar_carrinho(sessao_id, empresa_id)
            
            # Remover item
            carrinho.itens = [
                item for item in carrinho.itens
                if not (str(item.produto_id) == str(produto_id) and 
                       str(item.variante_id) == str(variante_id))
            ]
            
            # Recalcular totais
            carrinho.subtotal = sum(item.subtotal for item in carrinho.itens)
            carrinho.quantidade_itens = len(carrinho.itens)
            carrinho.atualizado_em = datetime.utcnow()
            
            # Salvar
            await r.setex(
                key,
                CarrinhoService.CARRINHO_TTL,
                carrinho.model_dump_json()
            )
            
            log.info(
                "item_removido",
                sessao_id=sessao_id,
                produto_id=str(produto_id)
            )
            
            return carrinho
            
        finally:
            await r.aclose()
    
    @staticmethod
    async def limpar_carrinho(
        sessao_id: str,
        empresa_id: int
    ) -> bool:
        """
        Remove carrinho completamente do Redis.
        """
        r = await CarrinhoService._get_redis()
        key = CarrinhoService._get_redis_key(sessao_id, empresa_id)
        
        try:
            deleted = await r.delete(key)
            
            if deleted:
                log.info(
                    "carrinho_limpo",
                    sessao_id=sessao_id,
                    empresa_id=empresa_id
                )
            
            return deleted > 0
            
        finally:
            await r.aclose()
    
    @staticmethod
    async def gerar_sessao_id() -> str:
        """
        Gera novo ID de sessão (UUID v4).
        Frontend deve armazenar em cookie.
        """
        return str(uuid4())
