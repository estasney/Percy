import re
import numpy as np
from gensim.corpora import Dictionary
from app_folder.site_config import FConfig


def word_math(request):
    pwords = request.form.get('pwords')
    neg_words = request.form.get('neg_words')

    if not pwords:
        return False, None  # Can't do anything

    ws = WordSims()

    pwords = re.findall(r"\"?'?([A-z ]{2,})\"?'?", pwords)
    pwords = [x.replace(" ", "_").lower() for x in pwords]

    if not pwords:
        return False, None

    unknown_words = []
    pwords_idx = ws.in_vocab(pwords)
    pwords, unknown_words_p = pwords_idx['known'], pwords_idx['unknown']

    if unknown_words_p:
        unknown_words.extend(unknown_words_p)

    if neg_words:
        neg_words = re.findall(r"\"?'?([A-z ]{2,})\"?'?", neg_words)
        neg_words = [x.replace(" ", "_").lower() for x in neg_words]
        neg_words_idx = ws.in_vocab(neg_words)
        neg_words, unknown_words_n = neg_words_idx['known'], neg_words_idx['unknown']
        if unknown_words_n:
            unknown_words.extend(unknown_words_p)
    else:
        neg_words = None

    if not pwords:
        return False, unknown_words

    vec = ws.word_math_vec_(pwords, neg_words)
    sims_success, sims = ws.find_similar_vec(vec)
    sims['equation'] = ws.as_equation(pwords, neg_words)
    return sims_success, sims


def word_sims(query):
    query = re.findall(r"\"?'?([A-z ]{2,})\"?'?", query)
    if not query:
        return False, None
    query = query[0]  # Selecting the first word
    query = query.replace(" ", "_").lower()
    ws = WordSims()
    sims = ws.find_similar(query)
    return sims


class WordSims(object):

    def __init__(self):
        self.array = np.load(FConfig.lda_pmi)
        self.idx = Dictionary.load(FConfig.dictionary)

    def find_similar(self, word):
        try:
            word_id = self.idx.token2id[word]
        except KeyError:
            return False, None

        dd = np.dot(self.array, self.array[word_id])  # Cosine similarity for this unigram against all others.
        sims = np.argsort(-1 * dd)[:100]
        sim_scores = [(self.idx.get(sim), dd[sim]) for sim in sims if word_id != sim]

        # Remove None Id2Word
        sim_scores = list(filter(lambda x: x[0] is not None, sim_scores))
        sim_scores.sort(key=lambda x: x[1], reverse=True)
        return True, sim_scores

    def find_similar_vec(self, vec):

        dd = np.dot(self.array, vec)  # Cosine similarity for this unigram against all others.
        sims = np.argsort(-1 * dd)[:100]
        sim_scores = [(self.idx.get(sim), dd[sim]) for sim in sims]

        # Remove None Id2Word
        sim_scores = list(filter(lambda x: x[0] is not None, sim_scores))
        sim_scores.sort(key=lambda x: x[1], reverse=True)
        return True, sim_scores

    def word_math_vec_(self, positive_words, negative_words=None):
        positive_words_ids = [self.idx.token2id.get(w) for w in positive_words]
        positive_word_vec = np.sum([self.array[x] for x in positive_words_ids], axis=0)
        if not negative_words:
            return positive_word_vec
        negative_words_ids = [self.idx.token2id.get(w) for w in negative_words]
        negative_word_vec = np.sum([self.array[x] for x in negative_words_ids], axis=0)
        result_vec = positive_word_vec - negative_word_vec
        return result_vec

    def in_vocab(self, words):
        known_words = list(filter(lambda x: self.idx.token2id.get(x) is not None, words))
        unknown_words = [word for word in words if word not in known_words]
        return {'known': known_words, 'unknown': unknown_words}

    def as_equation(self, positive_words, negative_words=None):
        peq = " + ".join(positive_words)
        if negative_words:
            neq = " + ".join(negative_words)
        if not negative_words:
            return peq
        else:
            return "({}) - ({})".format(peq, neq)

