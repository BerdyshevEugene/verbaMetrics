from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from loguru import logger


class TargetWordAnalyzer(ABC):
    '''абстрактный класс для анализа target_words'''
    @abstractmethod
    def analyze(self, tokens, target_words, result_key):
        pass


class MostFrequentTargetWordAnalyzer(TargetWordAnalyzer):
    def __init__(self, compare_function):
        self.compare_function = compare_function

    def analyze(self, tokens, target_words, result_key):
        category_counter = Counter()
        word_counter = defaultdict(lambda: Counter())

        for token in tokens:
            for category, phrases in target_words.items():
                for phrase in phrases:
                    if self.compare_function(token, phrase):
                        category_counter[category] += 1
                        word_counter[category][phrase] += 1

        if category_counter:
            most_common_category, total_frequency = category_counter.most_common(1)[
                0]

            for category, phrases_counter in word_counter.items():
                if category_counter[category] > 0:
                    details = ', '.join(
                        [f'{phrase}: {count} times' for phrase,
                            count in phrases_counter.items() if count > 0]
                    )
                    logger.info(
                        f'category "{category}": {category_counter[category]} times, including: "{details}"'
                    )

            logger.info(f'selected category: "{most_common_category}"')
            return most_common_category
        else:
            logger.info(f'no matches found in {result_key}')
            return None


class LastMentionedTargetWordAnalyzer(TargetWordAnalyzer):
    '''находит последнее упоминаемое слово среди target_words'''

    def __init__(self, compare_function):
        self.compare_function = compare_function

    def analyze(self, tokens, target_words, result_key):
        last_mentioned = None
        last_match = None

        for token in tokens:
            for key, phrases in target_words.items():
                for phrase in phrases:
                    for part in phrase.split():
                        if self.compare_function(token, part):
                            logger.info(
                                f'found word in {result_key}: "{part}" (matches "{key}")')
                            last_mentioned = key
                            last_match = part

        if last_mentioned:
            logger.info(
                f'last mentioned word in {result_key}: "{last_mentioned}" (last match: "{last_match}")'
            )
            return last_mentioned
        else:
            logger.info(f'no matches found in {result_key}')
            return None


class AdvertSourceTargetWordAnalyzer(TargetWordAnalyzer):
    '''находит источник информации откуда узнали о клинике'''

    def __init__(self, compare_function):
        self.compare_function = compare_function

    def analyze(self, text, target_words, result_key):
        answer = None

        for phrase in target_words:
            if phrase in text:
                phrase_start_index = text.find(phrase)
                abonent_start_index = text.find(
                    '\nабонент:', phrase_start_index)
                if abonent_start_index != -1:
                    abonent_start_index += len('\nабонент:')

                    answer = text[abonent_start_index:].split('\nоператор:')[
                        0].strip()
                    break

        return answer
