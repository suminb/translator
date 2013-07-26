from sqlalchemy import create_engine, MetaData
from datetime import datetime, timedelta, date
from math import log

from __init__ import db
from models import Translation, GeoIP

import json
import requests
import os, sys
import config
import re
import logging


engine = create_engine(config.DB_URI, convert_unicode=True)
metadata = MetaData(bind=engine)

logger = logging.getLogger('translator')
logger.addHandler(logging.StreamHandler(sys.stderr)) 
logger.setLevel(logging.INFO)


def jsonify_list(rows, keys=None):
    results = []
    for row in rows:
        if keys == None:
            results.append(row)
        else:
            for i in xrange(len(keys)):
                results.append({keys[i]: row[i]})

    return json.dumps(results)

def get_translation_count(conn):
    return conn.execute('SELECT count(id) FROM translation').first()[0]

def get_rating_stat(conn):
    cols = conn.execute('SELECT count(id), avg(rating), stddev_samp(rating) FROM rating').first()
    return [int(cols[0]), float(cols[1]), float(cols[2])]

def get_language_count(conn):
    return conn.execute('SELECT source, target, count(source) FROM translation GROUP BY source, target').first()

def get_char_length(conn):
    return conn.execute('SELECT sum(char_length(original_text)) FROM translation').first()[0]

def geolocation(conn):
    def ip_lookup(ip):
        import time

        # FIXME: Temporary cheating
        ip = ip.strip()
        if len(ip) > 15:
            return None

        geoip = GeoIP.query.filter_by(address=ip).first()

        if geoip != None:
            return geoip
        else:
            logger.info('Locating {}...'.format(ip))

            r = requests.get('http://freegeoip.net/json/' + ip)

            if r.status_code == 200:
                record = json.loads(r.content)

                geoip = GeoIP(
                    address=ip,
                    timestamp=datetime.now(),
                    latitude=record['latitude'],
                    longitude=record['longitude']
                )

                try:
                    db.session.add(geoip)
                    db.session.commit()
                except Exception as e:
                    logger.exception(e)
                    db.session.rollback()

                time.sleep(0.3)

                return geoip
            else:
                logger.error('Geo-location of {} is unknown (HTTP {})'.format(ip, r.status_code))

                return None

    def lookup_records():
        qdate = date.today() - timedelta(days=7)
        query = """
            SELECT *, count(*) FROM (
                SELECT latitude, longitude FROM translation
                INNER JOIN geoip ON translation.remote_address = geoip.address
                WHERE translation.timestamp >= date('{}')
            ) AS t
            GROUP BY t.latitude, t.longitude
        """.format(qdate.isoformat())
        for row in conn.execute(query):
            ip, latitude, longitude, count = row
            yield {'lat':latitude, 'lng':longitude, 'count':count}

    # FIXME: Temporary solution for pre-geocoding
    for row in db.session.query(Translation.remote_address) \
            .filter(Translation.remote_address != None) \
            .group_by(Translation.remote_address):
        ip_lookup(row.remote_address)

    mx = 0
    data = []
    for r in lookup_records():
        mx = r['count'] if r['count'] > mx else mx
        data.append(r)

    for d in data:
        d['count'] = log(d['count'])

    return {'max':log(mx), 'data':data}

def hourly(conn):
    sql = """
        SELECT extract(hour from "timestamp") as "hour", count("timestamp")
        FROM translation
        GROUP BY extract(hour from "timestamp")
        ORDER BY "hour"
    """
    for row in conn.execute(sql):
        yield [int(row[0]), int(row[1])]

def daily_hourly(conn):
    sql = """
        SELECT cast("timestamp" as date) as "date", extract(hour from "timestamp") as "hour", count("timestamp")
        FROM translation
        GROUP BY cast("timestamp" as date), extract(hour from "timestamp")
        ORDER BY "date", "hour"
    """
    for row in conn.execute(sql):
        yield [str(row[0]), int(row[1]), int(row[2])]

def generate_output():
    conn = engine.connect()

    buf = []

    buf.append('var stat_translation_count = %d;' % get_translation_count(conn))

    buf.append('var stat_rating = %s;' % str(get_rating_stat(conn)))

    #print jsonify_list(hourly(conn), ['date', 'hour', 'count'])
    buf.append('var stat_hourly = %s;' % jsonify_list(zip(*hourly(conn))))

    buf.append('var stat_heatmap = %s;' % json.dumps(geolocation(conn)))

    return '\n'.join(buf)

if __name__ == '__main__':
    print generate_output()

    #print get_language_count(engine.connect())

