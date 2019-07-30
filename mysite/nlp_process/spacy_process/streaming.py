import glob
import json
import os
import re
import typing
from functools import partial
from itertools import combinations

import toolz
from gensim.utils import strided_windows
from nltk.corpus import stopwords
from pampy import match

from nlp_process import ProcessConfig
from nlp_process.spacy_process.spacy_utils import unpack_doc

ls = typing.TypeVar('ls', list, str, typing.Callable, type(None))

"""

Streaming

"""


def stream_docs(files: typing.Iterable, data_key: ls):
    """

    :param files: Files to load and stream
    :param data_key: If none, stream the entire file.
    If string or list return the values from keys. Also supports a callable function such as tool.dicttoolz.get_in
    :return:
    """

    if data_key:
        if isinstance(data_key, str):
            data_get = lambda x: x[data_key]
        elif isinstance(data_key, list):
            data_get = lambda x: flatten([v for k, v in x.items() if k in data_key])
        else:
            data_get = data_key
    else:
        data_get = lambda x: x

    for f in files:
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        doc_text = data_get(doc)
        yield doc_text


class DataKeyMixin(object):

    def __init__(self, data_key: ls):
        if isinstance(data_key, str):
            data_get = lambda x: x[data_key]

        elif isinstance(data_key, list):
            data_get = lambda x: flatten([v for k, v in x.items() if k in data_key])

        else:
            data_get = data_key

        self.data_get = data_get


class DocStreamer(DataKeyMixin):

    def __init__(self, d, data_key):
        super().__init__(data_key)
        self.dir = d
        self.files = glob.glob(os.path.join(self.dir, "*.json"))

    def load_json_(self, f):
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        return self.data_get(doc)

    def __getitem__(self, i):
        file = self.files[i]
        doc = self.load_json_(file)
        return doc

    def __iter__(self):
        for file in self.files:
            doc = self.load_json_(file)
            for d in doc:
                yield d


def callable_pattern(x, pattern, action_call=None):
    # run pampy match
    if match(x, pattern, True, default=False):
        return action_call(x)
    else:
        return x


starts_with_punc_ = re.compile(r"^(!|\"|#|$|%|&|'|\(|\)|\*|\+|,|-|\.|/|:|;|<|=|>|\?|@|\[|\|\]|\^|_|`|{|}|~)")
remove_leading_punc = lambda x: starts_with_punc_.sub("", x)
starts_with_punc = partial(callable_pattern, pattern=starts_with_punc_, action_call=remove_leading_punc)

has_dates_anywhere_ = re.compile(r"(years?|days?|months?)", flags=re.IGNORECASE)
drop_token = lambda x: ""
has_dates_anywhere = partial(callable_pattern, pattern=has_dates_anywhere_, action_call=drop_token)

starts_with_num_ = re.compile(r"(^[0-9]+)")
starts_with_num = partial(callable_pattern, pattern=starts_with_num_, action_call=drop_token)

is_versioning_ = re.compile(r"([0-9\.]+)")
is_versioning = partial(callable_pattern, pattern=is_versioning_, action_call=drop_token)


class SpacyTokenCleaner(object):
    """
    Class that matches 'bad' tokens and attempts to correct them
    """
    TOKEN_PATTERNS = [starts_with_punc, has_dates_anywhere, starts_with_num, is_versioning]

    def __init__(self, token_key):
        self.token_key = token_key

    def clean_token(self, token):
        token_text = token.get(self.token_key, None)
        if not token_text:
            return ""
        for f in self.TOKEN_PATTERNS:
            token_text = f(token_text)
        return token_text


