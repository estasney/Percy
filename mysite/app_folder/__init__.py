from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from app_folder.site_config import FConfig

app_run = Flask(__name__)
app_run.config['UPLOAD_FOLDER'] = FConfig.UPLOAD_FOLDER

from app_folder import routes