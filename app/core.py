# -*- coding: utf-8 -*- 

from flask import Flask, jsonify, request, render_template, url_for, redirect, session
from flaskext.babel import Babel, gettext as _
from flask.ext.login import login_required, login_user, current_user
from flask_oauthlib.client import OAuth
from jinja2 import evalcontextfilter, Markup, escape
from jinja2.environment import Environment
from sqlalchemy.exc import IntegrityError

from __init__ import __version__, app, logger, login_manager
from models import *
from utils import *

import requests
import json
import urllib
import uuid
import datetime
import re
import nilsimsa # Locality Sensitive Hash
import base62
import os, sys
import facebook

import config

babel = Babel(app)
oauth = OAuth()

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

facebook_app = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=config.FACEBOOK_APP_ID,
    consumer_secret=config.FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email, publish_stream'}
)

# DO NOT MOVE THIS TO __init__.py
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


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


def __translate__(text, source, target, user_agent=DEFAULT_USER_AGENT):
    """
    text: text to be translated
    source: source language
    target: target language
    """

    from hallucination import ProxyFactory
    proxy_factory = ProxyFactory(
        config=dict(db_uri=config.HALLUCINATION_DB_URI),
        logger=logger
    )

    if source == target:
        return text

    if not re.match(r'Mozilla/\d+\.\d+ \(.*', user_agent):
        user_agent = 'Mozilla/5.0 (%s)' % user_agent

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

    r = None
    try:
        r = proxy_factory.make_request(url, headers=headers, params=payload, req_type=requests.post)
    except Exception as e:
        logger.error(str(e))

    if r == None:
        # if request via proxy fails
        r = requests.post(url, headers=headers, data=payload)

    if r.status_code != 200:
        raise HTTPException(('Google Translate returned HTTP %d' % r.status_code), r.status_code)

    data = json.loads(r.text)

    try:
        #if target == 'ja':
        #    sentences = data['sentences']
        sentences = data['sentences']
    except:
        sentences = data['results'][0]['sentences']

    result = ' '.join(map(lambda x: x['trans'], sentences))

    # Remove unneccessary white spaces
    return '\n'.join(map(lambda x: x.strip(), result.split('\n')))


def __language_options__():
    import operator

    tuples = [(key, _(VALID_LANGUAGES[key])) for key in VALID_LANGUAGES]
    sorted_tuples = sorted(tuples, key=operator.itemgetter(1))

    return '\n'.join(['<option value="%s">%s</option>' % (k, v) for k, v in sorted_tuples])


# @app.before_request
# def check_for_maintenance():
#     maintenance_mode = bool(os.environ.get('MAINTENANCE', 0))
#     if maintenance_mode and request.path != url_for('maintenance'): 
#         return redirect(url_for('maintenance'))

#
# Request handlers
#
@app.route('/')
@app.route('/sr/<serial>') # Deprecated (2013-07-24)
@app.route('/tr/<translation_id>')
def index(translation_id=None, serial=None):
    user_agent = request.headers.get('User-Agent')
    is_android = 'Android' in user_agent
    is_msie = 'MSIE' in user_agent

    context = dict(
        version=__version__,
        locale=get_locale(),
        serial=serial,
        is_android=is_android,
        is_msie=is_msie,
        language_options=__language_options__())

    row = None

    if translation_id != None:
        # FIXME: This UUID transitions are just a nonsense. Better fix this shit.
        translation_id = base62.decode(translation_id)
        row = Translation.query.get(str(uuid.UUID(int=translation_id)))

    elif serial != None:
        row = Translation.query.filter_by(serial=base62.decode(serial)).first()

    if (translation_id != None or serial != None) and row == None:
        context['message'] = _('Requrested resource does not exist')
        return render_template("404.html", **context)

    if row != None:
        context['og_description'] = row.original_text
        context['translation'] = json.dumps(row.serialize())
    else:
        context['og_description'] = _('app-description-text')

    return render_template('index.html', **context)


