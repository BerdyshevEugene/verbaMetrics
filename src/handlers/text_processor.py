import asyncio
import json
import pymorphy3
import re

from collections import Counter
from loguru import logger
from natasha import Doc, Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger

from rabbitmq.publisher import publish_results_verbametrics_dg_queue
from .dict import (
    stop_words, target_words_1, target_words_2, target_words_3, target_words_4)
from .target_word_analyzer import (
    MostFrequentTargetWordAnalyzer, LastMentionedTargetWordAnalyzer,
    AdvertSourceTargetWordAnalyzer
)


class TextProcessor:
    def __init__(
        self,
        target_words_1=None,
        target_words_2=None,
        target_words_3=None,
        target_words_4=None,
        stop_words=None
    ):
        self.segmenter = Segmenter()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.morph_vocab = MorphVocab()
        self.morph = pymorphy3.MorphAnalyzer()

        self.target_words_1 = target_words_1 or {}
        self.target_words_2 = target_words_2 or {}
        self.target_words_3 = target_words_3 or {}
        self.target_words_4 = target_words_4 or {}
        self.stop_words = stop_words or set()

        self.analyzers = {
            'target_words_1': MostFrequentTargetWordAnalyzer(self.compare_words),
            'target_words_2': MostFrequentTargetWordAnalyzer(self.compare_words),
            'target_words_3': LastMentionedTargetWordAnalyzer(self.compare_words),
            'target_words_4': AdvertSourceTargetWordAnalyzer(self.compare_words),
        }

    def compare_words(self, word1, word2):
        lemma1 = self.morph.parse(word1)[0].normal_form
        lemma2 = self.morph.parse(word2)[0].normal_form
        return lemma1 == lemma2

    def process_text(self, text):
        '''лемматизация текста'''
        text = text.lower()
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)

        # lemmatized_tokens = []
        root_tokens = []

        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
            if token.lemma in self.stop_words:
                continue
            # lemmatized_tokens.append((token.text, token.lemma, token.pos))
            root_tokens.append(token.lemma)

        return root_tokens,  # lemmatized_tokens

    def analyze_text(self, master_id, text):
        '''функция анализа текста'''
        root_tokens = self.process_text(text)[0]

        result_data = {
            key: analyzer.analyze(root_tokens, getattr(self, key), key)
            if key != 'target_words_4'
            else analyzer.analyze(text, getattr(self, key), key)
            for key, analyzer in self.analyzers.items()
        }
        logger.info(f'result data: {result_data}')

        return {
            'ChannelName': 'IncomingCall',
            'Event': 'verbaMetrics',
            'MasterID': master_id,
            **result_data
        }

    @staticmethod
    async def publish_results_to_queue(data):
        '''публикация результатов в очередь'''
        await publish_results_verbametrics_dg_queue(data)
        logger.info(f'publishing results to queue: {data}')

    @staticmethod
    async def handle_message(message):
        '''обработка входящих сообщений'''
        try:
            data = json.loads(message.body)
            logger.info(f'received message: {data}')

            master_id = data.get('MasterID')
            text = data.get('text')
            if not master_id or not text:
                logger.error('invalid message format, rejecting')
                await message.reject()
                return

            processor = TextProcessor(
                target_words_1=target_words_1,
                target_words_2=target_words_2,
                target_words_3=target_words_3,
                target_words_4=target_words_4,
                stop_words=stop_words
            )
            result_data = processor.analyze_text(master_id, text)

            await TextProcessor.publish_results_to_queue(result_data)
            await message.ack()

        except Exception as e:
            logger.error(f'error in handle_message: {e}')
            await message.reject()
