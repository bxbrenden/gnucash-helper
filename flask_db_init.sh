#!/bin/bash
export FLASK_APP=gch.py

/usr/local/bin/flask db migrate
/usr/local/bin/flask db upgrade
