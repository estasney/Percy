from flask import request, abort, jsonify
from app_folder.site_config import FConfig
from app_folder.api import bp
from app_folder.api.utils import load_p, request_message_details


@bp.route('spark', methods=['GET', 'POST'])
def listen_webhook():
    hook_data = request.json
    data_id = hook_data['data']['id']  # The message id

    # Request the message details
    message_details = request_message_details(data_id)

    # Make a reply
    reply_to = message_details['person_id']
    reply_body = "Hello to you too!"

    return ""




