from datetime import datetime

from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY, JSON

from app import app
import uuid64


db = SQLAlchemy(app)


class CRUDMixin(object):
    """Copied from https://realpython.com/blog/python/python-web-applications-with-flask-part-ii/
    """  # noqa

    __table_args__ = {'extend_existing': True}

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)

    @classmethod
    def create(cls, commit=True, **kwargs):
        kwargs.update(dict(id=uuid64.issue()))
        instance = cls(**kwargs)

        if hasattr(instance, 'timestamp') \
                and getattr(instance, 'timestamp') is None:
            instance.timestamp = datetime.utcnow()

        return instance.save(commit=commit)

    @classmethod
    def get(cls, id):
        return cls.query.get(id)

    # We will also proxy Flask-SqlAlchemy's get_or_44
    # for symmetry
    @classmethod
    def get_or_404(cls, id):
        return cls.query.get_or_404(id)

    @classmethod
    def exists(cls, **kwargs):
        row = cls.query.filter_by(**kwargs).first()
        return row is not None

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.iteritems():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()


class Sentence(db.Model, CRUDMixin):
    __tablename__ = 'sentence'
    __table_args__ = (db.UniqueConstraint('source_lang', 'target_lang',
                                          'source_text_hash'), {})
    observed_at = db.Column(db.DateTime(timezone=False))
    source_lang = db.Column(db.String(16))
    target_lang = db.Column(db.String(16))
    source_text_hash = db.Column(db.String(255))
    source_text = db.Column(db.Text)
    target_text = db.Column(db.Text)


class Phrase(db.Model, CRUDMixin):
    __tablename__ = 'phrase'
    __table_args__ = (db.UniqueConstraint('source_lang', 'target_lang',
                                          'source_text_hash'), {})
    observed_at = db.Column(db.DateTime(timezone=False))
    source_lang = db.Column(db.String(16))
    target_lang = db.Column(db.String(16))
    source_text_hash = db.Column(db.String(255))
    source_text = db.Column(db.String(255))
    target_texts = db.Column(ARRAY(db.String))
    raw = db.Column(JSON)
