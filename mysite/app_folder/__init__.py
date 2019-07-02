from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension
from app_folder.site_config import Config, FConfig
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


toolbar = DebugToolbarExtension()
moment = Moment()
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app_run = Flask(__name__)
    app_run.config.from_object(config_class)

    toolbar.init_app(app_run)
    moment.init_app(app_run)
    db.init_app(app_run)
    migrate.init_app(app_run, db)

    from app_folder.main import bp as main_bp
    app_run.register_blueprint(main_bp)

    from app_folder.api import bp as api_bp
    app_run.register_blueprint(api_bp, url_prefix='/api/v1')

    from app_folder.words import bp as words_bp
    app_run.register_blueprint(words_bp)

    from app_folder.autocomplete import bp as autocomplete_bp
    app_run.register_blueprint(autocomplete_bp, url_prefix='/autocomplete')

    @app_run.context_processor
    def static_vid():
        return {'static_version': Config.STATIC_VERSION_ID}

    return app_run
