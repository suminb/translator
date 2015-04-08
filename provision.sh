#!/bin/bash

if [ ! -a /vagrant/.provisioned ]; then
    #sudo apt-get update
    sudo apt-get -y install python2.7 python-pip
    sudo apt-get -y install libpq5 libpq-dev python-dev
    sudo apt-get -y install postgresql-contrib
    sudo apt-get -y install screen vim

    sudo pip install -r requirements.txt

    sudo su - postgres
    #echo "createuser -s vagrant" | psql
    echo "CREATE ROLE vagrant SUPERUSER LOGIN" | psql
    echo "CREATE DATABASE vagrant" | psql
    exit
    cat /vagrant/scheme.sql | psql

    touch /vagrant/.provisioned

fi
