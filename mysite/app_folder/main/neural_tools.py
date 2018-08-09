
import numpy as np
from gensim.corpora import Dictionary
from collections import OrderedDict
from operator import itemgetter
from app_folder.site_config import FConfig

def word_math(request):
    pwords = request.form.get('pwords').split(",")
    pwords = [x.replace(" ", "_").lower() for x in pwords]
    neg_words = request.form.get('neg_words')
    if neg_words:
        neg_words = neg_words.split(",")
        neg_words = [x.replace(" ", "_").lower() for x in neg_words]
    ws = WordSims()
    vec = ws.word_math_vec_(pwords, neg_words)
    sims = ws.find_similar_vec(vec)
    return sims




class WordSims(object):

    def __init__(self):
        self.array = np.load(FConfig.lda_pmi)
        self.idx = Dictionary.load(FConfig.dictionary)

    def find_similar(self, word):
        word = word.replace(" ", "_")
        try:
            word_id = self.idx.token2id[word]
        except KeyError:
            return None

        dd = np.dot(self.array, self.array[word_id])  # Cosine similarity for this unigram against all others.
        sims = np.argsort(-1 * dd)[:100]
        sim_scores = [(self.idx.get(sim), dd[sim]) for sim in sims if word_id != sim]

        # Remove None Id2Word
        sim_scores = list(filter(lambda x: x[0] is not None, sim_scores))
        sim_scores.sort(key=lambda x: x[1], reverse=True)
        return sim_scores

    def find_similar_vec(self, vec):

        dd = np.dot(self.array, vec)  # Cosine similarity for this unigram against all others.
        sims = np.argsort(-1 * dd)[:100]
        sim_scores = [(self.idx.get(sim), dd[sim]) for sim in sims]

        # Remove None Id2Word
        sim_scores = list(filter(lambda x: x[0] is not None, sim_scores))
        sim_scores.sort(key=lambda x: x[1], reverse=True)
        return sim_scores

    def word_math_vec_(self, positive_words, negative_words=None):
        positive_words_ids = [self.idx.token2id.get(w) for w in positive_words]
        positive_word_vec = np.sum([self.array[x] for x in positive_words_ids], axis=0)
        if not negative_words:
            return positive_word_vec
        negative_words_ids = [self.idx.token2id.get(w) for w in negative_words]
        negative_word_vec = np.sum([self.array[x] for x in negative_words_ids], axis=0)
        result_vec = positive_word_vec - negative_word_vec
        return result_vec
