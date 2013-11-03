# -*- coding: utf-8 -*- 

from py.test import *
from app import translate, HTTPException

import pytest
import requests
import json

HOST = 'http://localhost:5000'

def setup_module(module):
    """ setup any state specific to the execution of the given module."""

    from app.models import db

    db.create_all()


class TestBasic:

    # @class_setup
    # def class_setup(self):
    #     from app.models import db

    #     db.create_all()


    def test_pages(self):
        pages = ('', 'credits', 'discuss', 'disclaimers', 'privacy',
            'hrequest', 'corpus')

        for page in pages:
            req = requests.get('{}/{}'.format(HOST, page))
            assert req.status_code == 200

    def test_translate_1(self):
        """Tests translation where source language and target language are identical."""

        actual = translate('This is a test', 1, 'en', 'en')['translated_text']
        expected = 'This is a test'

        assert actual == expected

    def test_translate_2(self):
        """Tests translation where an empty text is given."""

        with pytest.raises(HTTPException):
            translate('', 1, 'en', 'ko')

    def test_translate_3(self):
        """Tests translation where an invalid source language is given."""

        with pytest.raises(HTTPException):
            translate('The cake was a lie', 1, 'unknown', 'ko')

    def test_translate_4(self):
        """Tests translation where an invalid target language is given."""

        with pytest.raises(HTTPException):
            translate('The cake was a lie', 1, 'en', 'unknown')

    def test_translate_5(self):
        params = dict(
            t=u'도요타는 일본의 자동차 제조사이다.',
            m=1, sl='ko', tl='en')

        req = requests.post('{}/v1.1/translate'.format(HOST), data=params)
        assert req.status_code == 200

        t = json.loads(req.text)

        with open('/tmp/output.log', 'w') as f:
            f.write(req.text)
            f.write('\n')

        assert 'Toyota' in t['translated_text']
        assert 'Japan' in t['translated_text']

    def test_translate_6(self):
        params = dict(
            t=u'구글은 세계 정복을 꿈꾸고 있다.',
            m=1, sl='ko', tl='en')

        req = requests.post('{}/v1.2/translate'.format(HOST), data=params)
        assert req.status_code == 200

        t = json.loads(req.text)
        tt = t['translated_text']

        assert ('Google' in tt) or ('We' in tt)
        assert 'dream' in tt
        assert 'world' in tt

    def test_translate_7(self):
        params = dict(
            t=u'Coca Cola is one of the most widely known brand names.',
            m=2, sl='en', tl='ko')

        req = requests.post('{}/v1.2/translate'.format(HOST), data=params)
        assert req.status_code == 200

        t = json.loads(req.text)
        tt = t['translated_text']

        assert u'코카콜라' in tt
        assert u'가장' in tt
        assert u'브랜드' in tt


    def test_locale_1(self):
        req = requests.get('{}/locale?locale=ko'.format(HOST))
        assert req.status_code == 200
        assert req.text != ''

    def test_locale_2(self):
        req = requests.get('{}/locale'.format(HOST))
        assert req.status_code == 400


    def test_languages_1(self):
        req = requests.get('{}/v1.0/languages?locale=en'.format(HOST))
        assert req.status_code == 200
        assert req.text != ''

    def test_languages_2(self):
        req = requests.get('{}/v1.0/languages'.format(HOST))
        assert req.status_code == 400


# TODO: Move this class elsewhere
class TestUser:
    def test_login(self):
        req = requests.get('{}/login'.format(HOST), allow_redirects=False)
        assert req.status_code == 302

    def test_user_page(self):
        """Try to access the user page without authentication."""
        req = requests.get('{}/user'.format(HOST), allow_redirects=False)
        assert req.status_code == 302

