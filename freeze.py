from flask_frozen import Freezer
from translator import create_app


app = create_app()
freezer = Freezer(app, with_no_argument_rules=False)

@freezer.register_generator
def generator():
    yield 'main.index', {'paths': ''}
    yield 'main.about', {'paths': ''}
    yield 'main.credits', {'paths': ''}
    yield 'main.discuss', {'paths': ''}
    yield 'main.disclaimers', {'paths': ''}


if __name__ == '__main__':
    freezer.freeze()
