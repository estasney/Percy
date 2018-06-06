from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from gensim.models.doc2vec import Doc2Vec
from gensim.models.wrappers.fasttext import FastText as FT_wrapper
from app_folder.site_config import Config, FConfig
import gensim
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from time import time
from chatterbot import ChatBot

chatbot = ChatBot("Percy", storage_adapter="chatterbot.storage.SQLStorageAdapter")
from chatterbot.trainers import ChatterBotCorpusTrainer
chatbot.set_trainer(ChatterBotCorpusTrainer)
print("Training Chatbot")
b = time()
chatbot.train(
    "chatterbot.corpus.english",
)
a = time()
print("Finished Training Chatbot in {}".format(a-b))

toolbar = DebugToolbarExtension()
b = time()
model = FT_wrapper.load(FConfig.model)
a = time()
print("Model Loaded in {}".format(a-b))
tfidf_model = TfidfModel.load(FConfig.tfidf_model)
print("TFIDF Loaded")
dictionary = Dictionary.load(FConfig.raw_dict)
print("Dictionary Loaded")
bigram_tfidf_model = TfidfModel.load(FConfig.bigram_tfidf_model_path)
print("Bigram TFIDF Loaded")
bigram_dictionary = Dictionary.load(FConfig.bigram_dict_path)
print("Bigram Dictionary Loaded")
lems_tfidf_model = TfidfModel.load(FConfig.lem_tfidf_model_path)
print("Lemmatized TFIDF Loaded")
lems_dictionary = Dictionary.load(FConfig.lem_dict_path)
print("Lemmatized Dictionary Loaded")
lg_tfidf_model = TfidfModel.load(FConfig.lg_tfidf_model_path)
print("Lemmatized, Bigrammed Model Loaded")
lg_dictionary = Dictionary.load(FConfig.lg_dict_path)
print("Lemmatized, Bigrammed Dictionary Loaded")
b = time()
bigram = gensim.models.phrases.Phraser.load(FConfig.gram_path)
a = time()
print("Bigrammer Loaded In {}".format(a-b))


def create_app(config_class=Config):
    app_run = Flask(__name__)
    app_run.config.from_object(config_class)
    toolbar.init_app(app_run)

    from app_folder.main import bp as main_bp
    app_run.register_blueprint(main_bp)

    from app_folder.api import bp as api_bp
    app_run.register_blueprint(api_bp, url_prefix='/api/v1')
    return app_run
