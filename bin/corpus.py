from flask.ext.script import Manager

from app import app
from app.models import TranslationResponse
from app.corpus.models import *

manager = Manager(app)


@manager.command
def extract():
    """Extract corpora from translation_response"""

    for tresponse in TranslationResponse.query \
        .filter(TranslationResponse.translated_raw != None) \
        .filter(TranslationResponse.aux_info == None) \
        .limit(1000):

        print tresponse.translated_text
        tresponse.process_corpora()

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
