#!/usr/bin/env bash
set -o errexit

SEED_MARKER="${SEED_ONCE_MARKER:-/var/data/.demo_seeded}"

mkdir -p "$(dirname "$SEED_MARKER")"

python manage.py migrate

if [ ! -f "$SEED_MARKER" ]; then
  python manage.py seed_demo_data
  python manage.py setup_role_users
  touch "$SEED_MARKER"
fi

gunicorn kindergarten_crm.wsgi:application
