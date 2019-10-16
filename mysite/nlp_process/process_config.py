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
        self.ANNOTATED_PHRASES = self.smart_path(self.PHRASE_FOLDER, 'annotated_phrases.txt')
        self.PHRASE_DUMP = self.smart_path(self.PHRASE_FOLDER, 'phrase_dump.txt')
        self.PHRASE_MODEL = self.smart_path(self.PHRASE_FOLDER, 'phrases.model')

        self.OUTPUT1 = self.smart_path(self.DATA_FOLDER, 'output1')
        self.OUTPUT2 = self.smart_path(self.DATA_FOLDER, 'output2')
        self.RESOURCES = self.smart_path(self.DATA_FOLDER, 'resources')
        self.RESOURCES_DICTIONARY_TOKENS = self.smart_path(self.RESOURCES, 'dictionary_tokens.model')
        self.RESOURCES_AUTOCOMPLETE_TOKENS = self.smart_path(self.RESOURCES, 'dictionary_autocomplete_tokens.txt')
        self.RESOURCES_DICTIONARY_SKILLS = self.smart_path(self.RESOURCES, 'dictionary_skills.model')
        self.RESOURCES_AUTOCOMPLETE_SKILLS = self.smart_path(self.RESOURCES,
                                                                        'dictionary_autocomplete_skills.txt')
        self.RESOURCES_CX_TOKENS = self.smart_path(self.RESOURCES, 'cx_tokens.pkl')
        self.RESOURCES_CXP_TOKENS = self.smart_path(self.RESOURCES, 'cxp_tokens.pkl')
        self.RESOURCES_CXY_TOKENS = self.smart_path(self.RESOURCES, 'cxy_tokens.pkl')
        self.RESOURCES_CXYP_TOKENS = self.smart_path(self.RESOURCES, 'cxyp_tokens.pkl')

        self.RESOURCES_LDA_PMI_TOKENS = self.smart_path(self.RESOURCES, 'lda_pmi_tokens.npy')
        self.RESOURCES_LDA_PMI_SKILLS = self.smart_path(self.RESOURCES, 'lda_pmi_skills.npy')

        self.RESOURCES_CX_SKILLS = self.smart_path(self.RESOURCES, 'cx_skills.pkl')
        self.RESOURCES_CXP_SKILLS = self.smart_path(self.RESOURCES, 'cxp_skills.pkl')
        self.RESOURCES_CXY_SKILLS = self.smart_path(self.RESOURCES, 'cxy_skills.pkl')
        self.RESOURCES_CXYP_SKILLS = self.smart_path(self.RESOURCES, 'cxyp_skills.pkl')

        self.RESOURCES_FINGERPRINT_TOKENS = self.smart_path(self.RESOURCES, 'fingerprint_tokens.npy')
        self.RESOURCES_FINGERPRINT_VEC_TOKENS = self.smart_path(self.RESOURCES, 'fingerprint_tokens_vec.pkl')

        self.CORPUS_FILE = self.smart_path(self.DATA_FOLDER, 'corpus', 'corpus.csv')
        self.CORPUS_FILE_2 = self.smart_path(self.DATA_FOLDER, 'corpus', 'corpus2.csv')

        self.N_WORKERS = 4


    def smart_path(self, *args):
        start_path = self.BASE_DIR
        for a in args:
            start_path = os.path.join(start_path, a)
        return start_path



if __name__ == "__main__":
    import re
    path_finder = re.compile(r"(?:/[A-z0-9]+)+|(?<=[A-z]:)(\\[A-z0-9]+)")
    ext_finder = re.compile(r"(\.[a-z]{2,4})")
    p = ProcessConfig()
    for attribute, value in p.__dict__.items():
        if attribute.isupper():
            print(attribute, value)

    for attribute, value in p.__dict__.items():
        if not isinstance(value, str):
            continue
        is_path_like = path_finder.search(value)
        if not is_path_like:
            continue
        is_dir = ext_finder.search(value) is None
        if not is_dir:
            continue
        dir_exists = os.path.isdir(value)
        if not dir_exists:
            print("Mkdir : {}".format(attribute))
            os.mkdir(value)
