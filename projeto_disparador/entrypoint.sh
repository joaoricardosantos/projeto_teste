#!/bin/bash

python manage.py makemigrations core
python manage.py migrate
python manage.py shell -c "from core.models import User; User.objects.filter(email='admin@admin.com').exists() or User.objects.create_superuser('admin@admin.com', 'admin123', name='Administrador')"

exec gunicorn core.wsgi:application --bind 0.0.0.0:8000