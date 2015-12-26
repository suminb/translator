import os
import sys
sys.path.insert(1, os.path.join(os.path.abspath('.'), 'lib'))

import yaml

from app import create_app


class DummyApp(object):
    def __init__(self):
        config = yaml.load(open('config.yml').read())
        self.app = create_app(config=config)

app = DummyApp()
