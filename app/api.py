# -*- coding: utf-8 -*-
import sys
import json
import re
import urllib

import requests
from flask import Blueprint, request, jsonify
from flask.ext.babel import gettext as _

from __init__ import logger, VALID_LANGUAGES, DEFAULT_USER_AGENT, \
    MAX_TEXT_LENGTH
from utils import HTTPException, parse_javascript


api_module = Blueprint('api', __name__)


def __payload_as_tuples__(payload):
    """Takes a dictionary and converts it to a list of tuples."""
    for key, value in payload.iteritems():
        if isinstance(value, list):
            for v in value:
                yield key, v
        else:
            yield key, value


def __params__(text, source, target, client='t',
               user_agent=DEFAULT_USER_AGENT):
    """Returns a dictionary containing all parameters to send a translation
    request to Google Translate."""

    headers = {
        'Referer': 'http://translate.google.com',
        'User-Agent': user_agent,
        'Content-Length': str(sys.getsizeof(text))
    }
    payload = {
        'client': client,
        'sl': source,
        'tl': target,
        'q': text,
        'dt': ['bd', 'ex', 'ld', 'md', 'qca', 'rw', 'rm', 'ss', 't', 'at'],
        'tk': len(text),
        'ssel': 0,
        'tsel': 3,
    }
    url = 'http://translate.google.com/translate_a/single'

    return {
        'headers': headers,
        'payload': payload,
        'url': url,
        'query': urllib.urlencode(list(__payload_as_tuples__(payload)))
    }


@api_module.route('/api/v1.3/params')
def params():
    text, source, target = \
        [request.args[x] for x in ('text', 'source', 'target')]
    return jsonify(__params__(text.encode('utf-8'), source, target))


@api_module.route('/api/v1.3/parse_javascript', methods=['post'])
def _parse_javascript():
    raw = request.form['raw']
    return jsonify({'parsed': parse_javascript(raw)})


@api_module.route('/api/v1.3/parse_result', methods=['post'])
def parse_result():
    """Parses a translation result."""
    raw = request.form['raw']
    parsed = parse_javascript(raw)
    import pdb; pdb.set_trace()


@api_module.route('/v1.0/languages')
@api_module.route('/api/v1.0/languages')
def languages():
    """Returns a list of supported languages."""
    locale = request.args['locale']  # noqa
    langs = {k: _(v) for (k, v) in zip(VALID_LANGUAGES.keys(),
                                       VALID_LANGUAGES.values())}

    return jsonify(langs)


@api_module.route('/v1.0/translate', methods=['POST'])
def translate_1_0():
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
        payload = translate(text, mode, source, target, 't')

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

        try:
            sentences = data['sentences']
        except:
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

    user_agent = request.headers.get('User-Agent')

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
