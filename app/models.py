from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.schema import CreateTable
from datetime import datetime

from app import app
# from utils import *

import uuid
import base62
import json

db = SQLAlchemy(app)

# Will this work?
if db.engine.driver != 'psycopg2':
    UUID = db.String
    ARRAY = db.String

def serialize(obj):
    import json
    if isinstance(obj.__class__, DeclarativeMeta):
        # an SQLAlchemy class
        fields = {}
        for field in [x for x in obj.__dict__ if not x.startswith('_') and x != 'metadata']:
            data = obj.__getattribute__(field)
            try:
                json.dumps(data) # this will fail on non-encodable values, like other classes
                fields[field] = data
            except TypeError:
                fields[field] = None
        # a json-encodable dict
        return fields


class BaseModel:
    def serialize(self):
        payload = serialize(self)

        for id_field in ('id', 'user_id', 'request_id', 'response_id', 'corpus_id'):
            if hasattr(self, id_field) and getattr(self, id_field) != None:
                value = uuid.UUID(getattr(self, id_field)).int
                payload[id_field] = base62.encode(value)

        return payload

    def delete(self, current_user, commit=True):
        if not hasattr(self, 'user_id'):
            raise Exception("{} has no 'user_id' attribute".format(self))

        elif self.user_id != current_user.id:
            raise Exception('Users are not allowed to delete entities that do not belong to them')

        else:
            db.session.delete(self)
            if commit: db.session.commit()

    @classmethod
    def validate(cls, **kwargs):
        return None

    @classmethod
    def insert(cls, commit=True, **kwargs):
        record = cls()

        if hasattr(record, 'id'): record.id = str(uuid.uuid4())
        if hasattr(record, 'timestamp'): record.timestamp = datetime.now()

        for key, value in kwargs.iteritems():

            # if not isinstance(value, str):
            #     value = json.dumps(value)

            setattr(record, key, value)

        db.session.add(record)
        if commit: db.session.commit()

        return record

    @classmethod
    def fetch(cls, id_b62=None):
        id = b62_to_uuid(id_b62)
        return cls.query.get(str(id))


class User(db.Model, UserMixin, BaseModel):
    __table_args__ = ( db.UniqueConstraint('oauth_provider', 'oauth_id'), {} )

    id = db.Column(UUID, primary_key=True)

    oauth_provider = db.Column(db.String(255))
    oauth_id = db.Column(db.String(255), unique=True)
    oauth_username = db.Column(db.String(255))

    family_name = db.Column(db.String(255))
    given_name = db.Column(db.String(255))
    email = db.Column(db.String(255))

    gender = db.Column(db.String(6))
    locale = db.Column(db.String(16))

    extra_info = db.Column(db.Text)

    @property
    def name(self):
        # FIXME: i18n
        return '{} {}'.format(self.given_name, self.family_name)

    @property
    def picture(self):
        try:
            extra_info = json.loads(self.extra_info)
            return extra_info['picture']['data']['url']
        except:
            return None

    @property
    def link(self):
        try:
            extra_info = json.loads(self.extra_info)
            return extra_info['link']
        except:
            return None

    @staticmethod
    def insert(**kwargs):
        user = User.query.filter_by(oauth_id=kwargs['oauth_id']).first()

        if user == None:
            user = User(id=str(uuid.uuid4()))
            #user.timestamp = datetime.now()

            for key, value in kwargs.iteritems():
                setattr(user, key, value);

            db.session.add(user)
            db.session.commit()

        return user

#
# Generating SQL from declarative model definitions:
#
#     print CreateTable(User.__table__).compile(db.engine)
#

if __name__ == '__main__':
    from app.corpus.models import Corpus, CorpusRaw, CorpusIndex
    #tables = (User, TranslationRequest, TranslationResponse, Rating, )
    tables = [Corpus, CorpusRaw, CorpusIndex]
    for table in tables:
        print '{};'.format(CreateTable(table.__table__).compile(db.engine))

    # db.create_all()
