import os

from app import create_app


application = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8001))
    debug = bool(os.environ.get('DEBUG', 0))

    application.run(host=host, port=port, debug=debug)
