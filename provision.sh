#!/bin/bash

if [ ! -a /home/vagrant/flag ]; then
    #sudo apt-get update
    sudo apt-get -y install python2.7 python-pip
    sudo apt-get -y install libpq5 libpq-dev python-dev

    sudo pip install flask-babel flask-sqlalchemy 
    sudo pip install requests
    sudo pip install sphinx sphinxcontrib-httpdomain
    sudo pip install psycopg2
    sudo pip install nilsimsa

    touch /home/vagrant/flag

fi