@app.route('/locale', methods=['POST'])
def set_locale():
    """Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""
    locale = request.form['locale']
    response = redirect(url_for('index'))
    response.set_cookie('locale', locale, 60 * 60 * 24 * 14)
    return response


@app.route('/languages')
@app.route('/v1.0/languages')
def languages():
    """Returns a list of supported languages."""
    locale = request.args['locale']
    langs = {k: _(v) for (k, v) in zip(VALID_LANGUAGES.keys(), VALID_LANGUAGES.values())}

    return jsonify(langs)

@app.route('/discuss')
def discuss():
    return render_template('discuss.html', version=__version__)


@app.route('/credits')
def credits():
    return render_template('credits.html', version=__version__)

@app.route('/statistics')
def statistics():
    if request.args.get('format') == 'json':
        from analytics import generate_output
        from flask import Response
        return Response(generate_output(), mimetype='application/json')
    else:
        context = dict(
            version=__version__,
            timestamp=datetime.datetime.now().strftime('%Y%m%d%H%M')
        )
        return render_template('statistics.html', **context)

# deprecated
@app.route('/translate', methods=['POST'])
@app.route('/v0.9/translate', methods=['POST'])
def translate_0_9():
    """
    Deprecated
    
    :param sl: source language
    :type sl: string
    :param tl: target language
    :type tl: string
    :param m: mode ( 1 for normal, 2 for better )
    :type m: int
    :param t: text to be translated
    :type t: string

    Translates given text.

    .. deprecated:: 2706db734a3654eed5ac84b7a2703d5b96df4cbc

    **Example Request**:

    .. sourcecode:: http

        POST /v0.9/translate HTTP/1.1
        User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22
        Host: 192.168.0.185:5000
        Accept: */*
        Content-Length: 37
        Content-Type: application/x-www-form-urlencoded

        sl=en&tl=ko&m=2&t=This is an example.

    **Example Response**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: text/html; charset=utf-8
        Content-Length: 23
        Server: Werkzeug/0.8.3 Python/2.7.3
        Date: Wed, 10 Apr 2013 06:37:40 GMT

        이것은 예입니다.
    """
    try:
        return translate()['translated_text']

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        return str(e), 500

@app.route('/v1.0/translate', methods=['POST'])
def translate_1_0():
    """
    :param sl: source language
    :type sl: string
    :param tl: target language
    :type tl: string
    :param m: mode ( 1 for normal, 2 for better )
    :type m: int
    :param t: text to be translated
    :type t: string

    Translates given text.

    **Example Request**:

    .. sourcecode:: http

        POST /v1.0/translate HTTP/1.1
        User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22
        Host: 192.168.0.185:5000
        Accept: */*
        Content-Length: 57
        Content-Type: application/x-www-form-urlencoded

        sl=ko&tl=en&m=2&t=여러분이 몰랐던 구글 번역기

    **Example Response**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 90
        Server: Werkzeug/0.8.3 Python/2.7.3
        Date: Wed, 10 Apr 2013 06:43:13 GMT

        {
          "translated_text": "Google translation that you did not know",
          "serial_b62": "0z19x",
          "intermediate_text": "\u7686\u3055\u3093\u304c\u77e5\u3089\u306a\u304b\u3063\u305fGoogle\u306e\u7ffb\u8a33"
        }

    **Example iOS Code using ILHTTPClient**

    ILHTTPClient: https://github.com/isaaclimdc/ILHTTPClient

    .. sourcecode:: objective-c

        ILHTTPClient *client = [ILHTTPClient clientWithBaseURL:@"http://translator.suminb.com/" showingHUDInView:self.view];
            NSDictionary *params = @{
                                        @"sl": @"en",
                                        @"tl": @"ko",
                                        @"m": @"2",
                                        @"t": @"Google translation that you did not know."
            };
            
            [client postPath:@"/v1.0/translate"
                  parameters:params
                 loadingText:@"Loading..."
                 successText:@"Success!"
               multiPartForm:^(id<AFMultipartFormData> formData) {
               }
                     success:^(AFHTTPRequestOperation *operation, NSString *response) {
                         NSLog(@"%@", response);
                     }
                     failure:^(AFHTTPRequestOperation *operation, NSError *error) {
                     }
            ];
    """
    try:
        return jsonify(translate())

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        return str(e), 500

def translate():
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    if source == target:
        return text

    if source not in VALID_LANGUAGES.keys():
        return 'Invalid source language\n', 400
    if target not in VALID_LANGUAGES.keys():
        return 'Invalid target language\n', 400

    original_text_hash = nilsimsa.Nilsimsa(text.encode('utf-8')).hexdigest()

    translation = Translation.fetch(None, original_text_hash, source, target, mode)

    if translation == None:
        user_agent = request.headers.get('User-Agent')

        # NOTE: The following is time consuming operations
        if mode == '2':
            intermediate = __translate__(text, source, 'ja', user_agent)
            translated = __translate__(intermediate, 'ja', target, user_agent)
        else:
            intermediate = None
            translated = __translate__(text, source, target, user_agent)

        # NOTE: Therefore check one more time if a record exists
        translation = Translation.fetch(None, original_text_hash, source, target, mode)

        if translation is None:
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
            translation.intermediate_text = intermediate
            translation.original_text_hash = original_text_hash

            db.session.add(translation)
            db.session.commit()

    return dict(
        id=translation.id,
        id_b62=base62.encode(uuid.UUID(translation.id).int),
        serial_b62=base62.encode(translation.serial),
        intermediate_text=translation.intermediate_text,
        translated_text=translation.translated_text)



@app.route('/v0.9/fetch/<serial>', methods=['GET'])
def fetch(serial):
    import base62

    serial = base62.decode(serial)

    row = Translation.query.filter_by(serial=serial).first()

    if row == None:
        return 'Requested resource does not exist\n', 404

    return jsonify(row.serialize())


@app.route('/v0.9/rate/<serial>', methods=['POST'])
def rate(serial):
    """
    Deprecated (2013-07-24)
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


