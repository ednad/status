#!/bin/bash

# Check to make sure the input args have been passed in
if [ -n "$DB_RESET" ] && [ -n "$DB_NAME" ] && [ -n "$DB_HOST" ] && [ -n "$DB_USER" ] && [ -n "$DB_PASS" ] && [ -n "$DB_PORT" ] && [ -n "$APP_IP" ] && [ -n "$APP_PORT" ] && [ -n "$ROUTES_URL" ] && [ -n "$ROUTES_PORT" ]; then
  echo "All parameters supplied...continuing..."
else
  echo "Missing a launch parameter?"
  echo "APP_IP=$APP_IP"
  echo "APP_PORT=$APP_PORT"
  echo "DB_HOST=$DB_HOST"
  echo "DB_NAME=$DB_NAME"
  echo "DB_PORT=$DB_PORT"
  echo "DB_USER=$DB_USER"
  echo "DB_PASS=$DB_PASS"
  echo "DB_RESET=$DB_RESET"
  echo "ROUTES_URL=$ROUTES_URL"
  echo "ROUTES_PORT=$ROUTES_PORT
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
sed -i -e "s/url: 127.0.0.1/url: $APP_IP/g" status_settings.yml
sed -i -e "s/port: 4070/port: $APP_PORT/g" status_settings.yml
sed -i -e "s/routes_url: localhost/routes_url: $ROUTES_URL/g" status_settings.yml
sed -i -e "s/routes_port: 4000/routes_port: $ROUTES_PORT/g" status_settings.yml

sed -i -e "s/host: localhost/host: $DB_HOST/g" status_settings.yml
sed -i -e "s/username: username/username: $DB_USER/g" status_settings.yml
sed -i -e "s/password: password/password: $DB_PASS/g" status_settings.yml
sed -i -e "s/database: pstats/database: $DB_NAME/g" status_settings.yml

# Reset the database
if [ "$DB_RESET" == "True" ]; then
  echo "Dropping and recreating database $DB_NAME on host $DB_HOST..."
  psql -h $DB_HOST -U $DB_USER -d postgres -c "DROP DATABASE $DB_NAME;"
  psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
fi

# Launch OOI UI Services
python status_handler.py