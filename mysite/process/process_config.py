import os
basedir = os.path.normpath(os.path.dirname(__file__))  # ./process


class ProcessConfig(object):

    def __init__(self, base_dir=basedir):
        self.BASE_DIR = base_dir
        self.DATA_FOLDER = self.smart_path('data')
        self.LANGUAGE_FOLDER = self.smart_path('data', 'language')
        self.LANGUAGE_ID = self.smart_path(self.LANGUAGE_FOLDER, 'lang_id.json')
        self.PHRASE_FOLDER = self.smart_path('data', 'phrases')
        self.PHRASE_EXCLUDED = self.smart_path(self.PHRASE_FOLDER, 'excluded.txt')
        self.PHRASE_INCLUDED = self.smart_path(self.PHRASE_FOLDER, 'included.txt')
        self.PHRASE_DUMP = self.smart_path(self.PHRASE_FOLDER, 'phrase_dump.txt')
        self.PHRASE_MODEL = self.smart_path(self.PHRASE_FOLDER, 'phrases.model')

        self.OUTPUT1 = self.smart_path(self.DATA_FOLDER, 'output1')
        self.OUTPUT2 = self.smart_path(self.DATA_FOLDER, 'output2')

    def smart_path(self, *args):
        start_path = self.BASE_DIR
        for a in args:
            start_path = os.path.join(start_path, a)
        return start_path



if __name__ == "__main__":
    p = ProcessConfig()
    for attribute, value in p.__dict__.items():
        if attribute.isupper():
            print(attribute, value)