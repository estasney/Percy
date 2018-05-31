import requests
from app_folder.site_config import FConfig


def request_message_details(message_id):
    s = requests.session()
    s.headers.update({'Authorization': FConfig.bot_key})
    s.headers.update({'Content-type': 'application/json; charset=utf-8'})
    message_details = s.get(FConfig.message_api_f.format(message_id))
    return parse_message(message_details.json())


def parse_message(message_details):
    created = message_details['created']
    person_email = message_details['personEmail']
    person_id = message_details['personId']
    message_body = message_details['text']
    td = {'created': created,
          'person_email': person_email,
          'person_id': person_id,
          'message_body': message_body}
    return td


def make_reply(message_text):
    s = requests.session()
    s.headers.update({'Authorization': FConfig.bot_key})
    s.headers.update({'Content-type': 'application/json; charset=utf-8'})

    request_params = {
        'roomId': FConfig.bot_room_id,
        'text': message_text
    }

    s.post(FConfig.message_api, json=request_params)




