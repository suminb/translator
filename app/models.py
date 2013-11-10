from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.schema import CreateTable
from datetime import datetime

from __init__ import app
from utils import *

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
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
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

        for id_field in ('id', 'user_id', 'request_id', 'response_id'):
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

            setattr(record, key, value);

        db.session.add(record)
        if commit: db.session.commit()

        return record

    @classmethod
    def fetch(cls, id_b62=None):
        id = b62_to_uuid(id_b62)
        return cls.query.get(str(id))


class TranslationRequest(db.Model, BaseModel):
    """
    -- Copied from http://www.scottlowe.eu/blog/2011/04/28/postgresql-full-text-search-is-often-good-enough/
    --
    -- Add the new tsvector column
    ALTER TABLE translation_request ADD COLUMN original_text_tsv tsvector;

    -- Create a function that will generate a tsvector from text data found in both the
    -- title and body columns, but give a higher relevancy rating 'A' to the title data  
    CREATE FUNCTION translation_request_generate_tsvector() RETURNS trigger AS $$
      begin
        new.original_text_tsv :=
          setweight(to_tsvector('pg_catalog.english', coalesce(new.original_text,'')), 'A');
        return new;
      end
    $$ LANGUAGE plpgsql;

    -- When articles row data is inserted or updated, execute the function
    -- that generates the tsvector data for that row
    CREATE TRIGGER tsvector_translation_request_upsert_trigger BEFORE INSERT OR UPDATE
      ON translation_request
      FOR EACH ROW EXECUTE PROCEDURE translation_request_generate_tsvector();

    -- When the migration is run, create tsvector data for all the existing records
    UPDATE translation_request SET original_text_tsv =
      setweight(to_tsvector('pg_catalog.english', coalesce(original_text,'')), 'A');

    -- Create an index for the tsv column that is specialised for tsvector data
    CREATE INDEX translation_request_tsv_idx ON translation_request USING gin(original_text_tsv);

    -- Fuzzy matching
    -- http://www.postgresql.org/docs/8.3/static/fuzzystrmatch.html
    CREATE EXTENSION fuzzystrmatch;


    CREATE UNIQUE INDEX
        unique_resquest ON translation_request
        (coalesce(user_id, '00000000-0000-0000-0000-000000000000'), source, target, original_text_hash);
    """
    #__table_args__ = ( db.UniqueConstraint('user_id', 'source', 'target', 'original_text_hash'), )

    id = db.Column(UUID, primary_key=True)
    user_id = db.Column(UUID, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime(timezone=True))
    source = db.Column(db.String(16))
    target = db.Column(db.String(16))
    original_text = db.Column(db.Text)
    original_text_hash = db.Column(db.String(255))

    user = relationship('User')

    @staticmethod
    def fetch(id=None, id_b62=None, original_text_hash=None, source=None, target=None):
        if id != None:
            return TranslationRequest.query.get(id)

        elif id_b62 != None:
            translation_id = base62.decode(id_b62)
            return TranslationRequest.query.get(str(uuid.UUID(int=translation_id)))

        else:
            return TranslationRequest.query.filter_by(
                original_text_hash=original_text_hash,
                source=source, target=target).first()


