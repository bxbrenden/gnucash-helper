#!/bin/bash
export FLASK_APP=gch.py

flask db migrate
flask db upgrade
rm -f /app/flask_db_init.sh
