import asyncio
import difflib
import json
import pymorphy3

from natasha import Doc, Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger
from collections import Counter
from loguru import logger

from .dict import stop_words, target_words, target_words_2


class TextProcessor:
    def __init__(self, target_words=None, stop_words=None):
        self.segmenter = Segmenter()
        self.emb = NewsEmbedding()
        self.morph_tagger = NewsMorphTagger(self.emb)
        self.morph_vocab = MorphVocab()

        self.morph = pymorphy3.MorphAnalyzer()
        self.target_words = target_words or []
        self.stop_words = stop_words or set()

    def compare_words(self, word1, word2, threshold=0.99):
        return difflib.SequenceMatcher(None, word1, word2).ratio() >= threshold

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

    def count_target_words(self, tokens, target_words):
        counter = Counter()
        for token in tokens:
            for target in target_words:
                if token == target or self.compare_words(token, target):
                    counter[target] += 1
        return counter

    def analyze_text(self, master_id, text):
        root_tokens, lemmatized_tokens = self.process_text(text)

        result_data = {}

        for idx, target_words in enumerate(self.target_words, start=1):
            root_count = self.count_target_words(root_tokens, target_words)

            if root_count:
                most_common_root, _ = root_count.most_common(1)[0]
                result_data[f'target_words_{idx}'] = most_common_root
                logger.info(
                    f'[{idx}] the most common root from the dictionary: "{most_common_root}"'
                )
            else:
                result_data[f'target_words_{idx}'] = None
                logger.info(f'[{idx}] no matches were found in the dictionary')

        logger.info(f'result data: {result_data}')

        return {
            'ChannelName': 'IncomingCall',
            'Event': 'verbaMetrics',
            'MasterID': master_id,
            **result_data
        }

    @staticmethod
    async def publish_results_to_queue(data):
        logger.info(f'publishing results to queue: {data}')
        pass

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
                target_words=[target_words, target_words_2], stop_words=stop_words)
            result_data = processor.analyze_text(master_id, text)

            await TextProcessor.publish_results_to_queue(result_data)
            await message.ack()

        except Exception as e:
            logger.error(f'error in handle_message: {e}')
            await message.reject()
