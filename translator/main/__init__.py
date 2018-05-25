# -*- coding: utf-8 -*-
from flask import Blueprint, request, render_template, url_for, redirect
from flask.ext.babel import gettext as _
from datetime import datetime

from translator import __version__, get_locale
from translator.utils import language_options_html

import json
import os

main_module = Blueprint('main', __name__, template_folder='templates')


@main_module.route('/about.html')
def about():
    return render_template('about.html')


@main_module.route('/longtext.html')
def longtext():
    return render_template('longtext.html')


@main_module.route('/backupdb')
def backupdb():
    """This is a temporary workaround. We shall figure out how to store
    data in a relational database directly from the GAE. The problem we had
    was that we could not use psycopg2 package on GAE."""

    # NOTE: Minimal protection against malicious parties...
    api_key = request.args.get('api_key')
    from app import config
    if api_key != config['api_key']:
        return 'Invalid API key', 401

    limit = int(request.args.get('limit', 1000))
    from app.corpus.models import CorpusRaw, ndb
    query = CorpusRaw.query()
    entries = query.fetch(limit)
    output = '\n'.join(['{}\t{}\t{}\t{}'.format(
        x.source_lang, x.target_lang, x.timestamp, x.raw) for x in entries])
    ndb.delete_multi([x.key for x in entries])
    return output


#
# Request handlers
#
@main_module.route('/')
@main_module.route('/tr/<translation_id>')
def index(translation_id=None):
    """The main page."""

    if request.host == 'translator.suminb.com':
        return redirect('http://better-translator.com')

    # NOTE: Do not use HTTP GET parameters 'sl', 'tl', 'm' and 't'. These are
    # reserved for special purposes.

    # FIXME: The following values must exist in other pages as well
    user_agent = request.headers.get('User-Agent', [])
    is_android = 'Android' in user_agent
    is_iphone = 'iPhone' in user_agent
    is_msie = 'MSIE' in user_agent

    context = dict(
        version=__version__,
        locale=get_locale(),
        is_android=is_android,
        is_iphone=is_iphone,
        is_mobile=is_android or is_iphone,
        is_msie=is_msie,
        language_options=language_options_html(),
        debug=os.environ.get('DEBUG', None),
    )

    tresponse = None

    translation_id = translation_id or request.args.get('tr', None)

    # if translation_id != None:
    #    tresponse = TranslationResponse.fetch(id_b62=translation_id)

    if translation_id is not None and tresponse is None:
        return redirect(url_for('main.index'))

    if tresponse is not None:
        translation = tresponse.serialize()
        translation['original_text'] = tresponse.request.original_text
        # translation['translated_text_dictlink'] = link_dictionary(
        #     translation['translated_text'], translation['source'],
        #     translation['target'])

        context['og_description'] = tresponse.request.original_text
        context['translation'] = json.dumps(translation)
    else:
        context['og_description'] = _('app-description-text')

    return render_template('index.html', **context)


@main_module.route('/locale', methods=['GET', 'POST'])
def set_locale():
    """Copied from https://github.com/lunant/lunant-web/blob/homepage/lunant/__init__.py"""  # noqa
    if request.method == 'GET':
        locale = request.args['locale']
    else:
        locale = request.form['locale']

    if request.referrer:
        dest = request.referrer
    else:
        dest = url_for('main.index')

    response = redirect(dest)
    response.set_cookie('locale', locale, 60 * 60 * 24 * 14)
    return response


@main_module.route('/discuss.html')
def discuss():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('discuss.html', **context)


@main_module.route('/credits.html')
def credits():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('credits.html', **context)


@main_module.route('/statistics')
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


@main_module.route('/v1.0/test')
def test():
    """Produces arbitrary HTTP responses for debugging purposes."""

    status_code = int(request.args['status_code'])
    message = request.args['message']

    if 200 <= status_code < 600 and len(message) <= 8000:
        return message, status_code
    else:
        return '', 400


@main_module.route('/disclaimers.html')
def disclaimers():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('disclaimers.html', **context)


@main_module.route('/tests')
def tests():
    return render_template('tests/test.html')


@main_module.teardown_request
def teardown_request(exception):
    """Refer http://flask.pocoo.org/docs/tutorial/dbcon/ for more details."""
    pass


@main_module.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', version=__version__,
                           message='Page Not Found'), 404


@main_module.route('/captcha', methods=['GET', 'POST'])
def captcha():
    return render_template('captcha.html')
