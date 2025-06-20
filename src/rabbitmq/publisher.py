import os
import json

from aio_pika import connect_robust, Message, exceptions
from loguru import logger


RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
VERBAMETRICS_DG_QUEUE = os.getenv(
    'VERBAMETRICS_DG_QUEUE', 'verbaMetrics_dg_queue')


async def publish_results_verbametrics_dg_queue(data: dict):
    '''
    отправка ключевых слов в dg
    '''
    connection = None
    try:
        connection = await connect_robust(RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue(VERBAMETRICS_DG_QUEUE, durable=True, passive=True)
            await channel.default_exchange.publish(
                Message(body=json.dumps(data).encode(), delivery_mode=2),
                routing_key=VERBAMETRICS_DG_QUEUE)
            logger.success(
                f'data published to queue {VERBAMETRICS_DG_QUEUE}: {data}')
    except exceptions.AMQPConnectionError as e:
        logger.error(f'failed to connect to RabbitMQ: {e}')
    except Exception as e:
        logger.error(f'error publishing message to RabbitMQ: {e}')
    finally:
        if connection and not connection.is_closed:
            await connection.close()
