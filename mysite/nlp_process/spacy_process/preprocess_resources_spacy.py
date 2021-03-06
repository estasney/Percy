import itertools
import re
import sys

sys.path.append(r"C:\Users\estasney\PycharmProjects\Percy\mysite")
import json
from tqdm import tqdm
import os
import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from collections import Counter
from math import log
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import svds
from sklearn.feature_extraction.text import TfidfVectorizer

import en_core_web_lg
import logging

from gensim.corpora.dictionary import Dictionary

from nlp_process import ProcessConfig
from nlp_process.spacy_process import (stream_docs, stream_skills, stream_pairs, stream_doc_summaries,
                                       stream_doc_jobs, stream_unpacked_docs, get_spacy_target_files, add_extra,
                                       SpacyReader, time_this, MyPhraser, get_sub_docs, detect_phrases, STOPWORDS)
from nlp_process.spacy_process import (lang_detect, lookup_language_detection, apply_by_multiprocessing,
                                       store_language_detection)

config = ProcessConfig()

TOKEN_KEY_TYPE = 'lemma'
MIN_WORD_COUNT = 20
MAX_WORD_RATIO = 0.9
MIN_SKILL_COUNT = 25
MAX_SKILL_RATIO = 0.9
WINDOW_SIZE = 5
WORD_VEC_SIZE = 200
SKILL_VEC_SIZE = 100



def spacify_docs(output1=config.OUTPUT1, output2=config.OUTPUT2, prettify=False, ignore_existing=False, max_files=None):
    """

    :param output1: From output1 to output2
    :param output2:
    :param prettify: Indent JSON Files
    :param ignore_existing: Bool, if true exclude files found in output2
    :param max_files: Int, if none process all files. If int, process up to this number
    :return:
    """

    from spacy.tokens import Span
    from spacy.tokens import Doc
    from spacy.matcher import PhraseMatcher

    Doc.set_extension("phrase_spans", default=None)

    start_time = datetime.now()
    print("Loading spacy model")
    nlp = en_core_web_lg.load()
    print("Model loaded in {}".format(datetime.now() - start_time))

    with open(config.ANNOTATED_PHRASES, "r") as fp:
        phrases = fp.read().splitlines()
        print("{} Phrases Loaded".format(len(phrases)))

    phrases_nlp = [nlp(p) for p in phrases]
    matcher = PhraseMatcher(nlp.vocab, attr='NORM')
    matcher.add("Phrase", None, *phrases_nlp)

    def merge_ents(doc):
        with doc.retokenize() as retokenizer:
            for ent in doc.ents:
                ent_start, ent_end = ent.start, ent.end
                attrs = {
                    "tag":   ent.root.tag, "dep": ent.root.dep, "ent_type": ent.label,
                    'LEMMA': "_".join([x.lemma_ for x in doc[ent_start:ent_end]]),
                    'NORM':  "_".join([x.norm_ for x in doc[ent_start:ent_end]])
                    }
                retokenizer.merge(ent, attrs=attrs)
        return doc

    def mark_phrases(doc, matcher=matcher):
        doc._.phrase_spans = matcher(doc)
        return doc

    def merge_phrases(doc):
        if not doc._.phrase_spans:
            return doc
        with doc.retokenize() as retokenizer:
            for phrase in doc._.phrase_spans:
                _, phrase_start, phrase_end = phrase
                lemma_phrase = "_".join([x.lemma_ for x in doc[phrase_start:phrase_end]])
                norm_phrase = "_".join([x.norm_ for x in doc[phrase_start:phrase_end]])
                attr = {"LEMMA": lemma_phrase, "NORM": norm_phrase}
                try:
                    retokenizer.merge(doc[phrase_start:phrase_end], attrs=attr)
                except ValueError:
                    continue
        return doc

    nlp.add_pipe(merge_ents, last=True)
    nlp.add_pipe(mark_phrases, last=True)
    nlp.add_pipe(merge_phrases, last=True)

    output1_files = get_spacy_target_files(ignore_existing, output1, output2)
    print("Found {} docs".format(len(output1_files)))
    if max_files:
        output1_files = output1_files[:max_files]
    print("Processing {} docs".format(len(output1_files)))

    spacify_summaries(nlp, output1_files, output2, prettify)
    spacify_jobs(nlp, output1_files, output2, prettify)



def spacify_jobs(nlp, output1_files, output2, prettify, cache_size=1000):
    def append_jobs(cache, output_folder, prettify):  # Find or make files and add jobs
        for doc_id, jobs in cache.items():
            doc_fp = os.path.join(output_folder, "{}.json".format(doc_id))
            if os.path.isfile(doc_fp):
                with open(doc_fp, "r") as json_file:
                    doc_data = json.load(json_file)
            else:
                doc_data = {'member_id': doc_id, 'jobs': []}
            doc_data_jobs = doc_data.get('jobs', [])
            doc_data_jobs = list(filter(lambda x: isinstance(x, str) is False, doc_data_jobs))
            doc_data_jobs.extend(jobs)
            doc_data['jobs'] = doc_data_jobs
            with open(doc_fp, "w") as json_file:
                if prettify:
                    json.dump(doc_data, json_file, indent=4)
                else:
                    json.dump(doc_data, json_file)

    pb = tqdm(total=len(output1_files), desc='Processing Jobs')
    doc_stream = stream_docs(files=output1_files, data_key=None)
    job_stream = stream_doc_jobs(doc_stream)
    job_cache = {}
    for nlp_doc, doc_id in nlp.pipe(job_stream, batch_size=50, as_tuples=True):
        pb.update(1)
        doc_not_cached = doc_id not in job_cache
        if doc_not_cached and len(job_cache) >= cache_size:
            append_jobs(job_cache, output_folder=output2, prettify=prettify)
            job_cache = {}
        doc_jobs = job_cache.get(doc_id, [])
        nlp_doc_json = add_extra(nlp_doc)
        doc_jobs.append(nlp_doc_json)
        job_cache[doc_id] = doc_jobs

    append_jobs(job_cache, output_folder=output2, prettify=prettify)
    pb.close()



