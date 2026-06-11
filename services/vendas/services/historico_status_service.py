"""
Service de Histórico de Status de Vendas.
Gerencia o registro de todas as mudanças de status das vendas.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import structlog

from models.venda import HistoricoStatusVenda

log = structlog.get_logger()


class HistoricoStatusService:
    """Service para operações de histórico de status."""
    
    @staticmethod
    async def registrar_mudanca(
        db: AsyncSession,
        venda_id: UUID,
        status_anterior: Optional[str],
        status_novo: str,
        alterado_por: Optional[UUID] = None,
        observacao: Optional[str] = None
    ) -> HistoricoStatusVenda:
        """
        Registra mudança de status de venda no histórico.
        
        Args:
            db: Sessão do banco
            venda_id: ID da venda
            status_anterior: Status anterior (NULL se primeira inserção)
            status_novo: Novo status
            alterado_por: ID do usuário que alterou (NULL = sistema automático)
            observacao: Observação sobre a mudança (ex: motivo cancelamento)
        
        Returns:
            HistoricoStatusVenda: Registro criado
        """
        try:
            historico = HistoricoStatusVenda(
                venda_id=venda_id,
                status_anterior=status_anterior,
                status_novo=status_novo,
                alterado_por=alterado_por,
                observacao=observacao,
                alterado_em=datetime.utcnow()
            )
            
            db.add(historico)
            await db.flush()
            
            log.info(
                "historico_status_registrado",
                venda_id=str(venda_id),
                status_anterior=status_anterior,
                status_novo=status_novo,
                alterado_por=str(alterado_por) if alterado_por else "sistema"
            )
            
            return historico
            
        except Exception as e:
            log.error(
                "erro_registrar_historico",
                venda_id=str(venda_id),
                error=str(e)
            )
            raise
    
    @staticmethod
    async def listar_por_venda(
        db: AsyncSession,
        venda_id: UUID
    ) -> List[HistoricoStatusVenda]:
        """
        Lista histórico de status de uma venda (ordenado por data).
        
        Args:
            db: Sessão do banco
            venda_id: ID da venda
        
        Returns:
            List[HistoricoStatusVenda]: Lista de mudanças de status
        """
        try:
            query = select(HistoricoStatusVenda).where(
                HistoricoStatusVenda.venda_id == venda_id
            ).order_by(HistoricoStatusVenda.alterado_em.asc())
            
            result = await db.execute(query)
            historicos = result.scalars().all()
            
            return list(historicos)
            
        except Exception as e:
            log.error(
                "erro_listar_historico",
                venda_id=str(venda_id),
                error=str(e)
            )
            raise
    
    @staticmethod
    async def obter_ultimo_status(
        db: AsyncSession,
        venda_id: UUID
    ) -> Optional[HistoricoStatusVenda]:
        """
        Obtém o último registro de status de uma venda.
        
        Args:
            db: Sessão do banco
            venda_id: ID da venda
        
        Returns:
            Optional[HistoricoStatusVenda]: Último registro ou None
        """
        try:
            query = select(HistoricoStatusVenda).where(
                HistoricoStatusVenda.venda_id == venda_id
            ).order_by(HistoricoStatusVenda.alterado_em.desc()).limit(1)
            
            result = await db.execute(query)
            historico = result.scalar_one_or_none()
            
            return historico
            
        except Exception as e:
            log.error(
                "erro_obter_ultimo_status",
                venda_id=str(venda_id),
                error=str(e)
            )
            raise
