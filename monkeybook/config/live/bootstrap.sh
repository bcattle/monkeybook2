#!/usr/bin/env bash

APP_PATH=/home/ubuntu/src/monkeybook2 
CONF_PATH=$APP_PATH/monkeybook/config/live

#sudo apt-get update; sudo apt-get upgrade
sudo apt-get install git python-pip python-virtualenv mongodb uwsgi nginx-light

# Home directory
mkdir -p /home/ubuntu/src

# Controlled by supervisord
sudo /etc/init.d/mongodb stop
sudo /etc/init.d/nginx stop
sudo /etc/init.d/uwsgi stop
sudo rm /etc/init.d/nginx /etc/init.d/uwsgi

# Supervisor
sudo pip install supervisor
sudo ln -s $CONF_PATH/supervisord.conf /etc/supervisord.conf

# Start supervisord at boot
sudo cp $CONF_PATH/supervisord /etc/init.d/
sudo chmod +x /etc/init.d/supervisord
sudo update-rc.d supervisord defaults

# Start supervisor
sudo service supervisord start

