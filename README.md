Build Status
------------
![Better Translator build status](https://travis-ci.org/suminb/translator.svg)
[![Coverage Status](https://coveralls.io/repos/suminb/translator/badge.svg?branch=develop&service=github)](https://coveralls.io/github/suminb/translator?branch=develop)

Important Notes
---------------

- Make sure the API Gateway is deployed.
- Fill out `api_base_url` and `api_version` in `translator/main/__init__.py`.

Text Localization
-----------------

Running the following command will generate `.mo` files based on `.po` files.

    ./localization.sh

Deploy Static Frontend
----------------------

Freeze the Flask app first:

    python freeze.py

Then upload to S3:

    aws s3 sync translator/build/ s3://better-translator.com/ \
        --grants read=uri=http://acs.amazonaws.com/groups/global/AllUsers

Deploy on AWS with Seamless
---------------------------

### Install required npm packages

    npm i --save serverless serverless-wsgi

### Deploy on AWS

    sls deploy --region=ap-northeast-2

### Serve locally

    sls wsgi serve

Deploy on AWS Elastic Beanstalk
-------------------------------

    eb deploy

Text Localization
-----------------

Running the following command will generate `.mo` files based on `.po` files.

    ./localization.sh

Data Warehousing
----------------

### Launch a PostgreSQL database

    docker run -d \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=${password} \
        -e POSTGRES_DB=test \
        -p 5432:5432 \
        --volume ${host_dir}:/var/lib/postgresql/data \
        postgres

### Deploy on AWS

    sls deploy --region=ap-northeast-2

### Serve locally

    sls wsgi serve

Credits
-------

* Translation service: <http://translate.google.com>
* App icon: <http://icon-generator.net>
* Loading icon: <http://www.ajaxload.info>

Sponsors
--------

<a href="https://www.browserstack.com">
  <img src="https://jordankasper.com/js-testing/images/browserstack.png"/>
</a>
