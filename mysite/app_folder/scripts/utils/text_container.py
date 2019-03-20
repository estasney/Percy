class Document(object):

    def __init__(self, raw: str):
        self.raw = raw
        self.sentences = []


class Sentence(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.phrases_ = []

    @property
    def phrases(self):
        if not self.phrases_:
            return self.tokens
        return self.phrases_


class Token(object):

    def __init__(self, token):
        self.token = token
        self.norm = None
        self.is_ignored = False

