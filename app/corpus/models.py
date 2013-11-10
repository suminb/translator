from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from winnowing import winnow, kgrams, winnowing_hash, sanitize

from app import app
from app.models import db, BaseModel

if db.engine.driver != 'psycopg2':
    UUID = db.String
    ARRAY = db.String


FINGERPRINT_K = 4


class Corpus(db.Model, BaseModel):
    """A corpus is a pair of strings shorter than 255 characters each."""

    __table_args__ = ( db.UniqueConstraint('source_lang', 'target_lang',
        'source_text', 'target_text'), )

    id = db.Column(UUID, primary_key=True)
    source_lang = db.Column(db.String(16))
    target_lang = db.Column(db.String(16))
    source_text = db.Column(db.String(255)) # NOTE: Not sure if this is the number of bytes or the number of characters
    target_text = db.Column(db.String(255))
    confidence = db.Column(db.Integer)
    frequency = db.Column(db.Integer)
    aux_info = db.Column(db.Text)
    avg_confidence = confidence / frequency


    def create_index(self):
        fingerprints = winnow(self.source_text, FINGERPRINT_K)
        #fingerprints = kgrams(self.source_text, 4)

        for i, h in fingerprints:
            #print i, h, self.source_text[i:]
            if i != -1:
                try:
                    CorpusIndex.insert(
                        source_hash=h,
                        source_index=i,
                        corpus_id=self.id,
                    )
                except IntegrityError as e:
                    db.session.rollback()


    @staticmethod
    def match(text):
        #fingerprints = winnow(text)
        
        agtext = zip(xrange(len(text)), text)
        agtext = sanitize(agtext)

        #print list(kgrams(agtext, FINGERPRINT_K))

        hashes = map(lambda x: winnowing_hash(x), kgrams(agtext, FINGERPRINT_K))

        #print zip(*hashes)

        # for kgram in kgrams(agtext, FINGERPRINT_K):
        #     print kgram, ', ',
        # print 
        # print hashes

        indices = CorpusIndex.query \
                    .filter(CorpusIndex.source_hash.in_(zip(*hashes)[1])) \
                    .all()

        buf = []
        for index in indices:
            t = (index.source_index, index.source_hash,
                index.corpus.id,
                index.corpus.source_text, index.corpus.target_text,
                index.corpus.confidence, index.corpus.frequency)
            buf.append(t)

        return buf


class CorpusIndex(db.Model, BaseModel):
    # Without __tablename__ attribute, the following error will occur.
    # sqlalchemy.exc.InvalidRequestError: Class <class 'app.models.Watching'>
    # does not have a __table__ or __tablename__ specified and does not inherit
    # from an existing table-mapped class.
    __tablename__ = 'corpus_index'
    __table_args__ = ( db.PrimaryKeyConstraint('source_hash', 'source_index',
        'corpus_id'), {} )

    source_hash = db.Column(db.Integer)
    source_index = db.Column(db.Integer)
    corpus_id = db.Column(UUID, db.ForeignKey('corpus.id'))
    corpus = relationship('Corpus')