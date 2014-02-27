from flask.ext.script import Manager

from app import app
from app.models import TranslationResponse, db
from app.corpus.models import *

manager = Manager(app)


@manager.command
def extract():
    """Extract corpora from translation_response"""

    for corpus_raw in CorpusRaw.query \
        .filter(CorpusRaw.flags == 0) \
        .limit(1000):

        print corpus_raw.raw[:80]

        try:
            corpus_raw.extract_corpora()
        except:
            db.session.rollback()


@manager.command
def index():
    """Produce corpus indices from corpora"""

    for corpus in Corpus.query \
        .filter(Corpus.aux_info == None) \
        .limit(1000):

        print '({}, {})'.format(
            corpus.source_text.encode('utf-8'),
            corpus.target_text.encode('utf-8'))

        corpus.create_index()

if __name__ == '__main__':
    manager.run()
