from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from __init__ import app

import uuid
import base62

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
        # Synthesized property
        self.id_b62 = '0z' + base62.encode(uuid.UUID(self.id).int)

        return serialize(self)

    @staticmethod
    def fetch(id_b62=None, original_text_hash=None, source=None, target=None, mode=None):
        if id_b62 != None:
            translation_id = base62.decode(id_b62)
            return Translation.query.get(str(uuid.UUID(int=translation_id)))

        else:
            return Translation.query.filter_by(
                original_text_hash=original_text_hash,
                source=source, target=target, mode=mode).first()


class TranslationResponse(db.Model):
    # Users may submit a translation response only once
    __table_args__ = ( db.UniqueConstraint('translation_id', 'user_id'), {} )

    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    text = db.Column(db.Text)

    def serialize(self):
        return serialize(self)

    @staticmethod
    def fetch(translation_id, user_id):
        return TranslationResponse.query.filter(and_(
            TranslationResponse.translation_id == str(translation_id),
            TranslationResponse.user_id == str(user_id)
        )).first()

    @staticmethod
    def insert_or_update(translation_id, user_id, values):
        tresponse = TranslationResponse.fetch(translation_id, user_id)
        text = values['text'].strip()

        if tresponse == None:
            tresponse = TranslationResponse(
                id=str(uuid.uuid4()),
                translation_id=translation_id,
                user_id=user_id,
                timestamp=datetime.now(),
                text=text,
            )
            db.session.add(tresponse)

        else:
            #tresponse.timestamp = datetime.now()
            tresponse.text = text

        db.session.commit()

        return tresponse


class Rating(db.Model):
    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    user_agent = db.Column(db.String(255))
    remote_address = db.Column(db.String(64))
    rating = db.Column(db.Integer)
    token = db.Column(db.String(128))


class User(db.Model, UserMixin):
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

        return user

    def serialize(self):
        return serialize(self)