from flask import Flask, jsonify, request, render_template, url_for, redirect, session
from flaskext.babel import gettext as _
from flask.ext.login import login_required, login_user, logout_user, current_user
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
import base62
import os, sys
import pytz
import facebook


@app.route('/tr/<translation_id>/request')
@login_required
def translation_request(translation_id):
    # FIXME: This UUID transitions are just a nonsense. Better fix this shit.
    translation_id = base62.decode(translation_id)
    translation = TranslationResponse.query.get(str(uuid.UUID(int=translation_id)))

    context = dict(
        version=__version__,
        locale=get_locale(),
        translation=translation,
    )

    return render_template('translation_request.html', **context)


@app.route('/v1.0/trs/<response_id>', methods=['DELETE'])
@login_required
def translation_response_delete(response_id):
    tres = TranslationResponse.fetch(response_id)

    try:
        db.session.delete(tres)
        db.session.commit()

        return jsonify(dict(request_id=uuid_to_b62(tres.request_id)))

    except Exception as e:
        logger.exception(e)
        return str(e), 500


@app.route('/trq/<request_id>/responses')
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

    ratings = Rating.query.filter(
        Rating.user_id == current_user.id,
        Rating.translation_id.in_(map(lambda r: r.id, tresponses))
    )

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
def translation_request_response_api(request_id):
    def post(request_id):
        translated_text = request.form['text'].strip()

        # FIXME: Temporary
        if len(translated_text) <= 0:
            context['error'] = _('Please provide a non-empty translation.')
            status_code = 400
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
            #context['tresponse'] = tresp
            #context['success'] = _('Thanks for your submission.')

        return redirect(url_for('translation_response', response_id=tresp.id_b62))

    treq = TranslationRequest.fetch(id_b62=request_id)

    if treq == None:
        return _('Requrested resource does not exist'), 404

    dispatch = dict(
        post=post)

    return dispatch[request.method.lower()](request_id)


@app.route('/trq/<request_id>/response')
@login_required
def translation_request_response(request_id):
    treq = TranslationRequest.fetch(id_b62=request_id)

    if treq == None:
        return render_template('404.html', message=_('Requrested resource does not exist'))

    tresp = TranslationResponse.fetch(
        user_id=current_user.id,
        original_text_hash=treq.original_text_hash,
        source=treq.source,
        target=treq.target,
        mode=3)

    if tresp != None:
        return redirect(url_for('translation_response', response_id=tresp.id_b62))

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

    return render_template('translation_response.html', **context)


@app.route('/trs/<response_id>')
@login_required
def translation_response(response_id):

    tresp = TranslationResponse.fetch(response_id)

    if tresp == None:
        return render_template("404.html", message=_('Requrested resource does not exist'))

    treq = TranslationRequest.fetch(id=tresp.request_id)

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

    return render_template('translation_response.html', **context), status_code


@app.route('/v1.0/tr/<tresponse_id>/post', methods=['POST'])
@login_required
def tresponse_post(tresponse_id):
    """
    https://developers.facebook.com/docs/reference/api/privacy-parameter/
    """
    translation = Translation.fetch(id_b62=tresponse_id)

    target_language = _(VALID_LANGUAGES[translation.target])

    graph = facebook.GraphAPI(session.get('oauth_token')[0])
    #graph.put_object('me', 'feed', message='This is a test with a <a href="http://translator.suminb.com">link</a>')
    post_id = graph.put_wall_post('', dict(
        name=_('app-title').encode('utf-8'),
        link='http://translator.suminb.com/trq/{}/responses'.format(uuid_to_b62(translation.request_id)),
        caption=_('{} has completed a translation challenge').format(translation.user.name).encode('utf-8'),
        description=_('How do you say "{0}" in {1}?').format(translation.original_text, target_language).encode('utf-8'),
        picture='http://translator.suminb.com/static/icon_128.png',
        privacy={'value':'SELF'}
    ))
    return str(post_id)


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
        return str(e), 500
