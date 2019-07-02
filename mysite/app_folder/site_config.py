import os
import pickle

basedir = os.path.abspath(os.path.dirname(__file__))


def load_p(fn):
    with open(fn, "rb") as pfile:
        p = pickle.load(pfile)
    return p


class Config(object):
    DEBUG = True
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
    UPLOAD_FOLDER = os.path.join(basedir, 'resources{}uploads').format(os.path.sep)
    SECRET_KEY = 'never-guess-this'
    SQLALCHEMY_DATABASE_URI = 'mysql://estasney:password@localhost:3306/names_db?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_POOL_RECYCLE = 299



class FConfig(object):
    STATIC_VERSION_ID = 1  # Increment to force loading cached static files

    def __init__(self, base_dir=basedir):
        self.BASE_DIR = base_dir
        self.RESOURCES = self.smart_path("resources")

        self.LDA_PMI_TOKENS = self.smart_path(self.RESOURCES, "lda_pmi_tokens.npy")
        self.LDA_PMI_SKILLS = self.smart_path(self.RESOURCES, "lda_pmi_skills.npy")

        self.DICTIONARY_TOKENS = self.smart_path(self.RESOURCES, "dictionary_tokens.model")
        self.DICTIONARY_SKILLS = self.smart_path(self.RESOURCES, "dictionary_skills.model")

        self.AUTOCOMPLETE_TOKENS = self.smart_path(self.RESOURCES, "dictionary_autocomplete_tokens.txt")
        self.AUTOCOMPLETE_SKILLS = self.smart_path(self.RESOURCES, "dictionary_autocomplete_skills.txt")

        self.PHRASE_MODEL = self.smart_path(self.RESOURCES, "phrases.model")

        self.FINGERPRINT_TOKENS = self.smart_path(self.RESOURCES, "fingerprint_tokens.npy")
        self.FINGERPRINT_SKILLS = self.smart_path(self.RESOURCES, "fingerprint_skills.npy")
        self.FINGERPRINT_TOKENS_VEC = self.smart_path(self.RESOURCES, "fingerprint_tokens_vec.pkl")

        self.NAMESEARCH = self.smart_path(self.RESOURCES, "namesearch.pkl")
        self.NAMESEARCH_V2 = self.smart_path(self.RESOURCES, "namesearch_6_11_2019.pkl")

        self.JOB_TITLE_SYNONYMS_FP = self.smart_path(self.RESOURCES, 'my_title_synonyms.json')
        self.JOB_TITLE_SYNONYMS2_FP = self.smart_path(self.RESOURCES, 'synonym_job_titles_for_search.json')

        self.BETA_PARAMS = self.smart_path(self.RESOURCES, 'beta_params.npy')

        self.BOT_KEY = load_p(self.smart_path(self.RESOURCES, "bot_key.pkl"))
        self.BOT_ROOM_ID = load_p(self.smart_path(self.RESOURCES, "bot_room_id.pkl"))
        self.MESSAGE_API_F = "https://api.ciscospark.com/v1/messages/{}"
        self.MESSAGE_API = "https://api.ciscospark.com/v1/messages"
        self.PERSON_DETAILS_API_F = "https://api.ciscospark.com/v1/people/{}"
        self.PERSON_DETAILS = "https://api.ciscospark.com/v1/people"

    def smart_path(self, *args):
        start_path = self.BASE_DIR
        for a in args:
            start_path = os.path.join(start_path, a)
        return start_path
