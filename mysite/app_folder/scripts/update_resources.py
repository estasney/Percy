import logging
import multiprocessing
import pickle
import string
from collections import Counter
from datetime import datetime
from itertools import combinations
from math import log
import re
import unicodedata
import numpy as np
import pandas as pd
from gensim.corpora.dictionary import Dictionary
from gensim.models.phrases import Phrases, Phraser
from gensim.utils import strided_windows
from langdetect import detect
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import svds
from sklearn.feature_extraction.text import TfidfVectorizer

from app_folder.main.text_tools import STOPWORDS

"""
Resources to update

Note: Preprocessing of text is done outside of text_tools
To preserve word context, text is sent_split with pattern

"""

"""

Words

"""

script_start = datetime.now()

def _apply_df(args):
    df, func, num, kwargs = args
    return num, df.apply(func, **kwargs)


def apply_by_multiprocessing(df, func, **kwargs):
    workers = kwargs.pop('workers')
    pool = multiprocessing.Pool(processes=workers)
    result = pool.map(_apply_df, [(d, func, i, kwargs) for i, d in enumerate(np.array_split(df, workers))])
    pool.close()
    result = sorted(result, key=lambda x: x[0])
    return pd.concat([i[1] for i in result])


def lang_detect(x):
    try:
        return detect(x['summary'])
    except:
        return ""

char_search = re.compile(r"[^\u0020-\u0023\u0027\u002b-\u002e\u0030-\u0039\u003f\u0041-\u005a\u0061-\u007a]")
strip_multi_ws = re.compile(r"( {2,})")
abbr = re.compile(r"(\.)\B")


def clean(s):
    s = unicodedata.normalize("NFKD", s)
    s = char_search.sub(" ", s)
    s = strip_multi_ws.sub(" ", s)
    s = abbr.sub("", s)
    return s

def filter_tokens(x):
    if x in set(string.punctuation) or x in set(string.whitespace):
        return False
    if not x.isprintable():
        return False
    if x.isnumeric():
        return False
    if "," in x and x.replace(",", "").isnumeric():  # 2,200
        return False
    if x in STOPWORDS:
        return False
    return True

def preprocess_text(x):
    from pattern.en import parsetree

    doc = clean(x['summary'])
    tree = parsetree(doc, tokenize=True, lemmata=True)
    doc = [sent.lemma for sent in tree]
    # if preserve_sent is False:
    #     pdoc = [word for sent in doc for word in sent]
    #     pdoc = [word for word in pdoc if word not in punc]
    #     pdoc = [word for word in pdoc if word not in stopwords]
    # else:
    pdoc = []
    for sent in doc:
        psent = list(filter(lambda x: filter_tokens(x), sent))
        pdoc.append(psent)
    return pdoc


def flatten_sents(x):
    doc = x['sent']
    return [clean(word) for sent in doc for word in sent]


if __name__ == "__main__":
    df = pd.read_csv(r"/home/eric/PycharmProjects/FlaskAPI/scripts2/corpus.csv")
    df.dropna(subset=['summary'], inplace=True)
    original_count = len(df)
    df.fillna("", inplace=True)
    start = datetime.now()
    print("Starting Resource Update")
    df['lang'] = apply_by_multiprocessing(df, lang_detect, axis=1, workers=8)
    elapsed = datetime.now() - start
    print("Finished Language Detection in {}".format(elapsed.seconds))
    df = df.loc[df['lang'] == 'en']
    print("Corpus loaded with {} records".format(original_count))
    print("Dropping {} non english records".format(original_count - len(df)))
    del df['lang']
    print("Preprocessing Text into Sentences")
    start = datetime.now()
    df['sent'] = apply_by_multiprocessing(df, preprocess_text, axis=1, workers=8)
    elapsed = datetime.now() - start
    print("Finished With Sentences in {}".format(elapsed.seconds))
    print("Flattening Doc")
    df['flat'] = apply_by_multiprocessing(df, flatten_sents, axis=1, workers=8)





