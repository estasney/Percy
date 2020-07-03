from flask import jsonify

from app_folder.webex_api import bp
from app_folder.webex_api.decorators import requires_api_key
from app_folder.webex_models import Person


@bp.route('/status', methods=['GET'])
@requires_api_key
def related():
    people = Person.query.all()
    data = [person.to_dict() for person in people]
    return jsonify({"data": data}), 200
