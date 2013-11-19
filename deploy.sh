#!/bin/bash

HOST="sumin@suminb.com"

# Compile .po files
#pybabel compile -d app/translations

# Delete .AppleDouble (effing OSX...)
rm -rf $(find . -name ".AppleDouble")

# Delete .pyc files
rm -rf $(find . -name "*.pyc")

# Deploy files
rsync -arzP -e ssh --exclude app/config.py --exclude app/static/statistics.js --exclude app/*.db * $HOST:webapps/translator/webapp

read -p "Restart the server? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
	echo "Restarting the server..."
	ssh $HOST 'webapps/translator/apache2/bin/restart'
fi
