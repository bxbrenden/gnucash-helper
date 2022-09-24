#!/bin/bash
export FLASK_APP=gch.py
export GCH_DEV='/home/brenden/gch-dev'
export GCH_LOG_DIR='/home/brenden/gch-dev/logs'
export EASY_CONFIG_DIR=$GCH_DEV
pyenv global 3.9.12
cd ~/git/gnucash-helper
python3 -m pip install --upgrade pipenv
echo -e "Running pipenv install with no args...\n"
pipenv install
mkdir -p $GCH_DEV
mkdir -p $GCH_LOG_DIR
if [ ! -f $GCH_DEV/demo-budget.gnucash ]; then
    cp ~/git/gnucash-helper/demo-budget.gnucash $GCH_DEV
fi
touch $GCH_LOG_DIR/gnucash-helper.log
export GNUCASH_DIR=$GCH_DEV
export GNUCASH_FILE=demo-budget.gnucash
export NUM_TRANSACTIONS=10000
echo -e "Running gnucash-helper via pipenv run gunicorn...\n"
pipenv run gunicorn -b 0.0.0.0:8000 --worker-tmp-dir /dev/shm gch:app

# UNCOMMENT BELOW FOR FLASK RUN
# echo "Running gnucash-helper via 'pipenv run flask run'"
# pipenv run flask run
