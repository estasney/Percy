import pickle
import requests
from app_folder.site_config import FConfig


def load_p(fn):
    with open(fn, "rb") as pfile:
        p = pickle.load(pfile)
    return p


def request_message_details(message_id):
    s = requests.session()
    s.headers.update({'Authorization': load_p(FConfig.key_path)})
    s.headers.update({'Content-type': 'application/json; charset=utf-8'})
    message_details = s.get(FConfig.message_api.format(message_id))
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
