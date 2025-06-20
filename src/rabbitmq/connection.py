import asyncio
import os

from aio_pika import connect_robust, exceptions
from loguru import logger

from handlers.message_handler import handle_message


RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
QUEUE_NAME = os.getenv('QUEUE_NAME', 'v2t_verbaMetrics')

shutdown_event = asyncio.Event()


async def connect_to_rabbitmq():
    '''
    подключение к rabbitmq с автоматическим переподключением
    '''
    while not shutdown_event.is_set():
        connection = None
        try:
            connection = await connect_robust(RABBITMQ_URL)
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)

            logger.info(f'connected to rabbitmq queue: {QUEUE_NAME}')
            consumer_tag = await queue.consume(handle_message)
            logger.info('consumer successfully registered')

            # ждем до сигнала на остановку
            await shutdown_event.wait()

            logger.info('shutdown_event set, cancelling consumer...')
            await queue.cancel(consumer_tag)

        except (exceptions.AMQPConnectionError, ConnectionError, RuntimeError) as e:
            logger.error(
                f'rabbitmq connection error: {e}. reconnecting in 5 seconds...')
            await asyncio.sleep(5)

        finally:
            if connection and not connection.is_closed:
                await connection.close()
                logger.info('rabbitmq connection closed')
