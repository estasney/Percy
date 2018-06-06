from flask import request
from app_folder.api import bp
from app_folder.api.utils import request_message_details, make_reply
from app_folder.api.nlp import IntentParser, SynonymParser


@bp.route('/spark', methods=['GET', 'POST'])
def listen_webhook():
    hook_data = request.json
    data_id = hook_data['data']['id']  # The message id
    room_type = hook_data['data']['roomType']  # direct or group

    message_details = request_message_details(data_id)

    intent_parser = IntentParser(SynonymParser())

    if message_details['message_body'] not in intent_parser:
        # Unable to match query
        return ""

    parser, answer = intent_parser.answer_question(message_details['message_body'])
    if not parser:
        answer = "{}".format(answer)
        make_reply(answer, room_type, message_details)
    else:
        answer = "Hi {}, {}".format(message_details['person_fname'], answer)
        make_reply(answer, room_type, message_details)

    return ""

