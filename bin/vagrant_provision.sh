#!/bin/bash

set -e

INSTALL_DIR=/home/vagrant

cd $INSTALL_DIR/kitsune

# Install package for add-apt-repository
apt-get install -y software-properties-common

# Install Elasticsearch 1.2.4 and set it up
curl https://packages.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://packages.elastic.co/elasticsearch/1.2/debian stable main" \
    > /etc/apt/sources.list.d/elasticsearch.list
apt-get update
apt-get install -y -q openjdk-7-jre-headless
apt-get install elasticsearch=1.2.4
update-rc.d elasticsearch defaults 95 10

# Add the needed repositories for Node/Redis/Python2.6
add-apt-repository ppa:chris-lea/node.js
add-apt-repository ppa:chris-lea/redis-server

apt-get update

# Set default password for MariaDB
export DEBIAN_FRONTEND=noninteractive
debconf-set-selections <<< 'mariadb-server-5.5 mysql-server/root_password password rootpass'
debconf-set-selections <<< 'mariadb-server-5.5 mysql-server/root_password_again password rootpass'

# Install services and their dependencies
# Services: Sphinx, MariaDB, Redis, and Memcached
apt-get install -y libapache2-mod-wsgi python-pip libmysqlclient-dev git \
                   libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev python-dev libssl-dev \
                   mariadb-server-5.5 nodejs redis-server memcached libffi-dev

# Setup the virtualenv and start using it
pip install virtualenv
virtualenv $INSTALL_DIR/virtualenv
chown -R vagrant $INSTALL_DIR/virtualenv
source $INSTALL_DIR/virtualenv/bin/activate

pip install -U 'pip<7'
$INSTALL_DIR/kitsune/peep.sh install -r $INSTALL_DIR/kitsune/requirements/default.txt
$INSTALL_DIR/kitsune/peep.sh install -r $INSTALL_DIR/kitsune/requirements/dev.txt

# Copy configurations for kitsune and mysql
# MySQL Default User: root
# MySQL Default Pass: rootpass
cp $INSTALL_DIR/kitsune/configs/vagrant/settings_local.py \
   $INSTALL_DIR/kitsune/kitsune/settings_local.py

cp $INSTALL_DIR/kitsune/configs/vagrant/my.cnf /etc/mysql/my.cnf

# Fix default port to match kitsune
sed -ie 's/^port 6379$/port 6383/' /etc/redis/redis.conf
service redis-server restart

# Create the kitsune database
mysql -e 'CREATE DATABASE kitsune CHARACTER SET utf8 COLLATE utf8_unicode_ci'
mysql -e "GRANT ALL ON kitsune.* TO kitsune@localhost IDENTIFIED BY 'password'"

# Install npm and included packages (lessc is the one we need of these)
npm install
./node_modules/.bin/gulp nunjucks
./node_modules/.bin/bower install

# Retrieve and store historical version data
./manage.py update_product_details

# Setup tables and generate some data
./manage.py migrate
./manage.py generatedata
