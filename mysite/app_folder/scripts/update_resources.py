import pandas as pd
from gensim.corpora.dictionary import Dictionary
from gensim.utils import strided_windows
from itertools import combinations
import logging
from collections import Counter
import numpy as np
from app_folder.main.text_tools import STOPWORDS
import string
from scipy.sparse import csc_matrix
from math import log
from scipy.sparse.linalg import svds
from datetime import datetime

"""
Resources to update

Note: Preprocessing of text is done outside of text_tools
To preserve word context, text is sent_split with pattern

"""

"""

Words

"""

df = pd.read_csv(r"/home/eric/PycharmProjects/FlaskAPI/scripts2/corpus.csv")
df.dropna(subset=['summary'], inplace=True)
docs = df['summary'].values.tolist()
del df

def preprocess_text(x, preserve_sent=False, stopwords=STOPWORDS):
    from pattern.en import parsetree

    punc = set(string.punctuation)
    tree = parsetree(x, tokenize=True, lemmata=True)
    doc = [sent.lemma for sent in tree]
    if preserve_sent is False:
        pdoc = [word for sent in doc for word in sent]
        pdoc = [word for word in pdoc if word not in punc]
        pdoc = [word for word in pdoc if word not in stopwords]
    else:
        pdoc = []
        for sent in doc:
            psent = [word for word in sent if word not in punc]
            psent = [word for word in psent if word not in stopwords]
            pdoc.append(psent)
    return pdoc


"""
DICTIONARY - Words
"""
print("Building Dictionary")
start = datetime.now()
pdocs = [preprocess_text(doc, preserve_sent=False) for doc in docs]
del docs
dictionary = Dictionary(pdocs)
print("Dictionary found {} unique tokens".format(len(dictionary)))
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
dictionary.filter_extremes(no_below=10, no_above=0.9)
dictionary.compactify()
dictionary.save(r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/dictionary.model")

elapsed = datetime.now() - start

print("Finished Dictionary in {} seconds".format(elapsed.seconds))



"""
VECTORS - Words
"""

print("Getting BOW for Occurence Counts")
start = datetime.now()
bow = list(map(lambda x: [z for z in dictionary.doc2idx(x) if z > -1], pdocs))
cx = Counter([i for doc in bow for i in doc])
word_sums = sum(cx.values())
probabilities = np.array(list(cx.values()))
probabilities = probabilities / word_sums
cxp = {k: v for k, v in zip(list(cx.keys()), probabilities)}
del bow, pdocs

df = pd.read_csv(r"/home/eric/PycharmProjects/FlaskAPI/scripts2/corpus.csv")
df.dropna(subset=['summary'], inplace=True)
docs = df['summary'].values.tolist()
del df

elapsed = datetime.now() - start
print("Bow Complete in {}".format(elapsed.seconds))

def stream_pairs(docs=docs):
    for doc in docs:
        pdoc = preprocess_text(doc, preserve_sent=True)
        if not pdoc:
            continue
        for sent in pdoc:
            bow_sent = dictionary.doc2idx(sent)
            bow_sent = [b for b in bow_sent if b > -1]
            if len(bow_sent) < 3:
                continue
            windows = strided_windows(bow_sent, window_size=5)
            for w in windows:
                for x, y in map(sorted, combinations(w, 2)):
                    yield x, y

print("Starting Pair Stream")
start = datetime.now()
pair_stream = stream_pairs()
cxy = Counter(pair_stream)

elapsed = datetime.now() - start
print("Got cxy values in {} seconds".format(elapsed.seconds))
pair_sums = sum(cxy.values())

probabilities = np.array(list(cxy.values()))
probabilities = probabilities / pair_sums

cxyp = {k: v for k, v in zip(list(cxy.keys()), probabilities)}

print('Building Sparse PMI Matrix')

pmi_samples = Counter()
data, rows, cols = [], [], []
for (x, y), n in cxy.items():
    rows.append(x)
    cols.append(y)
    data.append(log((n / pair_sums) / (cx[x] / word_sums) / (cx[y] / word_sums)))
    pmi_samples[(x, y)] = data[-1]
PMI = csc_matrix((data, (rows, cols)))

del data, rows, cols, probabilities

U, _, _ = svds(PMI, k=100)
norms = np.sqrt(np.sum(np.square(U), axis=1, keepdims=True))
U /= np.maximum(norms, 1e-9)

np.save("/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/lda_pmi.npy", U)



