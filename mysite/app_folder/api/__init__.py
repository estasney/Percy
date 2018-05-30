from flask import Blueprint

bp = Blueprint('api', __name__)

from app_folder.api import routes