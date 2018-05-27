# -*- coding: utf-8 -*-

import json

import pytest


def test_pages(testapp):
    pages = ('/', '/credits.html', '/discuss.html', '/disclaimers.html')

    for page in pages:
        resp = testapp.get(page)
        assert resp.status_code == 200


def test_locale_1(testapp):
    resp = testapp.get('/locale?locale=ko')
    assert resp.status_code == 302
    assert resp.data


def test_locale_2(testapp):
    resp = testapp.get('/locale')
    assert resp.status_code == 400


def test_languages_v1_0_t1(testapp):
    resp = testapp.get('/v1.0/languages?locale=en')
    assert resp.status_code == 200
    assert resp.data


def test_languages_v1_0_t2(testapp):
    resp = testapp.get('/v1.0/languages')
    assert resp.status_code == 400


def test_languages_v1_3_t1(testapp):
    resp = testapp.get('/api/v1.3/languages?locale=en&field=source')
    assert resp.status_code == 200
    assert resp.data

    languages = json.loads(resp.get_data(as_text=True))['languages']
    assert '' not in [k for k, v in languages]


def test_languages_v1_3_t2(testapp):
    resp = testapp.get('/api/v1.3/languages?locale=en&field=target')
    assert resp.status_code == 200
    assert resp.data

    languages = json.loads(resp.get_data(as_text=True))['languages']
    assert '' not in [k for k, v in languages]
    assert 'auto' not in [k for k, v in languages]


def test_languages_v1_3_t3(testapp):
    resp = testapp.get('/api/v1.3/languages?locale=en&field=intermediate')
    assert resp.status_code == 200
    assert resp.data

    languages = json.loads(resp.get_data(as_text=True))['languages']
    assert len(languages) >= 3
    assert '' in [k for k, v in languages]


def test_languages_v1_3_t4(testapp):
    resp = testapp.get('/api/v1.3/languages?locale=en&field=unknown')
    assert resp.status_code == 400


def test_languages_v1_3_t5(testapp):
    resp = testapp.get('/api/v1.3/languages?locale=en')
    assert resp.status_code == 400


def test_languages_v1_3_t6(testapp):
    resp = testapp.get('/api/v1.3/languages?field=source')
    assert resp.status_code == 400


def test_version_check(testapp):
    resp = testapp.get('/api/v1.3/version-check')
    assert resp.status_code == 400

    resp = testapp.get('/api/v1.3/version-check?version=0.0.0')
    result = json.loads(resp.get_data(as_text=True))
    assert not result['is_latest']
    assert 'latest_version' in result


def test_exception_v1_3(testapp):
    with pytest.raises(Exception):
        resp = testapp.get('/api/v1.3/exception?message=test')
