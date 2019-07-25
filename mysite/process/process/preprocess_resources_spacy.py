import json
import glob
import os
import re
import tempfile

import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from functools import wraps
from collections import Counter
from math import log
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import svds
from sklearn.feature_extraction.text import TfidfVectorizer

import en_core_web_lg
import logging

from gensim.corpora.dictionary import Dictionary

from process import ProcessConfig
from process.process.spacy_process.spacy_doc_piper import SpacyDocPiper
from process.process.spacy_process.streaming import stream_docs, stream_skills, stream_pairs
from process.process.spacy_process.spacy_utils import add_extra, STOPWORDS
from process.process.spacy_process.spacy_phrases import detect_phrases, MyPhraser
from process.process.spacy_process.lang import (lang_detect, lookup_language_detection, apply_by_multiprocessing,
                                                store_language_detection)
from process.process.spacy_process.streaming import SpacyReader

config = ProcessConfig()

OUTPUT1 = config.OUTPUT1
OUTPUT2 = config.OUTPUT2

LANG_FILE = config.LANGUAGE_ID

PHRASE_MODEL_FP = config.PHRASE_MODEL
PHRASE_DUMP_FP = config.PHRASE_DUMP
CORPUS_FP = config.CORPUS_FILE
N_WORKERS = config.N_WORKERS

MIN_WORD_COUNT = 20
MAX_WORD_RATIO = 0.9

MIN_SKILL_COUNT = 25
MAX_SKILL_RATIO = 0.9

WINDOW_SIZE = 3

WORD_VEC_SIZE = 200
SKILL_VEC_SIZE = 100


