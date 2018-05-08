from flask import Blueprint

bp = Blueprint('main', __name__)

from app_folder.main import routes