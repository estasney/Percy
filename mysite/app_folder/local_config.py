import os

cwd = os.getcwd()

resource_path = r'mysite/app_folder/resources'

rp = os.path.join(cwd, resource_path)


class Config(object):
    model = os.path.join(rp, 'mymodel.model')
    gram_path = os.path.join(rp, 'trigram_model.p')
    tree = os.path.join(rp, 'tree_classifier.pickle')
    name_dict = os.path.join(rp, 'name_dict.pickle')
    global_name_dict = os.path.join(rp, 'global_name_dict.pickle')
    name_file_path = os.path.join(rp, 'name_list.csv')
    raw_dict = os.path.join(rp, 'tfidf_dict.dict')
    tfidf_model = os.path.join(rp, 'tfidf.model')
    bigram_dict_path = os.path.join(rp, 'bigram_tfidf_dict.dict')
    bigram_tfidf_model_path = os.path.join(rp, 'bigram_tfidf.model')
    lem_dict_path = os.path.join(rp, 'l_dictionary.dict')
    lem_tfidf_model_path = os.path.join(rp, 'l_tfidf.model')
    lg_dict_path = os.path.join(rp, 'lg_dictionary.dict')
    lg_tfidf_model_path = os.path.join(rp, 'lg_tfidf.model')
    UPLOAD_FOLDER = os.path.join(cwd, r'mysite\uploads')
    dupcheck_version = '0.1.1'
    debug = False
    secret_key = 'its-a-secret'
    profiler = False




