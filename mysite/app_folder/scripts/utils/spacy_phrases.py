from pampy import match, _, HEAD, TAIL
from collections import namedtuple
from gensim.models.phrases import Phraser, Phrases
import re

Pattern = namedtuple('Pattern', 'pattern action default')

PHRASE_PATH = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/phrases/phrases.model"


def make_pattern(pattern, action=False, default=True):
    return Pattern(pattern, action, default)


f1 = make_pattern(["I", _])  # anything starting with i
f2 = make_pattern(["--", _])  # --_--

# 10_years, 3+_years
f3 = make_pattern([re.compile(r"([0-9]{1,2}\+?)"),
                   re.compile(r"(years?)")])

# 15_percent 15+_percent, 55_%
f4 = make_pattern([re.compile(r"([0-9]{1,}\+?)"),
                   re.compile(r"(%)|(percent)")])


phrase_patterns = [f1, f2, f3, f4]


def make_pattern(pattern, action=False, default=True):
    return Pattern(pattern, action, default)


def filter_phrases(phrase_line, patterns=phrase_patterns):
    temp_phrase = phrase_line[0].split("_")
    for pattern in patterns:
        keep_it = match(temp_phrase, pattern.pattern, pattern.action, default=pattern.default)
        if not keep_it:
            return False
    return True


class PhraseFilter(object):

    def __init__(self, patterns=phrase_patterns, phrase_delim="_"):
        self.patterns = patterns
        self.phrase_delim = phrase_delim

    def __contains__(self, item):
        temp_phrase = item.split(self.phrase_delim)
        for pattern in self.patterns:
            keep_it = match(temp_phrase, pattern.pattern, pattern.action, default=pattern.default)
            if not keep_it:
                return True
        return False


class MyPhraser(Phraser):

    def __init__(self, phrase_filter=PhraseFilter(), phrase_path=PHRASE_PATH, iter=2):
        phrase_model = Phrases.load(phrase_path)
        self.phrase_filter = phrase_filter
        self.iter = iter
        super().__init__(phrase_model)

    def phrase_once(self, item):
        transformed = super().__getitem__(item)
        filtered_transformed = []
        for token in transformed:
            if "_" not in token:
                filtered_transformed.append(token)
                continue
            else:
                if token in self.phrase_filter:
                    tokens = token.split("_")
                    filtered_transformed.extend(tokens)
                else:
                    filtered_transformed.append(token)

        return filtered_transformed

    def __getitem__(self, item):
        for i in range(self.iter):
            item = self.phrase_once(item)
        return item
