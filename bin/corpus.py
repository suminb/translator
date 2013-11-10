from flask.ext.script import Manager

from app import app
from app.corpus.models import *

manager = Manager(app)

@manager.command
def index():
    for corpus in Corpus.query:
        print '({}, {})'.format(
            corpus.source_text.encode('utf-8'),
            corpus.target_text.encode('utf-8'))

        corpus.create_index()

if __name__ == '__main__':
    manager.run()
