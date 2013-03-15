#!/bin/sh

# Compile .po files
pybabel compile -d app/translations

# Delete .AppleDouble (effing OSX...)
rm -rf $(find . -name ".AppleDouble")

# Deploy files
rsync -arzP -e ssh * suminb.com:webapps/translator/webapp