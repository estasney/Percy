from flask import request, abort, jsonify
from app_folder.site_config import FConfig
from app_folder.api import bp
from app_folder.api.utils import request_message_details, make_reply
from app_folder.api.nlp import IntentParser


@bp.route('/spark', methods=['GET', 'POST'])
def listen_webhook():
    hook_data = request.json
    data_id = hook_data['data']['id']  # The message id

    message_details = request_message_details(data_id)

    intent_parser = IntentParser([parser() for parser in FConfig.parsers])

    if message_details['message_body'] not in intent_parser:
        # Unable to match query
        return ""

    answer = intent_parser.answer_question(message_details['message_body'])
    answer = "Hi {}, {}".format(message_details['person_fname'], answer)
    make_reply(answer)

    return ""

