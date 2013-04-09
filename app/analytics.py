from sqlalchemy import create_engine, MetaData
import json
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

    return '\n'.join(buf)

if __name__ == '__main__':
    print generate_output()
