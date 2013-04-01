#!/bin/bash

if [ ! -a /home/vagrant/flag ]; then
    sudo apt-get update
    sudo apt-get -y install python2.7 python-pip
    sudo apt-get -y install libpq5

    sudo pip install flask-babel flask-sqlalchemy 
    sudo pip install requests
    sudo pip install sphinx
    sudo pip install psycopg2

    touch /home/vagrant/flag

fi
