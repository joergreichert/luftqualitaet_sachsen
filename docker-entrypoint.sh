#!/bin/bash
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
mkvirtualenv luftverschmutzung_sachsen
#make create-db
make migrate
make runserver HOST=0.0.0.0
#python manage.py migrate                  # Apply database migrations
#python manage.py collectstatic --noinput  # Collect static files

