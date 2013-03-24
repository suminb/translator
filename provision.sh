#!/bin/bash

if [ ! -a /home/vagrant/flag ]; then
    sudo apt-get update
    sudo apt-get -y install python2.7 python-pip

    sudo pip install flask-babel flask-sqlalchemy 
    sudo pip install requests
    sudo pip install sphinx

    touch /home/vagrant/flag

fi
