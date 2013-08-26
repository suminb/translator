from flask import Flask, jsonify, request, render_template, url_for, redirect, session
from flaskext.babel import gettext as _
from flask.ext.login import login_required, login_user, logout_user, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import func, select
from datetime import datetime

from __init__ import __version__, app, logger, login_manager, get_locale, \
    VALID_LANGUAGES, DEFAULT_USER_AGENT, MAX_TEXT_LENGTH
from models import *
from utils import *
from forms import *

import requests
import json
import urllib
import uuid
import re
import base62
import os, sys
import pytz
import facebook
import nilsimsa

import config

# @app.route('/tr/<translation_id>/request')
# @login_required
# def translation_request(translation_id):
#     # FIXME: This UUID transitions are just a nonsense. Better fix this shit.
#     translation_id = base62.decode(translation_id)
#     translation = TranslationResponse.query.get(str(uuid.UUID(int=translation_id)))

#     context = dict(
#         version=__version__,
#         locale=get_locale(),
#         translation=translation,
#     )

#     return render_template('translation_request.html', **context)


@app.route('/v1.0/trs/<response_id>', methods=['DELETE'])
@login_required
def translation_response_delete(response_id):
    tres = TranslationResponse.fetch(response_id)

    try:
        tres.delete(current_user)

        return jsonify(dict(request_id=uuid_to_b62(tres.request_id)))

    except Exception as e:
        logger.exception(e)
        return str(e), 500


@app.route('/trequest/<request_id>/responses')
def translation_responses(request_id):

    treq = TranslationRequest.fetch(id_b62=request_id)

    if treq == None:
        return render_template('404.html', message=_('Requrested resource does not exist'))

    tresp1 = TranslationResponse.query.filter_by(
        request_id=treq.id,
        mode=1).first()

    tresp2 = TranslationResponse.query.filter_by(
        request_id=treq.id,
        mode=2).first()

    tresponses = Translation.query.filter_by(
        request_id=treq.id, mode=3) \
        .order_by(Translation.rating.desc(), Translation.count.desc())

    if not current_user.is_anonymous():
        ratings = Rating.query.filter(
            Rating.user_id == current_user.id,
            Rating.translation_id.in_(map(lambda r: r.id, tresponses))
        )
    else:
        ratings = []

    context = dict(
        locale=get_locale(),
        trequest=treq,
        tresponse1=tresp1,
        tresponse2=tresp2,
        tresponses=tresponses,
        ratings=ratings,
    )

    return render_template('translation_responses.html', **context)


@app.route('/v1.0/trq/<request_id>/response', methods=['POST'])
@login_required
def translation_request_response_api(request_id):
    """Translation response API"""

    def post(request_id):
        translated_text = request.form['text'].strip()

        if len(translated_text) <= 0:
            return _('Please provide a non-empty translation.'), 400
        else:
            tresp = TranslationResponse.insert(
                request_id=treq.id,
                user_id=current_user.id,
                source=treq.source,
                target=treq.target,
                mode=3,
                original_text_hash=treq.original_text_hash,
                translated_text=translated_text,
            )

            # TODO: Refactor the following code. This should be handled in the model class.
            # More precisely, in the insert() function.

            # All users who are watching the translation request
            watching = Watching.query.filter_by(entity_type='TranslationRequest', entity_id=treq.id)

            message = '''{1},

            Someone has posted a translation. {2}
            '''
            url = url_for('translation_responses', request_id=treq.id, _external=True)
            message = _(message).format(current_user.family_name, current_user.given_name, url)

            # Put them in the queue to get notified
            for w in watching:
                NotificationQueue.insert(user_id=w.user_id, payload=message)

        payload = tresp.serialize()
        payload['message'] = _('Your translation has been posted.')

        return jsonify(payload)

    treq = TranslationRequest.fetch(id_b62=request_id)

    if treq == None:
        return _('Requrested resource does not exist'), 404

    dispatch = dict(
        post=post)

    try:
        return dispatch[request.method.lower()](request_id)
    except Exception as e:
        logger.exception(e)
        return str(e), 500


