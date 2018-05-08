from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from site_config import Config

toolbar = DebugToolbarExtension()

def create_app(config_class=Config):
    app_run = Flask(__name__)
    app_run.config.from_object(config_class)
    toolbar.init_app(app_run)

    from app_folder.main import bp as main_bp
    app_run.register_blueprint(main_bp)
    return app_run
