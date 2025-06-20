from collections import Counter
import re
import pymorphy3

from abc import ABC, abstractmethod
from collections import defaultdict
from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer


class TargetWordAnalyzer(ABC):
    """абстрактный класс для анализа target_words"""

    @abstractmethod
    def analyze(self, tokens, target_words, result_key):
        pass


class MostFrequentTargetWordAnalyzer(TargetWordAnalyzer):
    """поиск по самым часто встречающимся словам в тексте"""

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
            most_common_category, total_frequency = category_counter.most_common(1)[0]

            for category, phrases_counter in word_counter.items():
                if category_counter[category] > 0:
                    details = ", ".join(
                        [
                            f"{phrase}: {count} times"
                            for phrase, count in phrases_counter.items()
                            if count > 0
                        ]
                    )
                    logger.info(
                        f'category "{category}": {category_counter[category]} times, including: "{details}"'
                    )

            logger.info(f'selected category: "{most_common_category}"')
            return most_common_category
        else:
            logger.info(f"no matches found in {result_key}")
            return None


class LastMentionedTargetWordAnalyzer(TargetWordAnalyzer):
    """находит последнее упоминаемое слово среди target_words"""

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
                                f'found word in {result_key}: "{part}" (matches "{key}")'
                            )
                            last_mentioned = key
                            last_match = part

        if last_mentioned:
            logger.info(
                f'last mentioned word in {result_key}: "{last_mentioned}" (last match: "{last_match}")'
            )
            return last_mentioned
        else:
            logger.info(f"no matches found in {result_key}")
            return None


class AdvertSourceTargetWordAnalyzer(TargetWordAnalyzer):
    """
    находит источник информации откуда узнали о клинике, подставляет ответ
    абонента сразу после вопроса оператора
    """

    def __init__(self, compare_function, target_words_answer_tags):
        self.compare_function = compare_function
        self.answer_matcher = AnswerMatcher(target_words_answer_tags)

    def analyze(self, text, target_words, result_key):
        answer = None

        for phrase in target_words:
            if phrase in text:
                phrase_start_index = text.find(phrase)
                abonent_start_index = text.find("\nабонент:", phrase_start_index)
                if abonent_start_index != -1:
                    abonent_start_index += len("\nабонент:")

                    answer = text[abonent_start_index:].split("\nоператор:")[0].strip()
                    break

        matched_key = self.answer_matcher.match_answer(answer)
        return matched_key


class AnswerMatcher:
    def __init__(self, target_words_answer_tags):
        self.target_words_answer_tags = target_words_answer_tags

    def match_answer(self, answer):
        """
        сопоставляет ответ абонента с ключами из target_words_answer_tags.
        возвращает соответствующий ключ или 'неизвестно', если совпадений нет.
        """
        if not answer:
            logger.info("no answer")
            return "ответ отсутствует"
        for key, phrases in self.target_words_answer_tags.items():
            for phrase in phrases:
                logger.info(f"{phrase} -> {key}")
                if phrase.lower() in answer:
                    return key

        logger.info("No matches found, we are returning an unprocessed answer")
        return answer


class LastTargetPhraseAnalyzer(TargetWordAnalyzer):
    def __init__(self, compare_function):
        self.compare_function = compare_function
        self.morph = pymorphy3.MorphAnalyzer()

    def lemmatize_phrase(self, phrase):
        """лемматизация фразы"""
        tokens = phrase.split()
        lemmatized_tokens = [self.morph.parse(token)[0].normal_form for token in tokens]
        return " ".join(lemmatized_tokens)

    def find_last_match_in_text(self, tokens, target_phrases):
        """ищем последнюю найденную фразу в тексте"""
        text = " ".join(tokens)
        logger.info(f'lemmatized text: "{text}"')

        last_match = None
        last_position = -1

        for category, phrases in target_phrases.items():
            for phrase in phrases:
                lemmatized_phrase = self.lemmatize_phrase(phrase)
                pattern = r"\b" + re.escape(lemmatized_phrase)

                if category == "не отвечает" and self.is_last_phrase(
                    text, lemmatized_phrase
                ):
                    logger.info(
                        f'found match at end: "{lemmatized_phrase}" in category "{category}"'
                    )
                    return category

                match = re.search(pattern + r"\b", text)
                if match:
                    match_position = match.start()
                    if match_position > last_position:
                        last_position = match_position
                        last_match = category
                        logger.info(
                            f'found match: "{lemmatized_phrase}" in category "{category}" at position {match_position}'
                        )

        return last_match

    def is_last_phrase(self, text, phrase):
        """
        проверяет, является ли фраза последней в тексте,
        даже если она не полная
        """
        match = re.search(re.escape(phrase), text)
        if match:
            end_index = match.end()
            remaining_text = text[end_index:].strip()

            # если после фразы нет осмысленных слов, считаем разговор законченным
            if not remaining_text or remaining_text.isspace():
                return True

            # проверяем, является ли конец текста частью фразы
            if text.endswith(phrase[: len(text) - end_index].strip()):
                return True

        return False

    def analyze(self, tokens, target_words, result_key):
        """анализируем текст, выбирая последнее совпадение"""
        selected_category = self.find_last_match_in_text(tokens, target_words)

        if selected_category:
            logger.info(f'selected category: "{selected_category}"')
            return selected_category
        else:
            logger.info(f"no matches in {result_key}")
            return None


