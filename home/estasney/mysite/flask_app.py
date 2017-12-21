from flask import Flask, render_template, request, jsonify
from modules import text_tools
from modules import diversity_tools
from modules import upload_tools
from modules import neural_tools
from modules import Utils



""" LOAD CONFIG """

try:
    from config import local_config as config
except ImportError:
    from config import web_config as config

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
            return render_template('keywords.html', keywords=keywords, success='True',
                                   original=request.form['raw_text'])
        else:
            return render_template('keywords.html', success='False')


@app.route('/thisplusthat', methods=['GET', 'POST'])
def thisplusthat():
    if request.method == 'GET':
        return render_template('thisplusthat.html')
    elif request.method == 'POST':
        solution = neural_tools.word_math(request)
        if solution['success'] == True:
            return render_template('thisplusthat.html', result=solution['result'], success='True',
                                   user_equation=solution['user_equation'],
                                   word_one=solution['word_one'].strip(), word_two=solution['word_two'].strip(),
                                   word_three=solution['word_three'].strip())
        elif solution['success'] == False:
            return render_template('thisplusthat.html', result=solution['result'], success='False')


@app.route('/infer', methods=['GET', 'POST'])
def infer_name():
    if request.method == 'GET':
        return render_template('infer.html')
    elif request.method == 'POST':
        user_query_name = request.form['infer_name']
        global_names = request.form.get('use_global_names', False)
        inferred, data_sources = diversity_tools.infer_one(user_query_name, global_names)
    else:
        return render_template('infer.html')

    model_results = [result.result for result in inferred if 'model' in result.source][0]
    model_results = Utils.readable_gender(model_results)

    data_results = [result for result in inferred if 'data' in result.source]
    if len(data_results) != 0:
        database_name = data_results[0].source.split("-")[1]
        data_results = data_results[0].result
        data_results = Utils.readable_gender(data_results)
        return render_template('infer.html', user_query=user_query_name, success='True', gender_guess=model_results,
                               database_name=database_name, database_result=data_results)
    elif len(data_results) == 0:
        database_name = data_sources
        return render_template('infer.html', user_query=user_query_name, success='Partial',
                               gender_guess=model_results, database_name=database_name)
    else:
        return render_template('infer.html', success='False')


@app.route('/diversity', methods=['GET', 'POST'])
def diversity():
    if request.method == 'GET':
        return render_template('diversity_score.html')
    elif request.method == 'POST':
        upload_file = upload_tools.UploadManager(request)
    else:
        return render_template('diversity_score.html')

    # Check if anything went wrong with upload
    if upload_file.status != True:
        return render_template('diversity_score.html', success='False', error_message=upload_file.status)

    # Check whether to use global name dict
    user_form = request.form
    use_global = user_form.get('use_global_names', False)
    if use_global == 'on':
        use_global = True

    # Logic of checking names list
    names_list = upload_file.file_data()

    # Run the query
    name_results = diversity_tools.infer_many(names_list, use_global)
    cumul_count = name_results['Cumulative']
    total_count = len(names_list)
    male_count, female_count, amb_count = cumul_count['M'], cumul_count['F'], cumul_count['U']

    # Data only

    data_count = name_results['Data_Only']
    d_male_count, d_female_count, d_amb_count, d_unk_count = data_count['M'], data_count['F'], data_count['U'],\
                                                             data_count['Unk']

    return render_template('diversity_score.html', success='True', total_count=total_count, male_count=male_count,
                           female_count=female_count, amb_count=amb_count, d_male_count=d_male_count,
                           d_female_count=d_female_count, d_amb_count=d_amb_count, d_unk_count=d_unk_count)


@app.route('/tf_idf', methods=['GET', 'POST'])
def tfidf():
    if request.method == 'GET':
        return render_template('tf_idf.html')
    elif request.method == 'POST':
        user_input = request.form['tfidf_text']
        if isinstance(user_input, str) is False:
            return render_template('tf_idf.html', success='False', original="",
                                   error_message="This Form Only Accepts Text...")
        if len(user_input.split()) > 10000:
            return render_template('tf_idf.html', success='False', original=user_input,
                                   error_message="Word Limit Exceeded")
        user_form = request.form
        gram_mode = user_form.get('gram_tokens', False)
        lem_mode = user_form.get('lem_tokens', False)
        if gram_mode == 'on':
            gram_mode = True
        if lem_mode == 'on':
            lem_mode = True

        scored_tfidf = text_tools.score_tfidf(user_input, gram_mode, lem_mode)
        return render_template('tf_idf.html', success='True', original=user_input, result=scored_tfidf)


if __name__ == '__main__':
    app.run()
