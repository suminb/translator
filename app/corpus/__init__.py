from flask import Flask, Blueprint, jsonify, request, render_template, url_for
from flask.ext.paginate import Pagination

from app.corpus.models import Corpus

corpus_module = Blueprint('corpus', __name__, template_folder='templates')

print corpus_module.root_path

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


# FIXME: This should be a standalone script rather than an HTTP call
@corpus_module.route('/trigger-index')
def trigger_index():

    corpora = Corpus.query.filter(Corpus.source_lang == 'ko').limit(10)
    for corpus in corpora:
        corpus.create_index()

    return ''