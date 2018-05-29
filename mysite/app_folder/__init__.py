from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from gensim.models.doc2vec import Doc2Vec
from app_folder.site_config import Config, FConfig
import gensim
from gensim.corpora import Dictionary
from gensim.models import TfidfModel


toolbar = DebugToolbarExtension()

model = Doc2Vec.load(FConfig.model)
tfidf_model = TfidfModel.load(FConfig.tfidf_model)
dictionary = Dictionary.load(FConfig.raw_dict)
bigram_tfidf_model = TfidfModel.load(FConfig.bigram_tfidf_model_path)
bigram_dictionary = Dictionary.load(FConfig.bigram_dict_path)
lems_tfidf_model = TfidfModel.load(FConfig.lem_tfidf_model_path)
lems_dictionary = Dictionary.load(FConfig.lem_dict_path)
lg_tfidf_model = TfidfModel.load(FConfig.lg_tfidf_model_path)
lg_dictionary = Dictionary.load(FConfig.lg_dict_path)
bigram = gensim.models.phrases.Phraser(gensim.models.Phrases.load(FConfig.gram_path))

def create_app(config_class=Config):
    app_run = Flask(__name__)
    app_run.config.from_object(config_class)
    toolbar.init_app(app_run)

    from app_folder.main import bp as main_bp
    app_run.register_blueprint(main_bp)
    return app_run
