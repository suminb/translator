from sqlalchemy import create_engine, MetaData
import json
import config

engine = create_engine(config.DB_URI, convert_unicode=True)
metadata = MetaData(bind=engine)

def jsonify_list(keys, rows):
    results = []
    for row in rows:
        for i in xrange(len(keys)):
            results.append({keys[i]: row[i]})

    return json.dumps(results)

def get_translation_count(conn):
    return conn.execute('SELECT count(id) FROM translation').first()[0]


def get_rating_stat(conn):
    return conn.execute('SELECT count(id), avg(rating), stddev_samp(rating) FROM rating').first()

def hourly(conn):
    sql = """
        SELECT cast("timestamp" as date) as "date", extract(hour from "timestamp") as "hour", count("timestamp")
        FROM translation
        GROUP BY cast("timestamp" as date), extract(hour from "timestamp")
        ORDER BY "date", "hour"
    """
    for row in conn.execute(sql):
        yield [str(row[0]), int(row[1]), int(row[2])]

if __name__ == '__main__':

    conn = engine.connect()

    print get_translation_count(conn)
    print get_rating_stat(conn)
    #for row in hourly(conn):
    #    print row

    print jsonify_list(['date', 'hour', 'count'], hourly(conn))