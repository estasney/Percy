import click
from flask import Blueprint

bp = Blueprint('webex_api', __name__)

from app_folder.webex_api import routes


@bp.cli.command('create')
def create_api_user():
    from app_folder.webex_models import APIUser, db

    new_user = APIUser()
    db.session.add(new_user)
    db.session.commit()
    user_token = new_user.generate_api_token()
    print(user_token)
    db.session.commit()
