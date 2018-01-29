from flask import Flask
try:
    from app_folder.local_config import Config
except ImportError:
    from app_folder.web_config import Config

app_run = Flask(__name__)
app_run.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

from app_folder import routes