@app.route('/trequest/<request_id>/response')
def translation_request_response(request_id):
    treq = TranslationRequest.fetch(id_b62=request_id)

    if treq == None:
        return render_template('404.html', message=_('Requrested resource does not exist'))

    tresp = None

    if not current_user.is_anonymous():
        tresp = TranslationResponse.fetch(
            user_id=current_user.id,
            original_text_hash=treq.original_text_hash,
            source=treq.source,
            target=treq.target,
            mode=3)

    if tresp != None:
        return redirect(url_for('translation_response', response_id=uuid_to_b62(tresp.id)))

    tresp1 = TranslationResponse.query.filter_by(
        request_id=treq.id,
        mode=1).first()

    tresp2 = TranslationResponse.query.filter_by(
        request_id=treq.id,
        mode=2).first()

    context = dict(
        version=__version__,
        locale=get_locale(),
        trequest=treq,
        tresponse1=tresp1,
        tresponse2=tresp2,
    )

    return render_template('translation/response.html', **context)


# @app.route('/trq/<trequest_id>/help')
# def translation_help_request_embedded(trequest_id):
#     """Embedded"""

#     trequest = TranslationRequest.fetch(id_b62=trequest_id)

#     context = dict(
#         version=__version__,
#         locale=get_locale(),
#         trequest=trequest,
#     )

#     return render_template('embedded/translation_help_request.html', **context)


@app.route('/hrequest')
def translation_help_requests():

    hrequests = TranslationRequest.query.filter(TranslationRequest.user_id != None).order_by(func.random()).limit(25)

    context = dict(
        version=__version__,
        locale=get_locale(),
        hrequests=hrequests,
    )

    return render_template('translation_help_requests.html', **context)


@app.route('/trequest/new', methods=['GET', 'POST'])
@app.route('/trequest/<hrequest_id>', methods=['GET', 'POST'])
@login_required
def translation_request(trequest_id=None):

    form = TranslationRequestForm(request.form)

    status_code = 200
    context = dict(
        version=__version__,
        locale=get_locale(),
        form=form,
    )

    if form.validate_on_submit():
        source = request.form['source']
        target = request.form['target']
        text = request.form['text']
        text_hash = nilsimsa.Nilsimsa(text.encode('utf-8')).hexdigest()

        try:
            trequest = TranslationRequest.insert(
                user_id=current_user.id,
                source=source,
                target=target,
                original_text=text,
                original_text_hash=text_hash,
            )

            Watching.insert(
                user_id=current_user.id,
                entity_type='TranslationRequest',
                entity_id=trequest.id
            )

            return redirect(url_for('translation_help_requests'))

        except IntegrityError as e:
            # If translation request already exists, redirect to the responses page.
            db.session.rollback()

            trequest = TranslationRequest.fetch(source=source, target=target,
                original_text_hash=text_hash)

            return redirect(url_for('translation_responses',
                request_id=uuid_to_b62(trequest.id)))

        except Exception as e:
            db.session.rollback()

            context['error'] = str(e)
            status_code = 500

    return render_template('translation/request.html', **context), status_code


# @app.route('/v1.0/hrequest', methods=['POST', 'DELETE'])
# @login_required
# def translation_help_request_api():
#     def post():
#         trans_req_id = request.form['treq_id']
#         trans_req = TranslationRequest.fetch(id_b62=trans_req_id)

#         if trans_req == None:
#             return _('Requrested resource does not exist'), 404

#         help_req_id = request.form.get('hreq_id', None)
        
#         if help_req_id == None:
#             # insertion

#             help_req = TranslationHelpRequest.insert(
#                 request_id=trans_req.id,
#                 user_id=current_user.id,
#                 comment=request.form.get('comment', None)
#             )
#         else:
#             # update
#             raise Exception('Not implemented')

#         return jsonify(help_req.serialize())

#     def delete():
#         raise Exception('Not implemented')

#     dispatch = dict(
#         post=post,
#         delete=delete,
#     )

#     try:
#         return dispatch[request.method.lower()]()
#     except Exception as e:
#         logger.exception(e)
#         return str(e), 500

