import json
import hashlib
import os
from datetime import datetime

import yaml
from elasticsearch import Elasticsearch
from flask import Flask, Blueprint, jsonify, request, render_template, url_for
from flask.ext.paginate import Pagination

from app import config, logger
from app.corpus.models import Corpus, CorpusRaw
from app.utils import parse_javascript


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

    hash = hashlib.sha1(raw.encode('utf-8')).hexdigest(),

    body = {
        'timestamp': datetime.now(),
        'hash': hash,
        'raw': raw,
        'source_lang': source_lang,
        'target_lang': target_lang,
        'server': os.environ['SERVER_SOFTWARE'],
    }

    index = 'translator'
    doc_type = 'translation_android'

    es = Elasticsearch([{'host': config['es_host'], 'port': config['es_port']}])
    res = es.index(index=index, doc_type=doc_type, id=hash, body=body)
    return ''
