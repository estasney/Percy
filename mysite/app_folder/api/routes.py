from flask import request
from app_folder.api import bp
from app_folder.api.utils import request_message_details, make_reply
from app_folder.api.nlp import SynonymParser


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

