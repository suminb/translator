
Build Status
============
![Better Translator build status](https://travis-ci.org/suminb/translator.svg)
[![Coverage Status](https://coveralls.io/repos/suminb/translator/badge.svg?branch=develop&service=github)](https://coveralls.io/github/suminb/translator?branch=develop)

Deploy on AWS Elastic Beanstalk
===============================

Install EB CLI. For more details, refer [the official
documentation](http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html).

    pip install awsebcli

(TODO: Write some description how I set up things)

    eb deploy
    
Data Warehousing
================

### Launch a PostgreSQL database

    docker run -d -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=${password} -e POSTGRES_DB=test -p 5432:5432 --volume ${host_dir}:/var/lib/postgresql/data postgres

### Connect to the database

    psql -h localhost -U postgres translator

### Backup

    pg_dump -h localhost -U postgres -d translator -f translator.sql


Credits
=======

* Translation service: <http://translate.google.com>
* App icon: <http://icon-generator.net>
* Loading icon: <http://www.ajaxload.info>

Sponsors
========

<a href="https://www.browserstack.com">
  <img src="https://jordankasper.com/js-testing/images/browserstack.png"/>
</a>
