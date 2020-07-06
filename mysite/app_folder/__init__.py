from flask import Flask, render_template

from flask_login import LoginManager

from app_folder.site_config import Config, FConfig
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app_folder.flask_packer import Packer

# noinspection PyBroadException
try:
    from flask_debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension()
except Exception:
    toolbar = None

moment = Moment()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
packer = Packer()


def server_error_page(e):
    return render_template("percy/500.html"), 500


def create_app(config_class=Config):
    from logging.config import dictConfig
    dictConfig({
        'version':    1,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                }
            },
        'handlers':   {
            'wsgi': {
                'class':     'logging.StreamHandler',
                'stream':    'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'default'
                }
            },
        'root':       {
            'level':    'INFO',
            'handlers': ['wsgi']
            }
        })
    app_run = Flask(__name__)
    app_run.config.from_object(config_class)

    if toolbar:
        toolbar.init_app(app_run)
    moment.init_app(app_run)
    db.init_app(app_run)
    migrate.init_app(app_run, db)
    login_manager.init_app(app_run)
    packer.init_app(app_run)

    from app_folder.main import bp as main_bp
    app_run.register_blueprint(main_bp)

    from app_folder.api import bp as api_bp
    app_run.register_blueprint(api_bp, url_prefix='/api/v1')

    from app_folder.words import bp as words_bp
    app_run.register_blueprint(words_bp)

    from app_folder.autocomplete import bp as autocomplete_bp
    app_run.register_blueprint(autocomplete_bp, url_prefix='/autocomplete')

    from app_folder.anode import bp as anode_bp
    app_run.register_blueprint(anode_bp, url_prefix='/anode')

    from app_folder.webex_api import bp as webex_bp
    app_run.register_blueprint(webex_bp, url_prefix='/webex')

    @app_run.context_processor
    def static_version():
        return {'static_version': FConfig.STATIC_VERSION_ID}


    @app_run.template_filter('ratio')
    def ratio(value):
        return "{:.2f}".format(value * 100)

    app_run.register_error_handler(500, server_error_page)
    return app_run
