# -*- coding: utf-8 -*- 

__version__ = '1.1.11'

from flask import Flask
from flask.ext.login import LoginManager

import os, sys
import logging
import config

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

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22'
MAX_TEXT_LENGTH = 8000

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI
app.secret_key = config.SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

logger = logging.getLogger('translator')
logger.addHandler(logging.FileHandler('translator.log')) 
logger.setLevel(logging.INFO)

#app.jinja_env.filters['uuid_to_b62'] = uuid_to_b62

from core import *

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = bool(os.environ.get('DEBUG', 0))

    app.run(host=host, port=port, debug=debug)


if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    import os
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/': os.path.join(os.path.dirname(__file__), 'static')
    })
