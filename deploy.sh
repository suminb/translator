#!/bin/bash

HOST="sumin@suminb.com"

# Compile .po files
pybabel compile -d app/translations

# Delete .AppleDouble (effing OSX...)
rm -rf $(find . -name ".AppleDouble")

# Delete .pyc files
rm -rf $(find . -name "*.pyc")

# Deploy files
rsync -arzP -e ssh --exclude app/config.py --exclude app/static/statistics.js * $HOST:webapps/translator/webapp

# Deploy documents
rsync -arzP -e ssh docs/build/html/* $HOST:webapps/static/translator-docs/

read -p "Restart the server? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
	echo "Restarting the server..."
	ssh $HOST 'webapps/translator/apache2/bin/restart'
fi
