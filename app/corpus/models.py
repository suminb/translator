from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app import app
from app.models import db, BaseModel

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
    corpus_id = db.Column(UUID)
