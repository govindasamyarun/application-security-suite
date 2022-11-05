#!/bin/sh

if [ "$DB_DATABASE" = "postgres" ]
then
    echo "INFO - Waiting for PostgreSQL DB"

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "INFO - PostgreSQL DB started"
fi

python -u src/app.py

exec "$@"