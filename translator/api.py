# -*- coding: utf-8 -*-
from datetime import datetime
import json
import operator
import os
import random
import re
import sys
from urllib.parse import quote, quote_plus, urlencode
import uuid

import requests
from flask import Blueprint, request, jsonify
from flask_babel import gettext as _

from translator import logger, VALID_LANGUAGES, SOURCE_LANGUAGES, \
    TARGET_LANGUAGES, INTERMEDIATE_LANGUAGES, DEFAULT_USER_AGENT, \
    MAX_TEXT_LENGTH
from translator.utils import HTTPException, parse_javascript


api_module = Blueprint('api', __name__)


def get_lambda_client():
    """First attempt to get AWS configuration from the environment variables;
    then try to access the config object if environment variables are not
    available."""
    from boto3.session import Session
    access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = os.environ.get('AWS_DEFAULT_REGION')

    session = Session(aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key,
                      region_name=region)

    return session.client('lambda')

    import boto3
    client = boto3.client('lambda')
    return client


def lambda_get(url, params={}, data={}, headers={}):
    """Sends an HTTP GET request via AWS Lambda."""
    lambda_client = get_lambda_client()

    function_names = ['web_proxy', 'web_proxy2']

    payload = {
        'url': url,
        'params': params,
        'data': data,
        'headers': headers,
    }
    resp = lambda_client.invoke(
        FunctionName=random.choice(function_names),
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps(payload)
    )
    return resp


def __payload_as_tuples__(payload):
    """Takes a dictionary and converts it to a list of tuples."""
    for key, value in payload.items():
        if isinstance(value, list):
            for v in value:
                yield key, v
        else:
            yield key, value


def __params__(text, source, target, client='at',
               user_agent=DEFAULT_USER_AGENT):
    """Returns a dictionary containing all parameters to send a translation
    request to Google Translate."""

    headers = {
        'User-Agent': user_agent,
        'Content-Length': str(sys.getsizeof(text))
    }
    remote_addr = request.remote_addr if request.remote_addr else ''
    payload = {
        'client': client,
        'sl': source,
        'tl': target,
        'q': text,
        'dt': ['t', 'ld', 'qc', 'rm', 'bd'],
        'dj': 1,
        # Generate a UUID based on the remote client's IP address
        'iid': str(uuid.uuid5(uuid.NAMESPACE_DNS, remote_addr)),
        # 'itid': 'pk',
        # 'otf': 1,
        'ie': 'UTF-8',
    }
    url = 'https://translate.google.com/translate_a/single'

    if len(quote(text)) > 1000:
        method = 'post'
        del payload['q']
    else:
        method = 'get'
        del headers['Content-Length']

    return {
        'headers': headers,
        'payload': payload,
        'method': method,
        'url': url,
        'query': urlencode(list(__payload_as_tuples__(payload)))
    }


def get_languages(field):
    """Returns a list of languages.

    :param field: Indicate one of source, target and intermediate language.
    :type field: str
    """

    if field == 'source':
        return [(key, VALID_LANGUAGES[key]) for key in SOURCE_LANGUAGES]
    elif field == 'target':
        return [(key, VALID_LANGUAGES[key]) for key in TARGET_LANGUAGES]
    elif field == 'intermediate':
        return [(key, VALID_LANGUAGES[key]) for key in INTERMEDIATE_LANGUAGES]
    else:
        raise Exception('Invalid field: {}'.format(field))


@api_module.route('/api/v1.3/version-check')
def version_check():
    """Checks whether the client is the latest."""
    current_version = request.args['version']
    latest_version = os.environ.get('LATEST_CLIENT_VERSION', '(unknown)')
    return jsonify({'is_latest': current_version == latest_version,
                    'latest_version': latest_version})


@api_module.route('/api/v1.3/params', methods=['get', 'post'])
def params():
    request_params = request.form if request.method == 'POST' else request.args
    text, source, target = \
        [request_params[x] for x in ('text', 'source', 'target')]
    return jsonify(__params__(text, source, target))


@api_module.route('/api/v1.3/parse_javascript', methods=['post'])
def _parse_javascript():
    raw = request.form['raw']
    return jsonify({'parsed': parse_javascript(raw)})


@api_module.route('/api/v1.3/parse_result', methods=['post'])
def parse_result():
    """Parses a translation result."""
    raw = request.form['raw']
    parsed = parse_javascript(raw)

    # Extract translated sentences
    translations = [x[0] for x in parsed[0]]

    # Filter out None elements
    translations = filter(None, translations)

    return jsonify({'translated': ''.join(translations)})


