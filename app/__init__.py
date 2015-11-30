# -*- coding: utf-8 -*-

__version__ = '1.3.6'

import os
import sys
import logging

from flask import got_request_exception, Flask
from flask.ext.babel import Babel
import rollbar
import rollbar.contrib.flask
import yaml


VALID_LANGUAGES = {
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

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22'  # noqa
MAX_TEXT_LENGTH = 8000


try:
    config = yaml.load(open('config.yml'))
except IOError:
    # FIXME: This is a temporary workaround; use a dummy config object
    config = yaml.load(open('config.yml.dist'))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI')
app.secret_key = config['secret_key']

logger = logging.getLogger('translator')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

babel = Babel(app)


@babel.localeselector
def get_locale():
    """Selects an appropriate locale.

    Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""  # noqa
    try:
        return request.args['locale']
    except KeyError:
        try:
            return request.cookies['locale']
        except KeyError:
            return request.accept_languages.best_match(['ko', 'en'])


from core import *
from corpus import corpus_module
# from user import *
from api import api_module


app.register_blueprint(corpus_module, url_prefix='/corpus')
app.register_blueprint(api_module, url_prefix='')


@app.before_first_request
def init_rollbar():
    """init rollbar module"""
    rollbar.init(
        # access token
        config['rollbar_token'],
        # environment name
        config['rollbar_env'],
        # server root directory, makes tracebacks prettier
        root=os.path.dirname(os.path.realpath(__file__)),
        # flask already sets up logging
        allow_logging_basic_config=False,
        # Use HTTP as GAE does not allow the use of the SSL package
        endpoint='http://api.rollbar.com/api/1/')

    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8001))
    debug = bool(os.environ.get('DEBUG', 0))

    app.run(host=host, port=port, debug=debug)


if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    import os
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/': os.path.join(os.path.dirname(__file__), 'static')
    })
