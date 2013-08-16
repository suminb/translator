from functools import wraps
from flaskext.babel import gettext as _
from flask import g, request, redirect, url_for

from __init__ import app, VALID_LANGUAGES

import uuid, base62

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