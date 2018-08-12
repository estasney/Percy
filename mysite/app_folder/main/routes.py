from flask import render_template, request, jsonify, abort
from gensim.summarization.pagerank_weighted import pagerank_weighted

from app_folder.main import Utils, diversity_tools, neural_tools, upload_tools
from app_folder.main import bp
from app_folder.main import graph_tools, text_tools


@bp.route('/')
def open_page():
    return render_template('home_page.html')


@bp.route('/related', methods=['GET', 'POST'])
def related():
    if request.method == 'GET':
        if not request.args:
            return render_template('related.html')
        else:
            user_query, query_scope = request.args.get('q'), request.args.get('scope')
            result_success, result = neural_tools.word_sims(user_query, query_scope)
            if result_success:
                return render_template('related.html', result=result, success='True', title_h2='{} Similarity Score'.format(query_scope.title()),
                                       title_th='Similarity Score', original=user_query)
            else:
                return render_template('related.html', result=user_query, success='False')

    elif request.method == 'POST':
        user_query, query_scope = request.form.get('q'), request.form.get('scope')
        result_success, result = neural_tools.word_sims(user_query, query_scope)
        if result_success:
            return render_template('related.html', result=result, success='True', title_h2='{} Similarity Score'.format(query_scope.title()),
                                   title_th='Similarity Score', original=user_query)
        else:
            return render_template('related.html', result=user_query, success='False')


@bp.route('/keywords', methods=['GET'])
def keywords():
    return render_template('keywords.html')


@bp.route('/thisplusthat', methods=['GET', 'POST'])
def thisplusthat():
    if request.method == 'GET':
        return render_template('thisplusthat.html')
    elif request.method == 'POST':
        solution_success, solution = neural_tools.word_math(request)
        if solution_success:
            return render_template('thisplusthat.html', result=solution['scores'], success='True',
                                   user_equation=solution['equation'], pos_words=solution['positives'],
                                   neg_words=solution['negatives'], unknown_words=solution['unknowns'])
        else:
            return render_template('thisplusthat.html', success='False')


@bp.route('/infer', methods=['GET', 'POST'])
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


@bp.route('/diversity', methods=['GET', 'POST'])
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
    d_known = d_male_count + d_female_count

    # Population distrubition
    pop_values = diversity_tools.population_distro(male_count=d_male_count, female_count=d_female_count,
                                                   total_count=total_count)
    d_female_percent = "{:.2%}".format(pop_values['ratio_female'])

    confidence_interval = "{:.2%}".format(pop_values['confidence_interval'])


    return render_template('diversity_score.html', success='True', total_count=total_count, male_count=male_count,
                           female_count=female_count, amb_count=amb_count, d_male_count=d_male_count,
                           d_female_count=d_female_count, d_amb_count=d_amb_count, d_unk_count=d_unk_count,
                           d_known=d_known, d_female_percent=d_female_percent, confidence_interval=confidence_interval)


@bp.route('/tf_idf', methods=['GET', 'POST'])
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


@bp.route('/kw_data', methods=['POST'])
def kw_data():
    raw_text = request.form.get('raw_text')
    phrase_checked = request.headers.get('Phrase-Checked')
    if phrase_checked == 'true':
        phrase_checked = True
    else:
        phrase_checked = False
    if not raw_text:
        abort(401)

    window_size = int(request.headers.get('Window-Limit', 2))

    lem_text = text_tools.process_graph_text(raw_text, phrase_checked)
    graph = graph_tools.build_graph(lem_text, window_size)

    edges = graph.edges()
    data = []
    scores = pagerank_weighted(graph)
    dev_dict, dev_count = graph_tools.assign_deviations(scores)
    color_dict = graph_tools.compute_colors_dict(dev_count)
    for edge in edges:
        source, target = edge
        source_score, target_score = int(dev_dict.get(source, 0)), int(dev_dict.get(target, 0))
        source_color, target_color = (color_dict.get(source_score, color_dict[0])), (color_dict.get(target_score,
                                                                                                    color_dict[0]))
        td = {'source': source, 'source_score': source_score, 'target': target, 'target_score': target_score,
              'source_color': source_color, 'target_color': target_color}
        data.append(td)

    del edges, scores, dev_dict, dev_count, color_dict

    return jsonify({'data': data})