class TranslationResponse(db.Model, BaseModel):
    """Temporarily stores translation results.

    CREATE UNIQUE INDEX
        unique_response ON translation_response
        (coalesce(user_id, '00000000-0000-0000-0000-000000000000'), request_id, source, target, mode);
    """

    #__table_args__ = ( db.UniqueConstraint('user_id', 'request_id', 'source', 'target', 'mode'), )

    id = db.Column(UUID, primary_key=True)
    request_id = db.Column(UUID, db.ForeignKey('translation_request.id'))
    user_id = db.Column(UUID, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime(timezone=True))
    source = db.Column(db.String(16))
    target = db.Column(db.String(16))
    # mode
    # 1: regular translation
    # 2: better translation (use Japanese as an intermediate langauge)
    # 3: human translation
    mode = db.Column(db.Integer)
    original_text_hash = db.Column(db.String(255))

    # FIXME: The following four properties will be replaced by 'target_text'
    # in API v1.3 as the client will be responsible for handling intermediate
    # translations
    intermediate_text = db.Column(db.Text)
    _intermediate_raw = db.Column('intermediate_raw', db.Text)
    translated_text = db.Column(db.Text)
    _translated_raw = db.Column('translated_raw', db.Text)

    request = relationship('TranslationRequest')
    user = relationship('User')

    # FIXME: This may be a cause for degraded performance 
    @property
    def plus_ratings(self):
        return Rating.query.filter_by(translation_id=self.id, rating=1).count()

    # FIXME: This may be a cause for degraded performance 
    @property
    def minus_ratings(self):
        return Rating.query.filter_by(translation_id=self.id, rating=-1).count()


    def process_corpora(self):
        def insert_corpora(source_lang, source_text, target_lang, target_text, confidence):
            corpus = Corpus.query.filter_by(
                    source_lang=source_lang, target_lang=target_lang,
                    source_text=source_text, target_text=target_text,
                ).first()

            if corpus == None:
                corpus = Corpus.insert(
                    source_lang=source_lang, target_lang=target_lang,
                    source_text=source_text, target_text=target_text,
                    confidence=confidence, frequency=1,
                )
            else:
                corpus.confidence += confidence
                corpus.frequency += 1

                db.session.commit()


        source_lang, target_lang = self.source, self.target
        if self.mode == 2: source_lang = 'ja' # FIXME: This shall be removed for API v1.3

        for source, target in zip(self.translated_raw[5], self.translated_raw[4]):

            source_text, target_text = source[0], target[0]
            confidence = int(target[4])

            insert_corpora(source_lang.strip(), source_text.strip(),
                target_lang.strip(), target_text.strip(), confidence)

        if self.mode == 2:
            source_lang, target_lang = self.source, 'ja'
            
            for source, target in zip(self.intermediate_raw[5], self.intermediate_raw[4]):

                source_text, target_text = source[0], target[0]
                confidence = int(target[4])

                insert_corpora(source_lang.strip(), source_text.strip(),
                    target_lang.strip(), target_text.strip(), confidence)



    def intermediate_raw():
        doc = "The intermediate_raw property."
        def fget(self):
            try:
                return json.loads(self._intermediate_raw)
            except:
                return self._intermediate_raw

        def fset(self, value):
            try:
                self._intermediate_raw = json.dumps(value)
            except:
                self._intermediate_raw = value

        def fdel(self):
            del self._intermediate_raw
        return locals()
    intermediate_raw = property(**intermediate_raw())


    def translated_raw():
        doc = "The translated_raw property."
        def fget(self):
            try:
                return json.loads(self._translated_raw)
            except:
                return self._translated_raw

        def fset(self, value):
            try:
                self._translated_raw = json.dumps(value)
            except:
                self._translated_raw = value
                

        def fdel(self):
            del self._translated_raw
        return locals()
    translated_raw = property(**translated_raw())


    @staticmethod
    def fetch(id_b62=None, user_id=None, original_text_hash=None, source=None, target=None, mode=None):
        if id_b62 != None:
            translation_id = base62.decode(id_b62)
            return TranslationResponse.query.get(str(uuid.UUID(int=translation_id)))

        else:
            return TranslationResponse.query.filter_by(
                user_id=user_id, original_text_hash=original_text_hash,
                source=source, target=target, mode=mode).first()


class TranslationPostLog(db.Model, BaseModel):
    id = db.Column(UUID, primary_key=True)
    request_id = db.Column(UUID)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    target = db.Column(db.String(32)) # facebook, twitter, etc.
    post_id = db.Column(db.String(128))


class TranslationAccessLog(db.Model, BaseModel):
    """
    flag
    0001: Created: This flag is on upon creation of a TranslationResponse record
    0002:
    0004:
    ...

    translation_access_log_translation_id_fkey  
    FOREIGN KEY (translation_id) REFERENCES translation_response(id)
    """

    FLAG_CREATED = 1
    
    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    user_agent = db.Column(db.String(255))
    remote_address = db.Column(db.String(64))
    flag = db.Column(db.Integer, default=0)


class Rating(db.Model, BaseModel):
    __table_args__ = ( db.UniqueConstraint('translation_id', 'user_id'), )

    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    user_id = db.Column(UUID)
    timestamp = db.Column(db.DateTime(timezone=True))
    rating = db.Column(db.Integer)

    # FIXME: This may be a cause for degraded performance 
    @property
    def plus_ratings(self):
        return Rating.query.filter_by(translation_id=self.translation_id, rating=1).count()

    # FIXME: This may be a cause for degraded performance 
    @property
    def minus_ratings(self):
        return Rating.query.filter_by(translation_id=self.translation_id, rating=-1).count()

    def serialize(self):
        r = serialize(self)
        r['plus_ratings'] = self.plus_ratings
        r['minus_ratings'] = self.minus_ratings

        return r


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


class Watching(db.Model, BaseModel):
    # Without __tablename__ attribute, the following error will occur.
    # sqlalchemy.exc.InvalidRequestError: Class <class 'app.models.Watching'>
    # does not have a __table__ or __tablename__ specified and does not inherit
    # from an existing table-mapped class.
    __tablename__ = 'watching'
    __table_args__ = ( db.PrimaryKeyConstraint('user_id', 'entity_type', 'entity_id'), {} )

    user_id = db.Column(UUID, nullable=False)
    entity_type = db.Column(db.Enum('TranslationRequest', 'TranslationResponse', 'Comment', name='entity_type'), nullable=False)
    entity_id = db.Column(UUID, nullable=False)


class NotificationQueue(db.Model, BaseModel):

    id = db.Column(UUID, primary_key=True)
    user_id = db.Column(UUID, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True))
    payload = db.Column(db.Text, nullable=True)

    user = relationship('User')


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

if __name__ == '__main__':
    tables = (User, TranslationRequest, TranslationResponse, Rating, )
    for table in tables:
        print '{};'.format(CreateTable(table.__table__).compile(db.engine))
    
    #db.create_all(tables=[TranslationRequest, TranslationResponse,])