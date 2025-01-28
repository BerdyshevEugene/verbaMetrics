import asyncio
import json
import os

from loguru import logger
from aio_pika import IncomingMessage

from handlers.text_processor import TextProcessor
from .dict import stop_words, target_words, target_words_2


processor = TextProcessor(
    target_words=[target_words, target_words_2],
    stop_words=stop_words
)


async def handle_message(message: IncomingMessage):
    '''
    обработка данных из RabbitMQ
    '''
    try:
        data = json.loads(message.body)
        logger.info(f'received message: {data}')

        master_id = data.get('MasterID')
        text = data.get('text')
        if not master_id or not text:
            logger.error('invalid message format, rejecting')
            await message.reject()
            return

        # Передаем оба словаря отдельно
        processor = TextProcessor(
            target_words=target_words,  # передаем словарь target_words
            target_words_2=target_words_2,  # передаем словарь target_words_2
            stop_words=stop_words
        )
        result_data = processor.analyze_text(master_id, text)
        await processor.publish_results_to_queue(result_data)
        await message.ack()

    except Exception as e:
        logger.error(f'error in handle_message: {e}')
        await message.reject()
