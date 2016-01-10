from app.utils import HTTPException


def test_http_exception():
    try:
        raise HTTPException('An HTTP exception', 500)
        assert False
    except HTTPException as e:
        assert 'An HTTP exception' == e.message
        assert 500 == e.status_code
