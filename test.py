# -*- coding: utf-8 -*- 

from testify import *
from app import translate, HTTPException

import requests
import json

HOST = 'http://localhost:5000'

class DefaultTestCase(TestCase):

    @class_setup
    def class_setup(self):
        from app.models import db

        db.create_all()

    #     host = '0.0.0.0'
    #     port = 8080
    #     debug = False

    #     app.run(host=host, port=port, debug=debug)

    def test_pages(self):
        pages = ('', 'credits', 'discuss', 'disclaimers', 'privacy')

        for page in pages:
            req = requests.get('{}/{}'.format(HOST, page))
            assert_equal(req.status_code, 200)

    def test_translate_1(self):
        """Tests translation where source language and target language are identical."""

        actual = translate('This is a test', 1, 'en', 'en')['translated_text']
        expected = 'This is a test'

        assert_equal(actual, expected)

    def test_translate_2(self):
        """Tests translation where an empty text is given."""

        assert_raises(HTTPException, lambda: translate('', 1, 'en', 'ko'))

    def test_translate_3(self):
        """Tests translation where an invalid source language is given."""

        f = lambda: translate('The cake was a lie', 1, 'unknown', 'ko')
        assert_raises(HTTPException, f)

    def test_translate_4(self):
        """Tests translation where an invalid target language is given."""

        f = lambda: translate('The cake was a lie', 1, 'en', 'unknown')
        assert_raises(HTTPException, f)

    # def test_translate_5(self):
    #     params = dict(
    #         t=u'도요타는 일본의 자동차 제조사이다.',
    #         m=1, sl='ko', tl='en')

    #     req = requests.post('{}/v1.1/translate'.format(HOST), data=params)
    #     assert_equal(req.status_code, 200)

    #     t = json.loads(req.text)
    #     assert_in('Toyota', t['translated_text'])


    def test_locale_1(self):
        req = requests.get('{}/locale?locale=ko'.format(HOST))
        assert_equal(req.status_code, 200)
        assert_not_equal(req.text, '')

    def test_locale_2(self):
        req = requests.get('{}/locale'.format(HOST))
        assert_equal(req.status_code, 400)


    def test_languages_1(self):
        req = requests.get('{}/v1.0/languages?locale=en'.format(HOST))
        assert_equal(req.status_code, 200)
        assert_not_equal(req.text, '')

    def test_languages_2(self):
        req = requests.get('{}/v1.0/languages'.format(HOST))
        assert_equal(req.status_code, 400)


    @class_teardown
    def class_teardown(self):
        pass


class UserTestCase(TestCase):
    def test_login(self):
        req = requests.get('{}/login'.format(HOST), allow_redirects=False)
        assert_equal(req.status_code, 302)

    def test_user_page(self):
        """Try to access the user page without authentication."""
        req = requests.get('{}/user'.format(HOST), allow_redirects=False)
        assert_equal(req.status_code, 302)


if __name__ == '__main__':
    run()
