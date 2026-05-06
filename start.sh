#!/usr/bin/env bash
set -o errexit

DATA_DIR="${SQLITE_DATA_DIR:-data}"
SEED_MARKER="${SEED_ONCE_MARKER:-$DATA_DIR/.demo_seeded}"

mkdir -p "$DATA_DIR"

python manage.py migrate

if [ ! -f "$SEED_MARKER" ]; then
  python manage.py seed_demo_data
  python manage.py setup_role_users
  touch "$SEED_MARKER"
fi

gunicorn kindergarten_crm.wsgi:application
