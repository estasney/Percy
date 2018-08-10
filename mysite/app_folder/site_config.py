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
    PHRASER = os.path.join(basedir, 'resources{}phraser.model'.format(os.path.sep))
    message_api_f = "https://api.ciscospark.com/v1/messages/{}"
    message_api = "https://api.ciscospark.com/v1/messages"
    person_details_api_f = "https://api.ciscospark.com/v1/people/{}"
    person_details = "https://api.ciscospark.com/v1/people"