@api_module.route('/v1.0/languages')
@api_module.route('/api/v1.0/languages')
def languages_v1_0():
    """Returns a list of supported languages."""
    locale = request.args['locale']  # noqa
    langs = {k: _(v) for (k, v) in get_languages('target')}
    return jsonify(langs)


@api_module.route('/api/v1.3/languages')
def languages_v1_3():
    """Returns a list of supported languages."""
    locale = request.args['locale']  # noqa
    field = request.args['field']  # NOTE: Any better name?
    sortby = int(request.args.get('sortby', 1))

    try:
        languages = get_languages(field)
    except Exception as e:
        return str(e), 400

    languages = [(x, _(y)) for x, y in languages]

    # -1 indicates no sorting
    if sortby != -1:
        languages = sorted(languages, key=operator.itemgetter(sortby))

    return jsonify({'languages': languages})


@api_module.route('/v1.0/translate', methods=['POST'])
def translate_v1_0():
    """
    :param sl: source language
    :type sl: string
    :param tl: target language
    :type tl: string
    :param m: mode ( 1 for normal, 2 for better )
    :type m: int
    :param t: text to be translated
    :type t: string

    Translates given text.

    **Example Request**:

    .. sourcecode:: http

        POST /v1.0/translate HTTP/1.1
        User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.99 Safari/537.22
        Host: 192.168.0.185:5000
        Accept: */*
        Content-Length: 57
        Content-Type: application/x-www-form-urlencoded

        sl=ko&tl=en&m=2&t=여러분이 몰랐던 구글 번역기

    **Example Response**

    .. sourcecode:: http

        HTTP/1.0 200 OK
        Content-Type: application/json
        Content-Length: 90
        Server: Werkzeug/0.8.3 Python/2.7.3
        Date: Wed, 10 Apr 2013 06:43:13 GMT

        {
          "translated_text": "Google translation that you did not know",
          "serial_b62": "0z19x",
          "intermediate_text": "\u7686\u3055\u3093\u304c\u77e5\u3089\u306a\u304b\u3063\u305fGoogle\u306e\u7ffb\u8a33"
        }

    **Example iOS Code using ILHTTPClient**

    ILHTTPClient: https://github.com/isaaclimdc/ILHTTPClient

    .. sourcecode:: objective-c

        ILHTTPClient *client = [ILHTTPClient clientWithBaseURL:@"http://translator.suminb.com/" showingHUDInView:self.view];
            NSDictionary *params = @{
                                        @"sl": @"en",
                                        @"tl": @"ko",
                                        @"m": @"2",
                                        @"t": @"Google translation that you did not know."
            };

            [client postPath:@"/v1.0/translate"
                  parameters:params
                 loadingText:@"Loading..."
                 successText:@"Success!"
               multiPartForm:^(id<AFMultipartFormData> formData) {
               }
                     success:^(AFHTTPRequestOperation *operation, NSString *response) {
                         NSLog(@"%@", response);
                     }
                     failure:^(AFHTTPRequestOperation *operation, NSError *error) {
                     }
            ];
    """  # noqa
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    try:
        return jsonify(translate(text, mode, source, target))

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        logger.exception(e)
        return str(e), 500


@api_module.route('/v1.1/translate', methods=['POST'])
def translate_1_1():
    """
    :param sl: source language
    :type sl: string
    :param tl: target language
    :type tl: string
    :param m: mode ( 1 for normal, 2 for better )
    :type m: int
    :param t: text to be translated
    :type t: string

    Translates given text.
    """
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    try:
        payload = translate(text, mode, source, target)
        return jsonify(payload)

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        logger.exception(e)
        return str(e), 500


@api_module.route('/v1.2/translate', methods=['POST'])
def translate_1_2():
    """
    :param sl: source language
    :type sl: string
    :param tl: target language
    :type tl: string
    :param m: mode ( 1 for normal, 2 for better )
    :type m: int
    :param t: text to be translated
    :type t: string

    Translates given text.
    """
    keys = ('t', 'm', 'sl', 'tl')
    text, mode, source, target = map(lambda k: request.form[k].strip(), keys)

    try:
        payload = translate(text, mode, source, target)

        return jsonify(payload)

    except HTTPException as e:
        return e.message, e.status_code

    except Exception as e:
        logger.exception(e)
        return str(e), 500