def spacify_summaries(nlp, output1_files, output2, prettify):
    doc_stream = stream_docs(files=output1_files, data_key=None)  # As dict
    doc_stream_unpacked = stream_unpacked_docs(doc_stream)

    # Want to keep additional data from doc
    data_stream, nlp_stream = itertools.tee(doc_stream_unpacked, 2)
    summary_stream = stream_doc_summaries(nlp_stream)

    pb = tqdm(total=len(output1_files), desc='Processing Summaries')

    for nlp_doc, doc_id in nlp.pipe(summary_stream, batch_size=50, as_tuples=True):
        nlp_doc_json = add_extra(nlp_doc)
        doc_data = data_stream.__next__()
        doc_data['text'] = nlp_doc_json
        out_f = os.path.join(output2, "{}.json".format(doc_id))
        with open(out_f, 'w+') as json_file:
            if prettify:
                json.dump(doc_data, json_file, indent=4)
            else:
                json.dump(doc_data, json_file)
        pb.update(1)

    pb.close()




@time_this
def preprocess_csv(corpus_fp, n_workers, output1=config.OUTPUT1, prettify_output=False):
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
    df = lookup_language_detection(df, config.LANGUAGE_ID)
    df['lang'] = apply_by_multiprocessing(df, lang_detect, axis=1, workers=n_workers)
    elapsed = datetime.now() - start
    print("Finished Language Detection in {}".format(elapsed))

    # dump a list of languages detected
    store_language_detection(df, config.LANGUAGE_ID)
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
def make_token_dictionary(folder=config.OUTPUT2):
    doc_reader = SpacyReader(folder=folder, data_key=get_sub_docs, token_key=TOKEN_KEY_TYPE)
    doc_stream = doc_reader.as_sentences()
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
def make_skills_dictionary(folder=config.OUTPUT2):
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
    doc_reader = SpacyReader(folder=folder, data_key=get_sub_docs, token_key=TOKEN_KEY_TYPE)
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
def get_token_probabilities(folder=config.OUTPUT2):
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
def get_skill_probabilities(folder=config.OUTPUT2):
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
def get_token_pair_probabilities(folder=config.OUTPUT2):
    doc_reader = SpacyReader(folder=folder, data_key=get_sub_docs, token_key=TOKEN_KEY_TYPE)
    # doc_phraser = MyPhraser()
    doc_stream = doc_reader.as_sentences()
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
def get_skill_pair_probabilities(folder=config.OUTPUT2):
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
def get_fingerprint_tokens(folder=config.OUTPUT2):
    cnt = TfidfVectorizer(use_idf=True, sublinear_tf=True)
    doc_reader = SpacyReader(folder=folder, data_key=get_sub_docs, token_key=TOKEN_KEY_TYPE)
    # doc_phraser = MyPhraser()
    doc_stream = doc_reader.as_sentences()

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

def dump_text(output, format='fasttext'):

    if format not in ['fasttext']:
        raise NotImplementedError

    doc_reader = SpacyReader(folder=config.OUTPUT2, data_key=get_sub_docs, token_key=TOKEN_KEY_TYPE)
    replace_datum = re.compile("datum", re.IGNORECASE)
    stream = doc_reader.as_sentences()
    with open(output, encoding="utf-8", mode="w+") as fp:
        for sentence_tokens in stream:
            if not sentence_tokens:
                continue
            sentence_line = " ".join(sentence_tokens)
            sentence_line = replace_datum.sub("data", sentence_line)
            fp.write(sentence_line)
            fp.write("\n")




if __name__ == "__main__":
    # CSV To JSON
    # Remove Null Records
    # Remove Non-English Records

    # preprocess_csv(corpus_fp=config.CORPUS_FILE, n_workers=8)

    # # Tokenize JSON records
    spacify_docs(ignore_existing=False, max_files=None)
    # #
    # # # Train the phraser from JSON records
    # detect_phrases(input_dir=config.OUTPUT2, phrase_model_fp=config.PHRASE_MODEL,
    #                phrase_dump_fp=config.PHRASE_DUMP,
    #                common_words=STOPWORDS, min_count=10, threshold=30, token_key=TOKEN_KEY_TYPE)
    # make_token_dictionary()
    # make_skills_dictionary()
    # get_pmi_tokens()
    # get_pmi_skills()
    # get_fingerprint_tokens()
    dump_text("/home/eric/PycharmProjects/Percy/mysite/nlp_process/data/corpus/sent_corpus.txt")
