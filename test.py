from testify import *
from app import translate, HTTPException
import requests

class DefaultTestCase(TestCase):
    HOST = 'http://localhost:5000'

    def test_pages(self):
        pages = ('', 'credits', 'discuss', 'disclaimers', 'privacy')

        for page in pages:
            req = requests.get('{}/{}'.format(self.HOST, page))
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


if __name__ == '__main__':
    run()
