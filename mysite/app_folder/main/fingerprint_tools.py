from app_folder.site_config import FConfig
from app_folder.main.text_tools import preprocess_text
import pickle
import numpy as np

fconfig = FConfig()


class Fingerprint(object):

    def __init__(self, vec=fconfig.FINGERPRINT_TOKENS_VEC, pop_occ=fconfig.FINGERPRINT_TOKENS):
        self.vec = self._load_pickled(vec)
        self.pop_occ = np.load(pop_occ)
        self.id2term = self._make_id2term()

    def _load_pickled(self, fp):
        with open(fp, 'rb') as vec_file:
            pobj = pickle.load(vec_file)
            return pobj

    def _make_id2term(self):
        return {k: v for k, v in enumerate(self.vec.get_feature_names())}

    def _get_probs(self, v):
        doc_freqs_grp2 = np.sum(v, axis=0)
        doc_freqs_grp2 = np.array(doc_freqs_grp2)[0]
        doc_probs_grp2 = doc_freqs_grp2 / v.shape[0]
        return doc_probs_grp2

    def _get_informative(self, doc_probs):
        grp2_ids = np.where(self.pop_occ < doc_probs)[0]
        grp2 = [(self.id2term[x], doc_probs[x]) for x in grp2_ids]
        grp2.sort(key=lambda x: x[1], reverse=True)
        return grp2

    def fingerprint(self, text):
        text = preprocess_text(text)
        v = self.vec.transform([text])  # Expects iterable
        # Convert to probabilities
        v_probs = self._get_probs(v)
        # Find most informative by probabilty
        most_informative = self._get_informative(v_probs)
        return most_informative


