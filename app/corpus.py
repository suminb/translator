from flask import Flask, jsonify, request, render_template, url_for
from flask.ext.paginate import Pagination

from __init__ import __version__, app, logger, login_manager, get_locale, \
    VALID_LANGUAGES, DEFAULT_USER_AGENT, MAX_TEXT_LENGTH
from models import Corpus

@app.route('/corpus')
def corpus_list():

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    corpora = Corpus.query.order_by(Corpus.avg_confidence.desc(), Corpus.frequency.desc())

    pagination = Pagination(page=page, total=corpora.count(),
        per_page=20, 
        record_name='corpus')

    context = dict(
        # FIXME: Better way to deal with this?
        corpora=corpora.offset(pagination.per_page*(page-1)).limit(pagination.per_page),
        pagination=pagination,
    )

    return render_template('corpus/list.html', **context)
