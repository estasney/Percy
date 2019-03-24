import glob
import os
import json


"""

Streaming

"""


class DocStreamer(object):

    def __init__(self, d, text_key='token_summary'):
        self.dir = d
        self.files = glob.glob(os.path.join(self.dir, "*.json"))
        self.text_key = text_key

    def load_json_(self, f):
        with open(f, 'r') as json_file:
            return json.load(json_file)[self.text_key]

    def __getitem__(self, i):
        file = self.files[i]
        doc = self.load_json_(file)
        return doc

    def __iter__(self):
        for file in self.files:
            doc = self.load_json_(file)
            for sentence in doc:
                if sentence:
                    yield sentence


def stream_tokens(files):
    for f in files:
        with open(f, 'r') as json_file:
            doc = json.load(json_file)
        sentences = doc['clean_summary']
        for sentence in sentences:
            yield sentence