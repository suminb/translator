from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.dialects.postgresql import UUID
from __init__ import app

db = SQLAlchemy(app)

class Translation(db.Model):
    id = db.Column(UUID, primary_key=True)
    serial = db.Column(db.Integer, db.Sequence('translation_serial_seq'))
    timestamp = db.Column(db.DateTime(timezone=True))
    source = db.Column(db.String(16))
    target = db.Column(db.String(16))
    mode = db.Column(db.Integer)
    original_text = db.Column(db.Text)
    translated_text = db.Column(db.Text)
    is_sample = db.Column(db.Boolean)

class Rating(db.Model):
    id = db.Column(UUID, primary_key=True)
    translation_id = db.Column(UUID)
    rating = db.Column(db.Integer)
    ip = db.Column(db.String(64))
    token = db.Column(db.String(128))