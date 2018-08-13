from flask import render_template, request, jsonify, abort
from app_folder.main import neural_tools
from app_folder.main import bp
from app_folder.main import graph_tools, text_tools, fingerprint_tools, autocomplete_tools


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


@bp.route('/kw_data', methods=['POST'])
def kw_data():
    raw_text = request.form.get('raw_text')
    if not raw_text:
        abort(401)

    window_size = int(request.headers.get('Window-Limit', 2))

    lem_text = text_tools.process_graph_text(raw_text)
    graph = graph_tools.make_graph(lem_text, window_size)

    # Assign each word a color
    color_dict = graph_tools.get_colors(graph)
    data = []
    for edge in graph.edges():
        source, target = edge
        source_color, target_color = color_dict.get(source, (0, 0, 255)), color_dict.get(target, (0, 0, 255))
        td = {'source': source, 'target': target, 'source_color': source_color, 'target_color': target_color}
        data.append(td)

    return jsonify({'data': data})
