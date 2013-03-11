from flask import Flask, jsonify, request, render_template
from jinja2 import evalcontextfilter, Markup, escape
from jinja2.environment import Environment

import os
import requests
import json
import urllib

app = Flask(__name__)

def __translate__(text, source, target):
    """
    text: text to be translated
    source: source language
    target: target language
    """
    headers = {
        'referer': 'http://translate.google.com',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22'
    }
    params = {
        'client': 'x',
        'sl': source,
        'tl': target,
        'text': text
    }
    url = 'http://translate.google.com/translate_a/t'
    r = requests.get(url, headers=headers, params=params)

    data = json.loads(r.text)

    return data['sentences'][0]['trans']
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
    text = request.args.get('text')
    mode = request.args.get('mode')

    if mode == '2':
        translated = __translate__(text, 'ko', 'ja')
        translated = __translate__(translated, 'ja', 'en')
    else:
        translated = __translate__(text, 'ko', 'en')

    return translated

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
