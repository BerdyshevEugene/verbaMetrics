import asyncio
import json

from loguru import logger
from aio_pika import IncomingMessage

from handlers.text_processor import TextProcessor
from .dict import (
    stop_words,
    target_words_1,
    target_words_2,
    target_words_3,
    target_words_4,
    target_words_5,
    target_words_6,
    target_words_answer_tags,
)


processor = TextProcessor(
    target_words_1=target_words_1,
    target_words_2=target_words_2,
    target_words_3=target_words_3,
    target_words_4=target_words_4,
    target_words_5=target_words_5,
    target_words_6=target_words_6,
    stop_words=stop_words,
    target_words_answer_tags=target_words_answer_tags,
)


async def handle_message(message: IncomingMessage):
    """
    обработка данных из rabbitmq
    """
    try:
        data = json.loads(message.body)
        logger.info(f"received message: {data}")

        master_id = data.get("MasterID")
        text = data.get("text")
        if not master_id or not text:
            logger.error("invalid message format, rejecting")
            await message.reject()
            return

        loop = asyncio.get_event_loop()
        try:
            result_data = await asyncio.wait_for(
                loop.run_in_executor(None, processor.analyze_text, master_id, text),
                timeout=100.0,
            )
        except asyncio.TimeoutError:
            logger.error(f"text processing timeout for master_id={master_id}")
            await message.reject()
            return

        await processor.publish_results_to_queue(result_data)
        await message.ack()

    except Exception as e:
        logger.error(f"error in handle_message: {e}")
        await message.reject()
