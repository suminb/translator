# -*- coding: utf-8 -*-

import json


def test_pages(testapp):
    pages = ('/', '/credits', '/discuss', '/disclaimers')

    for page in pages:
        resp = testapp.get(page)
        assert resp.status_code == 200


def test_locale_1(testapp):
    req = testapp.get('/locale?locale=ko')
    assert req.status_code == 302
    assert req.data != ''


def test_locale_2(testapp):
    req = testapp.get('/locale')
    assert req.status_code == 400


def test_languages_v1_0_t1(testapp):
    req = testapp.get('/v1.0/languages?locale=en')
    assert req.status_code == 200
    assert req.data != ''


def test_languages_v1_0_t2(testapp):
    req = testapp.get('/v1.0/languages')
    assert req.status_code == 400


def test_languages_v1_3_t1(testapp):
    req = testapp.get('/api/v1.3/languages?locale=en&field=source')
    assert req.status_code == 200
    assert req.data != ''

    languages = json.loads(req.data)['languages']
    assert '' not in [k for k, v in languages]


def test_languages_v1_3_t2(testapp):
    req = testapp.get('/api/v1.3/languages?locale=en&field=target')
    assert req.status_code == 200
    assert req.data != ''

    languages = json.loads(req.data)['languages']
    assert '' not in [k for k, v in languages]
    assert 'auto' not in [k for k, v in languages]


def test_languages_v1_3_t3(testapp):
    req = testapp.get('/api/v1.3/languages?locale=en&field=intermediate')
    assert req.status_code == 200
    assert req.data != ''

    languages = json.loads(req.data)['languages']
    assert len(languages) >= 3
    assert '' in [k for k, v in languages]


def test_languages_v1_3_t4(testapp):
    req = testapp.get('/api/v1.3/languages?locale=en&field=unknown')
    assert req.status_code == 400


def test_languages_v1_3_t5(testapp):
    req = testapp.get('/api/v1.3/languages?locale=en')
    assert req.status_code == 400


def test_languages_v1_3_t6(testapp):
    req = testapp.get('/api/v1.3/languages?field=source')
    assert req.status_code == 400


def test_version_check(testapp):
    resp = testapp.get('/api/v1.3/version-check')
    assert resp.status_code == 400

    resp = testapp.get('/api/v1.3/version-check?version=0.0.0')
    result = json.loads(resp.data)
    assert not result['is_latest']
    assert 'latest_version' in result