class SpacyTokenFilter(object):
    DEFAULT_EXCLUDED = ["is_digit", "is_punct", "is_space", "is_currency", "like_url", "like_num", "like_email"]
    STOPWORDS = set(stopwords.words("english"))
    EXTRA_STOPWORDS = ["-PRON-", "-LRB-", "-RRB-", "'s", "7/"]
    CHAR_FILTER = "([^A-z0-9!#%\'()*+,-./:?@\[\]_~])"

    def __init__(self, stopwords=None, excluded_attributes=None, token_key='norm'):
        if stopwords:
            self.stopwords = stopwords
        elif stopwords is None:
            self.stopwords = self.STOPWORDS
            self.stopwords.update(set(self.EXTRA_STOPWORDS))
        else:
            self.stopwords = {}

        if excluded_attributes:
            self.excluded_attributes = excluded_attributes
        elif excluded_attributes is None:
            self.excluded_attributes = self.DEFAULT_EXCLUDED
        else:
            self.excluded_attributes = []

        self.token_key = token_key
        self.char_filter = re.compile(self.CHAR_FILTER)

    def filter_token(self, token: dict):
        token_text = token.get(self.token_key, None)
        if not token_text:
            return False
        if not self.char_filter.sub("", token_text):  # Empty string after removing special chars
            return False
        if token_text in self.stopwords:
            return False
        if any([token.get(attr, False) for attr in self.excluded_attributes]):
            return False
        return True


class SpacyReader(DataKeyMixin):
    """
    :param folder: directory for which to scan for files
    :param data_key
    :param
    """

    def __init__(self, folder, data_key: ls, token_key, token_filter=SpacyTokenFilter, token_cleaner=SpacyTokenCleaner):
        super().__init__(data_key=data_key)
        self.folder = folder
        self.files = glob.glob(os.path.join(self.folder, "*.json"))
        self.token_filter = token_filter(token_key=token_key)
        self.token_cleaner = token_cleaner(token_key=token_key)
        self.token_key = token_key
        self.phraser = None

    def load_json_(self, f):
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        return self.data_get(doc)

    def filter_tokens_(self, doc):
        if self.token_cleaner:
            for token in doc:
                old_text = token.get(self.token_key)
                new_text = self.token_cleaner.clean_token(token)
                if old_text != new_text:
                    token.update({self.token_key: new_text})
        if self.token_filter:
            tokens = list(filter(self.token_filter.filter_token, doc))
        else:
            tokens = doc
        return tokens

    def as_sentences(self):
        for f in self.files:
            doc = self.load_json_(f)
            for sent in doc:
                sent_tokens = self.filter_tokens_(sent)
                sent_tokens = list(filter(lambda x: x, sent_tokens))
                sent_tokens = [t.get(self.token_key, None) for t in sent_tokens]
                sent_tokens = list(filter(lambda x: x is not None, sent_tokens))
                if not sent_tokens:
                    continue
                yield sent_tokens

    def as_documents(self):
        return self.__iter__()

    def as_phrased_sentences(self, phraser):
        if self.phraser:
            setattr(self, 'phraser', None)
        setattr(self, 'phraser', phraser)

        for sent in self.as_sentences():
            yield self.phraser[sent]

    def as_phrased_documents(self, phraser):
        if self.phraser:
            setattr(self, 'phraser', None)
        setattr(self, 'phraser', phraser)

        for f in self.files:
            doc = self.load_json_(f)
            doc_output = []
            for sub_doc in doc:
                for sent in sub_doc:
                    sent_tokens = self.filter_tokens_(sent)
                    sent_tokens = list(filter(lambda x: x, sent_tokens))
                    sent_tokens = [t.get(self.token_key, None) for t in sent_tokens]
                    sent_tokens = list(filter(lambda x: x, sent_tokens))
                    if not sent_tokens:
                        continue
                    sent_tokens = self.phraser[sent_tokens]
                    doc_output.extend(sent_tokens)
                yield doc_output

    def __getitem__(self, item):

        # Get a list of tokens for the entire document

        file = self.files[item]
        doc = self.load_json_(file)
        doc = [self.filter_tokens_(sub_doc) for sub_doc in doc]
        doc = list(filter(lambda x: x, doc))
        doc = [item for sublist in doc for item in sublist]
        doc = [t.get(self.token_key, None) for t in doc]
        doc = list(filter(lambda x: x is not None, doc))
        return doc

    def __iter__(self):
        # Get a list of tokens for the entire document
        for i, _ in enumerate(self.files):
            doc = self.__getitem__(i)
            if doc:
                yield doc


