from functools import wraps
from flask.ext.babel import gettext as _
from flask import g, request, redirect, url_for, jsonify

from __init__ import app, VALID_LANGUAGES

import uuid, base62
import json

class HTTPException(RuntimeError):
    """HTTPError does not take keyword arguments, so we are defining a custom exception class."""
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        super(HTTPException, self).__init__()


def get_remote_address(req):
    if not req.headers.getlist('X-Forwarded-For'):
        return req.remote_addr
    else:
        return req.headers.getlist('X-Forwarded-For')[0]


@app.template_filter('uuid_to_b62')
def uuid_to_b62(value):
    return base62.encode(uuid.UUID(value).int)

def b62_to_uuid(value):
    return uuid.UUID(int=base62.decode(value))

@app.template_filter('date')
def _jinja2_filter_datetime(date, fmt=None):
    """Copied from http://monocaffe.blogspot.com/2013/03/jinja2-template-datetime-filters-in.html"""
    if fmt:
        return date.strftime(fmt)
    else:
        return date.strftime(_('%%m/%%d/%%Y'))


@app.template_filter('language_name')
def _jinja2_filter_language_name(value):
    if value in VALID_LANGUAGES:
        return _(VALID_LANGUAGES[value])
    else:
        return value

@app.template_filter('jsonify')
def _jinja2_filter_jsonify(value):
    return jsonify(value)


@app.template_filter('form_errors_to_js')
def form_errors_to_js(form):
    buf = []

    for field, errors in form.errors.items():
        errors = map(lambda x: "'{}'".format(x), errors)
        buf.append('{}: [{}]'.format(field, ','.join(errors)))

    return '{' + ','.join(buf) + '}'


def language_options():
    import operator

    tuples = [(key, _(VALID_LANGUAGES[key])) for key in VALID_LANGUAGES]
    return sorted(tuples, key=operator.itemgetter(1))

def language_options_html():
    import operator

    tuples = [(key, _(VALID_LANGUAGES[key])) for key in VALID_LANGUAGES]
    sorted_tuples = sorted(tuples, key=operator.itemgetter(1))

    return '\n'.join(['<option value="%s">%s</option>' % (k, v) for k, v in sorted_tuples])

def parse_javascript(text):
    # NOTE: This may not work in some cases...
    text = text.replace(',,,', ',null,null,')
    text = text.replace(',,', ',null,')
    text = text.replace('[,', '[null,')

    return json.loads(text.encode('utf-8'))
