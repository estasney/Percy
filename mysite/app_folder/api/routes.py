from app_folder.tools import sims_tools
from flask import request, jsonify

from app_folder.api import bp


@bp.route('/related', methods=['GET', 'POST'])
def related():
    if request.method == 'GET':
        if not request.args:
            return jsonify({'message': 'empty query'}), 422
        else:
            user_query, query_scope = request.args.get('q', None), request.args.get('scope', None)
            format_input = request.args.get('format_input', True)
    else:
        user_query = request.json.get('q', None)
        query_scope = request.json.get('scope', None)
        format_input = request.json.get('format_input', True)

    if not all([user_query, query_scope]):
        return jsonify({'message': 'missing one or more parameters'}), 422

    result_success, result = sims_tools.word_sims(user_query, query_scope, process_input=format_input)
    if result_success:
        return jsonify({
            'items': [{'word': word, 'score': score} for word, score in result], 'query': user_query,
            'scope': query_scope
            }), 201
    else:
        return jsonify({'message': 'query error', 'query': user_query, 'scope': query_scope}), 404
