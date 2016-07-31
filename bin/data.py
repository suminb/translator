"""Script to import data to Elasticsearch."""

import hashlib
import json
from datetime import datetime
from dateutil import parser
import os
import sys

import click
from elasticsearch import Elasticsearch
from logbook import Logger, StreamHandler
import sqlalchemy

from app import config
from app.analysis.model import db, Phrase, Sentence


es_host = os.environ.get('ES_HOST', 'localhost')
es_port = int(os.environ.get('ES_PORT', 9200))
es = Elasticsearch([{'host': es_host, 'port': es_port}])

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
                    observed_at=observed_at,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    source_text=source_text,
                    target_text=target_text)
            except sqlalchemy.exc.IntegrityError:
                db.session.rollback()
            except sqlalchemy.exc.DataError:
                db.session.rollback()


@click.group()
def cli():
    pass


@cli.command()
@click.argument('filename')
def import_to_es(filename):
    for line in open(filename):
        cols = [x.strip() for x in line.split('\t')]
        if len(cols) == 4:
            source_lang, target_lang, timestamp, raw_data = cols
        elif len(cols) == 5:
            source_lang, target_lang, timestamp, digest, raw_data = cols
        else:
            continue

        try:
            id = hashlib.sha1(raw_data.encode('utf-8')).hexdigest()
            doc = {'data': json.loads(raw_data),
                   'timestamp': int(unix_time(str2datetime(timestamp)) * 1000),
                   'source_lang': source_lang,
                   'target_lang': target_lang}
            res = es.index(index=os.environ['ES_INDEX'],
                           doc_type=os.environ['ES_DOC_TYPE'], id=id, body=doc)
            log.info(res)
        except:
            sys.stderr.write('Bad data: {}\n'.format(line))


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

        source_lang = raw_data[2] if raw_data[2] else \
            hit['_source']['source_lang']
        target_lang = hit['_source']['target_lang']
        log.info('{}, {}, {}'.format(source_lang, target_lang, doc_id))

        if len(raw_data) > 0 and raw_data[0]:
            store_sentences(source_lang, target_lang, observed_at,
                            extract_sentences(raw_data[0]))

        if len(raw_data) > 5 and raw_data[5]:
            store_phrases(source_lang, target_lang, observed_at,
                          extract_phrases(raw_data[5]))
        # raw_data[0]: sentences
        # raw_data[1]: dictionary data?
        # raw_data[2]: source language
        # raw_data[3]: (null)
        # raw_data[4]: (null)
        # raw_data[5]: phrases
        # raw_data[6]: some floating point value; potentially confidence?
        # raw_data[7]: (null)
        # raw_data[8]: source languages along with confidence?

        es.delete(index=config['es_index'], doc_type=config['es_doc_type'],
                  id=doc_id)


@cli.command()
@click.option('-n', '--size', type=int, default=10,
              help='# of documents to fetch at once')
@click.option('-m', '--skip', type=int, default=0,
              help='# of documents to skip')
@click.option('-p', '--processes', type=int, default=16,
              help='# of processes')
def process(size, skip, processes):
    """Processes data on Elasticsearch"""

    # Get all data (the batch size will be 10 or so)
    res = es.search(index=config['es_index'],
                    body={'query': {'match_all': {}}},
                    params={'size': size, 'from': skip})

    log.info("Got %d Hits:" % res['hits']['total'])

    # p = Pool(processes)
    # p.map(process_entry, res['hits']['hits'])
    for hit in res['hits']['hits']:
        process_entry(hit)


@cli.command()
def create_db():
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    cli()