def __translate__(text, source, target, client='x',
                  user_agent=DEFAULT_USER_AGENT):
    """
    text: text to be translated
    source: source language
    target: target language
    """

    if source == target:
        return text

    if not re.match(r'Mozilla/\d+\.\d+ \(.*', user_agent):
        user_agent = 'Mozilla/5.0 (%s)' % user_agent

    headers = {
        'Referer': 'http://translate.google.com',
        'User-Agent': user_agent,
        'Content-Length': str(sys.getsizeof(text))
    }
    payload = {
        'client': client,
        'sl': source,
        'tl': target,
        'text': text,
    }
    url = 'http://translate.google.com/translate_a/t'

    req = requests.post(url, headers=headers, data=payload)

    if req.status_code != 200:
        raise HTTPException(
            ('Google Translate returned HTTP {}'.format(req.status_code)),
            req.status_code)

    if client == 'x':
        data = json.loads(req.text)

        # It appears in some cases the Google Translate returns a string
        # rather than a dictionary
        try:
            if isinstance(data, unicode):
                return data
        except NameError:
            if isinstance(data, str):
                return data

        try:
            sentences = data['sentences']
        except TypeError:
            sentences = data['results'][0]['sentences']

        result = ' '.join(map(lambda x: x['trans'], sentences))

        # Remove unneccessary white spaces
        return '\n'.join(map(lambda x: x.strip(), result.split('\n')))

    elif client == 't':
        return parse_javascript(req.text)

    else:
        raise Exception("Unsupported client '{}'".format(client))


def translate(text, mode, source, target, client='x'):

    if len(text) == 0:
        raise HTTPException('Text cannot be empty.', 400)

    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException('Text too long.', 413)

    if source == target:
        return dict(
            id=None,
            id_b62=None,
            intermediate_text=None,
            translated_text=text)

    if source not in VALID_LANGUAGES.keys():
        raise HTTPException('Invalid source language.', 400)
    if target not in VALID_LANGUAGES.keys():
        raise HTTPException('Invalid target language.', 400)

    user_agent = request.headers.get('User-Agent', 'Unknown')

    translated_raw = None
    translated_text = None
    intermediate_raw = None
    intermediate_text = None

    # NOTE: The following may be time consuming operations
    # FIXME: Refactor this code. Looks crappy.
    if mode == '1':
        if client == 't':
            translated_raw = __translate__(text, source, target, client,
                                           user_agent)
            translated_text = ' '.join(map(lambda x: x[0], translated_raw[0]))
        else:
            translated_text = __translate__(text, source, target, client,
                                            user_agent)

    elif mode == '2':
        if client == 't':
            intermediate_raw = __translate__(text, source, 'ja', client,
                                             user_agent)
            intermediate_text = ' '.join(map(lambda x: x[0],
                                             intermediate_raw[0]))
            translated_raw = __translate__(intermediate_text, 'ja', target,
                                           client, user_agent)
            translated_text = ' '.join(map(lambda x: x[0], translated_raw[0]))

        else:
            intermediate_text = __translate__(text, source, 'ja', client,
                                              user_agent)
            translated_text = __translate__(intermediate_text, 'ja', target,
                                            client, user_agent)

    else:
        return HTTPException('Invalid translation mode.', 400)

    return dict(
        id=None,
        request_id=None,
        intermediate_text=intermediate_text,
        intermediate_raw=intermediate_raw,
        translated_text=translated_text,
        translated_raw=translated_raw,
    )


@api_module.route('/api/v1.3/translate', methods=['get', 'post'])
def translate_v1_3():
    # TODO: Use AWS Lambda to make translation requests
    request_params = request.form if request.method == 'POST' else request.args
    text, source, target = \
        [request_params[k] for k in ('text', 'source', 'target')]
    params = __params__(text, source, target)
    resp = lambda_get(params['url'], params=params['payload'],
                      headers=params['headers'])
    resp_content = json.loads(resp['Payload'].read().decode('utf-8'))
    resp_text = resp_content['text']
    resp_status_code = resp_content['status_code']

    return resp_text, resp_status_code


@api_module.route('/api/v1.4/translate', methods=['get', 'post'])
def translate_v1_4():
    request_params = request.form if request.method == 'POST' else request.args
    text, source, target = \
        [request_params[k] for k in ('text', 'source', 'target')]

    datehour = datetime.utcnow().strftime('%Y-%m-%d-%H')
    url = 'https://www.google.co.kr/async/translate?yv=3'
    headers = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.co.kr/',
        'Authority': 'www.google.co.kr',
        'Cookie': 'NID=131=; 1P_JAR={0}'.format(datehour),
    }
    data = 'async=translate,sl:{source},tl:{target},st:{text},id:{id}' \
           ',qc:true,ac:false,_id:tw-async-translate,_pms:s,_fmt:pc'.format(
               source=source, target=target, text=quote_plus(text), id=1)
    resp = requests.post(url, headers=headers, data=data, timeout=10)
    index = resp.text.find('<span')
    result = resp.text[index:]

    return result, resp.status_code


@api_module.route('/api/v1.3/exception')
def exception():
    raise Exception(request.args.get('message', 'Anything you can imagine'))
