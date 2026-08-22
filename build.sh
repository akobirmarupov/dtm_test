#!/usr/bin/env bash
# Render build bosqichi. Har qanday xatoda darhol to'xtaydi.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate --no-input
