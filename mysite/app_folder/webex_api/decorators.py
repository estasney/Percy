from functools import wraps

from flask import request, jsonify

from app_folder.webex_models import APIUser


def requires_api_key(func):
    @wraps(func)
    def decorated_view_api(*args, **kwargs):
        if APIUser.verify_auth_token(request):
            return func(*args, **kwargs)
        else:
            return jsonify(message="Unauthorized"), 403

    return decorated_view_api
