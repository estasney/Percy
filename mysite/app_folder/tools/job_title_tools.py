import json
import re

from flashtext.keyword import KeywordProcessor

from app_folder.site_config import FConfig

config = FConfig()


class JobTitlePreprocessor(object):

    def __init__(self):
        self.trailing_seniority = re.compile(r"(?<=[A-z ])([0-9]$)")
        self.sub_trailing_seniority = lambda x: self.trailing_seniority.sub("", x)
        self.flatten = lambda x: [item for sublist in x for item in sublist]
        self.is_truthy = lambda x: True if x else False
        self.filter_is_truthy = lambda i: list(filter(self.is_truthy, i))
        self.strip_tokens = lambda tokens: [t.strip() for t in tokens]
        self.lower_tokens = lambda tokens: [t.lower() for t in tokens]
        self.romanize = lambda tokens: [int_to_roman(t) for t in tokens]
        self.join_tokens = lambda tokens: " ".join(tokens)

        self.kp = self.make_kp(config.JOB_TITLE_SYNONYMS_FP)
        self.kp1 = self.make_kp(config.JOB_TITLE_SYNONYMS2_FP)

        self.steps = [self.sub_trailing_seniority, self.kp_replace, self.kp1_replace, wordpunct]

    def make_kp(self, fp):
        with open(fp, "r", encoding="utf-8") as f:
            kws = json.load(f)
        kp = KeywordProcessor()
        for kw in kws:
            kp.add_keywords_from_dict(kw)
        return kp

    def kp_replace(x: str, kp=kp):
        return kp.replace_keywords(x)

    def kp1_replace(x: str, kp1=kp1):
        return kp1.replace_keywords(x)

    def remove_stopwords(x: list, stopwords=stops):
        return [token for token in x if token not in stopwords]


def int_to_roman(x):
    """
    Normalizing titles like software engineer 3

    Also filters out numbers that are not likely part of a seniority description, i.e. 2000
    """

    if not x.isnumeric():
        return x
    x = int(x)
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I')
    result = []
    for i in range(len(ints)):
        count = int(x / ints[i])
        result.append(nums[i] * count)
        x -= ints[i] * count
    result = ''.join(result).lower()
    if any([n in result for n in ['m', 'c', 'd', 'x', 'l']]):
        return ""
    return ''.join(result).lower()


def preprocess_title(x: str, steps):
    if pd.isna(x) or x == "":
        return []
    tokens = x
    for step in steps:
        if not tokens:
            return []
        tokens = step(tokens)
    return tokens
