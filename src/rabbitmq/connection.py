import asyncio
import os

from aio_pika import connect_robust, exceptions
from loguru import logger

from handlers.message_handler import handle_message


RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
QUEUE_NAME = os.getenv('QUEUE_NAME', 'v2t_verbaMetrics')


async def connect_to_rabbitmq():
    '''
    подключение и регистрация обработчика сообщений
    '''
    while True:
        try:
            connection = await connect_robust(RABBITMQ_URL)
            channel = await connection.channel()

            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)
            logger.info(f'connected to RabbitMQ queue: {QUEUE_NAME}')

            await queue.consume(handle_message)
            logger.info('consumer successfully registered')

            await asyncio.Future()
        except exceptions.AMQPConnectionError as e:
            logger.error(f'connection to RabbitMQ failed: {e}. Retrying...')
            await asyncio.sleep(5)
