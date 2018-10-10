from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from app_folder.site_config import Config, FConfig

toolbar = DebugToolbarExtension()


def create_app(config_class=Config):
    app_run = Flask(__name__)
    app_run.config.from_object(config_class)
    toolbar.init_app(app_run)

    from app_folder.main import bp as main_bp
    app_run.register_blueprint(main_bp)

    from app_folder.api import bp as api_bp
    app_run.register_blueprint(api_bp, url_prefix='/api/v1')
    return app_run