"""
DICTIONARY - Words
"""
print("Building Dictionary")
start = datetime.now()
dictionary = Dictionary([word for word in df['flat'].values.tolist() if len(word) > 2])
print("Dictionary found {} unique tokens".format(len(dictionary)))
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
dictionary.filter_extremes(no_below=10, no_above=0.9)
dictionary.compactify()
dictionary.save(r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/dictionary.model")

# Write out autocomplete
with open(r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/dictionary_autocomplete.txt", "w+", encoding='utf-8') as tfile:
    for term in dictionary.values():
        term += "\n"
        tfile.write(term)

elapsed = datetime.now() - start
print("Finished Dictionary in {} seconds".format(elapsed.seconds))

"""

VECTORS - Words

"""

print("Getting Occurrence Counts for Words")
start = datetime.now()
bow = list(map(lambda x: [z for z in dictionary.doc2idx(x) if z > -1], df['flat'].values.tolist()))
cx = Counter([i for doc in bow for i in doc])
del bow
word_sums = sum(cx.values())
probabilities = np.array(list(cx.values()))
probabilities = probabilities / word_sums
cxp = {k: v for k, v in zip(list(cx.keys()), probabilities)}
elapsed = datetime.now() - start
print("Bow Complete in {}".format(elapsed.seconds))


def stream_pairs(docs=df['sent'].values.tolist()):
    for doc in docs:
        for sent in doc:
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
del U, norms, pmi_samples, cx, cxy, cxp, cxyp

"""

Words - Fingerprinting

"""

print("Starting Fingerprint")
start = datetime.now()
cnt = TfidfVectorizer(use_idf=True, sublinear_tf=True)
X = cnt.fit_transform([" ".join(doc) for doc in df['flat'].values.tolist()])
X_grp1 = X
doc_freqs_grp1 = np.sum(X_grp1, axis=0)
doc_freqs_grp1 = np.array(doc_freqs_grp1)[0]
# Calculate probabilities
doc_probs_grp1 = doc_freqs_grp1 / X_grp1.shape[0]
np.save(arr=doc_probs_grp1,
        file=r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/fingerprint_pop_occ.npy")

del X, X_grp1, doc_probs_grp1, doc_freqs_grp1

elapsed = datetime.now() - start

with open(r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/fingerprint_vec.pkl", 'wb+') as pfile:
    pickle.dump(cnt, pfile)
print("Finished Fingerprint in {}".format(elapsed.seconds))

del cnt



"""

SKILLS

"""
df = df.loc[df['skills'] != ""]
df['skills'] = df['skills'].apply(lambda x: x.lower().split(", "))


"""
DICTIONARY - Skills
"""
print("Building Skills Dictionary")
start = datetime.now()
dictionary = Dictionary(df['skills'].values.tolist())
print("Dictionary found {} unique tokens".format(len(dictionary)))
dictionary.filter_extremes(no_below=10, no_above=0.9)
dictionary.compactify()
dictionary.save(r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/dictionary_skills.model")

# Write out autocomplete
with open(r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/dictionary_skills_autocomplete.txt",
          "w+") as tfile:
    for term in dictionary.values():
        term += "\n"
        tfile.write(term)

elapsed = datetime.now() - start
print("Finished Skills Dictionary in {} seconds".format(elapsed.seconds))

"""
VECTORS - Skills
"""

print("Getting Skills Occurrence Counts")
start = datetime.now()
bow = list(map(lambda x: [z for z in dictionary.doc2idx(x) if z > -1], df['skills'].values.tolist()))
cx = Counter([i for doc in bow for i in doc])
word_sums = sum(cx.values())
probabilities = np.array(list(cx.values()))
probabilities = probabilities / word_sums
cxp = {k: v for k, v in zip(list(cx.keys()), probabilities)}
elapsed = datetime.now() - start
print("Bow Complete in {}".format(elapsed.seconds))


def stream_skills(docs=df['skills'].values.tolist()):
    for skill_grp in docs:
        if not skill_grp:
            continue
        skill_grp = dictionary.doc2idx(skill_grp)
        skill_grp = [x for x in skill_grp if x > -1]
        if len(skill_grp) < 3:
            continue
        for x, y in map(sorted, combinations(skill_grp, 2)):
            yield x, y


print("Starting Skills Pair Stream")
start = datetime.now()
pair_stream = stream_skills()
cxy = Counter(pair_stream)
pair_sums = sum(cxy.values())
probabilities = np.array(list(cxy.values()))
probabilities = probabilities / pair_sums
cxyp = {k: v for k, v in zip(list(cxy.keys()), probabilities)}
print('Building Sparse PMI Matrix for Skills')
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

np.save("/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/lda_pmi_skills.npy", U)
elapsed = datetime.now() - start
print("Finished Skills Vec in {}".format(elapsed.seconds))

del cx, cxp, cxyp, cxy, pmi_samples, bow

"""
Phraser
"""

def stream_phrases(docs=df['sent'].values.tolist()):
    for doc in docs:
        for sent in doc:
            yield sent

phrase_stream = stream_phrases()
print("Starting Phrase Stream")
start = datetime.now()
phrase_model = Phrases(phrase_stream)
phrase = Phraser(phrase_model)
phrase.save(r"/home/eric/PycharmProjects/Percy/mysite/app_folder/resources/phrases.model")
elapsed = datetime.now() - start
print("Finished Phrase Model in {}:{} minutes".format(elapsed.seconds // 60, elapsed.seconds % 60))

script_elapsed = (datetime.now() - script_start).seconds
script_elapsed_minutes = script_elapsed // 60
script_elapsed_seconds = script_elapsed % 60
print("Finished updating resources in {}:{}".format(script_elapsed_minutes, script_elapsed_seconds))