from flask import Blueprint

bp = Blueprint('anode', __name__)

from app_folder.anode import routes
