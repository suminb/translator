from sqlalchemy import create_engine, MetaData
import json
import requests
import os, sys
import config

engine = create_engine(config.DB_URI, convert_unicode=True)
metadata = MetaData(bind=engine)

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

def geolocation(conn):
    def ip_lookup(ip):
        import time

        f = open('/tmp/geoip.json', 'r')
        try:
            geoipdb = json.loads(f.read())
        except ValueError:
            geoipdb = {}
        f.close()

        if ip in geoipdb:
            return geoipdb[ip]
        # A naive conditional statement to look for a valid IP address. This shall be replaced with a regular expression.
        elif len(ip.split('.')) == 4:
            sys.stderr.write('Locating %s...\n' % ip)
            r = requests.get('http://freegeoip.net/json/' + ip)
            if r.status_code == 200:
                record = json.loads(r.content)
                geoipdb[ip] = {'latitude':record['latitude'], 'longitude':record['longitude']}

                f = open('/tmp/geoip.json', 'w+')
                f.write(json.dumps(geoipdb))
                f.close()

                time.sleep(0.3)
                return record
            else:
                sys.stderr.write('Geo-location of %s is unknown (HTTP %d)\n' % (ip, r.status_code))
                return None

    def lookup_records():
        geoip = {}
        for row in conn.execute('SELECT remote_address, count(remote_address) FROM translation GROUP BY remote_address'):
            ip, count = row[0], row[1]

            if ip != None:
                record = ip_lookup(ip)
                if record != None:
                    yield {'lat':record['latitude'], 'lng':record['longitude'], 'count':count}

    mx = 0
    data = []
    for r in lookup_records():
        mx = r['count'] if r['count'] > mx else mx
        data.append(r)

    return {'max':mx, 'data':data}

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
