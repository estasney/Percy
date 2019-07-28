import json
import os
import sys
from datetime import datetime

import pandas as pd
from nlp_process.process.legacy.lang import lang_detect, lookup_language_detection, apply_by_multiprocessing, \
    store_language_detection

from nlp_process.process.legacy.process import pool_process_text, STOPWORDS
from nlp_process.process.legacy.phrases import detect_phrases

from nlp_process.process_config import ProcessConfig

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


config = ProcessConfig()
LANG_FILE = config.LANGUAGE_ID
CORPUS_FILE = r"/home/eric/PycharmProjects/FlaskAPI/scripts2/corpus.csv"
TMP_DIR_OUTPUT = config.OUTPUT1
TMP_DIR_PHRASES = config.PHRASE_FOLDER


"""

SETUP

"""
script_start = datetime.now()

"""

Words

"""


def export_df(df, prettify=True, dir_out=TMP_DIR_OUTPUT):
    for i, row in df.iterrows():
        file_name = "{}.json".format(row['member_id'])
        file_name = os.path.join(dir_out, file_name)
        with open(file_name, "w+") as jfile:
            if prettify:
                json.dump(row.to_dict(), jfile, indent=4)
            else:
                json.dump(row.to_dict(), jfile)


if __name__ == "__main__":
    print("Starting Resource Update")
    df = pd.read_csv(CORPUS_FILE)
    original_count = len(df)
    df.dropna(subset=['summary'], inplace=True)

    print("Dropped {} Null Records from Summary".format(original_count - len(df)))
    original_count = len(df)
    df.fillna("", inplace=True)
    start = datetime.now()

    print("Starting Language Detection")

    # merge in lookups if they exist
    df = lookup_language_detection(df, LANG_FILE)
    df['lang'] = apply_by_multiprocessing(df, lang_detect, axis=1, workers=WORKERS)
    elapsed = datetime.now() - start
    print("Finished Language Detection in {}".format(elapsed.seconds))

    # dump a list of languages detected
    store_language_detection(df, LANG_FILE)
    df = df.loc[df['lang'] == 'en']
    print("Corpus loaded with {} records".format(original_count))
    print("Dropping {} non english records".format(original_count - len(df)))
    del df['lang']

    print("Dumping DF to JSON")
    export_df(df)


    print("Preprocessing Text into Sentences")
    start = datetime.now()

    pool_process_text(TMP_DIR_OUTPUT, WORKERS)
    elapsed = datetime.now() - start
    print("Finished Preprocessing in {}".format(elapsed.seconds))

    # Phrases
    print("Detecting Phrases")
    start = datetime.now()
    detect_phrases(tmp_dir_sent=TMP_DIR_OUTPUT, tmp_dir_phrases=TMP_DIR_PHRASES, common_words=STOPWORDS, min_count=100,
                   threshold=30, max_layers=2)
    elapsed = datetime.now() - start
    print("Finished Phrase Detection in {}".format(elapsed.seconds))

    # print("Phrasing Docs")
    # start = datetime.now()
    # phrase_docs(TMP_DIR_OUTPUT)
    # elapsed = datetime.now() - start
    # print("Finished Phrasing Docs in {}".format(elapsed.seconds))




