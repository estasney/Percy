import requests
from app_folder.site_config import FConfig
from datetime import datetime


def request_message_details(message_id):
    s = requests.session()
    s.headers.update({'Authorization': FConfig.bot_key})
    s.headers.update({'Content-type': 'application/json; charset=utf-8'})
    message_details = s.get(FConfig.message_api_f.format(message_id))

    # Get sender's display name
    # TODO Cache this
    sender_id = message_details.json()['personId']
    sender_details = s.get(FConfig.person_details_api_f.format(sender_id))

    return parse_message(message_details.json(), sender_details.json())


def parse_message(message_details, sender_details):
    try:
        created = datetime.strptime(message_details['created'], "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        created = message_details['created']
    person_email = message_details['personEmail']
    person_id = message_details['personId']
    message_body = message_details['text']
    sender_fname = sender_details.get("firstName", None)
    sender_lname = sender_details.get("lastName", None)
    sender_displayname = sender_details.get("displayName", None)
    sender_nname = sender_details.get("nickName", None)

    td = {'created': created,
          'message_body': message_body,
          'person_email': person_email,
          'person_id': person_id,
          'person_fname': sender_fname,
          'person_lname': sender_lname,
          'person_displayname': sender_displayname,
          'person_nname': sender_nname}
    return td


def make_reply(message_text, room_type, message_details):
    s = requests.session()
    s.headers.update({'Authorization': FConfig.bot_key})
    s.headers.update({'Content-type': 'application/json; charset=utf-8'})

    if room_type == 'group':

        request_params = {
            'roomId': FConfig.bot_room_id,
            'markdown': message_text
        }

    else:
        request_params = {
            'toPersonEmail': message_details['person_email'],
            'markdown': message_text
        }

    s.post(FConfig.message_api, json=request_params)

def make_error_response():
    return "Sorry I didn't understand that"
