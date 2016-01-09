__version__ = '0.1.0'

import requests


def lambda_handler(event, context):
    print(event)
    print(context)
    url = event['url']
    params = event.get('params', {})
    data = event.get('data', {})
    headers = event.get('headers', {})
    resp = requests.get(url, params=params, data=data, headers=headers)
    return {'text': resp.text, 'status_code': resp.status_code}
