"""
Job para limpar carrinhos abandonados (>7 dias).
Remove carrinhos do Redis que não foram acessados há mais de 7 dias.

Deve rodar a cada 1 dia (diariamente) via cron ou scheduler.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json
import redis.asyncio as redis

# Adicionar path do projeto
sys.path.append(str(Path(__file__).parent.parent))

import structlog

from config import settings

log = structlog.get_logger()


async def _get_redis() -> redis.Redis:
    """Retorna cliente Redis."""
    return redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )


async def limpar_carrinhos_abandonados():
    """
    Limpa carrinhos abandonados do Redis (>7 dias sem acesso).
    
    Critério: carrinhos cuja última atualização (atualizado_em) é maior que 7 dias.
    """
    log.info("job_limpar_carrinhos_iniciado")
    
    r = await _get_redis()
    try:
        # Padrão de chaves de carrinho: carrinho:{sessao_id}:{empresa_id}
        pattern = "carrinho:*"
        cursor = "0"
        
        carrinhos_verificados = 0
        carrinhos_removidos = 0
        
        # Limite de 7 dias
        limite = datetime.utcnow() - timedelta(days=7)
        
        # Varrer todas as chaves de carrinho
        while cursor != 0:
            cursor, keys = await r.scan(
                cursor=int(cursor),
                match=pattern,
                count=100
            )
            
            for key in keys:
                try:
                    carrinhos_verificados += 1
                    
                    # Obter carrinho do Redis
                    carrinho_json = await r.get(key)
                    
                    if not carrinho_json:
                        continue
                    
                    carrinho_data = json.loads(carrinho_json)
                    
                    # Verificar data de atualização
                    atualizado_em_str = carrinho_data.get('atualizado_em')
                    
                    if not atualizado_em_str:
                        # Se não tem data, considerar como abandonado (caso antigo)
                        await r.delete(key)
                        carrinhos_removidos += 1
                        
                        log.info(
                            "carrinho_removido_sem_data",
                            key=key
                        )
                        continue
                    
                    # Parsear data
                    try:
                        atualizado_em = datetime.fromisoformat(atualizado_em_str.replace('Z', '+00:00'))
                    except:
                        # Formato inválido - remover
                        await r.delete(key)
                        carrinhos_removidos += 1
                        continue
                    
                    # Verificar se está abandonado (>7 dias)
                    if atualizado_em < limite:
                        await r.delete(key)
                        carrinhos_removidos += 1
                        
                        log.info(
                            "carrinho_abandonado_removido",
                            key=key,
                            atualizado_em=atualizado_em_str,
                            dias_abandonado=(datetime.utcnow() - atualizado_em).days
                        )
                
                except Exception as e:
                    log.error(
                        "erro_processar_carrinho",
                        key=key,
                        error=str(e)
                    )
        
        log.info(
            "job_limpar_carrinhos_concluido",
            carrinhos_verificados=carrinhos_verificados,
            carrinhos_removidos=carrinhos_removidos
        )
        
    except Exception as e:
        log.error(
            "job_limpar_carrinhos_erro",
            error=str(e)
        )
    finally:
        await r.aclose()


if __name__ == "__main__":
    """
    Executar:
    python jobs/limpar_carrinhos_abandonados.py
    
    Configurar cron (Linux) - a cada 1 dia (3h da manhã):
    0 3 * * * cd /path/to/vendas-service && python jobs/limpar_carrinhos_abandonados.py
    
    Configurar Task Scheduler (Windows):
    - Trigger: Diariamente às 3h
    - Action: python.exe jobs/limpar_carrinhos_abandonados.py
    """
    asyncio.run(limpar_carrinhos_abandonados())
