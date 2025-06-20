import json
import pymorphy3

from loguru import logger
from natasha import Doc, Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger

from rabbitmq.publisher import publish_results_verbametrics_dg_queue
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
from .target_word_analyzer import (
    LastMentionedTargetWordAnalyzer,
    AdvertSourceTargetWordAnalyzer,
    MostFrequentTargetPhraseAnalyzer,
    MostValuableWordAnalyzer,
)


class TextProcessor:
    def __init__(
        self,
        target_words_1=None,
        target_words_2=None,
        target_words_3=None,
        target_words_4=None,
        target_words_5=None,
        target_words_6=None,
        stop_words=None,
        target_words_answer_tags=None,
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
        self.target_words_5 = target_words_5 or {}
        self.target_words_6 = target_words_6 or {}
        self.stop_words = stop_words or set()
        self.target_words_answer_tags = target_words_answer_tags

        self.analyzers = {
            "target_words_1": MostValuableWordAnalyzer(self.compare_words),
            "target_words_2": MostFrequentTargetPhraseAnalyzer(self.compare_words),
            "target_words_3": LastMentionedTargetWordAnalyzer(self.compare_words),
            "target_words_4": AdvertSourceTargetWordAnalyzer(
                self.compare_words, self.target_words_answer_tags
            ),
            "target_words_5": MostFrequentTargetPhraseAnalyzer(self.compare_words),
            "target_words_6": MostFrequentTargetPhraseAnalyzer(self.compare_words),
        }

    def compare_words(self, word1, word2):
        lemma1 = self.morph.parse(word1)[0].normal_form
        lemma2 = self.morph.parse(word2)[0].normal_form
        return lemma1 == lemma2

    def process_text(self, text):
        """лемматизация текста"""
        logger.info("processing text...")
        text = text.lower()
        logger.debug(f"original text: {text[:200]}...")

        doc = Doc(text)
        logger.info("segmenting...")
        doc.segment(self.segmenter)

        logger.info("tagging morphology...")
        doc.tag_morph(self.morph_tagger)

        root_tokens = []

        for i, token in enumerate(doc.tokens):
            try:
                token.lemmatize(self.morph_vocab)
                if token.lemma in self.stop_words:
                    continue
                root_tokens.append(token.lemma)
            except Exception as e:
                logger.error(f"lemmatization failed for token {i}: {e}")
                continue

        logger.info(f"total root tokens: {len(root_tokens)}")
        return root_tokens

    def analyze_text(self, master_id, text):
        """функция анализа текста"""
        logger.info(f"analyzing text for master_id: {master_id}")
        root_tokens = self.process_text(text)

        result_data = {}

        try:
            logger.info("analyzing target_words_5...")
            target_words_5_result = self.analyzers["target_words_5"].analyze(
                root_tokens, self.target_words_5, "target_words_5"
            )
            result_data["target_words_5"] = target_words_5_result
        except Exception as e:
            logger.error(f"error analyzing target_words_5: {e}")
            result_data["target_words_5"] = None
            target_words_5_result = None

        try:
            if target_words_5_result is None:
                logger.info("target_words_5 not found, analyzing target_words_6...")
                target_words_6_result = self.analyzers["target_words_6"].analyze(
                    root_tokens, self.target_words_6, "target_words_6"
                )
                result_data["target_words_6"] = target_words_6_result
            else:
                result_data["target_words_6"] = None
        except Exception as e:
            logger.error(f"error analyzing target_words_6: {e}")
            result_data["target_words_6"] = None

        for key, analyzer in self.analyzers.items():
            if key not in ["target_words_5", "target_words_6"]:
                try:
                    logger.info(f"analyzing {key}...")
                    source = root_tokens if key != "target_words_4" else text
                    result_data[key] = analyzer.analyze(source, getattr(self, key), key)
                except Exception as e:
                    logger.error(f"error analyzing {key}: {e}")
                    result_data[key] = None

        logger.info(f"result data: {result_data}")
        return {
            "ChannelName": "IncomingCall",
            "Event": "verbaMetrics",
            "MasterID": master_id,
            **result_data,
        }

    @staticmethod
    async def publish_results_to_queue(data):
        """публикация результатов в очередь"""
        logger.info("publishing results to queue...")
        await publish_results_verbametrics_dg_queue(data)
        logger.info(f"published: {data}")

    @staticmethod
    async def handle_message(message):
        """обработка входящих сообщений"""
        try:
            data = json.loads(message.body)
            logger.info(f"received message: {data}")

            master_id = data.get("MasterID")
            text = data.get("text")
            if not master_id or not text:
                logger.error("invalid message format, rejecting")
                await message.reject()
                return

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
            result_data = processor.analyze_text(master_id, text)

            await TextProcessor.publish_results_to_queue(result_data)
            await message.ack()

        except Exception as e:
            logger.error(f"error in handle_message: {e}")
            await message.reject()
