from flask import Flask, Blueprint, jsonify, request, render_template, url_for
from flask.ext.paginate import Pagination

from app.corpus.models import Corpus

import json
import uuid, base62

corpus_module = Blueprint('corpus', __name__, template_folder='templates')


@corpus_module.route('/')
def corpus_list():

    page = int(request.args.get('page', 1))
    source_lang = request.args.get('sl', None)
    target_lang = request.args.get('tl', None)

    corpora = Corpus.query \
        .order_by(Corpus.avg_confidence.desc(), Corpus.frequency.desc())

    # TODO: Move this code to the models class
    if source_lang != None:
        corpora = corpora.filter_by(source_lang=source_lang)
    if target_lang != None:
        corpora = corpora.filter_by(target_lang=target_lang)

    pagination = Pagination(page=page, total=corpora.count(),
        per_page=20, 
        record_name='corpus')

    context = dict(
        # FIXME: Better way to deal with this?
        corpora=corpora.offset(pagination.per_page*(page-1)).limit(pagination.per_page),
        pagination=pagination,
    )

    return render_template('list.html', **context)


@corpus_module.route('/v1.2/match')
def corpus_match():

    query = request.args.get('q', '')
    source_lang = request.args.get('sl', None)
    target_lang = request.args.get('tl', None)

    matches = Corpus.match(query, source_lang, target_lang)

    return json.dumps(map(lambda x: x.serialize(), matches))
