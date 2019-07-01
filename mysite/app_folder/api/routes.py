from flask import request, jsonify
from app_folder.api import bp
from app_folder.api.utils import request_message_details, make_reply
from app_folder.api.nlp import SynonymParser
from app_folder.tools import sims_tools


@bp.route('/spark', methods=['GET', 'POST'])
def listen_webhook():
    hook_data = request.json
    data_id = hook_data['data']['id']  # The message id
    room_type = hook_data['data']['roomType']  # direct or group

    print(hook_data)

    message_details = request_message_details(data_id)

    print(message_details)

    intent_parser = SynonymParser()

    answer = intent_parser.answer_question(message_details['message_body'])
    if not answer:
        answer = "Sorry {}, I didn't understand that".format(message_details['person_fname'])
    else:
        answer = "Hi {}, {}".format(message_details['person_fname'], answer)
    make_reply(answer, room_type, message_details)
    return ""


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
        return jsonify({'items': [{'word': word, 'score': score} for word, score in result], 'query': user_query, 'scope': query_scope}), 201
    else:
        return jsonify({'message': 'query error', 'query': user_query, 'scope': query_scope}), 404
