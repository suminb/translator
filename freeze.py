from flask_frozen import Freezer
from translator import create_app


app = create_app()
freezer = Freezer(app, with_no_argument_rules=False)


@freezer.register_generator
def generator():
    yield 'main.index', {}
    yield 'main.about', {}
    yield 'main.credits', {}
    yield 'main.discuss', {}
    yield 'main.disclaimers', {}
    yield 'main.longtext', {}


if __name__ == '__main__':
    freezer.freeze()
