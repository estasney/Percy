import glob
import json
import en_core_web_md
from process.process.utils import stream_docs, add_extra, process_phrase_tokens, MyPhraser
from datetime import datetime
from process import ProcessConfig

config = ProcessConfig()

INPUT_FOLDER = config.OUTPUT1
OUTPUT_FOLDER = config.OUTPUT2


def preprocess_docs(input_files, output_folder, prettify=True):

    """

    :param files: From output1 to output2
    :param prettify:
    :return:
    """

    start_time = datetime.now()
    print("Loading spacy model")
    nlp = en_core_web_md.load()
    print("Model loaded")
    doc_stream = stream_docs(files=input_files, data_key='summary')
    for i, doc in enumerate(nlp.pipe(doc_stream, batch_size=50)):
        json_doc = add_extra(doc)
        out_f = "{}\{}.json".format(output_folder, i)
        with open(out_f, 'w+') as json_file:
            if prettify:
                json.dump(json_doc, json_file, indent=4)
            else:
                json.dump(json_doc, json_file)
        if i % 1000 == 0:
            elapsed = datetime.now() - start_time
            print("Now on {} after {} elapsed".format(i, elapsed))


def phrase_docs(target_folder):
    start_time = datetime.now()
    phraser = MyPhraser()
    target_files_pattern = "{}\*.json".format(target_folder)
    target_files = glob.glob(target_files_pattern)
    process_phrase_tokens(target_files, phraser)
    elapsed = datetime.now() - start_time
    print(elapsed)


if __name__ == "__main__":
    print("Running docs through spacy")
    files = glob.glob("{}\*.json".format(INPUT_FOLDER))
    preprocess_docs(files, OUTPUT_FOLDER)
    print("Running docs through phraser")
    phrase_docs(OUTPUT_FOLDER)
