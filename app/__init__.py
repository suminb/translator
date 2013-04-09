# -*- coding: utf-8 -*- 

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
import uuid
import datetime

import base62

import config


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_URI

babel = Babel(app)

from models import *

VALID_LANGUAGES = ['en', 'es', 'fr', 'ja', 'ko', 'ru', 'zh-CN', 'id']

# FIXME: This is a temporary solution to deal with burst peak of traffic
TR_CACHE = {
    u'여러분이 몰랐던 구글 번역기': ['You did not know Google translator', 'Google translation that you did not know'],
    u'청년들을 타락시킨 죄로 독콜라를 마시는 홍민희': ['Poison drinking cola sin corrupting the youth hongminhui', 'Honminfui cola drink poison sin was to corrupt the youth'],
    u'샌디에고에 살고 있는 김근모씨는 오늘도 힘찬 출근': ['Keun Mossi live in San Diego energetic to work today', 'Mr. Gimugun who lives in San Diego today healthy attendance'],
    u'구글은 세계 정복을 꿈꾸고 있다.': ['I dream of world conquest.', 'Google have a dream to conquer the world.'],
    u'호준이는 비싼 학비 때문에 허리가 휘어집니다.': ['Because the waist is bent. Hojun expensive tuition', 'Hojun will stoop for expensive tuition.'],
    u'강선구 이사님은 오늘도 새로운 기술을 찾아나선다.': ['Sets out to find a new technology today. Gangseongu Shirley', 'Gansongu director leaves to find a new technology today.'],
}

class HTTPException(RuntimeError):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super(HTTPException, self).__init__()

def get_remote_address(req):
    if not req.headers.getlist('X-Forwarded-For'):
        return req.remote_addr
    else:
        return req.headers.getlist('X-Forwarded-For')[0]

