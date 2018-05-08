import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = True
    UPLOAD_FOLDER = os.path.join(basedir, 'resources/uploads')
    SECRET_KEY = 'never-guess-this'


class FConfig(object):
    model = os.path.join(basedir, 'resources/mymodel.model')
    gram_path = os.path.join(basedir, 'resources/trigram_model.p')
    tree = os.path.join(basedir, 'resources/tree_classifier.pickle')
    name_dict = os.path.join(basedir, 'resources/name_dict.pickle')
    global_name_dict = os.path.join(basedir, 'resources/global_name_dict.pickle')
    name_file_path = os.path.join(basedir, 'resources/name_list.csv')
    raw_dict = os.path.join(basedir, 'resources/tfidf_dict.dict')
    tfidf_model = os.path.join(basedir, 'resources/tfidf.model')
    bigram_dict_path = os.path.join(basedir, 'resources/bigram_tfidf_dict.dict')
    bigram_tfidf_model_path = os.path.join(basedir, 'resources/bigram_tfidf.model')
    lem_dict_path = os.path.join(basedir, 'resources/l_dictionary.dict')
    lem_tfidf_model_path = os.path.join(basedir, 'resources/l_tfidf.model')
    lg_dict_path = os.path.join(basedir, 'resources/lg_dictionary.dict')
    lg_tfidf_model_path = os.path.join(basedir, 'resources/lg_tfidf.model')

