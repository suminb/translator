# -*- coding: utf-8 -*- 

from flask import Flask, jsonify, request, render_template, url_for, redirect, session
from flask.ext.babel import gettext as _
from flask.ext.login import login_required, login_user, logout_user, current_user
from flask_oauthlib.client import OAuth
from jinja2 import evalcontextfilter, Markup, escape
from jinja2.environment import Environment
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from __init__ import __version__, app, logger, login_manager, get_locale, \
    VALID_LANGUAGES, DEFAULT_USER_AGENT, MAX_TEXT_LENGTH
from models import *
from utils import *

import requests
import json
import urllib
import uuid
import re
import hashlib
import nilsimsa # Locality Sensitive Hash
import base62
import os, sys
import pytz
import facebook

try:
    import config
except:
    import dummyconfig as config

oauth = OAuth()

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


def __translate__(text, source, target, client='x', user_agent=DEFAULT_USER_AGENT):
    """
    text: text to be translated
    source: source language
    target: target language
    """

    if source == target:
        return text

    from hallucination import ProxyFactory
    proxy_factory = ProxyFactory(
        db_engine=db.engine,
        logger=logger
    )

    if not re.match(r'Mozilla/\d+\.\d+ \(.*', user_agent):
        user_agent = 'Mozilla/5.0 (%s)' % user_agent

    headers = {
        'Referer': 'http://translate.google.com',
        'User-Agent': user_agent,
        'Content-Length': str(sys.getsizeof(text))
    }
    payload = {
        'client': client,
        'sl': source,
        'tl': target,
        'text': text
    }
    url = 'http://translate.google.com/translate_a/t'

    req = None
    try:
        req = proxy_factory.make_request(url, headers=headers, params=payload,
            req_type=requests.post, timeout=2, pool_size=10)
    except Exception as e:
        logger.exception(e)

    if req == None:
        # if request via proxy fails
        req = requests.post(url, headers=headers, data=payload)

    if req.status_code != 200:
        raise HTTPException(
            ('Google Translate returned HTTP {}'.format(req.status_code)),
            req.status_code)


    if client == 'x':
        data = json.loads(req.text)

        try:
            #if target == 'ja':
            #    sentences = data['sentences']
            sentences = data['sentences']
        except:
            sentences = data['results'][0]['sentences']

        result = ' '.join(map(lambda x: x['trans'], sentences))

        # Remove unneccessary white spaces
        return '\n'.join(map(lambda x: x.strip(), result.split('\n')))
    
    elif client == 't':
        # NOTE: This may break down in some cases...
        text = req.text
        text = text.replace(',,,', ',null,null,')
        text = text.replace(',,', ',null,')

        parsed = json.loads(text)

        return parsed

    else:
        raise Exception("Unsupported client '{}'".format(client))


# def __language_options__():
#     import operator

#     tuples = [(key, _(VALID_LANGUAGES[key])) for key in VALID_LANGUAGES]
#     sorted_tuples = [('', '')] + sorted(tuples, key=operator.itemgetter(1))

#     return '\n'.join(['<option value="%s">%s</option>' % (k, v) for k, v in sorted_tuples])


#
# Request handlers
#
@app.route('/')
@app.route('/tr/<translation_id>')
def index(translation_id=None):
    
    if request.host == 'translator.suminb.com':
        return redirect('http://better-translator.com')

    """
    NOTE: Do not use HTTP GET parameters 'sl', 'tl', 'm' and 't'. These are
    reserved for special purposes.
    """
    user_agent = request.headers.get('User-Agent')
    is_android = 'Android' in user_agent
    is_iphone = 'iPhone' in user_agent
    is_msie = 'MSIE' in user_agent

    context = dict(
        version=__version__,
        locale=get_locale(),
        is_android=is_android,
        is_msie=is_msie,
        language_options=language_options_html(),
        debug=os.environ.get('DEBUG', None),
    )

    row = None

    translation_id = translation_id or request.args.get('tr', None)

    if translation_id != None:
        row = Translation.fetch(id_b62=translation_id)

    if translation_id != None and row == None:
        return redirect(url_for('index'))

    if row != None:
        translation = row.serialize()
        translation['translated_text_dictlink'] = link_dictionary(
            translation['translated_text'], translation['source'], translation['target'])

        context['og_description'] = row.original_text
        context['translation'] = json.dumps(translation)
    else:
        context['og_description'] = _('app-description-text')

    return render_template('index.html', **context)


