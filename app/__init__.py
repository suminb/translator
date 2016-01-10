# -*- coding: utf-8 -*-

__version__ = '1.3.10'

import os
import sys
import logging

from flask import got_request_exception, Flask, request
from flask.ext.babel import Babel
import rollbar
import rollbar.contrib.flask
import yaml

VALID_LANGUAGES = {
    '': 'None',
    'auto': 'Auto',
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ru': 'Russian',
    'zh-CN': 'Chinese',
    'id': 'Indonesian',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'it': 'Italian',
    'de': 'German',
    'tl': 'Filipino',
    'ar': 'Arabic',
    'cs': 'Czech',
    'iw': 'Hebrew',
    'pl': 'Polish',
    'pt': 'Portuguese',
    'sv': 'Swedish',
    'tr': 'Turkish',
}

SOURCE_LANGUAGES = list(filter(lambda x: x not in ['', 'auto'],
                               VALID_LANGUAGES.keys()))
TARGET_LANGUAGES = list(filter(lambda x: x not in ['', 'auto'],
                               VALID_LANGUAGES.keys()))
INTERMEDIATE_LANGUAGES = ['', 'ja', 'ru']

DEFAULT_USER_AGENT = 'AndroidTranslate/4.4.0.RC01.104701208-44000162 5.1 ' \
    'tablet GTR_TRANS_WLOPV1_ANDROID GTR_TRANS_WLOPV1_DE_EN_AR'
MAX_TEXT_LENGTH = 8000


try:
    config = yaml.load(open('config.yml'))
except IOError:
    # FIXME: This is a temporary workaround; use a dummy config object
    config = yaml.load(open('config.yml.dist'))

logger = logging.getLogger('translator')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

babel = Babel()


def create_app(name=__name__, config={}):
    app = Flask(name)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
    # app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.secret_key = config.get('secret_key', '(secret key is not set)')

    app.config.update(config)

    from app.analysis.model import db
    db.init_app(app)

    from app.api import api_module
    from app.main import main_module
    from app.corpus import corpus_module
    app.register_blueprint(api_module, url_prefix='')
    app.register_blueprint(main_module, url_prefix='')
    app.register_blueprint(corpus_module, url_prefix='/corpus')

    from app.utils import register_filters
    register_filters(app)

    babel.init_app(app)

    if app.config['DEBUG']:
        from werkzeug import SharedDataMiddleware
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/': os.path.join(os.path.dirname(__file__), 'static')
        })

    @app.before_first_request
    def init_rollbar():
        """init rollbar module"""
        rollbar.init(
            # access token
            os.environ.get('ROLLBAR_TOKEN', ''),
            # environment name
            os.environ.get('ROLLBAR_ENV', 'development'),
            # server root directory, makes tracebacks prettier
            root=os.path.dirname(os.path.realpath(__file__)),
            # flask already sets up logging
            allow_logging_basic_config=False,
            # Use HTTP as GAE does not allow the use of the SSL package
            endpoint='http://api.rollbar.com/api/1/')

        # send exceptions from `app` to rollbar, using flask's signal system.
        got_request_exception.connect(rollbar.contrib.flask.report_exception,
                                      app)

    @babel.localeselector
    def get_locale():
        """Selects an appropriate locale.

        Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""  # noqa
        try:
            locale = request.args['locale']
        except KeyError:
            try:
                locale = request.cookies['locale']
            except KeyError:
                locale = request.accept_languages.best_match(['ko', 'en'])

        return locale if locale else 'en'

    return app


# FIXME: Could we de-duplicate this function definition? @babel.localeselector
# is the problem.
def get_locale():
    """Selects an appropriate locale.

    Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""  # noqa
    try:
        locale = request.args['locale']
    except KeyError:
        try:
            locale = request.cookies['locale']
        except KeyError:
            locale = request.accept_languages.best_match(['ko', 'en'])

    return locale if locale else 'en'
