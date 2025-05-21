#!/usr/bin/env bash
# build.sh — prepara seu Django antes do start
set -o errexit

# 1) instala suas dependências
pip install -r requirements.txt

# 2) migra o banco (vai usar a DATABASE_URL do env do Render)
python manage.py migrate

# 3) coleta todos os staticfiles para a pasta staticfiles/
python manage.py collectstatic --noinput
