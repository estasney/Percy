import os
basedir = os.path.abspath(os.path.dirname(__file__))


class FConfig(object):
    model = os.path.join(basedir, 'app_folder/mymodel.model')
    gram_path = os.path.join(basedir, 'app_folder/trigram_model.p')
    tree = os.path.join(basedir, 'app_folder/tree_classifier.pickle')
    name_dict = os.path.join(basedir, 'app_folder/name_dict.pickle')
    global_name_dict = os.path.join(basedir, 'app_folder/global_name_dict.pickle')
    name_file_path = os.path.join(basedir, 'app_folder/name_list.csv')
    raw_dict = os.path.join(basedir, 'app_folder/tfidf_dict.dict')
    tfidf_model = os.path.join(basedir, 'app_folder/tfidf.model')
    bigram_dict_path = os.path.join(basedir, 'app_folder/bigram_tfidf_dict.dict')
    bigram_tfidf_model_path = os.path.join(basedir, 'app_folder/bigram_tfidf.model')
    lem_dict_path = os.path.join(basedir, 'app_folder/l_dictionary.dict')
    lem_tfidf_model_path = os.path.join(basedir, 'app_folder/l_tfidf.model')
    lg_dict_path = os.path.join(basedir, 'app_folder/lg_dictionary.dict')
    lg_tfidf_model_path = os.path.join(basedir, 'app_folder/lg_tfidf.model')
    UPLOAD_FOLDER = os.path.join(basedir, 'app_folder/uploads')










