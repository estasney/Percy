from flask import Blueprint

bp = Blueprint('autocomplete', __name__)

from app_folder.autocomplete import routes