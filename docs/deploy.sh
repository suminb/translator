#!/bin/sh

aws s3 sync build/html s3://better-translator.com/docs/ \
    --grants read=uri=http://acs.amazonaws.com/groups/global/AllUsers
