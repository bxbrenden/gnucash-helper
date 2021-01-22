from gnucash_helper import list_accounts,\
                           get_book_name_from_env,\
                           open_book,\
                           add_transaction,\
                           get_gnucash_dir,\
                           git_pull,\
                           git_add_commit_and_push,\
                           get_github_token_and_url_from_env,\
                           git_ensure_cloned,\
                           git_set_user_and_email,\
                           get_git_user_name_and_email_from_env,\
                           git_ensure_discard_uncommitted,\
                           logger,\
                           last_n_transactions,\
                           get_env_var

from decimal import ROUND_HALF_UP
from os import environ as env
import sys

from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import DecimalField,\
                    SelectField,\
                    SubmitField,\
                    TextAreaField

from wtforms.validators import DataRequired

book_name = get_book_name_from_env()
gnucash_dir = get_gnucash_dir()
path_to_book = gnucash_dir + '/' + book_name


class TransactionForm(FlaskForm):
    global book_name
    global gnucash_dir
    global path_to_book
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
                          validators=[DataRequired('Do not include a dollar sign or a comma.')],
                          places=2,
                          rounding=ROUND_HALF_UP,
                          render_kw={'placeholder': 'Ex: 4.20'})
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')


app = Flask(__name__)
app.config['SECRET_KEY'] = env.get('FLASK_SECRET_KEY',
                                   'Mjpe[){i>"r3}]Fm+-{7#,m}qFtf!w)T')
bootstrap = Bootstrap(app)


@app.before_first_request
def configure_git():
    '''Do all the legwork of setting up git user, git user's email,
       personal access token, repo URL, and ensuring the repo has
       already been cloned (clone should already be done by docker).'''
    global logger
    global gnucash_dir
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
    global logger
    global book_name
    global gnucash_dir
    logger.info('Running pre-request git cleanup commands')
    git_ensure_discard_uncommitted(gnucash_dir, book_name)
    git_pull(gnucash_dir)


@app.route('/', methods=['GET', 'POST'])
def index():
    global logger
    global book_name
    global gnucash_dir
    global path_to_book
    form = TransactionForm()
    if form.validate_on_submit():
        # Add the transaction to the GnuCash book
        gnucash_book = open_book(path_to_book)
        descrip = form.description.data
        amount = form.amount.data
        credit = form.credit.data
        debit = form.debit.data
        added_txn = add_transaction(gnucash_book, descrip, amount, debit, credit)
        gnucash_book.close()

        if added_txn:
            flash(f'Transaction for {float(amount):.2f} saved to GnuCash file.',
                  'success')
        else:
            flash(f'Transaction for {float(amount):.2f} was not saved to GnuCash file.',
                  'danger')

        git_result, git_output = git_add_commit_and_push(gnucash_dir, book_name, descrip)
        if git_result:
            success_msg = f'Transaction for ${float(form.amount.data):.2f} committed to GitHub.'
            flash(success_msg, 'success')
            logger.info(success_msg)
        else:
            failure_msg = f'Transaction ${float(form.amount.data):.2f} not synced to GitHub'
            flash(failure_msg, 'danger')
            flash(git_output, 'danger')
            logger.critical(failure_msg)
            logger.critical(git_result)
        return redirect(url_for('index'))
    return render_template('index.html', form=form)


@app.route('/transactions')
def transactions():
    global path_to_book
    book = open_book(path_to_book)

    # determine the number of transactions to display based on env var
    num_transactions = int(get_env_var('NUM_TRANSACTIONS'))
    if num_transactions is None:
        transactions = last_n_transactions(book)
    else:
        transactions = last_n_transactions(book, n=num_transactions)
    book.close()

    return render_template('transactions.html',
                           transactions=transactions,
                           n=num_transactions)


@app.route('/balances')
def balances():
    global path_to_book
    book = open_book(path_to_book, readonly=True)
    accounts = []
    for acc in book.accounts:
        account = {}
        fn = acc.fullname
        bal = acc.get_balance()
        bal = f'${bal:>10.2f}'
        account['fullname'] = fn
        account['balance'] = bal
        accounts.append(account)
    accounts = sorted(accounts, key=lambda x: x['fullname'])
    book.close()

    return render_template('balances.html',
                           accounts=accounts)


@app.errorhandler(404)
def page_nout_found(e):
    return render_template('404.html')


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html')
