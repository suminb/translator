from flask import Flask, jsonify, request, render_template, url_for, redirect, session
from flask.ext.babel import gettext as _
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

try:
    import config
except:
    import dummyconfig as config


@app.route('/user')
@login_required
def user_page():

    hrequests = TranslationRequest.query \
        .filter_by(user_id=current_user.id) \
        .order_by(TranslationRequest.timestamp.desc())

    context = dict(
        version=__version__,
        locale=get_locale(),
        hrequests=hrequests,
    )

    return render_template('user_page.html', **context)

    
@app.route('/user/<user_id>/responses')
@login_required
def user_translation_responses(user_id):
    user_id = b62_to_uuid(user_id)
    tresponses = TranslationResponse.query \
        .filter_by(user_id=str(user_id)) \
        .order_by(TranslationResponse.timestamp.desc())

    context = dict(
        version=__version__,
        locale=get_locale(),
        tresponses=tresponses,
    )

    return render_template('user/translation_responses.html', **context)


