from flask import render_template, request, jsonify, abort

from app_folder.main import graph_tools, text_tools, fingerprint_tools, autocomplete_tools, neural_tools, bp,\
    upload_tools, diversity_tools, web_tools


@bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    terms = autocomplete_tools.get_autocomplete(dataset='words')
    return jsonify(terms)


@bp.route('/autocomplete_skills', methods=['GET'])
def autocomplete_skills():
    terms = autocomplete_tools.get_autocomplete(dataset='skills')
    return jsonify(terms)


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
                                       title_th='Similarity Score', original=user_query, scope=query_scope)
            else:
                return render_template('related.html', result=user_query, success='False')

    elif request.method == 'POST':
        user_query, query_scope = request.form.get('q'), request.form.get('scope')
        result_success, result = neural_tools.word_sims(user_query, query_scope)
        if result_success:
            return render_template('related.html', result=result, success='True', title_h2='{} Similarity Score'.format(query_scope.title()),
                                   title_th='Similarity Score', original=user_query, scope=query_scope)
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
        scope = request.form.get('scope')
        if solution_success:
            return render_template('thisplusthat.html', result=solution['scores'], success='True',
                                   user_equation=solution['equation'], pos_words=solution['positives'],
                                   neg_words=solution['negatives'], unknown_words=solution['unknowns'],
                                   scope=scope)
        else:
            return render_template('thisplusthat.html', success='False')


@bp.route('/tf_idf', methods=['GET', 'POST'])
def tfidf():
    if request.method == 'GET':
        return render_template('tf_idf.html')
    elif request.method == 'POST':
        user_input = request.form['tfidf_text']
        fp = fingerprint_tools.Fingerprint()
        scored_tfidf = fp.fingerprint(user_input)
        return render_template('tf_idf.html', success='True', original=user_input, result=scored_tfidf)


@bp.route('/diversity', methods=['GET', 'POST'])
def infer_diversity():
    if request.method == "GET":
        return render_template('diversity_score.html')

    file_upload = upload_tools.UploadManager(request)

    if not file_upload.status:
        return render_template('diversity_score.html', success='False')

    names_list = file_upload.file_data()

    if not names_list or names_list is False:
        return render_template('diversity_score.html', success='False', error_message=file_upload.status)

    results = diversity_tools.search_data(names_list)

    """
    Returns a dict with
        :total - the number of names
        :male - n male
        :female - n female
        :unknown - n unknown
        :95 - +/- for 95% confidence
        :99 - +/- for 99% confidence
        :ratio_female - n female / total
    """
    return render_template('diversity_score.html', n_known=results['known'], total=results['total'],
                           r_female=results['ratio_female'], n_unknown=results['unknown'], ci_95=results['95'],
                           ci_99=results['99'], success='True', n_male=results['male'], n_female=results['female'])


@bp.route('/kw_data', methods=['POST'])
def kw_data():
    raw_text = request.form.get('raw_text')
    if not raw_text:
        abort(401)

    window_size = int(request.headers.get('Window-Limit', 2))

    # Get data-type : req_pill or paste_pill
    data_type = request.headers.get('Data-Type')
    if data_type == "req_pill":
        raw_text = web_tools.get_job_posting(raw_text)
        if not raw_text:
            return jsonify({'data': []})

    lem_text = text_tools.process_graph_text(raw_text)
    graph = graph_tools.make_graph(lem_text, window_size)
    edge_dict = graph_tools.get_n_edges(graph)
    base_color = graph_tools.compute_colors_dict(edge_dict)
    color_dict = {}
    for word, edge in edge_dict.items():
        word_color = base_color[edge]
        color_dict[word] = word_color
    data = []
    for edge in graph.edges():
        source, target = edge
        source_color, target_color = color_dict.get(source, (0, 0, 255)), color_dict.get(target, (0, 0, 255))
        source_n_links, target_n_links = edge_dict.get(source, 1), edge_dict.get(target, 1)
        td = {'source': source, 'target': target, 'source_color': source_color, 'target_color': target_color,
              'source_n_links': source_n_links, 'target_n_links': target_n_links}
        data.append(td)

    return jsonify({'data': data})
