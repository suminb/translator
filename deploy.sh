#!/bin/bash

HOST="sumin@suminb.com"

# Compile .po files
pybabel compile -d app/translations

# Delete .AppleDouble (effing OSX...)
rm -rf $(find . -name ".AppleDouble")

# Deploy files
rsync -arzP -e ssh * $HOST:webapps/translator/webapp

read -p "Restart the server? " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
	echo "Restarting the server..."
	ssh $HOST 'webapps/translator/apache2/bin/restart'
fi