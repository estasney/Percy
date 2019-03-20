from cytoolz import sliding_window
from abc import ABC, abstractmethod
import glob
import random

class PatternMatch(ABC):

    def __init__(self):
        pass

    def __getitem__(self, item):
        """
        Passed an iterable detect patterns

        l = ["After", "today", "I", "'m", "beat"]
        PatternMatch[l] = ["After", "today", "I'm", "beat"]

        """
        if isinstance(item, str):
            return item
        return self.patternize(item)

    @property
    @abstractmethod
    def patterns(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def pattern_action(self):

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

    def patternize(self, l):

        """
        Scan the iterable for any pattern matches, noting their indexes

        ['As', 'a', 'founder', 'I', "'ve", 'done', 'everything', 'from', 'running', 'product', 'teams', 'to', 'getting', 'on', 'a', 'plane', 'and', 'closing', 'deals', '.']

        """
        window_size = len(self.patterns)
        if window_size > len(l):
            return l
        matched_indices = []

        for window_i, window in enumerate(sliding_window(window_size, l)):
            if all([pattern(window) for pattern in self.patterns]):

                # the pattern matches! The match_start is given by window_i, match_end = match_start + window_size
                match_start = window_i
                match_end = match_start + window_size
                matched_indices.append((match_start, match_end))

        if matched_indices:
            output = self.apply_pattern(l, matched_indices)
        else:
            output = l

        return output


class RejoinPattern(PatternMatch):

    @abstractmethod
    def rejoin_logic(self, target):
        raise NotImplementedError

    @property
    @abstractmethod
    def patterns(self):
        raise NotImplementedError

    @property
    def pattern_action(self):

        def rejoin(l, match_start, match_end):

            target = l[match_start: match_end]
            transformed_target = self.rejoin_logic(target)
            del l[match_start: match_end]
            l.insert(match_start, transformed_target)
            return l

        return rejoin

class PossessivePattern(PatternMatch):

    @property
    def patterns(self):
        f1 = lambda window: window[0].isalpha() and window[0] not in {'it', 'he', 'she'}
        f2 = lambda window: window[1] == "'s"
        return [f1, f2]

    @property
    def pattern_action(self):

        def drop_possesive(l, match_start, match_end):

            if not l:
                return l

            target = l[match_start: match_end]

            if not target:
                return l

            transformed_target = target[0]

            del l[match_start:match_end]

            l.insert(match_start, transformed_target)
            return l

        return drop_possesive


class ContractionPattern(RejoinPattern):


    def rejoin_logic(self, target):
        return "".join(target)

    @property
    def patterns(self):
        f1 = lambda window: window[0].lower() in {"i", "it", "we", "were"}
        f2 = lambda window: window[1].lower() in {"'ve", "n't", "'s", "'m", "'re"}
        return [f1, f2]


class PercentagePattern(RejoinPattern):

    def rejoin_logic(self, target):
        target = "_".join(target)
        target = target.replace("%", "percent")
        return target

    @property
    def patterns(self):
        f1 = lambda window: window[0].isnumeric()
        f2 = lambda window: window[1] == "%"
        return [f1, f2]

class UnTokenizePattern(object):

    def __init__(self):
        pass

    def __getitem__(self, item):
        return self.patternize(item)

    def rejoin_logic(self, target):
        return "".join(target)

    @property
    def patterns(self):
        p = [
            {'pattern': ["c", "++"], 'casing_required': False},
            {'pattern': ["c", "+", "+"], 'casing_required': False},
            {'pattern': ["at", "&", "t"], 'casing_required': False},
            {'pattern': ["p", "&", "l"], 'casing_required': False},
            {'pattern': ["r", "&", "d"], 'casing_required': False}
            ]
        return p

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


    def patternize(self, sentence):
        for pattern_group in self.patterns:
            pattern, no_lower = pattern_group['pattern'], pattern_group['casing_required']
            window_size = len(pattern)
            if window_size > len(sentence):
                continue

            matched_indices = []
            for window_i, window in enumerate(sliding_window(window_size, sentence)):

                if no_lower is False:
                    window = [word.lower() for word in window]
                if window == pattern:
                    match_start = window_i
                    match_end = match_start + window_size
                    matched_indices.append((match_start, match_end))

                # the pattern matches! The match_start is given by window_i, match_end = match_start + window_size

            if matched_indices:
                sentence = self.apply_pattern(sentence, matched_indices)
            else:
                continue

        return sentence





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

