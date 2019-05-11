from flask import Blueprint

bp = Blueprint('words', __name__)

from app_folder.words import routes