class SpacyBowReader(SpacyReader):

    def __init__(self, **kwargs):
        phraser = kwargs.pop('phraser')
        dictionary = kwargs.pop('dictionary')
        super().__init__(**kwargs)
        self.phraser = phraser
        self.dictionary = dictionary

    def __iter__(self):
        for f in self.files:
            doc = self.load_json_(f)
            tokens = doc[self.text_keys]
            doc_output = []
            for sent in tokens:
                sent_tokens = self.filter_tokens_(sent)
                sent_tokens = [t.get(self.token_key, None) for t in sent_tokens]
                sent_tokens = list(filter(lambda x: x is not None, sent_tokens))
                if not sent_tokens:
                    continue
                sent_tokens = self.phraser[sent_tokens]
                bow_tokens = self.dictionary.doc2bow(sent_tokens)
                doc_output.extend(bow_tokens)
            yield doc_output


def stream_skills(folder):
    files = glob.glob(os.path.join(folder, "*.json"))
    for f in files:
        with open(f, "r") as json_file:
            doc = json.load(json_file)
        skills = doc['skills']
        if skills:
            yield skills


def stream_pairs(docs, dictionary, window_size):
    for doc in docs:
        bow_sent = dictionary.doc2idx(doc)
        bow_sent = [x for x in bow_sent if x > -1]
        if len(bow_sent) < 3:
            continue
        windows = strided_windows(bow_sent, window_size=window_size)
        for w in windows:
            for x, y in map(sorted, combinations(w, 2)):
                yield x, y


def stream_tokens(files):
    for f in files:
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        sentences = doc['clean_summary']
        for sentence in sentences:
            yield sentence


def stream_ngrams(fp, model, layers=1, text_key='token_summary'):
    files = glob.glob(os.path.join(fp, "*.json"))

    def phrase_once(doc, model):
        return model[doc]

    def phrase_many(doc, model, ntimes):
        for i in range(ntimes):
            doc = phrase_once(doc, model)
        return doc

    for f in files:
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        sentences = doc[text_key]
        for s in sentences:
            if s:
                doc = phrase_many(s, model, layers)
                yield doc


def stream_unpacked_docs(stream):
    for doc in stream:
        doc = unpack_doc(doc)
        yield doc


def stream_doc_summaries(stream):
    for doc in stream:
        doc_id = doc['member_id']
        doc_summary = doc['summary']
        if doc_summary:
            yield doc_summary, doc_id
        else:
            yield "", doc_id


def stream_doc_jobs(stream):
    for doc in stream:
        doc = unpack_doc(doc)
        doc_id = doc['member_id']
        doc_jobs = doc['jobs']
        if not doc_jobs:
            continue
        for job in doc_jobs:
            if job:
                yield job, doc_id


def get_sub_docs(x):
    """
    Get an iterable of summary, job_0, job_1, etc

    Each subdoc will be an iterable of sentences
    Each sentence will be an iterable of tokens

    :param x:
    :return:
    """
    sub_docs = []
    summary_tokens = toolz.dicttoolz.get_in(['summary', 'tokens'], x, default=[])
    sub_docs.extend(summary_tokens)
    jobs = toolz.dicttoolz.get_in(['jobs'], x, default=[])
    for job in jobs:
        if job:
            job_tokens = job.get('tokens', [])
            if job_tokens:
                sub_docs.extend(job_tokens)
    return sub_docs


if __name__ == "__main__":
    config = ProcessConfig()
    r = SpacyReader(config.OUTPUT2, get_sub_docs)
    phraser = MyPhraser()
    d = r.as_phrased_documents(phraser)
    for i in range(10):
        print(" ".join(next(d)))
