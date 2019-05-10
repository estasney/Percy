import glob
import json
from gensim.corpora.dictionary import Dictionary

fp = r"/home/eric/PycharmProjects/Percy/mysite/app_folder/scripts/tmp/output/*.json"


class Streamer(object):

    def __init__(self, fp, data_key):
        self.files = glob.glob(fp)
        self.data_key = data_key

    def __iter__(self):
        for file in self.files:
            with open(file, 'r') as json_file:
                doc = json.load(json_file)

            if isinstance(self.data_key, list):
                doc = [doc[k] for k in self.data_key]
                for sub_doc in doc:
                    for sentence in sub_doc:
                        yield sentence
            else:
                doc = doc[self.data_key]
                for sentence in doc:
                    yield sentence

    def __getitem__(self, item):
        file = self.files[item]
        with open(file, 'r') as json_file:
            doc = json.load(json_file)

        if isinstance(self.data_key, list):
            doc = [doc[k] for k in self.data_key]
            return doc

        else:
            doc = doc[self.data_key]
            return doc

