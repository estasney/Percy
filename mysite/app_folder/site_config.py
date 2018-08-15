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
    UPLOAD_FOLDER = os.path.join(basedir, 'resources/uploads')
    SECRET_KEY = 'never-guess-this'


class FConfig(object):
    lda_pmi = os.path.join(basedir, 'resources{}lda_pmi.npy').format(os.path.sep)
    dictionary = os.path.join(basedir, 'resources{}dictionary.model').format(os.path.sep)
    dictionary_autocomplete = os.path.join(basedir, 'resources{}dictionary_autocomplete.txt').format(os.path.sep)

    lda_pmi_skills = os.path.join(basedir, 'resources{}lda_pmi_skills.npy').format(os.path.sep)
    dictionary_skills = os.path.join(basedir, 'resources{}dictionary_skills.model').format(os.path.sep)
    dictionary_skills_autocomplete = os.path.join(basedir, 'resources{}dictionary_skills_autocomplete.txt').format(os.path.sep)

    phraser = os.path.join(basedir, 'resources{}phrases.model').format(os.path.sep)
    fingerprint_vec = os.path.join(basedir, 'resources{}fingerprint_vec.pkl').format(os.path.sep)
    fingerprint_pop_occ = os.path.join(basedir, 'resources{}fingerprint_pop_occ.npy').format(os.path.sep)

    namesearch = os.path.join(basedir, 'resources{}namesearch.pkl').format(os.path.sep)

    bot_key = load_p(os.path.join(basedir, 'resources{}bot_key.pkl'.format(os.path.sep)))
    bot_room_id = load_p(os.path.join(basedir, 'resources{}bot_room_id.pkl'.format(os.path.sep)))
    message_api_f = "https://api.ciscospark.com/v1/messages/{}"
    message_api = "https://api.ciscospark.com/v1/messages"
    person_details_api_f = "https://api.ciscospark.com/v1/people/{}"
    person_details = "https://api.ciscospark.com/v1/people"



