import glob
import en_core_web_md
import json
from mysite.app_folder.scripts.utils.streaming import stream_docs, add_extra
from mysite.app_folder.scripts.utils.spacy_utils import process_phrase_tokens
from mysite.app_folder.scripts.utils.spacy_phrases import MyPhraser
from datetime import datetime

INPUT_FOLDER = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/output/*.json"
OUTPUT_FOLDER = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/output2/{}.json"

# nlp = en_core_web_md.load()

files = glob.glob(INPUT_FOLDER)


def preprocess_docs():
    start_time = datetime.now()
    doc_stream = stream_docs(files=files, data_key='summary')
    for i, doc in enumerate(nlp.pipe(doc_stream, batch_size=50)):
        json_doc = add_extra(doc)
        out_f = OUTPUT_FOLDER.format(i)
        with open(out_f, 'w+') as json_file:
            json.dump(json_doc, json_file)
        if i % 1000 == 0:
            elapsed = (datetime.now() - start_time).seconds
            elapsed_minutes = elapsed // 60
            print("Now on {} after {} minutes".format(i, elapsed_minutes))

def phrase_docs():
    start_time = datetime.now()
    phraser = MyPhraser()
    target_files = glob.glob(OUTPUT_FOLDER.format("*"))
    process_phrase_tokens(target_files, phraser)
    elapsed = datetime.now() - start_time
    print(elapsed)

if __name__ == "__main__":
    # print("Running docs through spacy")
    # preprocess_docs()
    print("Running docs through phraser")
    phrase_docs()
