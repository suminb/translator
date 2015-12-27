# -*- coding: utf-8 -*-
from flask import Blueprint, request, render_template, url_for, redirect
from flask.ext.babel import gettext as _
from datetime import datetime

from app import __version__, get_locale
from app.utils import language_options_html

import json
import os

main_module = Blueprint('main', __name__, template_folder='templates')


@main_module.route('/longtext')
def longtext():
    return render_template('longtext.html')


@main_module.route('/download-clients')
def download_clients():
    # Indicates whether we want to show a 'your client is outdated' message
    outdated = bool(request.args.get('outdated', False))

    from app import config
    context = {'config': config, 'outdated': outdated}

    return render_template('download_clients.html', **context)


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
    from corpus.models import CorpusRaw, ndb
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

    """
    NOTE: Do not use HTTP GET parameters 'sl', 'tl', 'm' and 't'. These are
    reserved for special purposes.
    """
    user_agent = request.headers.get('User-Agent', [])
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

    tresponse = None

    translation_id = translation_id or request.args.get('tr', None)

    #if translation_id != None:
    #    tresponse = TranslationResponse.fetch(id_b62=translation_id)

    if translation_id is not None and tresponse is None:
        return redirect(url_for('index'))

    if tresponse is not None:
        translation = tresponse.serialize()
        translation['original_text'] = tresponse.request.original_text
        #translation['translated_text_dictlink'] = link_dictionary(
        #translation['translated_text'], translation['source'], translation['target'])

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


@main_module.route('/discuss')
def discuss():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('discuss.html', **context)


@main_module.route('/credits')
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


@main_module.route('/disclaimers')
def disclaimers():
    context = dict(
        version=__version__,
        locale=get_locale(),
    )
    return render_template('disclaimers.html', **context)


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
    return """
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head><meta http-equiv="content-type" content="text/html; charset=utf-8"><meta name="viewport" content="initial-scale=1"><title>http://translate.google.com/translate_a/t?client=t</title></head>
<body style="font-family: arial, sans-serif; background-color: #fff; color: #000; padding:20px; font-size:18px;" onload="e=document.getElementById('captcha');if(e){e.focus();}">
<div style="max-width:400px;">
 <hr noshade size="1" style="color:#ccc; background-color:#ccc;"><br>
 
  To continue, please type the characters below:<br><br>
  <img src="/sorry/image?id=15806218432220984486&amp;hl=en" border="1" alt="Please enable images"><br><br><form action="CaptchaRedirect" method="get"><input type="hidden" name="continue" value="http://translate.google.com/translate_a/t?client=t"><input type="hidden" name="id" value="15806218432220984486"><input type="text" name="captcha" value="" id="captcha" size="12" style="font-size:16px; padding:3px 0 3px 5px; margin-left:0px;"><input type="submit" name="submit" value="Submit" style="font-size:18px; padding:4px 0;"><br><br><br></form>
  <hr noshade size="1" style="color:#ccc; background-color:#ccc;">
  
   <div style="font-size:13px;">
    <b>About this page</b><br><br>Our systems have detected unusual traffic from your computer network.  This page checks to see if it&#39;s really you sending the requests, and not a robot.  <a href="#" onclick="document.getElementById('infoDiv').style.display='block';">Why did this happen?</a><br><br>
    <div id="infoDiv" style="display:none; background-color:#eee; padding:10px; margin:0 0 15px 0; line-height:1.4em;">
     This page appears when Google automatically detects requests coming from your computer network which appear to be in violation of the <a href="//www.google.com/policies/terms/">Terms of Service</a>. The block will expire shortly after those requests stop.  In the meantime, solving the above CAPTCHA will let you continue to use our services.<br><br>This traffic may have been sent by malicious software, a browser plug-in, or a script that sends automated requests.  If you share your network connection, ask your administrator for help &mdash; a different computer using the same IP address may be responsible.  <a href="//support.google.com/websearch/answer/86640">Learn more</a><br><br>Sometimes you may be asked to solve the CAPTCHA if you are using advanced terms that robots are known to use, or sending requests very quickly.
    </div>

 
 
 
 IP address: 8.35.200.36<br>Time: 2013-11-17T10:28:53Z<br>URL: http://translate.google.com/translate_a/t?client=t<br>
 </div>
</div>
</body>
</html>
""".strip()
