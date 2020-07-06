import click
from flask import Blueprint

bp = Blueprint('webex_api', __name__)

from app_folder.webex_api import routes


@bp.cli.command('create')
@click.option('--username', type=str, required=True, prompt=True)
@click.password_option()
def create_api_user(username, password):
    from app_folder.webex_models import APIUser, db

    new_user = APIUser()
    new_user.username = username
    new_user.password = password
    db.session.add(new_user)
    db.session.commit()
    print(f"Added User {new_user.username}")
