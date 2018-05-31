import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = True
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
    UPLOAD_FOLDER = os.path.join(basedir, 'resources/uploads')
    SECRET_KEY = 'never-guess-this'


class FConfig(object):
    model = os.path.join(basedir, 'resources{}indeed_model_wrapper'.format(os.path.sep))
    gram_path = os.path.join(basedir, 'resources{}trigram_model.p'.format(os.path.sep))
    tree = os.path.join(basedir, 'resources{}tree_classifier.pickle'.format(os.path.sep))
    name_dict = os.path.join(basedir, 'resources{}name_dict.pickle'.format(os.path.sep))
    global_name_dict = os.path.join(basedir, 'resources{}global_name_dict.pickle'.format(os.path.sep))
    name_file_path = os.path.join(basedir, 'resources{}name_list.csv'.format(os.path.sep))
    raw_dict = os.path.join(basedir, 'resources{}tfidf_dict.dict'.format(os.path.sep))
    tfidf_model = os.path.join(basedir, 'resources{}tfidf.model'.format(os.path.sep))
    bigram_dict_path = os.path.join(basedir, 'resources{}bigram_tfidf_dict.dict'.format(os.path.sep))
    bigram_tfidf_model_path = os.path.join(basedir, 'resources{}bigram_tfidf.model'.format(os.path.sep))
    lem_dict_path = os.path.join(basedir, 'resources{}l_dictionary.dict'.format(os.path.sep))
    lem_tfidf_model_path = os.path.join(basedir, 'resources{}l_tfidf.model'.format(os.path.sep))
    lg_dict_path = os.path.join(basedir, 'resources{}lg_dictionary.dict'.format(os.path.sep))
    lg_tfidf_model_path = os.path.join(basedir, 'resources{}lg_tfidf.model'.format(os.path.sep))
    key_path = os.path.join(basedir, 'resources{}bot_key.pkl'.format(os.path.sep))
    message_api = "https://api.ciscospark.com/v1/messages/{}"

