#!/bin/bash
cd /volume1/web/app_offerte
source venv/bin/activate
export FLASK_ENV=production
export PORT=5002
python wsgi.py >> logs/app.log 2>&1