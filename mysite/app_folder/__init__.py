from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from app_folder.site_config import Config

app_run = Flask(__name__)
app_run.config.from_object(Config)
toolbar = DebugToolbarExtension()


def create_app(config_class=Config):
    app_run = Flask(__name__)
    app_run.config.from_object(config_class)
    toolbar.init_app(app_run)
    return app_run
