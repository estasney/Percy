from flask import render_template, request, jsonify, abort

from app_folder.words import bp
from app_folder.tools import fingerprint_tools, sims_tools, text_tools, graph_tools, web_tools


@bp.route('/related', methods=['GET', 'POST'])
def related():
    if request.method == 'GET':
        if not request.args:
            return render_template('related.html')
        else:
            user_query, query_scope = request.args.get('q'), request.args.get('scope')
            result_success, result = sims_tools.word_sims(user_query, query_scope)
            if result_success:
                return render_template('related.html', result=result, success='True',
                                       title_h2='{} Similarity Score'.format(query_scope.title()),
                                       title_th='Similarity Score', original=user_query, scope=query_scope)
            else:
                return render_template('related.html', result=user_query, success='False')

    elif request.method == 'POST':
        user_query, query_scope = request.form.get('q'), request.form.get('scope')
        result_success, result = sims_tools.word_sims(user_query, query_scope)
        if result_success:
            return render_template('related.html', result=result, success='True',
                                   title_h2='{} Similarity Score'.format(query_scope.title()),
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
        solution_success, solution = sims_tools.word_math(request)
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


@bp.route('/kw_data', methods=['POST'])
def kw_data():
    raw_text = request.form.get('raw_text')
    if not raw_text:
        abort(404)

    window_size = int(request.headers.get('Window-Limit', 2))

    # Get data-type : req_pill or paste_pill
    data_type = request.headers.get('Data-Type')
    if data_type == "v-pills-cisco-tab":
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
