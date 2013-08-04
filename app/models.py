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


class TranslationRequest(db.Model):
    id = db.Column(UUID, primary_key=True)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    source = db.Column(db.String(16))
    target = db.Column(db.String(16))
    original_text = db.Column(db.Text)
    original_text_hash = db.Column(db.String(255))

    def serialize(self):
        # Synthesized property
        self.id_b62 = base62.encode(uuid.UUID(self.id).int)

        return serialize(self)

    @staticmethod
    def fetch(id_b62=None, original_text_hash=None, source=None, target=None):
        if id_b62 != None:
            translation_id = base62.decode(id_b62)
            return TranslationRequest.query.get(str(uuid.UUID(int=translation_id)))

        else:
            return TranslationRequest.query.filter_by(
                original_text_hash=original_text_hash,
                source=source, target=target).first()

    @staticmethod
    def insert(**kwargs):
        treq = TranslationRequest(id=str(uuid.uuid4()))
        treq.timestamp = datetime.now()

        for key, value in kwargs.iteritems():
            setattr(treq, key, value);

        db.session.add(treq)
        db.session.commit()

        return treq


class TranslationResponse(db.Model):
    __table_args__ = ( db.UniqueConstraint('user_id', 'source', 'target', 'mode', 'original_text_hash'), )

    id = db.Column(UUID, primary_key=True)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    source = db.Column(db.String(16))
    target = db.Column(db.String(16))
    mode = db.Column(db.Integer)
    original_text_hash = db.Column(db.String(255))
    intermediate_text = db.Column(db.Text)
    translated_text = db.Column(db.Text)

    def serialize(self):
        # Synthesized property
        self.id_b62 = base62.encode(uuid.UUID(self.id).int)

        return serialize(self)

    @staticmethod
    def fetch(id_b62=None, original_text_hash=None, source=None, target=None, mode=None):
        if id_b62 != None:
            translation_id = base62.decode(id_b62)
            return TranslationResponse.query.get(str(uuid.UUID(int=translation_id)))

        else:
            return TranslationResponse.query.filter_by(
                original_text_hash=original_text_hash,
                source=source, target=target, mode=mode).first()

    @staticmethod
    def insert(**kwargs):
        tresp = TranslationResponse(id=str(uuid.uuid4()))
        tresp.timestamp = datetime.now()

        for key, value in kwargs.iteritems():
            setattr(tresp, key, value);

        db.session.add(tresp)
        db.session.commit()

        return tresp

class Translation(db.Model):
    """
    CREATE VIEW translation AS
        SELECT tres.id, tres.user_id, tres.timestamp,
            tres.source, tres.target, tres.mode,
            treq.original_text, tres.original_text_hash, tres.intermediate_text,
            tres.translated_text FROM translation_response AS tres
        JOIN translation_request AS treq ON
            tres.source = treq.source AND
            tres.target = treq.target AND
            tres.original_text_hash = treq.original_text_hash
    """
    id = db.Column(UUID, primary_key=True)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    source = db.Column(db.String(16))
    target = db.Column(db.String(16))
    mode = db.Column(db.Integer)
    original_text = db.Column(db.Text)
    original_text_hash = db.Column(db.String(255))
    intermediate_text = db.Column(db.Text)
    translated_text = db.Column(db.Text)

    def serialize(self):
        # Synthesized property
        self.id_b62 = base62.encode(uuid.UUID(self.id).int)

        return serialize(self)

"""
class TranslationResponse(db.Model):
    # Users may submit a translation response only once
    _table_args__ = ( db.UniqueConstraint('translation_id', 'user_id'), {} )

    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    text = db.Column(db.Text)

    def serialize(self):
        return serialize(self)

    @staticmethod
    def fetch(id_b62):
        tresponse_id = base62.decode(id_b62)
        return TranslationResponse.query.get(str(uuid.UUID(int=tresponse_id)))

    @staticmethod
    def fetch_all(translation_id, user_id):
        return TranslationResponse.query.filter(and_(
            TranslationResponse.translation_id == str(translation_id),
            TranslationResponse.user_id == str(user_id)
        )).order_by(TranslationResponse.timestamp.desc())

    @staticmethod
    def insert(translation_id, user_id, values):
        text = values['text'].strip()

        tresponse = TranslationResponse(
            id=str(uuid.uuid4()),
            translation_id=str(translation_id),
            user_id=user_id,
            timestamp=datetime.now(),
            text=text,
        )
        db.session.add(tresponse)
        db.session.commit()

        return tresponse


class TranslationResponseLatest(db.Model):
    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    text = db.Column(db.Text)
"""

class Rating(db.Model):
    __table_args__ = ( db.UniqueConstraint('translation_id', 'user_id'), )

    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    rating = db.Column(db.Integer)


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


class GeoIP(db.Model):
    """The primary purpose of this table is to hold IP-geolocation pairs.
    The table name itself is pretty mucy self-explanatory."""

    __tablename__ = 'geoip'

    address = db.Column(db.String(40), primary_key=True) # We may hold IPv6 addresses as well
    timestamp = db.Column(db.DateTime(timezone=True))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)


#
# Generating SQL from declarative model definitions:
#
#     print CreateTable(User.__table__).compile(db.engine)
#