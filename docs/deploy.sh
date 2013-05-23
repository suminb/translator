#!/bin/sh

HOST="sumin@suminb.com"

# Deploy documents
rsync -arzP -e ssh build/html/* $HOST:webapps/static/translator-docs/

