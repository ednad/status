#!/bin/bash

# Check to make sure the input args have been passed in
if [ -n "$DB_RESET" ] && [ -n "$DB_NAME" ] && [ -n "$DB_HOST" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASS" ] && [ -n "$DB_PORT" ] && [ -n "$DB_SCHEMA" ] && [ -n "$HOST_IP" ] && [ -n "$DEFAULT_ADMIN_USERNAME" ] && [ -n "$DEFAULT_ADMIN_PASSWORD" ]; then
  echo "All parameters supplied...continuing..."
else
  echo "Missing a launch parameter?"
  echo "HOST_IP=$HOST_IP"
  echo "DB_HOST=$DB_HOST"
  echo "DB_NAME=$DB_NAME"
  echo "DB_PORT=$DB_PORT"
  echo "DB_USER=$DB_USER"
  echo "DB_PASS=$DB_PASS"
  echo "DB_RESET=$DB_RESET"
  exit
fi

# Add credentials to .pgpass for database access
echo $DB_HOST:$DB_PORT:*:$DB_USER:$DB_PASS > ~/.pgpass
chmod 600 ~/.pgpass

# Get our virtual environment set up
source ~/.bash_profile
workon ooiuistatus
export PYTHONPATH=$PYTHONPATH:.

# Make the config files conform to the launch parameters
#sed -i -e "s/HOST: localhost/HOST: $HOST_IP/g" ooiservices/app/config.yml
#sed -i -e "s/postgres@localhost\/$DB_NAME/$DB_USER:$DB_PASS@$DB_HOST\/$DB_NAME/g" ooiservices/app/config.yml

# Reset the database
if [ "$DB_RESET" == "True" ]; then
  echo "Dropping and recreating database $DB_NAME on host $DB_HOST..."
  psql -h $DB_HOST -U $DB_USER -d postgres -c "DROP DATABASE $DB_NAME;"
  psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
fi

# Launch OOI UI Services
python status_handler.py