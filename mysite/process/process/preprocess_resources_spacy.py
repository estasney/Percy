import glob
import json
import en_core_web_md
from process.process.utils import stream_docs, add_extra, process_phrase_tokens, MyPhraser
from datetime import datetime
from process import ProcessConfig

config = ProcessConfig()

INPUT_FOLDER = config.OUTPUT1
OUTPUT_FOLDER = config.OUTPUT2

files = glob.glob(INPUT_FOLDER)


def preprocess_docs(files):
    start_time = datetime.now()
    print("Loading spacy model")
    nlp = en_core_web_md.load()
    print("Model loaded")
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
    print("Running docs through spacy")
    # preprocess_docs()
    # print("Running docs through phraser")
    # phrase_docs()
