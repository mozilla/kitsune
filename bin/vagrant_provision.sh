#!/bin/bash

set -e
set -x

INSTALL_DIR=/home/vagrant

cd $INSTALL_DIR/kitsune

# Configure locales
export LC_ALL="en_US.UTF-8"
locale-gen en_US.UTF-8

# Install package for add-apt-repository
apt-get install -y software-properties-common

# Add the needed repositories for Node/Redis/Python2.6
add-apt-repository ppa:chris-lea/node.js
add-apt-repository ppa:chris-lea/redis-server

apt-get update

# Install Python development-related things
apt-get install -y -q libapache2-mod-wsgi python-pip python-virtualenv libpython-dev

# Install services and their dependencies
# Services: Sphinx, Redis, and Memcached
apt-get install -y libxml2-dev libxslt1-dev zlib1g-dev libjpeg-dev libssl-dev \
                   nodejs redis-server memcached libffi-dev

# Install git
apt-get install -y -q git

# Install mysql
export DEBIAN_FRONTEND=noninteractive
debconf-set-selections <<< 'mysql-server mysql-server/root_password password rootpass'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password rootpass'
apt-get install -y -q mysql-client mysql-server libmysqlclient-dev

# Install Elasticsearch 1.2.4 and set it up
curl https://packages.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://packages.elastic.co/elasticsearch/1.2/debian stable main" \
    > /etc/apt/sources.list.d/elasticsearch.list
apt-get update
apt-get install -y -q openjdk-7-jre-headless elasticsearch=1.2.4
update-rc.d elasticsearch defaults 95 10

# Copy over mysql cnf file
cp $INSTALL_DIR/kitsune/configs/vagrant/my.cnf /etc/mysql/my.cnf
service mysql restart

# Create the kitsune database
mysql -e 'CREATE DATABASE kitsune CHARACTER SET utf8 COLLATE utf8_unicode_ci'
mysql -e "GRANT ALL ON kitsune.* TO kitsune@localhost IDENTIFIED BY 'password'"

# Fix default port for redis to match kitsune
sed -ie 's/^port 6379$/port 6383/' /etc/redis/redis.conf
service redis-server restart

# Copy configurations for kitsune and mysql
# MySQL Default User: root
# MySQL Default Pass: rootpass
sudo -H -u vagrant cp $INSTALL_DIR/kitsune/configs/vagrant/settings_local.py \
                      $INSTALL_DIR/kitsune/kitsune/settings_local.py

# Build virtual environment
VENV=/home/vagrant/virtualenv

sudo -H -u vagrant -s -- <<EOF
virtualenv $VENV
source $VENV/bin/activate
cd ~/kitsune
./peep.sh install -r requirements/default.txt
./peep.sh install -r requirements/dev.txt
EOF

# Install npm and included packages (lessc is the one we need of these)
sudo -H -u vagrant -s -- <<EOF
npm install
./node_modules/.bin/gulp nunjucks
./node_modules/.bin/bower install
EOF

# Set up kitsune environment
sudo -H -u vagrant -s -- <<EOF
source $VENV/bin/activate
cd ~/kitsune
./manage.py update_product_details
./manage.py migrate
./manage.py generatedata
EOF


cat <<EOF

************************************************************************

If it gets here, then the Vagrant VM is provisioned. You should be all
set.

Consult the documentation on how to use and maintain this VM.

https://kitsune.readthedocs.io/

Next steps:

1. hop on #sumodev on irc.mozilla.org and say hi
2. find a bug to work on

************************************************************************

EOF
