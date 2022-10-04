#!/bin/sh

# Migrate db
flask db upgrade

exec "$@"
