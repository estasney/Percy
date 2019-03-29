from cytoolz import sliding_window
from abc import ABC, abstractmethod
import glob
import random
from functools import partial
import string
import types
from pampy import match, _, HEAD, TAIL
from collections import namedtuple
from cytoolz import groupby
import re
Pattern = namedtuple('Pattern', 'pattern action default')


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



class PatternMatch(ABC):

    def __init__(self):
        self.patterns_ = None

    def __getitem__(self, item):
        """
        Passed an iterable detect patterns

        l = ["After", "today", "I", "'m", "beat"]
        PatternMatch[l] = ["After", "today", "I'm", "beat"]

        """
        if isinstance(item, str):
            return item
        return self.patternize(item)

    @staticmethod
    def pattern_factory(pattern, casing_required):
        """
        Convenience method for quickly generating functions that evaluate against a pattern and return a bool

        :param pattern: iterable that will be evaluated
        :param casing_required: if False, text should be lowercased
        :return:
        """

        pc_functions = []

        def f1(*args, **kwargs):
            pc = kwargs.pop('pattern_component')
            x = args[0]
            return x == pc

        def f2(*args, **kwargs):
            pc = kwargs.pop('pattern_component')
            x = args[0]
            return x in pc

        def f3(*args, **kwargs):
            pc = kwargs.pop('pattern_component')
            x = args[0]
            method = getattr(x, pc, False)
            if not method:
                return False
            x = pc(x)
            return x

        def f4(*args, **kwargs):
            pc = kwargs.pop('pattern_component')
            x = args[0]
            return isinstance(x, pc)

        def f5(*args, **kwargs):
            pc = kwargs.pop('pattern_component')
            x = args[0]
            return any([x in pc, type(x) in pc])

        for pattern_component in pattern:
            if isinstance(pattern_component, str):
                fp = partial(f1, pattern_component=pattern_component)
                pc_functions.append(fp)
            elif isinstance(pattern_component, set):

                # test for membership by value
                fp = partial(f2, pattern_component=pattern_component)
                pc_functions.append(fp)

                # test for membership by value or type
                fp = partial(f5, pattern_component=pattern_component)
                pc_functions.append(fp)

            elif isinstance(pattern_component, types.BuiltinFunctionType):
                fp = partial(f3, pattern_component=pattern_component)
                pc_functions.append(fp)
            elif isinstance(pattern_component, types.FunctionType):
                pc_functions.append(pattern_component)
            elif isinstance(pattern_component, type):
                fp = partial(f4, pattern_component=pattern_component)
                pc_functions.append(fp)

        def pattern_(text_window, pc_functions=pc_functions):
            if len(text_window) < len(pc_functions):
                return False

            if not casing_required:
                text_window = [token.lower() for token in text_window]

            if all([f(token) for f, token in zip(pc_functions, text_window)]):
                return True
            else:
                return False

        return pattern_

    @property
    @abstractmethod
    def patterns(self):
        raise NotImplementedError

    @abstractmethod
    def pattern_action(self, *args, **kwargs):

        """
        Function accepts an iterable and matched_indices. Modifies the iterable and returns it

        def join_conjuction(l, match_start, match_end):

            target = l[match_start : match_end]
            transformed_target = "".join(target)
            del l[match_start : match_end]
            l.insert(match_start, transformed_target)
            return l

        """
        raise NotImplementedError

    def apply_pattern(self, l, matched_indices):

        """

        Continues passing iterable and matched_index to self.pattern_action until matched_indices is exhausted

        :param l: Iterable
        :param matched_indices: Tuples of form match_start, match_end
        :return: modified iterable
        """

        for match_start, matched_end in matched_indices:
            l = self.pattern_action(l, match_start, matched_end)

        return l

    def patternize(self, sentence):
        for pattern_group in self.patterns:
            f = pattern_group['f']
            window_size = len(pattern_group['pattern'])
            if window_size > len(sentence):
                continue

            matched_indices = []
            for window_i, window in enumerate(sliding_window(window_size, sentence)):
                if f(window):
                    match_start = window_i
                    match_end = match_start + window_size
                    matched_indices.append((match_start, match_end))

                # the pattern matches! The match_start is given by window_i, match_end = match_start + window_size

            if matched_indices:
                sentence = self.apply_pattern(sentence, matched_indices)
            else:
                continue

        return sentence


class UnTokenizePattern(PatternMatch):

    letters = set(string.ascii_letters)
    alpha_test = partial(lambda x: getattr(x, 'isalpha', False)())
    numeric_test = partial(lambda x: getattr(x, 'isnumeric', False)())
    s1 = {"i", "it", "we", "were"}
    s2 = {"'ve", "n't", "'s", "'m", "'re"}

    def __init__(self):
        super().__init__()

    def rejoin_logic(self, target):
        return "".join(target)

    @property
    def patterns(self):

        if self.patterns_:
            return self.patterns_

        p = [
            {'pattern': ["c", "++"], 'casing_required': False},
            {'pattern': ["c", "+", "+"], 'casing_required': False},
            {'pattern': ["at", "&", "t"], 'casing_required': False},
            {'pattern': [self.letters, "&", self.letters], 'casing_required': False},
            {'pattern': [lambda x: x.isalpha() and x not in {'it', 'he', 'she'},
                         "'s"], 'casing_required': False},
            {'pattern': [self.s1, self.s2], 'casing_required': False},
            {'pattern': [self.numeric_test, "%"], 'casing_required': False}
            ]

        fp = [{'f': self.pattern_factory(x['pattern'], x['casing_required']),
              'pattern': x['pattern'], 'casing_required': x['casing_required']} for x in p]

        self.patterns_ = fp
        return fp

    def pattern_action(self, l, match_start, match_end):

        target = l[match_start: match_end]
        transformed_target = self.rejoin_logic(target)
        del l[match_start: match_end]
        l.insert(match_start, transformed_target)
        return l

    def apply_pattern(self, l, matched_indices):
        for match_start, matched_end in matched_indices:
            l = self.pattern_action(l, match_start, matched_end)

        return l


class BulletedPattern(object):

    def __init__(self):
        pass

    def __getitem__(self, item):
        return self.patternize(item)


    @property
    def bullets(self):
        return {"•", "●", "·", "•", "◦", "∙", "o", "*", "◊", "·"}

    def patternize(self, sentence):

        bullet_matches = [i for i, token in enumerate(sentence) if token in self.bullets]
        if not bullet_matches:
            return [sentence]  # Expect chain.from_iterable

        split_sentences = []

        bullet_matches.insert(0, -1)  # To capture tokens prior to first bullet point
        for b1, b2 in sliding_window(2, bullet_matches):
            sentence_fragment = sentence[(b1 + 1): b2]
            split_sentences.append(sentence_fragment)

        return split_sentences





# TODO Pattern to Sent Tokenize on Bullet Points





# import json
# import copy
#
# def get_random_file():
#     folder = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/sent/*.json"
#     files = glob.glob(folder)
#     f = random.choice(files)
#     with open(f, "r") as j:
#         doc = json.load(j)
#
#     return doc['token_summary']
#
# c = PercentagePattern()
# looking = True
# while looking:
#     for line in get_random_file():
#         x = copy.copy(line)
#         a = c[x]
#         b = line
#         if a != b:
#             print(" ".join(a))
#             print(" ".join(b))
#             looking = False
#

