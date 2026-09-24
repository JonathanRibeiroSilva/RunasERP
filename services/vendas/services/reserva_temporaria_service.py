"""
Service de Reservas Temporárias de Estoque.
Gerencia reservas de estoque para o carrinho com Redis Lock e TTL.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from decimal import Decimal
import httpx
import redis.asyncio as redis
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models.venda import ReservaTemporaria
from config import settings
from interno import auth_interno

log = structlog.get_logger()


class ReservaTemporariaService:
    """
    Service para gerenciar reservas temporárias de estoque (carrinho).
    
    Usa Redis Lock para evitar race conditions e garantir consistência.
    Reservas expiram automaticamente após 15 minutos.
    """
    
    RESERVA_TTL_MINUTOS = 15
    REDIS_LOCK_TIMEOUT = 5  # segundos
    
    @staticmethod
    async def _get_redis() -> redis.Redis:
        """Retorna conexão Redis."""
        return redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=False  # Para locks, não precisa decode
        )
    
    @staticmethod
    async def _get_lock_key(produto_id: UUID, variante_id: Optional[UUID] = None) -> str:
        """Gera chave para lock Redis."""
        if variante_id:
            return f"lock:estoque:{produto_id}:{variante_id}"
        return f"lock:estoque:{produto_id}"
    
    @staticmethod
    async def _obter_quantidade_fisica(
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID] = None
    ) -> Decimal:
        """
        Obtém a quantidade física real no serviço de estoque.

        Em caso de falha de comunicação, retorna 0 (fail-closed): é preferível bloquear
        uma reserva temporária do que permitir overselling com dado de estoque incerto.
        """
        url = f"{settings.ESTOQUE_URL}/estoque/disponibilidade"
        headers = {"X-Empresa-Id": str(empresa_id)}
        params = {"produto_id": str(produto_id)}
        if variante_id:
            params["variante_id"] = str(variante_id)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, headers=auth_interno(headers), timeout=5.0)
            if response.status_code == 200:
                return Decimal(str(response.json().get("quantidade", 0)))
            log.warning(
                "estoque_disponibilidade_status_inesperado",
                status=response.status_code,
                produto_id=str(produto_id)
            )
            return Decimal('0.0')
        except Exception as e:
            log.error(
                "erro_consultar_disponibilidade_estoque",
                error=str(e),
                produto_id=str(produto_id)
            )
            return Decimal('0.0')

    @staticmethod
    async def calcular_disponivel(
        db: AsyncSession,
        empresa_id: int,
        produto_id: UUID,
        variante_id: Optional[UUID] = None
    ) -> Decimal:
        """
        Calcula estoque disponível DINAMICAMENTE.

        Fórmula: disponível = física_real - reservas_temporárias_não_expiradas

        A quantidade física vem do serviço de estoque (fonte de verdade). As reservas
        temporárias (carrinho) são subtraídas para refletir o que ainda pode ser vendido.

        Returns:
            Decimal: Quantidade disponível (nunca negativo)
        """
        # Buscar quantidade física real do serviço de estoque
        quantidade_fisica = await ReservaTemporariaService._obter_quantidade_fisica(
            empresa_id, produto_id, variante_id
        )

        # Somar reservas não expiradas
        stmt = select(func.coalesce(func.sum(ReservaTemporaria.quantidade), 0)).where(
            and_(
                ReservaTemporaria.empresa_id == empresa_id,
                ReservaTemporaria.produto_id == produto_id,
                ReservaTemporaria.variante_id == variante_id if variante_id else ReservaTemporaria.variante_id.is_(None),
                ReservaTemporaria.expira_em > datetime.utcnow()
            )
        )
        
        result = await db.execute(stmt)
        reservado = Decimal(str(result.scalar() or 0))
        
        disponivel = quantidade_fisica - reservado
        
        # Garantir que nunca retorna negativo
        return max(disponivel, Decimal('0.0'))
    
    @staticmethod
    async def reservar(
        db: AsyncSession,
        empresa_id: int,
        produto_id: UUID,
        quantidade: Decimal,
        sessao_id: str,
        variante_id: Optional[UUID] = None
    ) -> tuple[bool, Optional[Decimal], Optional[str]]:
        """
        Reserva estoque temporariamente (15 minutos) com Redis Lock.
        
        Returns:
            tuple: (sucesso, disponivel, mensagem_erro)
                - sucesso: True se reservou, False se não há estoque
                - disponivel: quantidade disponível atual
                - mensagem_erro: mensagem de erro se falhou
        """
        r = await ReservaTemporariaService._get_redis()
        lock_key = await ReservaTemporariaService._get_lock_key(produto_id, variante_id)
        
        try:
            # Adquirir lock (timeout 5 segundos)
            async with r.lock(
                lock_key,
                timeout=ReservaTemporariaService.REDIS_LOCK_TIMEOUT
            ):
                # 1. Calcular disponível (dentro do lock)
                disponivel = await ReservaTemporariaService.calcular_disponivel(
                    db, empresa_id, produto_id, variante_id
                )
                
                log.info(
                    "reserva_verificando_estoque",
                    empresa_id=empresa_id,
                    produto_id=str(produto_id),
                    variante_id=str(variante_id) if variante_id else None,
                    quantidade_solicitada=float(quantidade),
                    disponivel=float(disponivel)
                )
                
                # 2. Verificar se tem estoque suficiente
                if disponivel < quantidade:
                    log.warning(
                        "reserva_estoque_insuficiente",
                        empresa_id=empresa_id,
                        produto_id=str(produto_id),
                        solicitado=float(quantidade),
                        disponivel=float(disponivel)
                    )
                    return (False, disponivel, f"Apenas {disponivel} unidades disponíveis")
                
                # 3. Criar reserva (transação atômica)
                expira_em = datetime.utcnow() + timedelta(
                    minutes=ReservaTemporariaService.RESERVA_TTL_MINUTOS
                )
                
                reserva = ReservaTemporaria(
                    empresa_id=empresa_id,
                    produto_id=produto_id,
                    variante_id=variante_id,
                    quantidade=quantidade,
                    sessao_id=sessao_id,
                    expira_em=expira_em
                )
                
                db.add(reserva)
                await db.commit()
                
                log.info(
                    "reserva_criada",
                    empresa_id=empresa_id,
                    produto_id=str(produto_id),
                    quantidade=float(quantidade),
                    sessao_id=sessao_id,
                    expira_em=expira_em.isoformat()
                )
                
                return (True, disponivel, None)
                
        except Exception as e:
            await db.rollback()
            log.error(
                "reserva_erro",
                error=str(e),
                empresa_id=empresa_id,
                produto_id=str(produto_id)
            )
            return (False, None, f"Erro ao reservar estoque: {str(e)}")
        
        finally:
            await r.aclose()
    
    @staticmethod
    async def atualizar_reserva(
        db: AsyncSession,
        empresa_id: int,
        produto_id: UUID,
        sessao_id: str,
        nova_quantidade: Decimal,
        variante_id: Optional[UUID] = None
    ) -> tuple[bool, Optional[Decimal], Optional[str]]:
        """
        Atualiza quantidade de uma reserva existente com Redis Lock.
        
        Returns:
            tuple: (sucesso, disponivel, mensagem_erro)
        """
        r = await ReservaTemporariaService._get_redis()
        lock_key = await ReservaTemporariaService._get_lock_key(produto_id, variante_id)
        
        try:
            async with r.lock(lock_key, timeout=ReservaTemporariaService.REDIS_LOCK_TIMEOUT):
                # 1. Buscar reserva existente
                stmt = select(ReservaTemporaria).where(
                    and_(
                        ReservaTemporaria.empresa_id == empresa_id,
                        ReservaTemporaria.produto_id == produto_id,
                        ReservaTemporaria.variante_id == variante_id if variante_id else ReservaTemporaria.variante_id.is_(None),
                        ReservaTemporaria.sessao_id == sessao_id,
                        ReservaTemporaria.expira_em > datetime.utcnow()
                    )
                )
                
                result = await db.execute(stmt)
                reserva = result.scalar_one_or_none()
                
                if not reserva:
                    return (False, None, "Reserva não encontrada ou expirada")
                
                # 2. Calcular disponível considerando a reserva atual
                disponivel_total = await ReservaTemporariaService.calcular_disponivel(
                    db, empresa_id, produto_id, variante_id
                )
                
                # Somar a quantidade da reserva atual (que será liberada)
                disponivel_com_atual = disponivel_total + reserva.quantidade
                
                # 3. Verificar se nova quantidade é possível
                if disponivel_com_atual < nova_quantidade:
                    return (False, disponivel_com_atual, f"Apenas {disponivel_com_atual} unidades disponíveis")
                
                # 4. Atualizar reserva
                reserva.quantidade = nova_quantidade
                reserva.expira_em = datetime.utcnow() + timedelta(
                    minutes=ReservaTemporariaService.RESERVA_TTL_MINUTOS
                )
                
                await db.commit()
                
                log.info(
                    "reserva_atualizada",
                    empresa_id=empresa_id,
                    produto_id=str(produto_id),
                    nova_quantidade=float(nova_quantidade),
                    sessao_id=sessao_id
                )
                
                return (True, disponivel_com_atual, None)
                
        except Exception as e:
            await db.rollback()
            log.error("reserva_atualizar_erro", error=str(e))
            return (False, None, str(e))
        
        finally:
            await r.aclose()
    
    @staticmethod
    async def liberar_reserva(
        db: AsyncSession,
        empresa_id: int,
        produto_id: UUID,
        sessao_id: str,
        variante_id: Optional[UUID] = None
    ) -> bool:
        """
        Libera (remove) reserva de estoque.
        Usado quando item é removido do carrinho.
        
        Returns:
            bool: True se liberou, False se não encontrou
        """
        try:
            stmt = select(ReservaTemporaria).where(
                and_(
                    ReservaTemporaria.empresa_id == empresa_id,
                    ReservaTemporaria.produto_id == produto_id,
                    ReservaTemporaria.variante_id == variante_id if variante_id else ReservaTemporaria.variante_id.is_(None),
                    ReservaTemporaria.sessao_id == sessao_id,
                    ReservaTemporaria.expira_em > datetime.utcnow()
                )
            )
            
            result = await db.execute(stmt)
            reserva = result.scalar_one_or_none()
            
            if reserva:
                await db.delete(reserva)
                await db.commit()
                
                log.info(
                    "reserva_liberada",
                    empresa_id=empresa_id,
                    produto_id=str(produto_id),
                    quantidade=float(reserva.quantidade),
                    sessao_id=sessao_id
                )
                
                return True
            
            return False
            
        except Exception as e:
            await db.rollback()
            log.error("reserva_liberar_erro", error=str(e))
            return False
    
    @staticmethod
    async def liberar_todas_sessao(
        db: AsyncSession,
        sessao_id: str,
        empresa_id: int
    ) -> int:
        """
        Libera todas as reservas de uma sessão (ao finalizar checkout ou limpar carrinho).
        
        Returns:
            int: Número de reservas liberadas
        """
        try:
            stmt = select(ReservaTemporaria).where(
                and_(
                    ReservaTemporaria.sessao_id == sessao_id,
                    ReservaTemporaria.empresa_id == empresa_id
                )
            )
            
            result = await db.execute(stmt)
            reservas = result.scalars().all()
            
            count = len(reservas)
            
            for reserva in reservas:
                await db.delete(reserva)
            
            await db.commit()
            
            if count > 0:
                log.info(
                    "reservas_sessao_liberadas",
                    sessao_id=sessao_id,
                    empresa_id=empresa_id,
                    quantidade_liberada=count
                )
            
            return count
            
        except Exception as e:
            await db.rollback()
            log.error("reservas_liberar_sessao_erro", error=str(e))
            return 0
    
    @staticmethod
    async def limpar_expiradas(db: AsyncSession) -> int:
        """
        Remove reservas expiradas.
        Deve ser executado por job/cron a cada 1 minuto.
        
        Returns:
            int: Número de reservas removidas
        """
        try:
            stmt = select(ReservaTemporaria).where(
                ReservaTemporaria.expira_em <= datetime.utcnow()
            )
            
            result = await db.execute(stmt)
            expiradas = result.scalars().all()
            
            count = len(expiradas)
            
            for reserva in expiradas:
                await db.delete(reserva)
            
            await db.commit()
            
            if count > 0:
                log.info(
                    "reservas_expiradas_limpas",
                    quantidade=count
                )
            
            return count
            
        except Exception as e:
            await db.rollback()
            log.error("limpar_expiradas_erro", error=str(e))
            return 0
