#!/bin/bash
cd "/volume1/web/app_offerte"
export FLASK_ENV=production
export FLASK_CONFIG=synology
python3 start_synology.py