def log(source, target, mode, text, translated):
    """Naive logging function"""

    from datetime import datetime
    from random import randint
    from json import dumps

    home = os.path.expanduser("~")
    log_path = os.path.join(home, 'logs/user/translator/stat.%d.log' % randint(0, 99))

    f = open(log_path, 'a')
    payload = [
        datetime.now().isoformat(),
        source,
        target,
        mode,
        '"%s"' % text.replace('"', '\\"').replace('\r', '').replace('\n', '\\n'),
        '"%s"' % translated[0].replace('"', '\\"').replace('\r', '').replace('\n', '\\n')
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


def __translate__(text, source, target, user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22'):
    """
    text: text to be translated
    source: source language
    target: target language
    """

    if source == target:
        return text

    headers = {
        'Referer': 'http://translate.google.com',
        'User-Agent': user_agent,
        #'Content-Length': str(sys.getsizeof(text))
    }
    payload = {
        'client': 'x',
        'sl': source,
        'tl': target,
        'text': text
    }
    url = 'http://translate.google.com/translate_a/t'
    r = requests.post(url, headers=headers, data=payload)

    if r.status_code != 200:
        raise HTTPException(('Google Translate returned HTTP %d' % r.status_code), r.status_code)

    try:
        data = json.loads(r.text)

        try:
            #if target == 'ja':
            #    sentences = data['sentences']
            sentences = data['sentences']
        except:
            sentences = data['results'][0]['sentences']

        return ' '.join(map(lambda x: x['trans'], sentences))

    except Exception as e:
        raise Exception('An error has occured: "%s" If the problem persists, you may report it <a href="/discuss">here</a>.' % str(e))


#
# Request handlers
#
@app.route('/')
@app.route('/sr/<serial>')
def index(serial=''):
    user_agent = request.headers.get('User-Agent')
    is_android = 'Android' in user_agent

    context = dict(locale=get_locale(),
        serial=serial,
        is_android=is_android)

    if serial != '':
        row = Translation.query.filter_by(serial=base62.decode(serial)).first()

        if row == None:
            context['message'] = _('Requrested resource does not exist')
            return render_template("404.html", **context)

        context['og_description'] = row.original_text
        context['translation'] = json.dumps(row.serialize())
    else:
        context['og_description'] = _("app-description-text")

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
    return render_template('discuss.html')


@app.route('/credits')
def credits():
    return render_template('credits.html')

@app.route('/statistics')
def statistics():
    if request.args.get('format') == 'json':
        from analytics import generate_output
        from flask import Response
        return Response(generate_output(), mimetype='application/json')
    else:
        return render_template('statistics.html')

# deprecated
@app.route('/translate', methods=['GET', 'POST'])
@app.route('/v0.9/translate', methods=['GET', 'POST'])
def translate_0_9():
    return translate()['translated_text']

@app.route('/v1.0/translate', methods=['GET', 'POST'])
def translate_1_0():
    return jsonify(translate())

def translate():
    text = request.form['t'].strip()
    mode = request.form['m'].strip()
    source = request.form['sl'].strip()
    target = request.form['tl'].strip()

    # FIXME: This is a temporary solution to deal with burst peak of traffic
    if text in TR_CACHE:
        if source == 'ko' and target == 'en':
            i = 0 if mode == '1' else 1

            return dict(
                serial_b62=None,
                translated_text=TR_CACHE[text][i])

    user_agent = request.headers.get('User-Agent')

    if source == target:
        return text

    if source not in VALID_LANGUAGES:
        return 'Invalid source language\n', 400
    if target not in VALID_LANGUAGES:
        return 'Invalid target language\n', 400

    try:
        if mode == '2':
            translated = __translate__(text, source, 'ja', user_agent)
            translated = __translate__(translated, 'ja', target, user_agent)
        else:
            translated = __translate__(text, source, target, user_agent)

        # Legacy logger
        log(source, target, mode, text, translated)

        # TODO: Refactor this section
        translation = Translation(id=str(uuid.uuid4()))
        translation.timestamp = datetime.datetime.now()
        translation.user_agent = user_agent
        translation.remote_address = get_remote_address(request)
        translation.source = source
        translation.target = target
        translation.mode = mode
        translation.original_text = text
        translation.translated_text = translated

        db.session.add(translation)
        db.session.commit()

        return dict(
            serial_b62='0z'+base62.encode(translation.serial),
            translated_text=translated)

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        return str(e), 500


@app.route('/v0.9/fetch/<serial>', methods=['GET'])
def fetch(serial):
    import base62

    if not serial.startswith('0z'):
        return 'Invalid serial format\n', 400

    serial = base62.decode(serial[2:])

    row = Translation.query.filter_by(serial=serial).first()

    if row == None:
        return 'Requested resource does not exist\n', 404

    return jsonify(row.serialize())


@app.route('/v0.9/store', methods=['POST'])
def store():
    """Stores a translation and generates a permalink.
    """

    # TODO: Clean up the following code
    original = request.form['t']
    translated = request.form['s']
    mode = request.form['m']
    source = request.form['sl']
    target = request.form['tl']

    if source not in VALID_LANGUAGES:
        return 'Invalid source language\n', 400
    if target not in VALID_LANGUAGES:
        return 'Invalid target language\n', 400

    import psycopg2.extras

    psycopg2.extras.register_uuid()

    t = Translation(id=uuid.uuid4(), timestamp=datetime.datetime.now())
    t.source = source
    t.target = target
    t.mode = mode
    t.original_text = original
    t.translated_text = translated
    t.is_sample = False

    try:
        db.session.add(t)
        db.session.commit()

        # FIXME: Base62 encoding must be done in the frontend
        # NOTE: UUID is not JSON serializable
        return jsonify(id=str(t.id), serial=t.serial, base62='0z'+base62.encode(t.serial))
    
    except Exception as e:
        return str(e), 500


@app.route('/v0.9/rate/<serial>', methods=['POST'])
def rate(serial):
    """
    :param id: Translation serial
    :type id: string (base62 representation)
    """

    rating = request.form['r']

    t = Translation.query.filter_by(serial=base62.decode(serial)).first()

    if t == None:
        return 'Requested resource does not exist\n', 404

    r = Rating(id=str(uuid.uuid4()), translation_id=t.id, timestamp=datetime.datetime.now())
    r.rating = int(rating)
    r.user_agent = request.headers.get('User-Agent')
    r.remote_address = get_remote_address(request)

    try:
        db.session.add(r)
        db.session.commit()

        # NOTE: UUID is not JSON serializable
        return jsonify(id=str(r.id))
    
    except Exception as e:
        return str(e), 500


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', message='Page Not Found'), 404


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