@app.route('/locale', methods=['GET', 'POST'])
def set_locale():
    """Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""
    if request.method == 'GET':
        locale = request.args['locale']
    else:
        locale = request.form['locale']

    if request.referrer:
        dest = request.referrer
    else:
        dest = url_for('index')

    response = redirect(dest)
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
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('discuss.html', **context)


@app.route('/credits')
def credits():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('credits.html', **context)

@app.route('/statistics')
def statistics():
    if request.args.get('format') == 'json':
        from analytics import generate_output
        from flask import Response
        return Response(generate_output(), mimetype='application/json')
    else:
        context = dict(
            version=__version__,
            timestamp=datetime.now().strftime('%Y%m%d%H%M')
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
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    try:
        return translate(text, mode, source, target)['translated_text']

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
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    try:
        return jsonify(translate(text, mode, source, target))

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        logger.exception(e)
        return str(e), 500


@app.route('/v1.1/translate', methods=['POST'])
def translate_1_1():
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
    """
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    try:
        payload = translate(text, mode, source, target)
        payload['translated_text_dictlink'] = link_dictionary(
            payload['translated_text'], source, target)
        return jsonify(payload)

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        logger.exception(e)
        return str(e), 500


@app.route('/v1.2/translate', methods=['POST'])
def translate_1_2():
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
    """
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    try:
        payload = translate(text, mode, source, target, 't')

        return jsonify(payload)

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        logger.exception(e)
        return str(e), 500


def translate(text, mode, source, target, client='x'):

    if len(text) == 0:
        raise HTTPException('Text cannot be empty.', 400)

    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException('Text too long.', 413)

    if source == target:
        return dict(
            id=None,
            id_b62=None,
            intermediate_text=None,
            translated_text=text)

    if source not in VALID_LANGUAGES.keys():
        raise HTTPException('Invalid source language.', 400)
    if target not in VALID_LANGUAGES.keys():
        raise HTTPException('Invalid target language.', 400)

    original_text_hash = nilsimsa.Nilsimsa(text.encode('utf-8')).hexdigest()
    user_agent = request.headers.get('User-Agent')

    access_log = TranslationAccessLog.insert(
        commit=False,
        user_id=current_user.id if not current_user.is_anonymous() else None,
        user_agent=user_agent,
        remote_address=get_remote_address(request),
    )

    treq = TranslationRequest.fetch(
        original_text_hash=original_text_hash,
        source=source, target=target)

    if treq == None:
        treq = TranslationRequest.insert(
            commit=False,
            user_id=None,
            source=source,
            target=target,
            original_text=text,
            original_text_hash=original_text_hash,
        )

    tresp = TranslationResponse.fetch(
        original_text_hash=original_text_hash,
        source=source, target=target, mode=mode)

    if tresp == None:

        # NOTE: The following may be time consuming operations
        if mode == '1':
            intermediate = None
            translated = __translate__(text, source, target, client, user_agent)
        elif mode == '2':
            intermediate = __translate__(text, source, 'ja', client, user_agent)

            if client == 't':
                intermediate = intermediate[0][0][0]

            translated = __translate__(intermediate, 'ja', target, client, user_agent)
        else:
            return HTTPException('Invalid translation mode.', 400)

        tresp = TranslationResponse.insert(
            commit=False,
            request_id=treq.id,
            source=source,
            target=target,
            mode=mode,
            original_text_hash=original_text_hash,
            intermediate_text=intermediate,
            translated_text=translated,
        )

        if access_log.flag == None:
            access_log.flag = TranslationAccessLog.FLAG_CREATED
        else:
            access_log.flag |= TranslationAccessLog.FLAG_CREATED


    access_log.translation_id = tresp.id

    try:
        db.session.commit()
    except Exception as e:
        logger.exception(e)
        db.session.rollback()

    return dict(
        id=base62.encode(uuid.UUID(tresp.id).int),
        request_id=base62.encode(uuid.UUID(treq.id).int),
        intermediate_text=tresp.intermediate_text,
        translated_text=tresp.translated_text)


def link_dictionary(text, source, target):
    """A naive implementation of English dictionary link feature."""

    if source == 'ko' and target == 'en':
        pattern = re.compile(r'[a-zA-Z_-]+')
        buf = []

        for line in text.split('\n'):
            for word in line.split():
                if len(word) > 1 and pattern.match(word) != None:
                    # TODO: Prettify code
                    buf.append('<a href="{}" class="dictionary-link">{}</a>'.format(
                        url_for('dictionary', query=word, source=source, target=target), word))
                else:
                    buf.append(word)

                buf.append(' ')
            buf.append('\n')

        return ''.join(buf)

    else:
        return text


@app.route('/dictionary')
def dictionary():
    keys = ('query', 'source', 'target')
    query, source, target = map(lambda k: request.args[k].strip(), keys)

    # TODO: URL encode

    if source == 'ko' and target == 'en':
        return redirect('http://endic.naver.com/search.nhn?searchOption=all&query={}'.format(query))
    elif source == 'en' and target == 'ko':
        return redirect('http://endic.naver.com/search.nhn?searchOption=all&query={}'.format(query))
    else:
        return 'Dictionary not available', 406


@app.route('/v1.0/test')
def test():
    """Produces arbitrary HTTP responses for debugging purposes."""

    status_code = int(request.args['status_code'])
    message = request.args['message']

    if 200 <= status_code < 600 and len(message) <= 8000:
        return message, status_code
    else:
        return '', 400


@app.route('/disclaimers')
def disclaimers():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('disclaimers.html', **context)


@app.route('/privacy')
def privacy():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('privacy.html', **context)


@app.route('/flush-queue')
def flush_notification_queue():
    """I know this is a pretty silly solution, but for some reason gettext()
    does not work when I invoke it from notification.py that runs on a shell."""

    def sendmail(notification):

        url = url_for('translation_responses', request_id=notification.payload, _external=True)
        body = _('{0},\n\nSomeone has posted a translation. Check out at {1}').format(notification.user.name, url)

        message = Message(
            subject=_('You have a notification from Better Translator'),
            body=body,
            sender=(_('app-title'), 'translator@suminb.com'),
            recipients=[notification.user.email]
        )

        mail.send(message)
        db.session.delete(notification)

    from flask.ext.mail import Mail, Message

    app.config['MAIL_SERVER'] = config.MAIL_SERVER
    app.config['MAIL_PORT'] = config.MAIL_PORT
    app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD

    mail = Mail(app)

    try:
        for notification in NotificationQueue.query.limit(100):
            sendmail(notification)

        db.session.commit()

        return ''

    except Exception as e:
        logger.exception(e)
        return str(e), 500


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

    # Fields to fetch
    # https://developers.facebook.com/docs/reference/api/user/
    fields = ('id', 'name', 'first_name', 'last_name', 'middle_name',
        'username', 'gender', 'locale', 'picture', 'link', 'age_range', 'timezone',
        'updated_time', 'verified', 'bio', 'birthday', 'email', 'location',
        'website', 'work')

    me = facebook_app.get('/me', data=dict(fields=','.join(fields)))

    print me.data

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
        'gender': 'gender',
    }

    try:
        user = User.query.filter_by(oauth_id=me.data['id']).first()

        if user == None:
            payload = dict(extra_info=json.dumps(me.data))

            for key in key_mappings:
                oauth_key = key_mappings[key]
                payload[key] = me.data[oauth_key]

            user = User.insert(**payload)

        else:
            key_mappings.pop('oauth_id')
            for key in key_mappings:
                oauth_key = key_mappings[key]
                setattr(user, key, me.data[oauth_key])

            user.extra_info = json.dumps(me.data)

            db.session.commit()

    # except IntegrityError as e:
    #     logger.info('User %s (%s) already exists.' % (payload['oauth_username'],
    #         payload['oauth_id']))

    except Exception as e:
        logger.exception(e)
        return str(e), 500

    login_user(user)
    
    keys = ('id', 'username', 'first_name', 'last_name', 'email', 'locale', 'gender',)
    for key in keys:
        session['oauth_%s' % key] = me.data[key]

    return redirect(request.args.get('next', '/'))

    #return 'Logged in as id=%s name=%s, email=%s, redirect=%s' % \
    #    (me.data['id'], me.data['name'], me.data['email'], request.args.get('next'))


@app.route('/logout')
def logout():
    session['login'] = False
    logout_user()
    # if request.referrer:
    #     return redirect(request.referrer)
    # else:
    return redirect('/')


@facebook_app.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')


@app.teardown_request
def teardown_request(exception):
    """Refer http://flask.pocoo.org/docs/tutorial/dbcon/ for more details."""
    if db is not None:
        db.session.close()


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html',
        version=__version__, message='Page Not Found'), 404


# NOTE: Temporary
# def integrate():
#     for tresp in TranslationResponse.query.filter_by(request_id=None):
#         treq = TranslationRequest.fetch(
#             original_text_hash=tresp.original_text_hash,
#             source=tresp.source, target=tresp.target)
#         tresp.request_id = treq.id

#     db.session.commit()

#     return ''
