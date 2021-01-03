from gnucash_helper import list_accounts,\
                           get_book_name_from_env,\
                           open_book,\
                           get_account,\
                           add_transaction,\
                           get_gnucash_dir,\
                           git_pull,\
                           git_add_commit_and_push,\
                           get_github_token_and_url_from_env,\
                           git_ensure_cloned,\
                           git_set_user_and_email,\
                           get_git_user_name_and_email_from_env,\
                           git_ensure_discard_uncommitted

from decimal import Decimal, ROUND_HALF_UP
import logging
from os import environ as env

from flask import Flask, render_template, session, redirect, url_for, flash
from flask.logging import default_handler
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import DecimalField,\
                    SelectField,\
                    StringField,\
                    SubmitField,\
                    TextAreaField

from wtforms.validators import DataRequired


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
fh = logging.FileHandler('/gnucash-helper.log', encoding='utf-8')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s:%(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)


class TransactionForm(FlaskForm):
    book_name = get_book_name_from_env()
    gnucash_dir = get_gnucash_dir()
    path_to_book = gnucash_dir + '/' + book_name
    accounts = list_accounts(path_to_book)

    debit = SelectField('From Account (Debit)',
                        validators=[DataRequired()],
                        choices=accounts,
                        validate_choice=True)
    credit = SelectField('To Account (Credit)',
                         validators=[DataRequired()],
                         choices=accounts,
                         validate_choice=True)
    amount = DecimalField('Amount ($)',
                        validators=[DataRequired('Do not include a dollar sign $')],
                        places=2,
                        rounding=ROUND_HALF_UP,
                        render_kw={'placeholder': 'Ex: 4.20'})
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')


app = Flask(__name__)
app.config['SECRET_KEY'] = env.get('FLASK_SECRET_KEY',
                                   'Mjpe[){i>"r3}]Fm+-{7#,m}qFtf!w)T')
app.logger.removeHandler(default_handler)

bootstrap = Bootstrap(app)


@app.before_first_request
def configure_git():
    '''Do all the legwork of setting up git user, git user's email,
       personal access token, repo URL, and ensuring the repo has
       already been cloned (clone should already be done by docker).'''
    logger = logging.getLogger(__name__)
    gnucash_dir = get_gnucash_dir()
    gh_token, gh_url = get_github_token_and_url_from_env()
    git_user, git_email = get_git_user_name_and_email_from_env()
    git_configured = git_set_user_and_email(git_user, git_email)

    if git_configured:
        cloned = git_ensure_cloned(gnucash_dir, gh_token, gh_url)
        if not cloned:
            logger.critical('Git clone of GitHub repo failed. Exiting')
            sys.exit(1)
    else:
        logger.critical('git configuration of name and email failed. Exiting')
        sys.exit(1)


@app.before_request
def git_ensure_good_state():
    '''Ensure that any uncommitted changes are discarded, and do a `git pull`.'''
    logger = logging.getLogger(__name__)
    logger.critical('Running pre-request git cleanup commands')
    gnucash_dir = get_gnucash_dir()
    book_name = get_book_name_from_env()
    git_ensure_discard_uncommitted(gnucash_dir, book_name)
    git_pull(gnucash_dir)


@app.route('/', methods=['GET', 'POST'])
def index():
    logger = logging.getLogger(__name__)
    form = TransactionForm()
    if form.validate_on_submit():
        # Add the transaction to the GnuCash book
        book_name = get_book_name_from_env()
        gnucash_dir = get_gnucash_dir()
        path_to_book = gnucash_dir + '/' + book_name
        gnucash_book = open_book(path_to_book)
        descrip = form.description.data
        amount = form.amount.data
        credit = form.credit.data
        debit = form.debit.data
        added_txn = add_transaction(gnucash_book, descrip, amount, debit, credit)
        gnucash_book.close()

        git_result, git_output = git_add_commit_and_push(gnucash_dir, book_name, descrip)
        if added_txn and git_result:
            success_msg = f'Transaction for ${float(form.amount.data):.2f} saved!'
            flash(success_msg, category='success')
            logger.info(success_msg)
        else:
            failure_msg = f'Transaction ${float(form.amount.data):.2f} was saved'
            flash(failure_msg, 'danger')
            flash(git_output, 'danger')
            logger.critical(failure_msg)
            logger.critical(git_result)
        return redirect(url_for('index'))
    return render_template('index.html', form=form)


@app.errorhandler(404)
def page_nout_found(e):
    return render_template('404.html')


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html')
