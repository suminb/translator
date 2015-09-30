"""Script to import data to Elasticsearch."""

import sys
import json
from datetime import datetime

from elasticsearch import Elasticsearch


es = Elasticsearch([{'host': '52.68.65.104', 'port': 9200}])


def str2datetime(s):
    """Parse a datetime string (with milliseconds)."""
    parts = s.split('.')
    dt = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
    return dt.replace(microsecond=int(parts[1]))


def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def main(filename):
    for line in open(filename):
        cols = [x.strip() for x in line.split('\t')]
        if len(cols) != 5:
            continue

        doc = {'data': json.loads(cols[4]),
               'timestamp': int(unix_time(str2datetime(cols[2])) * 1000),
               'source_lang': cols[0],
               'target_lang': cols[1]}
        res = es.index(index='translation', doc_type='translation', id=cols[3], body=doc)
        print(res)


if __name__ == '__main__':
    main(sys.argv[1])
