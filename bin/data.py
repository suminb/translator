"""Script to import data to Elasticsearch."""

import sys
import hashlib
import json
from datetime import datetime

import click
from elasticsearch import Elasticsearch
import sqlalchemy

from app import config
from app.analysis.model import db, Phrase, Sentence


es = Elasticsearch([{'host': config['es_host'], 'port': config['es_port']}])


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
        if s[0] is None or s[1] is None:
            continue
        yield (s[1].strip(), s[0].strip())  # source, target


def store_sentences(source_lang, target_lang, sentences):
    """
    :param sentences: list of (source, target) sentences
    """
    for source_text, target_text in sentences:
        source_hash = hashlib.sha1(source_text.encode('utf-8')).hexdigest()
        try:
            Sentence.create(
                observed_at=datetime.utcnow(),
                source_lang=source_lang,
                target_lang=target_lang,
                source_text_hash=source_hash,
                source_text=source_text,
                target_text=target_text)
        except sqlalchemy.exc.IntegrityError:
            db.session.rollback()


def extract_phrases(raw):
    """
    :type raw: list
    """
    for p in raw:
        source = p[0]
        try:
            targets = [x[0] for x in p[2]]
        except TypeError:
            continue

        yield source, targets


def store_phrases(source_lang, target_lang, phrases):
    for source_text, target_texts in phrases:
        source_hash = hashlib.sha1(source_text.encode('utf-8')).hexdigest()
        try:
            Phrase.create(
                observed_at=datetime.utcnow(),
                source_lang=source_lang,
                target_lang=target_lang,
                source_text_hash=source_hash,
                source_text=source_text,
                target_texts=target_texts)
        except sqlalchemy.exc.IntegrityError:
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
            id = hashlib.sha1(raw_data).hexdigest()
            doc = {'data': json.loads(raw_data),
                   'timestamp': int(unix_time(str2datetime(timestamp)) * 1000),
                   'source_lang': source_lang,
                   'target_lang': target_lang}
            res = es.index(index=config['es_index'],
                           doc_type=config['es_doc_type'], id=id, body=doc)
            print(res)
        except:
            sys.stderr.write('Bad data: {}\n'.format(line))


@cli.command()
@click.option('-t', '--term', help='Search term')
def process(term):
    """Processes data on Elasticsearch"""

    # Get all data (the batch size will be 10 or so)
    res = es.search(index=config['es_index'],
    #                body={'query': {'match_all': {}}})
                    body={'query': {'match': {'raw': term}}})

    print("Got %d Hits:" % res['hits']['total'])

    from app import create_app
    app = create_app()
    with app.app_context():
        for hit in res['hits']['hits']:
            doc_id = hit['_id']
            try:
                raw_data = hit['_source']['raw']
            except KeyError:
                raw_data = hit['_source']['data']
            source_lang = raw_data[2] if raw_data[2] else \
                hit['_source']['source_lang']
            target_lang = hit['_source']['target_lang']
            # import pdb; pdb.set_trace()
            # for i in [1, 2, 3, 4, 6, 7, 8]:
            #    print('raw_data[{}]: {}'.format(i, raw_data[i]))
            print('{}, {}, {}'.format(source_lang, target_lang, doc_id))

            if raw_data[0]:
                store_sentences(source_lang, target_lang,
                                extract_sentences(raw_data[0]))

            if raw_data[5]:
                store_phrases(source_lang, target_lang,
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
def create_db():
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    cli()
