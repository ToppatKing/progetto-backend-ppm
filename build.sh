#!/usr/bin/env bash
# Script di build per il deployment su PaaS (Render, Railway, ecc.)
# Installa le dipendenze, raccoglie i file statici, applica le migrazioni
# e popola i dati demo (il seeding è idempotente - sicuro da eseguire a
# ogni deploy).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_demo_data
