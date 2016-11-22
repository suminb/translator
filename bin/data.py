"""Script to process translation data. We'd like to store things in a form of
phrases that are broken down to meaningful units, not the entire translation.
"""

from datetime import datetime
from dateutil import parser
import hashlib
import json
import sys
import time

import click
from logbook import Logger, StreamHandler
import sqlalchemy

from app.analysis.model import db, Phrase, RawTranslation, Sentence
from app.corpus.models import Translation


StreamHandler(sys.stderr, level='INFO').push_application()
log = Logger('')


def str2datetime(s):
    """Parse a datetime string (with milliseconds)."""
    parts = s.split('.')
    dt = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
    return dt.replace(microsecond=int(parts[1]))


def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def extract_sentences(raw):
    """
    :type raw: list
    """
    for s in raw:
        if isinstance(s, str):
            continue
        if s[0] is None or s[1] is None:
            continue
        yield (s[1].strip(), s[0].strip())  # source, target


def store_sentences(source_lang, target_lang, observed_at, sentences):
    """
    :type observed_at: datetime

    :param sentences: list of (source, target) sentences
    """
    for source_text, target_text in sentences:
        source_hash = hashlib.sha1(source_text.encode('utf-8')).hexdigest()
        try:
            log.info('  - {} -> {}'.format(source_text, target_text))
            Sentence.create(
                observed_at=observed_at,
                source_lang=source_lang,
                target_lang=target_lang,
                source_text_hash=source_hash,
                source_text=source_text,
                target_text=target_text)
        except sqlalchemy.exc.IntegrityError:
            log.warn('Sentence already exists.')
            db.session.rollback()
        except sqlalchemy.exc.DataError as e:
            log.warn(str(e))
            db.session.rollback()


def extract_phrases(raw):
    """
    :type raw: list
    """
    for p in raw:
        if isinstance(p, str):
            continue
        source = p[0]
        try:
            targets = [x[0] for x in p[2]]
        except TypeError:
            continue

        yield source, targets


def store_phrases(source_lang, target_lang, observed_at, phrases):
    """
    :type observed_at: datetime
    """
    for source_text, target_texts in phrases:
        for target_text in target_texts:
            try:
                Phrase.create(
                    first_observed_at=observed_at,
                    last_observed_at=observed_at,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    source_text=source_text,
                    target_text=target_text,
                    count=1)
            except sqlalchemy.exc.IntegrityError:
                db.session.rollback()

                phrase = Phrase.query.filter(
                    Phrase.source_text == source_text,
                    Phrase.source_lang == source_lang,
                    Phrase.target_text == target_text,
                    Phrase.target_lang == target_lang
                ).first()
                phrase.count += 1
                if phrase.first_observed_at is not None \
                        and observed_at < phrase.first_observed_at:
                    phrase.first_observed_at = observed_at
                if phrase.last_observed_at is not None \
                        and observed_at > phrase.last_observed_at:
                    phrase.last_observed_at = observed_at
                db.session.commit()
            except sqlalchemy.exc.DataError:
                db.session.rollback()


def store_raw(source_lang, target_lang, observed_at, raw):
    """Stores raw data.

    :type source_lang: str
    :type target_lang: str
    :type observed_at: datetime
    :type raw: dict
    """
    # raw_str = json.dumps(raw, ensure_ascii=False)
    # hash = hashlib.sha1(raw_str.encode('utf-8')).hexdigest()

    RawTranslation.create(
        observed_at=observed_at,
        source_lang=source_lang,
        target_lang=target_lang,
        raw=raw,
    )


@click.group()
def cli():
    pass


@cli.command()
@click.option('--interval', type=float, default=0.25)
def process(interval):
    from app import create_app
    app = create_app()
    with app.app_context():
        for translation in Translation.scan():
            raw = json.loads(translation.raw)
            log.info('{}, {}, {}',
                     translation.source_lang, translation.target_lang,
                     raw['sentences'])
            try:
                store_raw(translation.source_lang, translation.target_lang,
                          translation.timestamp, raw)
            except Exception as e:
                log.error(e)
            else:
                translation.delete()
                time.sleep(interval)


def process_entry(hit):
    """Processes a single ES hit entry."""

    from app import create_app
    app = create_app()
    with app.app_context():
        doc_id = hit['_id']
        try:
            raw_data = hit['_source']['raw']
        except KeyError:
            raw_data = hit['_source']['data']

        # Ignore bad data
        if isinstance(raw_data, str):
            return

        timestamp = hit['_source']['timestamp']
        if isinstance(timestamp, int):
            observed_at = datetime.fromtimestamp(timestamp / 1000.0)
        else:
            observed_at = parser.parse(hit['_source']['timestamp'])

        source_lang = raw_data['src'] if raw_data['src'] else \
            hit['_source']['source_lang']
        target_lang = hit['_source']['target_lang']
        log.info('{}, {}, {}'.format(source_lang, target_lang, doc_id))

        store_raw(source_lang, target_lang, observed_at, raw_data)

        # if len(raw_data) > 0 and raw_data[0]:
        #     store_sentences(source_lang, target_lang, observed_at,
        #                     extract_sentences(raw_data[0]))

        # if len(raw_data) > 5 and raw_data[5]:
        #     store_phrases(source_lang, target_lang, observed_at,
        #                   extract_phrases(raw_data[5]))

        # raw_data[0]: sentences
        # raw_data[1]: dictionary data?
        # raw_data[2]: source language
        # raw_data[3]: (null)
        # raw_data[4]: (null)
        # raw_data[5]: phrases
        # raw_data[6]: some floating point value; potentially confidence?
        # raw_data[7]: (null)
        # raw_data[8]: source languages along with confidence?


@cli.command()
def create_db():
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    cli()
