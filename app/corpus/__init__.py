from flask import Flask, Blueprint, jsonify, request, render_template, url_for
from flask.ext.paginate import Pagination

from app.corpus.models import Corpus

import json
import uuid, base62

corpus_module = Blueprint('corpus', __name__, template_folder='templates')


@corpus_module.route('/')
def corpus_list():

    page = int(request.args.get('page', 1))

    corpora = Corpus.query \
        .filter(Corpus.frequency > 1) \
        .order_by(Corpus.avg_confidence.desc(), Corpus.frequency.desc())

    pagination = Pagination(page=page, total=corpora.count(),
        per_page=20, 
        record_name='corpus')

    context = dict(
        # FIXME: Better way to deal with this?
        corpora=corpora.offset(pagination.per_page*(page-1)).limit(pagination.per_page),
        pagination=pagination,
    )

    return render_template('list.html', **context)


@corpus_module.route('/match')
def corpus_match():

    query = request.args.get('query', '')

    matches = Corpus.match(query)

    # NOTE: Not sure how efficient the following is going to be.
    if len(matches) > 0:
        matches = zip(*matches)
        matches[2] = map(lambda x: base62.encode(uuid.UUID(x).int), matches[2])
        matches = zip(*matches)

    return json.dumps(matches)