@app.route('/v1.0/rate/<translation_id>', methods=['POST'])
def rate_v1_0(translation_id):
    """
    :param id: Translation id
    :type id: string (base62 representation)
    """

    t = Translation.fetch(id_b62=translation_id)

    if t == None:
        return 'Requested resource does not exist\n', 404

    r = Rating(id=str(uuid.uuid4()), translation_id=t.id, timestamp=datetime.datetime.now())
    r.rating = int(request.form['r'])
    r.user_agent = request.headers.get('User-Agent')
    r.remote_address = get_remote_address(request)

    try:
        db.session.add(r)
        db.session.commit()

        # NOTE: UUID is not JSON serializable
        return jsonify(id=str(r.id))
    
    except Exception as e:
        return str(e), 500


@app.route('/v1.0/test')
def test():
    """Produces arbitrary HTTP responses for debugging purposes."""

    status_code = int(request.args['status_code'])
    message = request.args['message']

    if 200 <= status_code < 600 and len(message) <= 8000:
        return message, status_code
    else:
        return '', 400

@app.route('/maintenance')
def maintenance():
    return render_template('maintenance.html', version=__version__), 503


@app.route('/tr/<translation_id>/request')
@login_required
def translation_request(translation_id):
    # FIXME: This UUID transitions are just a nonsense. Better fix this shit.
    translation_id = base62.decode(translation_id)
    translation = Translation.query.get(str(uuid.UUID(int=translation_id)))

    context = dict(
        referrer=request.referrer,
        locale=get_locale(),
        translation=translation,
    )

    return render_template('translation_request.html', **context)


@app.route('/tr/<translation_id>/response', methods=['GET', 'POST'])
@login_required
def translation_response(translation_id):
    # FIXME: This UUID transitions are just a nonsense. Better fix this shit.
    translation_id = uuid.UUID(int=base62.decode(translation_id))

    if request.method == 'POST':
        TranslationResponse.insert_or_update(translation_id, current_user.id, request.form)

        return redirect(url_for('translation_response',
            translation_id=base62.encode(translation_id.int)))
    else:
        translation = Translation.query.get(str(translation_id))
        tresponse = TranslationResponse.fetch(translation_id, current_user.id)

        context = dict(
            referrer=request.referrer,
            locale=get_locale(),
            translation=translation,
            tresponse=tresponse,
        )

        return render_template('translation_response.html', **context)


@app.route('/tr/<translation_id>/post')
def translation_post(translation_id):
    print session.get('oauth_token')
    graph = facebook.GraphAPI(session.get('oauth_token')[0])
    #graph.put_object('me', 'feed', message='This is a test with a <a href="http://translator.suminb.com">link</a>')
    post_id = graph.put_wall_post('message body', dict(
        name='Link name',
        link='http://translator.suminb.com',
        caption='{*actor*} posted a new stuff',
        description='This is a longer description of the attachment',
        picture='http://translator.suminb.com/static/icon_256.png',
    ))
    return str(post_id)


@app.route('/login')
def login():
    session['login'] = True
    return facebook_app.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))


@app.route('/login/authorized')
@facebook_app.authorized_handler
def facebook_authorized(resp):
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        ), 401

    session['oauth_token'] = (resp['access_token'], '')

    me = facebook_app.get('/me')

    # Somehow this not only is disfunctional, but also it prevents other 
    # session values to be set
    #session['oauth_data'] = me.data

    key_mappings = {
        # User model : Facebook OAuth
        'oauth_id': 'id',
        'oauth_username': 'username',
        'given_name': 'first_name',
        'family_name': 'last_name',
        'email': 'email',
        'locale': 'locale',
    }

    payload = {}

    for key in key_mappings:
        oauth_key = key_mappings[key]
        payload[key] = me.data[oauth_key]

    try:
        user = User.insert(payload)
        login_user(user)

    except IntegrityError as e:
        logger.info(str(e))
        #logger.info('User %s (%s) already exists.' % (payload['oauth_username'],
        #    payload['oauth_id']))
    
    keys = ('id', 'username', 'first_name', 'last_name', 'email', 'locale', 'gender',)
    for key in keys:
        session['oauth_%s' % key] = me.data[key]

    return redirect('/')

    #return 'Logged in as id=%s name=%s, email=%s, redirect=%s' % \
    #    (me.data['id'], me.data['name'], me.data['email'], request.args.get('next'))


@facebook_app.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html',
        version=__version__, message='Page Not Found'), 404
