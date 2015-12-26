import pytest


@pytest.fixture
def testapp():
    from app import create_app
    app = create_app(config={'DEBUG': True})
    return app.test_client()
