from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
try:
    from app_folder.local_config import Config
except ImportError:
    from app_folder.web_config import Config

app_run = Flask(__name__)
app_run.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app_run.config['DEBUG'] = Config.debug
app_run.config['SECRET_KEY'] = Config.secret_key
app_run.config['DEBUG_TB_PROFILER_ENABLED'] = Config.profiler

toolbar = DebugToolbarExtension(app_run)

from app_folder import routes