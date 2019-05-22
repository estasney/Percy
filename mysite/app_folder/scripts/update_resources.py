import logging
import glob
import multiprocessing
import pickle
import string
from collections import Counter
from datetime import datetime
from itertools import combinations
from math import log
import re
import os
import unicodedata
import numpy as np
import pandas as pd
import json
from gensim.corpora.dictionary import Dictionary
from gensim.models.phrases import Phrases, Phraser
from gensim.utils import strided_windows
from langdetect import detect
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import svds
from sklearn.feature_extraction.text import TfidfVectorizer
from pattern.en import parsetree

from app_folder.tools.text_tools import STOPWORDS

"""
Resources to update

Note: Preprocessing of text is done outside of text_tools
To preserve word context, text is sent_split with pattern

"""

"""

Parameters

"""

WINDOW_SIZE = 5
WORD_VEC_SIZE = 200
SKILL_VEC_SIZE = 100
WORKERS = 4
MIN_WORD_COUNT = 10
MAX_WORD_RATIO = 0.9
MIN_SKILL_COUNT = 25
MAX_SKILL_RATIO = 0.9
TMP_DIR = "/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp"

"""

SETUP

"""

def make_tmp_dir():
    if not os.path.isdir(TMP_DIR):
        os.mkdir(TMP_DIR)
    else:
        existing_files = os.listdir(TMP_DIR)
        for f in existing_files:
            f = os.path.join(TMP_DIR, f)
            if os.path.isfile(f):
                os.remove(f)

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

def do_by_multiprocessing(files, func, **kwargs):
    workers = kwargs.pop('workers')
    pool = multiprocessing.Pool(processes=workers)
    result = pool.map(multiprocess_preprocess, )


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


def preprocess_text(text):

    doc = clean(text)
    tree = parsetree(doc, tokenize=True, lemmata=True)
    doc = [sent.lemma for sent in tree]
    pdoc = []
    for sent in doc:
        psent = list(filter(lambda x: filter_tokens(x), sent))
        pdoc.append(psent)
    return pdoc

def multiprocess_preprocess(fp, data_key_raw, data_key_out, prefix_out):

    with open(fp, 'r') as json_file:
        record = json.load(json_file)

    raw_summary = record[data_key_raw]
    clean_summary = preprocess_text(raw_summary)
    record[data_key_out] = clean_summary
    # add clean summary to record and dump to json
    fp = os.path.join(TMP_DIR, "{}_{}.json".format(prefix_out, record['member_id']))
    with open(fp, 'w') as json_file:
        json.dump(record, json_file)

def fetch_tmp_files(prefix):
    file_pattern = "{}_*.json".format(prefix)
    file_pattern = os.path.join(TMP_DIR, file_pattern)
    file_list = glob.glob(file_pattern)
    return file_list


def worker_process_text(files, data_key_raw='summary', data_key_out='clean_summary', prefix_out='clean'):
    for f in files:
        multiprocess_preprocess(f, data_key_raw, data_key_out, prefix_out)


def pool_process_text(prefix):
    # Get the work to be done
    file_list = fetch_tmp_files(prefix)

    # Split the work based on number of workers
    file_subsets = np.array_split(file_list, WORKERS)

    # Open a pool
    pool = multiprocessing.Pool(processes=WORKERS)
    pool.map(worker_process_text, file_subsets)
    pool.close()






def flatten_sents(x):
    doc = x['sent']
    return [clean(word) for sent in doc for word in sent]


def export_df(df, prefix, fp=TMP_DIR):
    for i, row in df.iterrows():
        file_name = "{}_{}.json".format(prefix, row['member_id'])
        file_name = os.path.join(fp, file_name)
        with open(file_name, "w+") as jfile:
            json.dump(row.to_dict(), jfile)

def make_target_file_list(n_workers=WORKERS):

    json_files = glob.glob("{}/*.json".format(TMP_DIR))
    return np.array_split(json_files, n_workers)


def stream_data(data_key, files):
    for f in files:
        with open(f, 'r') as json_file:
            record = json.load(json_file)
        yield record[data_key]





if __name__ == "__main__":
    make_tmp_dir()
    df = pd.read_csv(r"/home/eric/PycharmProjects/FlaskAPI/scripts2/corpus.csv")
    df.dropna(subset=['summary'], inplace=True)
    original_count = len(df)
    df.fillna("", inplace=True)
    start = datetime.now()
    print("Starting Resource Update")
    df['lang'] = apply_by_multiprocessing(df, lang_detect, axis=1, workers=WORKERS)
    elapsed = datetime.now() - start
    print("Finished Language Detection in {}".format(elapsed.seconds))
    df = df.loc[df['lang'] == 'en']
    print("Corpus loaded with {} records".format(original_count))
    print("Dropping {} non english records".format(original_count - len(df)))
    del df['lang']

    print("Dumping DF to JSON")
    export_df(df, prefix="raw")

    print("Preprocessing Text into Sentences")
    start = datetime.now()
    pool_process_text("raw")



    df['sent'] = apply_by_multiprocessing(df, preprocess_text, axis=1, workers=WORKERS)
    elapsed = datetime.now() - start
    print("Finished With Sentences in {}".format(elapsed.seconds))
    print("Flattening Doc")
    df['flat'] = apply_by_multiprocessing(df, flatten_sents, axis=1, workers=WORKERS)
    export_df(df)
    del df



"""
DICTIONARY - Words
"""
print("Building Dictionary")
start = datetime.now()
doc_stream = stream_data('summary')
dictionary = Dictionary([word for word in df['flat'].values.tolist() if len(word) > 2])
print("Dictionary found {} unique tokens".format(len(dictionary)))
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
dictionary.filter_extremes(no_below=MIN_WORD_COUNT, no_above=MAX_WORD_RATIO)
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
            windows = strided_windows(bow_sent, window_size=WINDOW_SIZE)
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
U, _, _ = svds(PMI, k=WORD_VEC_SIZE)
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
dictionary.filter_extremes(no_below=MIN_SKILL_COUNT, no_above=MAX_SKILL_RATIO)
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

U, _, _ = svds(PMI, k=SKILL_VEC_SIZE)
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