import unicodedata
import re
import string
from nltk.corpus import stopwords
from nltk import word_tokenize, sent_tokenize
from pattern.en import parsetree
from functools import partial
from itertools import chain
import json
import os
import glob
import numpy as np
import multiprocessing
from .patterns import BulletedPattern, PossessivePattern, ContractionPattern, PercentagePattern, UnTokenizePattern

STOPWORDS = set(stopwords.words('english'))


char_search = re.compile(r"[^\u000a\u0020-\u0023\u0027\u002b-\u002e\u0030-\u0039\u003f\u0041-\u005a\u0061-\u007a]")
strip_multi_ws = re.compile(r"( {2,})")
abbr = re.compile(r"(\.)\B")


def clean(s):
    s = unicodedata.normalize("NFKD", s)
    s = char_search.sub(" ", s)
    s = strip_multi_ws.sub(" ", s)
    return s


def preprocess_text(text):

    doc = clean(text)
    tree = parsetree(doc, tokenize=True, lemmata=True)
    doc = [sent.lemma for sent in tree]
    return doc


def tokenize_text(text):
    # sent tokenize the text
    sentences = sent_tokenize(text)
    # split on newlines as well
    s1 = chain.from_iterable([s.splitlines() for s in sentences])
    del sentences
    # split on common bullet points
    s2 = [word_tokenize(w) for w in s1]
    bullet_split = BulletedPattern()
    s3 = chain.from_iterable([bullet_split[s] for s in s2])
    del s2



    contraction = ContractionPattern()
    possessive = PossessivePattern()
    percentage = PercentagePattern()
    program = UnTokenizePattern()

    s3 = [contraction[sentence] for sentence in s3]
    s3 = [possessive[sentence] for sentence in s3]
    s3 = [percentage[sentence] for sentence in s3]
    s3 = [program[sentence] for sentence in s3]

    punc = set(string.punctuation)
    s3 = [[word for word in sentence if word not in punc] for sentence in s3]

    return s3



def multiprocess_preprocess(fp, data_key_raw, data_key_out, dir_out):

    with open(fp, 'r') as json_file:
        record = json.load(json_file)

    raw_summary = record[data_key_raw]
    clean_summary = tokenize_text(raw_summary)
    record[data_key_out] = clean_summary
    # add clean summary to record and dump to json
    fp = os.path.join(dir_out, "{}.json".format(record['member_id']))
    with open(fp, 'w') as json_file:
        json.dump(record, json_file)


def worker_process_text(files, dir_out, data_key_raw='summary', data_key_out='token_summary'):
    for f in files:
        multiprocess_preprocess(f, data_key_raw, data_key_out, dir_out)




def fetch_tmp_files(d):
    file_pattern = "*.json"
    file_pattern = os.path.join(d, file_pattern)
    file_list = glob.glob(file_pattern)
    return file_list


def pool_process_text(d, workers, dir_out):
    # Get the work to be done
    file_list = fetch_tmp_files(d)

    # Split the work based on number of workers
    file_subsets = np.array_split(file_list, workers)

    process_text = partial(worker_process_text, dir_out=dir_out)
    # Open a pool
    pool = multiprocessing.Pool(processes=workers)
    pool.map(process_text, file_subsets)
    pool.close()


def flatten_sents(x):
    doc = x['sent']
    return [clean(word) for sent in doc for word in sent]

