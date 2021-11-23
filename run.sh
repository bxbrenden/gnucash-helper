#!/bin/bash
pyenv global 3.9.8
cd ~/git/gnucash-helper
pip install -r requirements.txt
sudo mkdir /gnucash
sudo cp ~/git/gnucash-helper/demo-budget.gnucash /gnucash
sudo touch /gnucash-helper.log
sudo chown -R brenden:brenden /gnucash*
export GNUCASH_DIR=/gnucash
export GNUCASH_FILE=demo-budget.gnucash
export NUM_TRANSACTIONS=200
gunicorn -b 0.0.0.0:8000 --worker-tmp-dir /dev/shm app:app
