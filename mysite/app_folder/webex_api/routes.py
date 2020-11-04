from flask import jsonify, request

from app_folder import db
from app_folder.webex_api import bp
from app_folder.webex_api.decorators import requires_api_key
from app_folder.webex_models import Person, APIUser


@bp.route('/status', methods=['GET'])
@requires_api_key
def related():
    people = db.session.query(Person).filter(Person.tracking.is_(True)).all()
    data = [person.to_dict() for person in people]
    return jsonify({"data": data}), 200


@bp.route('/login', methods=['POST'])
def login():
    verified_user = APIUser.verify_auth_basic(request)
    if not verified_user:
        return jsonify(message="Unauthorized"), 403
    token = verified_user.generate_api_token()
    db.session.commit()
    return jsonify(token=token), 200
