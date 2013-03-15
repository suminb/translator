#!/bin/bash

pybabel extract -o app/translations/messages.pot -F babel.cfg app
pybabel update -i app/translations/messages.pot -d app/translations
pybabel compile -d app/translations