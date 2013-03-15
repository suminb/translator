from flask import Flask, jsonify, request, render_template
from jinja2 import evalcontextfilter, Markup, escape
from jinja2.environment import Environment

# This guy does not take keyword arguments
#from requests.exceptions import HTTPError

import os, sys
import requests
import json
import urllib

app = Flask(__name__)

class HTTPException(RuntimeError):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super(HTTPException, self).__init__()


def __translate__(text, source, target):
    """
    text: text to be translated
    source: source language
    target: target language
    """
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

        try:
            sentences = data['sentences']
        except:
            sentences = data['results'][0]['sentences']

        return ' '.join(map(lambda x: x['trans'], sentences)), 200

    except Exception as e:
        raise Exception('An error has occured: "%s" If the problem persists, you may report it <a href="/discuss">here</a>.' % str(e))
#
# Request handlers
#
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/discuss')
def discuss():
    return render_template("discuss.html")

@app.route('/translate')
def translate():
    valid_languages = ['en', 'ja', 'ko']

    text = request.args.get('text')
    mode = request.args.get('mode')
    source = request.args.get('source')
    target = request.args.get('target')

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
