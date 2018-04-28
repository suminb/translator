#!/bin/bash

pybabel extract -o translator/translations/messages.pot -F babel.cfg translator
pybabel update -i translator/translations/messages.pot -d translator/translations
pybabel compile -d translator/translations
