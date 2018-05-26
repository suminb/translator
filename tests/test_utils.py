from translator.utils import (
    HTTPException, language_options, language_options_html,
    parse_javascript)


def test_http_exception():
    try:
        raise HTTPException('An HTTP exception', 500)
        assert False
    except HTTPException as e:
        assert 'An HTTP exception' == e.message
        assert 500 == e.status_code


def test_language_options():
    options = language_options()
    for lang, name in options:
        assert isinstance(lang, str)
        assert isinstance(name, str)


def test_language_options_html():
    options = language_options_html()
    for option in options.split('\n'):
        assert option.startswith('<option')


def test_parse_javascript():
    assert parse_javascript('[,1,,2,,,3]') == \
        [None, 1, None, 2, None, None, 3]
