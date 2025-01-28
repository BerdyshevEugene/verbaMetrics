import asyncio
import json
import pymorphy3
import re

from collections import Counter
from loguru import logger

from natasha import Doc, Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger
from rabbitmq.publisher import publish_results_verbametrics_dg_queue
from .dict import stop_words, target_words, target_words_2


class TextProcessor:
    def __init__(self, target_words=None, target_words_2=None, stop_words=None):
        self.segmenter = Segmenter()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.morph_vocab = MorphVocab()
        self.morph = pymorphy3.MorphAnalyzer()
        self.target_words = target_words or {}
        self.target_words_2 = target_words_2 or {}
        self.stop_words = stop_words or set()

    def compare_words(self, word1, word2, threshold=0.8):
        return re.fullmatch(r'\b' + re.escape(word2) + r'\b', word1) is not None

    def process_text(self, text):
        text = text.lower()
        doc = Doc(text)
        doc.segment(self.segmenter)
        doc.tag_morph(self.morph_tagger)

        lemmatized_tokens = []
        root_tokens = []

        for token in doc.tokens:
            token.lemmatize(self.morph_vocab)
            if token.lemma in self.stop_words:
                continue
            lemmatized_tokens.append((token.text, token.lemma, token.pos))
            root_tokens.append(token.lemma)

        return root_tokens, lemmatized_tokens

    def count_target_words_with_logging(self, tokens, target_words):
        counter = Counter()
        for token in tokens:
            for key, phrases in target_words.items():
                for phrase in phrases:
                    if self.compare_words(token, phrase):
                        counter[key] += 1
                        logger.info(
                            f'match found: "{key}", found in dictionary: {token}')
        return counter

    def analyze_target_words(self, tokens, target_words, result_key):
        counter = self.count_target_words_with_logging(tokens, target_words)
        if counter:
            most_common_word, frequency = counter.most_common(1)[0]
            logger.info(
                f'most frequent word in {result_key}: "{most_common_word}" with frequency {frequency}')
            return most_common_word
        else:
            logger.info(f'no matches found in {result_key}')
            return None

    def analyze_text(self, master_id, text):
        root_tokens, _ = self.process_text(text)

        result_data = {
            'target_words_1': self.analyze_target_words(root_tokens, self.target_words, 'target_words_1'),
            'target_words_2': self.analyze_target_words(root_tokens, self.target_words_2, 'target_words_2')
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
        await publish_results_verbametrics_dg_queue(data)
        logger.info(f'publishing results to queue: {data}')

    @staticmethod
    async def handle_message(message):
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
                target_words=target_words, target_words_2=target_words_2, stop_words=stop_words)
            result_data = processor.analyze_text(master_id, text)

            await TextProcessor.publish_results_to_queue(result_data)
            await message.ack()

        except Exception as e:
            logger.error(f'error in handle_message: {e}')
            await message.reject()
