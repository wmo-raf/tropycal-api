#!/bin/sh

echo "Migrating Database..."
# Migrate db
flask db upgrade

exec "$@"
