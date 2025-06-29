#!/bin/bash
# Build script for Django deployment

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser if needed (uncomment if needed)
# python manage.py createsuperuser --noinput 