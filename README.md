# GnuCash-Helper

GnuCash-Helper is a small Flask app for entering GnuCash transactions from a web browser.


# Requirements
You will need `python 3.9` and `pip`.

Use `pip install -r requirements.txt` to install the dependencies.


# Configuration

`gnucash_helper` needs several environment variables configured.
It also requires a git repo that contains your `.gnucash` file.


## Environment Variables
- `GNUCASH_DIR`: the fully qualified path to the directory with your `.gnucash` file, e.g. `/home/brenden/budget`
- `GNUCASH_BOOK_NAME`: the name of your `.gnucash` file, e.g. `budget.gnucash`
- `FLASK_APP`: the name of the Flask application, e.g. `app.py`
- `FLASK_SECRET_KEY`: a long, random string of chars for Flask CSRF protection


## Git Repo
This tool assumes you are keeping your `.gnucash` file up to date in a git repository.
It also assumes that your `.gnucash` file is saved in the `sqlite3` format.

**This will not work if your `.gnucash` file is in XML or PostgreSQL format**


# Usage

1. Clone this repository to your workstation / server.
2. In a separate directory, clone your GnuCash repository.
3. Run `pip3 install -r requirements.txt` to install the dependencies.
4. Set the environment variables mentioned in the `Environment Variables` section of this readme file.
5. Run the app with `flask run`. **Note: need to change this to gunicorn and add auth. for prod!** 
6. Visit the URl of your running app, and add a transaction to test.
