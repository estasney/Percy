import spacy
from typing import Callable


class SpacyDocPiper(object):
    """

    Wrapper that handles and preseves JSON documents

    """

    def __init__(self, nlp, doc_keys: list, doc_func: Callable):
        self.nlp_ = nlp
        self.doc_keys = set(doc_keys)
        self.doc_func = doc_func if doc_func else lambda x: x
        self.is_truthy = lambda x: True if x else False

    def pipe(self, doc: dict):
        output_doc = {k: v for k, v in doc.items() if
                      k not in self.doc_keys}  # Keep data here that will not be processed
        for doc_key in self.doc_keys:
            doc_text_output = []
            doc_texts = doc[doc_key]
            doc_texts = list(filter(self.is_truthy, doc_texts))
            for text in self.nlp_.pipe(doc_texts, batch_size=50):
                doc_text_output.append(self.doc_func(text))
            output_doc[doc_key] = doc_text_output
        return output_doc
