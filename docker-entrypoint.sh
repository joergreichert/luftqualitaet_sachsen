#!/bin/bash
service postgresql start
make runserver HOST=0.0.0.0
#python manage.py collectstatic --noinput  # Collect static files

