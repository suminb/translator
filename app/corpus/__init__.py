from flask import Flask, Blueprint, jsonify, request, render_template, url_for
from flask.ext.paginate import Pagination

from app import logger
from app.models import db
from app.corpus.models import Corpus, CorpusRaw
from app.utils import parse_javascript

import json
import uuid, base62
import hashlib

corpus_module = Blueprint('corpus', __name__, template_folder='templates')


@corpus_module.route('/match')
def corpus_match():

    query = request.args.get('q', '')
    source_lang = request.args.get('sl', None)
    target_lang = request.args.get('tl', None)

    matches = Corpus.match(query, source_lang, target_lang)

    return json.dumps(map(lambda x: x.serialize(), matches))

@corpus_module.route('/raw', methods=['POST'])
def corpus_raw():
    """Collects raw corpus data."""

    raw, source_lang, target_lang = \
        map(lambda x: request.form[x], ('raw', 'sl', 'tl'))

    try:
        # See if 'raw' is a valid JavaScript string
        parsed = parse_javascript(raw)

        # Then insert it to the database
        CorpusRaw.insert(
            hash=hashlib.sha1(raw.encode('utf-8')).hexdigest(),
            raw=json.dumps(parsed),
            source_lang=source_lang,
            target_lang=target_lang,
        )
    except Exception as e:
        logger.exception(e)
        db.session.rollback()

        return str(e), 500

    return ''
