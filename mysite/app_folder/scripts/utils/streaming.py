import glob
import os
import json


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


def add_extra(d):
    others = ['is_alpha', 'is_ascii', 'is_digit', 'is_punct', 'is_left_punct', 'is_right_punct',
              'is_space', 'is_bracket', 'is_quote', 'is_currency', 'like_url', 'like_num', 'like_email',
              'is_oov', 'is_stop']

    json_data = d.to_json()
    for i, t in enumerate(d):
        token_data = json_data['tokens'][i]
        token_data.update({'lemma': t.lemma_, 'norm': t.norm_, 'text': t.text})
        conjuncts = list(t.conjuncts)
        if conjuncts:
            conjuncts = [c.text for c in conjuncts]
        token_data.update({'conjuncts': conjuncts})
        for o in others:
            token_data.update({o: getattr(t, o, None)})

    # segment the tokens into sentences using the 'sents' key

    return json_data



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