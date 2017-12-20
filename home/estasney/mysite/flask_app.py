import pickle
import re
from flask import Flask, render_template, request, jsonify
from gensim.models import Doc2Vec, TfidfModel
from gensim.corpora import Dictionary

from nltk.tokenize import sent_tokenize
from werkzeug.utils import secure_filename
from home.estasney.mysite.modules import text_tools
from home.estasney.mysite.modules import diversity_tools
from home.estasney.mysite.modules import upload_tools
from home.estasney.mysite.modules import neural_tools


""" LOAD CONFIG """

try:
    from home.estasney.mysite.config import local_config as config
except ImportError:
    from home.estasney.mysite.config import web_config as config



UPLOAD_FOLDER = config.UPLOAD_FOLDER
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

"""

Hack to include an API for other projects

"""

@app.route('/api/dupchecker/version', methods=['GET'])
def get_version():
    dupcheck_version = config.dupcheck_version
    return jsonify({'version': dupcheck_version})

"""

APP ROUTING

"""

@app.route('/')
def open_page():
    return render_template('home_page.html')

@app.route('/related', methods=['GET', 'POST'])
def related():
    if request.method == 'GET':
        return render_template('related.html')
    elif request.method == 'POST':
        user_query = request.form['query'].lower()
        result = neural_tools.word_sims(user_query)
        if result[0] is True:
            return render_template('related.html', result=result[1], success='True', title_h2='Word Similarity Score',
                                   title_th='Similarity Score', original=user_query)
        if result[0] is False:
            error_message = str(result[1])
            offending_term = error_message.split("'")[1]
            result = offending_term.title()
            return render_template('related.html', result=result[1], success='False')

@app.route('/stemmed', methods=['GET', 'POST'])
def stemmed():
    if request.method == 'GET':
        return render_template('stemmed.html')
    elif request.method == 'POST':
        search = request.form['raw_stem']
        stemmed_search = text_tools.wild_stem(search)
        return render_template('stemmed.html', stemmed_bool=stemmed_search, success='True', original=search)


@app.route('/keywords', methods=['GET', 'POST'])
def keywords():
    if request.method == 'GET':
        return render_template('keywords.html')
    elif request.method == 'POST':
        keywords = text_tools.get_keywords(request.form['raw_text'])
        if keywords:
            return render_template('keywords.html', keywords=keywords, success='True', original=raw_text)
        else:
            return render_template('keywords.html', success='False')


@app.route('/thisplusthat', methods=['GET', 'POST'])
def thisplusthat():
    if request.method == 'GET':
        return render_template('thisplusthat.html')
    elif request.method == 'POST':
        solution = neural_tools.word_sims(request)
        if solution['success'] == True:
            return render_template('thisplusthat.html', result=solution['result'], success='True',
                                   user_equation=solution['user_equation'],
                                   word_one=solution['word_one'].strip(), word_two=solution['word_two'].strip(),
                                   word_three=solution['word_three'].strip())
        elif solution['success'] == False:
            return render_template('thisplusthat.html', result=solution['result'], success='False')


@app.route('/infer', methods=['GET', 'POST'])
def infer():
    if request.method == 'GET':
        return render_template('infer.html')
    elif request.method == 'POST':
        inferred, data_sources = diversity_tools.infer_one(request)
        user_query_name = request.form['infer-name']


    model_results = [result for result in inferred if 'model' in result.source][0]
    if model_results == 'M':
        model_results = 'Male'
    elif model_results == 'F':
        model_results = 'Female'
    elif model_results == 'U':
        model_results = 'Ambiguous'
    data_results = [result for result in inferred if 'data' in result.source][0]
    if len(data_results) != 0:
        database_name = data_results[0].source.split("-")[1]

        return render_template('infer.html', user_query=user_query_name, success='True',
                           gender_guess=model_results, database_name=database_name, database_result=data_results)
    elif len(data_results) == 0:
        database_name = data_sources
        return render_template('infer.html', user_query=user_query_name, success='Partial',
                               gender_guess=model_results, database_name=database_name)
    else:
        return render_template('infer.html', success='False')



#
# @app.route('/diversity')
# def diversity():
#     return render_template('diversity_score.html')
#
# @app.route('/tfidf_measures')
# def tfidf():
#     return render_template('tf_idf.html')
#
# # TODO Get this into a module
# @app.route('/tfidf_measures', methods=['POST'])
# def post_tfidf():
#     user_input = request.form['tfidf_text']
#     if len(user_input) > 10000:
#         return render_template('tf_idf.html', success='False', original="Text Size Limit Exceeded",
#                                error_message="Text Size Limit Exceeded")
#     user_form = request.form
#     gram_mode = user_form.get('gram_tokens', False)
#     lem_mode = user_form.get('lem_tokens', False)
#     if gram_mode == 'on':
#         gram_mode = True
#     if lem_mode == 'on':
#         lem_mode = True
#     # clean text returned is string.
#     clean_text = clean_it(user_input, lem_tokens=lem_mode, gram_tokens=gram_mode)
#     # choose model from gram tokens parameter
#     if gram_mode is False and lem_mode is False:
#         d = dictionary
#         m = tfidf_model
#     elif gram_mode is True and lem_mode is False:
#         d = bigram_dictionary
#         m = bigram_tfidf_model
#     elif gram_mode is True and lem_mode is True:
#         d = lg_dictionary
#         m = lg_tfidf_model
#     elif gram_mode is False and lem_mode is True:
#         d = lems_dictionary
#         m = lems_tfidf_model
#     else:
#         d = dictionary
#         m = tfidf_model
#
#     tfidf_values = dict(m[d.doc2bow(clean_text.split())])
#     tfidf_tokens = {}
#     for id_token, tfidf_value in tfidf_values.items():
#         token = d[id_token]
#         tfidf_tokens[token] = round(tfidf_value, 4)
#     # Sort the values
#     tfidf_scored = sorted(tfidf_tokens.items(), key=lambda x: x[1], reverse=True)
#     # Limit to 25
#     tfidf_scored = tfidf_scored[:25]
#     return render_template('tf_idf.html', success='True', original=user_input, result=tfidf_scored)
#
#



if __name__ == '__main__':
    app.run()
