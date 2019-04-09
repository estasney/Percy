import glob
import os
import json
from nltk.corpus import stopwords


"""

Streaming

"""


def stream_docs(files, data_key):
    for f in files:
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        if data_key:
            doc_text = doc[data_key]
        else:
            doc_text = doc
        yield doc_text


class DocStreamer(object):

    def __init__(self, d, text_key='token_summary'):
        self.dir = d
        self.files = glob.glob(os.path.join(self.dir, "*.json"))
        self.text_key = text_key

    def load_json_(self, f):
        with open(f, 'r') as json_file:
            return json.load(json_file)[self.text_key]

    def __getitem__(self, i):
        file = self.files[i]
        doc = self.load_json_(file)
        return doc

    def __iter__(self):
        for file in self.files:
            doc = self.load_json_(file)
            for sentence in doc:
                if sentence:
                    yield sentence


class SpacyTokenFilter(object):

    DEFAULT_EXCLUDED = ["is_digit", "is_punct", "is_space", "is_currency", "like_url", "like_num", "like_email"]
    STOPWORDS = set(stopwords.words("english"))
    EXTRA_STOPWORDS = ["-PRON-", "-LRB-", "-RRB-"]

    def __init__(self, stopwords=None, excluded_attributes=None, token_key='lemma'):
        self.stopwords = stopwords if stopwords is not None else self.STOPWORDS
        self.stopwords.update(set(self.EXTRA_STOPWORDS))
        self.token_key = token_key
        self.excluded_attributes = excluded_attributes if excluded_attributes is not None else self.DEFAULT_EXCLUDED

    def filter_token(self, token):
        token_text = token.get(self.token_key, None)
        if not token_text:
            return False
        if token_text in self.stopwords:
            return False
        if any([token.get(attr, False) for attr in self.excluded_attributes]):
            return False
        return True


class SpacyReader(object):
    def __init__(self, folder, text_key, token_filter, sent_tokenize=True, token_key='lemma'):
        self.folder = folder
        self.files = glob.glob(os.path.join(self.folder, "*.json"))
        self.text_key = text_key
        self.token_filter = token_filter
        self.sent_tokenize = sent_tokenize
        self.token_key = token_key

    def load_json_(self, f):
        with open(f, 'r') as json_file:
            return json.load(json_file)

    def filter_tokens_(self, doc):
        tokens = list(filter(self.token_filter.filter_token, doc))
        return tokens

    def build_idx(self, tokens):
        start2idx = {token['start']: i for i, token in enumerate(tokens)}
        end2idx = {token['end']: i for i, token in enumerate(tokens)}
        return start2idx, end2idx

    def __getitem__(self, item):
        file = self.files[item]
        doc = self.load_json_(file)
        if not self.sent_tokenize:
            tokens = self.filter_tokens_(doc['tokens'])
            tokens = [t.get(self.token_key, None) for t in tokens]
            tokens = list(filter(lambda x: x is not None, tokens))
            return tokens
        else:
            tokens = doc['tokens']
            start2idx, end2idx = self.build_idx(tokens)
            output = []
            for sent in doc['sents']:
                sent_tokens = tokens[start2idx[sent['start']]: (end2idx[sent['end']]+1)]
                sent_tokens = self.filter_tokens_(sent_tokens)
                sent_tokens = [t.get(self.token_key, None) for t in sent_tokens]
                sent_tokens = list(filter(lambda x: x is not None, sent_tokens))
                output.append(sent_tokens)
            return output

    def __iter__(self):
        for f in self.files:
            doc = self.load_json_(f)
            if not self.sent_tokenize:
                tokens = self.filter_tokens_(doc['tokens'])
                tokens = [t.get(self.token_key, None) for t in tokens]
                tokens = list(filter(lambda x: x is not None, tokens))
                yield tokens
            else:
                tokens = doc['tokens']
                start2idx, end2idx = self.build_idx(tokens)
                for sent in doc['sents']:
                    sent_tokens = tokens[start2idx[sent['start']]: (end2idx[sent['end']] + 1)]
                    sent_tokens = self.filter_tokens_(sent_tokens)
                    sent_tokens = [t.get(self.token_key, None) for t in sent_tokens]
                    sent_tokens = list(filter(lambda x: x is not None, sent_tokens))
                    yield sent_tokens



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