def time_this(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        start_time = datetime.now()
        print("Starting {}".format(func.__name__))
        result = func(*args, **kwargs)
        elapsed = datetime.now() - start_time
        print("Finished {} in {}".format(func.__name__, elapsed))
        return result

    return wrapped


@time_this
def spacify_docs(output1=OUTPUT1, output2=OUTPUT2, prettify=False, ignore_existing=False):
    """

    :param output1: From output1 to output2
    :param output2:
    :param prettify: Indent JSON Files
    :return:
    """

    start_time = datetime.now()
    print("Loading spacy model")
    nlp = en_core_web_lg.load()
    print("Model loaded in {}".format(datetime.now() - start_time))

    if prettify:
        write_to_json = lambda x, y: json.dump(x, y, indent=4)
    else:
        write_to_json = lambda x, y: json.dump(x, y)

    # glob files
    if ignore_existing:
        new_files = []
        output1_files = glob.glob(os.path.join(output1, "*.json"))
        for file in output1_files:
            file_name = os.path.basename(file)
            output2_file_path = os.path.join(output2, file_name)
            if not os.path.isfile(output2_file_path):
                new_files.append(file)
        output1_files = new_files
    else:
        output1_files = glob.glob(os.path.join(output1, "*.json"))

    # keep reference to member_ids from file names
    file_names = [os.path.basename(x) for x in output1_files]

    print("Found {} docs".format(len(output1_files)))

    # Stream components by flattening and rejoining later
    doc_summary_stream = stream_docs(files=output1_files, data_key='summary')
    doc_job_stream_raw = stream_docs(files=output1_files, data_key='jobs')

    jobidx = []

    def stream_jobs(job_stream):
        for i, job in enumerate(job_stream):
            doc_id = file_names[i]
            doc_name, ext = os.path.splitext(doc_id)
            jobs = job.split("<__sep__>")
            jobs = list(filter(lambda x: x, jobs))
            for i, j in enumerate(jobs):
                fp = "{}_{}".format(doc_name, i)
                jobidx.append(fp)
                yield j

    doc_job_stream = stream_jobs(doc_job_stream_raw)

    # make a temp folder
    summary_temp = tempfile.TemporaryDirectory()
    summary_temp_path = summary_temp.name

    timings = []

    for i, summary in enumerate(nlp.pipe(doc_summary_stream, batch_size=50)):
        start_time = datetime.now()
        summary = add_extra(summary)
        out_f = os.path.join(summary_temp_path, file_names[i])
        with open(out_f, 'w+') as y:
            write_to_json(summary, y)
        elapsed = (datetime.now() - start_time).total_seconds()
        timings.append(elapsed)

        if i % 1000 == 0 and i > 0:
            step_mean = np.array(timings).mean()
            timings = []
            print("Step {} of Summaries, Avg {} per step".format(i, step_mean))

    job_temp = tempfile.TemporaryDirectory()
    job_temp_path = job_temp.name

    timings = []

    for i, job in enumerate(nlp.pipe(doc_job_stream, batch_size=50)):
        start_time = datetime.now()
        job = add_extra(job)
        filename = jobidx[i] + ".json"
        out_f = os.path.join(job_temp_path, filename)
        with open(out_f, 'w+') as y:
            write_to_json(job, y)

        elapsed = (datetime.now() - start_time).total_seconds()
        timings.append(elapsed)

        if i % 1000 == 0 and i > 0:
            step_mean = np.array(timings).mean()
            timings = []
            print("Step {} of Jobs, Avg {} per step".format(i, step_mean))

    doc_stream = stream_docs(output1_files, data_key=None)

    job_sort = re.compile(r"(?<=_)([0-9]+)")

    def sort_jobs(fps):
        fps = sorted(fps, key=lambda x: int(job_sort.search(x).group()))
        return fps

    timings = []

    for i, doc in enumerate(doc_stream):
        start_time = datetime.now()
        doc.update({'skills': doc.get('skills', "").split(", ")})
        doc.update({'titles': doc.get('titles', "").split("<__sep__>")})
        # Remove and add from tempfiles
        del doc['summary']
        del doc['jobs']

        doc_id = file_names[i]
        # get the summary
        summary_fp = os.path.join(summary_temp_path, doc_id)
        with open(summary_fp, "r") as f:
            summary = json.load(f)
        doc['summary'] = summary

        # get the jobs
        doc_id, _ = os.path.splitext(doc_id)
        job_fp_pattern = "{}_*.json".format(doc_id)
        job_full_path = os.path.join(job_temp_path, job_fp_pattern)
        job_files = glob.glob(job_full_path)
        job_files = sort_jobs(job_files)

        job_holder = []
        for jf in job_files:
            with open(jf, 'r') as f:
                j = json.load(f)
                job_holder.append(j)

        doc['jobs'] = job_holder
        out_f = os.path.join(output2, file_names[i])
        with open(out_f, 'w+') as json_file:
            if prettify:
                json.dump(doc, json_file, indent=4)
            else:
                json.dump(doc, json_file)

        elapsed = (datetime.now() - start_time).total_seconds()
        timings.append(elapsed)

        if i % 1000 == 0 and i > 0:
            step_mean = np.array(timings).mean()
            timings = []
            print("Step {} of Merging, Avg {} per step".format(i, step_mean))


@time_this
def preprocess_csv(corpus_fp, n_workers, output1=OUTPUT1, prettify_output=False):
    print("Filtering CSV")
    df = pd.read_csv(corpus_fp)
    original_count = len(df)
    df.dropna(subset=['summary', 'jobs'], thresh=1, inplace=True)

    print("Dropped {} Records where Summary and Jobs is Null".format(original_count - len(df)))
    original_count = len(df)
    df.fillna("", inplace=True)
    start = datetime.now()

    print("Starting Language Detection")

    # merge in lookups if they exist
    df = lookup_language_detection(df, LANG_FILE)
    df['lang'] = apply_by_multiprocessing(df, lang_detect, axis=1, workers=n_workers)
    elapsed = datetime.now() - start
    print("Finished Language Detection in {}".format(elapsed))

    # dump a list of languages detected
    store_language_detection(df, LANG_FILE)
    df = df.loc[df['lang'] == 'en']
    print("Corpus loaded with {} records".format(original_count))
    print("Dropping {} non english records".format(original_count - len(df)))
    del df['lang']

    def export_df(df, prettify, dir_out):
        for i, row in df.iterrows():
            file_name = "{}.json".format(row['member_id'])
            file_name = os.path.join(dir_out, file_name)
            with open(file_name, "w+") as jfile:
                if prettify:
                    json.dump(row.to_dict(), jfile, indent=4)
                else:
                    json.dump(row.to_dict(), jfile)

    print("Exporting DataFrame")
    export_df(df, prettify_output, output1)


@time_this
def make_token_dictionary(folder=OUTPUT2):
    doc_reader = SpacyReader(folder=folder, text_key="tokens")
    doc_phraser = MyPhraser()
    doc_stream = doc_reader.as_phrased_sentences(doc_phraser)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    dictionary = Dictionary(doc_stream)
    print("Dictionary found {} unique tokens".format(len(dictionary)))
    dictionary.filter_extremes(no_below=MIN_WORD_COUNT, no_above=MAX_WORD_RATIO)
    dictionary.compactify()
    dictionary.save(config.RESOURCES_DICTIONARY_TOKENS)
    with open(config.RESOURCES_AUTOCOMPLETE_TOKENS, "w+", encoding="utf-8") as tfile:
        for term in dictionary.values():
            term += "\n"
            tfile.write(term)


@time_this
def make_skills_dictionary(folder=OUTPUT2):
    skill_stream = stream_skills(folder)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    dictionary = Dictionary(skill_stream)
    dictionary.filter_extremes(no_below=MIN_WORD_COUNT, no_above=MAX_WORD_RATIO)
    dictionary.compactify()
    dictionary.save(config.RESOURCES_DICTIONARY_SKILLS)
    with open(config.RESOURCES_AUTOCOMPLETE_SKILLS, "w+", encoding="utf-8") as tfile:
        for term in dictionary.values():
            term += "\n"
            tfile.write(term)


@time_this
def get_token_counts(folder, dictionary_fp=config.RESOURCES_DICTIONARY_TOKENS):
    doc_reader = SpacyReader(folder=folder, text_key="tokens")
    doc_phraser = MyPhraser()
    doc_stream = doc_reader.as_phrased_sentences(doc_phraser)
    dictionary = Dictionary.load(dictionary_fp)
    bow = (dictionary.doc2idx(x) for x in doc_stream)
    cx = Counter()
    for bow_doc in bow:
        filtered_doc = filter(lambda x: x > -1, bow_doc)
        cx.update(filtered_doc)

    return cx


@time_this
def get_skills_counts(folder, dictionary_fp=config.RESOURCES_DICTIONARY_SKILLS):
    doc_stream = stream_skills(folder)
    dictionary = Dictionary.load(dictionary_fp)
    bow = (dictionary.doc2idx(x) for x in doc_stream)
    cx = Counter()
    for bow_doc in bow:
        filtered_doc = filter(lambda x: x > -1, bow_doc)
        cx.update(filtered_doc)

    return cx


@time_this
def get_token_probabilities(folder=OUTPUT2):
    cx = get_token_counts(folder)
    token_sums = sum(cx.values())
    probabilities = np.array(list(cx.values()))
    probabilities = probabilities / token_sums
    cxp = {k: v for k, v in zip(list(cx.keys()), probabilities)}
    with open(config.RESOURCES_CX_TOKENS, "wb+") as pfile:
        pickle.dump(cx, pfile)

    with open(config.RESOURCES_CXP_TOKENS, "wb+") as pfile:
        pickle.dump(cxp, pfile)


@time_this
def get_skill_probabilities(folder=OUTPUT2):
    cx = get_skills_counts(folder)
    token_sums = sum(cx.values())
    probabilities = np.array(list(cx.values()))
    probabilities = probabilities / token_sums
    cxp = {k: v for k, v in zip(list(cx.keys()), probabilities)}
    with open(config.RESOURCES_CX_SKILLS, "wb+") as pfile:
        pickle.dump(cx, pfile)

    with open(config.RESOURCES_CXP_SKILLS, "wb+") as pfile:
        pickle.dump(cxp, pfile)


@time_this
def get_token_pair_probabilities(folder=OUTPUT2):
    doc_reader = SpacyReader(folder=folder, text_key="tokens")
    doc_phraser = MyPhraser()
    doc_stream = doc_reader.as_phrased_sentences(doc_phraser)
    dictionary = Dictionary.load(config.RESOURCES_DICTIONARY_TOKENS)

    pair_stream = stream_pairs(doc_stream, dictionary, window_size=WINDOW_SIZE)
    cxy = Counter(pair_stream)
    pair_sums = sum(cxy.values())
    probabilities = np.array(list(cxy.values()))
    probabilities = probabilities / pair_sums
    cxyp = {k: v for k, v in zip(list(cxy.keys()), probabilities)}

    with open(config.RESOURCES_CXY_TOKENS, "wb+") as pfile:
        pickle.dump(cxy, pfile)

    with open(config.RESOURCES_CXYP_TOKENS, "wb+") as pfile:
        pickle.dump(cxyp, pfile)


@time_this
def get_skill_pair_probabilities(folder=OUTPUT2):
    doc_stream = stream_skills(folder)
    dictionary = Dictionary.load(config.RESOURCES_DICTIONARY_SKILLS)

    pair_stream = stream_pairs(doc_stream, dictionary, window_size=WINDOW_SIZE)
    cxy = Counter(pair_stream)
    pair_sums = sum(cxy.values())
    probabilities = np.array(list(cxy.values()))
    probabilities = probabilities / pair_sums
    cxyp = {k: v for k, v in zip(list(cxy.keys()), probabilities)}

    with open(config.RESOURCES_CXY_SKILLS, "wb+") as pfile:
        pickle.dump(cxy, pfile)

    with open(config.RESOURCES_CXYP_SKILLS, "wb+") as pfile:
        pickle.dump(cxyp, pfile)


@time_this
def get_pmi_tokens():
    get_token_probabilities()
    get_token_pair_probabilities()
    pmi_samples = Counter()
    with open(config.RESOURCES_CX_TOKENS, "rb") as pfile:
        cx = pickle.load(pfile)
    with open(config.RESOURCES_CXY_TOKENS, "rb") as pfile:
        cxy = pickle.load(pfile)

    word_sums = sum(cx.values())
    pair_sums = sum(cxy.values())
    data, rows, cols = [], [], []
    for (x, y), n in cxy.items():
        rows.append(x)
        cols.append(y)
        data.append(log((n / pair_sums) / (cx[x] / word_sums) / (cx[y] / word_sums)))
        pmi_samples[(x, y)] = data[-1]

    PMI = csc_matrix((data, (rows, cols)))
    del data, rows, cols
    U, _, _ = svds(PMI, k=WORD_VEC_SIZE)
    norms = np.sqrt(np.sum(np.square(U), axis=1, keepdims=True))
    U /= np.maximum(norms, 1e-9)
    np.save(config.RESOURCES_LDA_PMI_TOKENS, U)


@time_this
def get_pmi_skills():
    get_skill_probabilities()
    get_skill_pair_probabilities()
    pmi_samples = Counter()
    with open(config.RESOURCES_CX_SKILLS, "rb") as pfile:
        cx = pickle.load(pfile)
    with open(config.RESOURCES_CXY_SKILLS, "rb") as pfile:
        cxy = pickle.load(pfile)

    word_sums = sum(cx.values())
    pair_sums = sum(cxy.values())
    data, rows, cols = [], [], []
    for (x, y), n in cxy.items():
        rows.append(x)
        cols.append(y)
        data.append(log((n / pair_sums) / (cx[x] / word_sums) / (cx[y] / word_sums)))
        pmi_samples[(x, y)] = data[-1]

    PMI = csc_matrix((data, (rows, cols)))
    del data, rows, cols
    U, _, _ = svds(PMI, k=SKILL_VEC_SIZE)
    norms = np.sqrt(np.sum(np.square(U), axis=1, keepdims=True))
    U /= np.maximum(norms, 1e-9)
    np.save(config.RESOURCES_LDA_PMI_SKILLS, U)


@time_this
def get_fingerprint_tokens(folder=OUTPUT2):
    cnt = TfidfVectorizer(use_idf=True, sublinear_tf=True)
    doc_reader = SpacyReader(folder=folder, text_key="tokens")
    doc_phraser = MyPhraser()
    doc_stream = doc_reader.as_phrased_sentences(doc_phraser)

    # Tfidf doesn't accept lists
    def stream_tokens_from_sentences(doc_stream):
        for doc in doc_stream:
            for token in doc:
                yield token

    token_stream = stream_tokens_from_sentences(doc_stream)
    X = cnt.fit_transform(token_stream)
    doc_freqs_grp1 = np.sum(X, axis=0)
    doc_freqs_grp1 = np.array(doc_freqs_grp1)[0]
    # Calculate probabilities
    doc_probs_grp1 = doc_freqs_grp1 / X.shape[0]
    np.save(config.RESOURCES_FINGERPRINT_TOKENS, doc_probs_grp1)
    with open(config.RESOURCES_FINGERPRINT_VEC_TOKENS, "wb+") as pfile:
        pickle.dump(cnt, pfile)


if __name__ == "__main__":
    # CSV To JSON
    # Remove Null Records
    # Remove Non-English Records

    # preprocess_csv(corpus_fp=config.CORPUS_FILE_2, n_workers=N_WORKERS)

    # Tokenize JSON records
    spacify_docs(ignore_existing=False, prettify=False)
    # #
    # # # Train the phraser from JSON records
    # detect_phrases(input_dir=OUTPUT2, phrase_model_fp=PHRASE_MODEL_FP, phrase_dump_fp=PHRASE_DUMP_FP,
    #                common_words=STOPWORDS, min_count=10, threshold=30)
    # make_token_dictionary()
    # make_skills_dictionary()
    # get_pmi_tokens()
    # get_pmi_skills()
    # get_fingerprint_tokens()
