from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.dialects.postgresql import UUID
from __init__ import app

import uuid

db = SQLAlchemy(app)

def serialize(obj):
    import json
    if isinstance(obj.__class__, DeclarativeMeta):
        # an SQLAlchemy class
        fields = {}
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
            data = obj.__getattribute__(field)
            try:
                json.dumps(data) # this will fail on non-encodable values, like other classes
                fields[field] = data
            except TypeError:
                fields[field] = None
        # a json-encodable dict
        return fields


class Translation(db.Model):
    id = db.Column(UUID, primary_key=True)
    serial = db.Column(db.Integer, db.Sequence('translation_serial_seq'))
    timestamp = db.Column(db.DateTime(timezone=True))
    user_agent = db.Column(db.String(255))
    remote_address = db.Column(db.String(64))
    source = db.Column(db.String(16))
    target = db.Column(db.String(16))
    mode = db.Column(db.Integer)
    original_text = db.Column(db.Text)
    translated_text = db.Column(db.Text)
    intermediate_text = db.Column(db.Text)
    original_text_hash = db.Column(db.String(255))

    def serialize(self):
        return serialize(self)


class Rating(db.Model):
    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    user_agent = db.Column(db.String(255))
    remote_address = db.Column(db.String(64))
    rating = db.Column(db.Integer)
    token = db.Column(db.String(128))


class User(db.Model):
    __table_args__ = ( db.UniqueConstraint('oauth_provider', 'oauth_id'), {} )

    id = db.Column(UUID, primary_key=True)

    oauth_provider = db.Column(db.String(255))
    oauth_id = db.Column(db.String(255))
    oauth_username = db.Column(db.String(255))

    family_name = db.Column(db.String(255))
    given_name = db.Column(db.String(255))
    email = db.Column(db.String(255))

    gender = db.Column(db.String(6))
    locale = db.Column(db.String(16))

    @staticmethod
    def insert(payload={}):
        user = User(id=str(uuid.uuid4()))
        for key in payload:
            user.__setattr__(key, payload[key])

        db.session.add(user)
        db.session.commit()

    def serialize(self):
        return serialize(self)