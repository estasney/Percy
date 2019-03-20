from utils.files import make_tmp_dirs, fetch_tmp_files
from words.lang import lang_detect, lookup_language_detection, apply_by_multiprocessing, store_language_detection
from words.process import pool_process_text, STOPWORDS
from words.phrases import detect_phrases
from datetime import datetime
import os
import pandas as pd
import json
import sys

sys.path.append(r"/home/eric/PycharmProjects/Percy/mysite")



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
WORKERS = 8
MIN_WORD_COUNT = 10
MAX_WORD_RATIO = 0.9
MIN_SKILL_COUNT = 25
MAX_SKILL_RATIO = 0.9
TMP_DIR = "/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp"
TMP_DIR_RAW = os.path.join(TMP_DIR, "raw")
TMP_DIR_SENT = os.path.join(TMP_DIR, "sent")
TMP_DIR_PHRASES = os.path.join(TMP_DIR, "phrases")
LANG_FILE = "/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/lang/lang_id.json"

"""

SETUP

"""
d_list = [TMP_DIR, TMP_DIR_SENT, TMP_DIR_RAW]
script_start = datetime.now()

"""

Words

"""


def export_df(df, dir_out=TMP_DIR_RAW):
    for i, row in df.iterrows():
        file_name = "{}.json".format(row['member_id'])
        file_name = os.path.join(dir_out, file_name)
        with open(file_name, "w+") as jfile:
            json.dump(row.to_dict(), jfile)

# files = glob.glob(os.path.join(TMP_DIR_SENT, "*.json"))

if __name__ == "__main__":
    make_tmp_dirs(d_list)

    df = pd.read_csv(r"/home/eric/PycharmProjects/FlaskAPI/scripts2/corpus.csv")
    df.dropna(subset=['summary'], inplace=True)
    original_count = len(df)
    df.fillna("", inplace=True)
    start = datetime.now()

    print("Starting Resource Update")
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

    pool_process_text(TMP_DIR_RAW, WORKERS, TMP_DIR_SENT)
    elapsed = datetime.now() - start
    print("Finished Preprocessing in {}".format(elapsed.seconds))

    # Phrases
    print("Detecting Phrases")
    start = datetime.now()
    detect_phrases(tmp_dir_sent=TMP_DIR_SENT, tmp_dir_phrases=TMP_DIR_PHRASES, common_words=STOPWORDS, min_count=100,
                   threshold=30)
    elapsed = datetime.now() - start
    print("Finished Phrase Detection in {}".format(elapsed.seconds))


