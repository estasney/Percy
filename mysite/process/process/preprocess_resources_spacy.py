import json
import glob
import os
import pandas as pd
from datetime import datetime

import en_core_web_lg

from process import ProcessConfig
from process.process.spacy_process.streaming import stream_docs
from process.process.spacy_process.spacy_utils import add_extra, STOPWORDS
from process.process.spacy_process.spacy_phrases import detect_phrases
from process.process.spacy_process.lang import lang_detect, lookup_language_detection, apply_by_multiprocessing,\
    store_language_detection


config = ProcessConfig()

OUTPUT1 = config.OUTPUT1
OUTPUT2 = config.OUTPUT2

LANG_FILE = config.LANGUAGE_ID

PHRASE_MODEL_FP = config.PHRASE_MODEL
PHRASE_DUMP_FP = config.PHRASE_DUMP
CORPUS_FP = config.CORPUS_FILE
N_WORKERS = config.N_WORKERS


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

    doc_stream = stream_docs(files=output1_files, data_key='summary')
    for i, doc in enumerate(nlp.pipe(doc_stream, batch_size=50)):  # streams in original order
        json_doc = add_extra(doc)
        out_f = os.path.join(output2, file_names[i])
        with open(out_f, 'w+') as json_file:
            if prettify:
                json.dump(json_doc, json_file, indent=4)
            else:
                json.dump(json_doc, json_file)
        if i % 1000 == 0:
            elapsed = datetime.now() - start_time
            print("Now on {} after {} elapsed".format(i, elapsed))


def preprocess_csv(corpus_fp, n_workers, output1=OUTPUT1, prettify_output=False):
    print("Filtering CSV")
    df = pd.read_csv(corpus_fp)
    original_count = len(df)
    df.dropna(subset=['summary'], inplace=True)

    print("Dropped {} Null Records from Summary".format(original_count - len(df)))
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
    start_time = datetime.now()
    export_df(df, prettify_output, output1)
    print("Finished Exporting DataFrame in {}".format(datetime.now() - start_time))


if __name__ == "__main__":

    # CSV To JSON
    # Remove Null Records
    # Remove Non-English Records

    # preprocess_csv(corpus_fp=CORPUS_FP, n_workers=N_WORKERS)

    # Tokenize JSON records
    # spacify_docs()

    # Train the phraser from JSON records
    detect_phrases(input_dir=OUTPUT2, phrase_model_fp=PHRASE_MODEL_FP, phrase_dump_fp=PHRASE_DUMP_FP,
                   common_words=STOPWORDS, min_count=10, threshold=30)
