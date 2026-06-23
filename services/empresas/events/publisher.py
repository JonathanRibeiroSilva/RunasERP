"""
Publisher de eventos para o serviço de empresas.
"""
import json
from typing import Any
import aio_pika
from aio_pika import Message
import structlog

from config import settings

log = structlog.get_logger()


class EventPublisher:
    """
    Publisher de eventos via RabbitMQ.
    """
    
    def __init__(self):
        self.connection = None
        self.channel = None
    
    async def connect(self):
        """Estabelece conexão com RabbitMQ."""
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            log.info("rabbitmq.connected")
        except Exception as e:
            log.error("rabbitmq.connection_failed", error=str(e))
            raise
    
    async def close(self):
        """Fecha a conexão com RabbitMQ."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        log.info("rabbitmq.disconnected")
    
    async def publish(self, event_type: str, data: dict[str, Any]):
        """
        Publica um evento no RabbitMQ.
        
        Args:
            event_type: Tipo do evento (ex: 'empresa.criada', 'empresa.atualizada')
            data: Dados do evento
        """
        if not self.channel:
            await self.connect()
        
        exchange = await self.channel.declare_exchange(
            "empresas",
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        message_body = {
            "event_type": event_type,
            "data": data
        }
        
        message = Message(
            body=json.dumps(message_body).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await exchange.publish(message, routing_key=event_type)
        
        log.info("event.published", event_type=event_type, empresa_id=data.get("id"))


# Instância global do publisher
event_publisher = EventPublisher()
