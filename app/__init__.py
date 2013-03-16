from flask import Flask, jsonify, request, render_template
from flaskext.babel import Babel, gettext as _
from flaskext.babel import *
from jinja2 import evalcontextfilter, Markup, escape
from jinja2.environment import Environment

# This guy does not take keyword arguments
#from requests.exceptions import HTTPError

import os, sys
import requests
import json
import urllib

app = Flask(__name__)

babel = Babel(app)


class HTTPException(RuntimeError):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super(HTTPException, self).__init__()

def log(source, target, mode, text, translated):
    """Naive logging function"""

    from datetime import datetime
    from random import randint
    from json import dumps

    f = open('../../logs/stat.%d.log' % randint(0, 100), 'a')
    payload = [
        datetime.now().isoformat(),
        target,
        source,
        mode,
        '"%s"' % text.replace('"', '\\"'),
        '"%s"' % translated[0].replace('"', '\\"')
    ]
    f.write((','.join(payload) + '\n').encode('utf-8'))
    f.close()

@babel.localeselector
def get_locale():
    """Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""
    try:
        return request.args['locale']
    except KeyError:
        try:
            return request.cookies['locale']
        except KeyError:
            return request.accept_languages.best_match(['ko', 'en'])


def __translate__(text, source, target):
    """
    text: text to be translated
    source: source language
    target: target language
    """

    if source == target:
        return text

    headers = {
        'Referer': 'http://translate.google.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22',
        #'Content-Length': str(sys.getsizeof(text))
    }
    payload = {
        'client': 'x',
        'sl': source,
        'tl': target,
        'text': text
    }
    url = 'http://translate.google.com/translate_a/t'
    r = requests.get(url, headers=headers, params=payload)

    if r.status_code != 200:
        raise HTTPException(('Google Translate returned HTTP %d' % r.status_code), r.status_code)

    try:
        data = json.loads(r.text)

        print data

        try:
            #if target == 'ja':
            #    sentences = data['sentences']
            sentences = data['sentences']
        except:
            sentences = data['results'][0]['sentences']

        print 'aaaaa'

        return ' '.join(map(lambda x: x['trans'], sentences)), 200

    except Exception as e:
        raise Exception('An error has occured: "%s" If the problem persists, you may report it <a href="/discuss">here</a>.' % str(e))


#
# Request handlers
#
@app.route('/')
def index():
    print babel.list_translations()
    context = dict(locale=get_locale())
    return render_template("index.html", **context)


@app.route("/locale", methods=['POST'])
def set_locale():
    """Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""
    locale = request.form["locale"]
    response = redirect(url_for("index"))
    response.set_cookie("locale", locale, 60 * 60 * 24 * 14)
    return response


@app.route('/discuss')
def discuss():
    return render_template("discuss.html")


@app.route('/credits')
def credits():
    return render_template("credits.html")


@app.route('/translate', methods=['POST'])
def translate():
    valid_languages = ['en', 'fr', 'ja', 'ko', 'ru', 'zh-CN']

    text = request.form['text']
    mode = request.form['mode']
    source = request.form['source']
    target = request.form['target']

    if source == target:
        return text

    if source not in valid_languages:
        return 'Invalid source language\n', 400
    if target not in valid_languages:
        return 'Invalid target language\n', 400

    try:
        if mode == '2':
            translated = __translate__(text, source, 'ja')
            translated = __translate__(translated, 'ja', target)
        else:
            translated = __translate__(text, source, target)

        log(source, target, mode, text, translated)

        return translated

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        return str(e), 500


if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 80))
    debug = bool(os.environ.get('DEBUG', 0))

    app.run(host=host, port=port, debug=debug)

if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    import os
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/': os.path.join(os.path.dirname(__file__), 'static')
    })
