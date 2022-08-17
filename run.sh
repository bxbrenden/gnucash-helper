#!/bin/bash
export GCH_DEV='/home/brenden/gch-dev'
export GCH_LOG_DIR='/home/brenden/gch-dev/logs'
pyenv global 3.9.12
cd ~/git/gnucash-helper
python3 -m install --upgrade pipenv
echo -e "Running pipenv install with no args...\n"
pipenv install
mkdir -p $GCH_DEV
mkdir -p $GCH_LOG_DIR
cp ~/git/gnucash-helper/demo-budget.gnucash $GCH_DEV
touch $GCH_LOG_DIR/gnucash-helper.log
export GNUCASH_DIR=$GCH_DEV
export GNUCASH_FILE=demo-budget.gnucash
export NUM_TRANSACTIONS=200
echo -e "Running gnucash-helper via pipenv run gunicorn...\n"
pipenv run gunicorn -b 0.0.0.0:8000 --worker-tmp-dir /dev/shm app:app