@app.route('/tresponse/<response_id>')
@login_required
def translation_response(response_id):

    tresp = TranslationResponse.fetch(response_id)

    if tresp == None:
        return render_template("404.html", message=_('Requrested resource does not exist'))

    treq = TranslationRequest.fetch(id=tresp.request_id)

    # if tresp.mode in (1, 2):
    #     return redirect(url_for('index', translation_id=tresp.id_b62))

    tresp1 = TranslationResponse.query.filter_by(
        request_id=treq.id,
        mode=1).first()

    tresp2 = TranslationResponse.query.filter_by(
        request_id=treq.id,
        mode=2).first()

    context = dict(
        version=__version__,
        locale=get_locale(),
        trequest=treq,
        tresponse=tresp,
        tresponse1=tresp1,
        tresponse2=tresp2,
    )
    status_code = 200

    return render_template('translation/response.html', **context), status_code


@app.route('/v1.0/tr/<tresponse_id>/post/facebook', methods=['POST'])
@login_required
def tresponse_post_facebook(tresponse_id):
    """
    Post a link on the current_user's Facebook timeline

    https://developers.facebook.com/docs/reference/api/privacy-parameter/
    """
    tresp = TranslationResponse.fetch(id_b62=tresponse_id)

    target_language = _(VALID_LANGUAGES[tresp.request.target])

    try:
        graph = facebook.GraphAPI(session.get('oauth_token')[0])
        #graph.put_object('me', 'feed', message='This is a test with a <a href="http://translator.suminb.com">link</a>')
        post = graph.put_wall_post('', dict(
            name=_('app-title').encode('utf-8'),
            link='http://translator.suminb.com/trequest/{}/responses'.format(uuid_to_b62(tresp.request_id)),
            caption=_('{} has completed a translation challenge').format(tresp.user.name).encode('utf-8'),
            description=_('How do you say "{0}" in {1}?').format(tresp.request.original_text, target_language).encode('utf-8'),
            picture='http://translator.suminb.com/static/icon_128.png',
            #privacy={'value':'SELF'}
        ))

        post_log = TranslationPostLog.insert(
            request_id=tresp.request_id,
            user_id=current_user.id,
            target='Facebook',
            post_id=post['id'],
        )

        return jsonify(dict(
            post_id=post['id'],
            message=_('Your translation has been posted on your timeline.')
        ))

    except Exception as e:
        logger.exception(e)
        return str(e), 500


@app.route('/v1.0/tr/<tresponse_id>/rate', methods=['GET', 'POST'])
@login_required
def tresponse_rate(tresponse_id):
    rv = int(request.form['r'])
    if not (rv == -1 or rv == 1):
        return 'Invalid rating\n', 400

    tresponse = TranslationResponse.fetch(id_b62=tresponse_id)

    if tresponse == None:
        return 'Requested resource does not exist\n', 404

    r = Rating.query.filter_by(translation_id=tresponse.id, user_id=current_user.id).first()

    if r == None:
        r = Rating.insert(
            commit=False,
            translation_id=tresponse.id,
            user_id=current_user.id,
            rating=rv
        )
    else:
        r.timestamp = datetime.now(tz=pytz.utc)
        r.rating = rv

    try:
        db.session.commit()

        return jsonify(r.serialize())
    
    except Exception as e:
        logger.exception(e)
        db.session.rollback()

        return str(e), 500


@app.route('/nt')
def notification_test():

    params = dict(
        client_id=config.FACEBOOK_APP_ID,
        client_secret=config.FACEBOOK_APP_SECRET,
        grant_type='client_credentials')

    req = requests.get('https://graph.facebook.com/oauth/access_token', params=params)
    
    app_access_token = req.text[len('access_token='):]

    payload = dict(
        access_token=app_access_token,
        href='http://blog.suminb.com',
        template='This is a test',
    )
    print payload
    req = requests.post('https://graph.facebook.com/{}/notifications'.format(current_user.oauth_id), params=payload)

    return req.text, req.status_code
