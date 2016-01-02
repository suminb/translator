# -*- coding: utf-8 -*-

from app.api import translate, HTTPException

import pytest
import json


def test_translate_1():
    """Tests translation where source language and target language are
    identical."""

    actual = translate('This is a test', 1, 'en', 'en')['translated_text']
    expected = 'This is a test'

    assert actual == expected


def test_translate_2():
    """Tests translation where an empty text is given."""

    with pytest.raises(HTTPException):
        translate('', 1, 'en', 'ko')


def test_translate_3():
    """Tests translation where an invalid source language is given."""

    with pytest.raises(HTTPException):
        translate('The cake was a lie', 1, 'unknown', 'ko')


def test_translate_4():
    """Tests translation where an invalid target language is given."""

    with pytest.raises(HTTPException):
        translate('The cake was a lie', 1, 'en', 'unknown')


def test_translate_5(testapp):
    params = dict(
        t=u'도요타는 일본의 자동차 제조사이다.',
        m=1, sl='ko', tl='en')

    resp = testapp.post('/v1.1/translate', data=params)
    assert resp.status_code == 200

    t = json.loads(resp.data)

    with open('/tmp/output.log', 'w') as f:
        f.write(resp.data)
        f.write('\n')

    assert 'Toyota' in t['translated_text']
    assert 'Japan' in t['translated_text']


def test_translate_6(testapp):
    params = dict(
        t=u'구글은 세계 정복을 꿈꾸고 있다.',
        m=1, sl='ko', tl='en')

    req = testapp.post('/v1.2/translate', data=params)
    assert req.status_code == 200

    t = json.loads(req.data)
    tt = t['translated_text']

    assert ('Google' in tt) or ('We' in tt) or ('I' in tt)
    assert 'dream' in tt
    assert 'world' in tt


def test_translate_7(testapp):
    params = dict(
        t=u'Coca Cola is one of the most widely known brand names.',
        m=2, sl='en', tl='ko')

    resp = testapp.post('/v1.2/translate', data=params)
    assert resp.status_code == 200

    data = json.loads(resp.data)
    tt = data['translated_text']

    assert u'코카콜라' in tt
    assert u'가장' in tt
    assert u'브랜드' in tt


def test_translate_v1_3_1(testapp):
    params = {
        'text': 'Python can be easy to pick up whether you\'re a first time '
                'programmer or you\'re experienced with other languages.',
        'source': 'en',
        'target': 'es',
    }
    resp = testapp.post('/api/v1.3/translate', data=params)
    assert resp.status_code == 200

    resp_data = json.loads(resp.data)
    assert resp_data['sentences']

    sentences = ' '.join([x['trans'] for x in resp_data['sentences']])
    assert 'Python' in sentences
    assert 'programador' in sentences
    assert 'experiencia' in sentences
    assert 'lenguajes' in sentences