class MostValuableWordAnalyzer(TargetWordAnalyzer):
    def __init__(self, compare_function):
        self.compare_function = compare_function

    def analyze(self, tokens, target_words, result_key):
        target_phrases = []
        for category, phrases in target_words.items():
            for phrase in phrases:
                target_phrases.append(phrase)

        text = " ".join(tokens)

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()

        phrase_tfidf = {}
        for i, phrase in enumerate(target_phrases):
            if phrase in feature_names:
                idx = feature_names.tolist().index(phrase)
                tfidf_value = tfidf_matrix[0, idx]
                phrase_tfidf[phrase] = tfidf_value

        category_counter = Counter()
        word_counter = defaultdict(lambda: Counter())

        additional_weights = {
            "Катаракта": 1.6,
            "ЛКЗ": 1.5,
            "Диагностика": 0.4,
            "Косоглазие": 1.3,
            "Блефаропластика": 1.3,
            "Глаукома": 1.3,
            "ИВВ": 1.3,
            "Сетчатка": 1.3,
            "Полостные операции": 1.3,
            "ОК-линзы": 1.3,
            "Аппаратное лечение": 1.3,
            "Подбор очков / линз": 1.3,
            "Осмотр": 1.3,
            "ОМС": 1.3,
            "Предоперационная подготовка": 1.3,
        }

        for token in tokens:
            for category, phrases in target_words.items():
                for phrase in phrases:
                    if self.compare_function(token, phrase):
                        category_weight = phrase_tfidf.get(
                            phrase, 0
                        ) * additional_weights.get(category, 1)
                        category_counter[category] += category_weight
                        word_counter[category][phrase] += category_weight

        if category_counter:
            most_common_categories = category_counter.most_common(2)

            for category, phrases_counter in word_counter.items():
                if category_counter[category] > 0:
                    details = ", ".join(
                        [
                            f"{phrase}: {count} times"
                            for phrase, count in phrases_counter.items()
                            if count > 0
                        ]
                    )
                    logger.info(
                        f'category "{category}": {category_counter[category]} times, including: "{details}"'
                    )

            if len(most_common_categories) == 1:
                most_common_category = most_common_categories[0][0]
                logger.info(f'selected category: "{most_common_category}"')
                return most_common_category
            else:
                selected_categories = ", ".join(
                    [cat for cat, _ in most_common_categories]
                )
                logger.info(f"selected categories: {selected_categories}")
                return selected_categories
            # if most_common_category == "Диагностика" and total_weight < max(category_counter.values()):
            #     most_common_category = [
            #         cat for cat, _ in category_counter.most_common() if cat != "Диагностика"][0]

            # logger.info(f'final selected category: "{most_common_category}"')
            # return most_common_category
        else:
            logger.info(f"no matches found in {result_key}")
            return None


class MostFrequentTargetPhraseAnalyzer(TargetWordAnalyzer):
    def __init__(self, compare_function):
        self.compare_function = compare_function
        self.morph = pymorphy3.MorphAnalyzer()

    def lemmatize_phrase(self, phrase):
        """лемматизация фразы"""
        tokens = phrase.split()
        lemmatized_tokens = [self.morph.parse(token)[0].normal_form for token in tokens]
        return " ".join(lemmatized_tokens)

    def count_matches_in_text(self, tokens, target_phrases):
        """подсчет количества совпадений для каждой категории"""
        text = " ".join(tokens)
        logger.info(f'lemmatized text: "{text}"')

        category_counts = {}

        for category, phrases in target_phrases.items():
            category_counts[category] = 0

            for phrase in phrases:
                lemmatized_phrase = self.lemmatize_phrase(phrase)
                pattern = r"\b" + re.escape(lemmatized_phrase) + r"\b"
                matches = re.findall(pattern, text)

                if matches:
                    category_counts[category] += len(matches)
                    logger.info(
                        f'found {len(matches)} matches for phrase "{lemmatized_phrase}" in category "{category}"'
                    )

        return category_counts

    def analyze(self, tokens, target_words, result_key):
        """анализируем текст, выбирая категорию с наибольшим количеством совпадений"""
        category_counts = self.count_matches_in_text(tokens, target_words)

        if not category_counts:
            logger.info(f"no matches in {result_key}")
            return None

        max_count = max(category_counts.values())
        max_categories = [
            category
            for category, count in category_counts.items()
            if count == max_count
        ]

        if len(max_categories) > 1:
            selected_category = max_categories[-1]
        else:
            selected_category = max_categories[0]
        # selected_category = max(category_counts, key=category_counts.get)
        # max_count = category_counts[selected_category]

        if max_count > 0:
            logger.info(
                f'selected category: "{selected_category}" with {max_count} matches'
            )
            return selected_category
        else:
            logger.info(f"no matches in {result_key}")
            return None
