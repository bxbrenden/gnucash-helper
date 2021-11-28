from gnucash_helper import list_accounts,\
                           get_book_name_from_env,\
                           open_book,\
                           add_transaction,\
                           get_gnucash_dir,\
                           last_n_transactions,\
                           get_env_var,\
                           logger,\
                           summarize_transaction,\
                           delete_transaction,\
                           delete_account_with_inheritance,\
                           add_account,\
                           get_scaleway_s3_client,\
                           download_gnucash_file_from_scaleway_s3,\
                           upload_gnucash_file_to_s3_and_delete_local,\
                           delete_local_gnucash_file

from decimal import ROUND_HALF_UP
import os
from os import environ as env

from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import DecimalField,\
                    SelectField,\
                    SubmitField,\
                    TextAreaField,\
                    StringField

from wtforms.validators import DataRequired

book_name = get_book_name_from_env()
gnucash_dir = get_gnucash_dir()
path_to_book = gnucash_dir + '/' + book_name
s3_bucket_name = get_env_var('SCALEWAY_S3_BUCKET')
s3_client = get_scaleway_s3_client()
book_downloaded = download_gnucash_file_from_scaleway_s3(book_name, path_to_book, s3_bucket_name, s3_client)
book_exists = os.path.exists(path_to_book)
if not book_exists:
    logger.critical(f'The file "{path_to_book}" does not exist, so gnucash-helper cannot start.')
    raise SystemExit


class TransactionForm(FlaskForm):
    debit = SelectField('From Account (Debit)',
                        validators=[DataRequired()],
                        validate_choice=True)
    credit = SelectField('To Account (Credit)',
                         validators=[DataRequired()],
                         validate_choice=True)
    amount = DecimalField('Amount ($)',
                          validators=[DataRequired('Do not include a dollar sign or a comma.')],
                          places=2,
                          rounding=ROUND_HALF_UP,
                          render_kw={'placeholder': 'Ex: 4.20'})
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Submit')

    @classmethod
    def new(cls):
        """Instantiate a new TransactionForm."""
        global logger, path_to_book, book_name, s3_client, s3_bucket_name
        logger.info(f'Attempting to download GnuCash file {book_name} from Scaleway S3.')
        if downloaded := download_gnucash_file_from_scaleway_s3(book_name, path_to_book, s3_bucket_name, s3_client):
            logger.info('Successfully downloaded GnuCash file from S3 for /entry.')
        else:
            logger.critical('Failed to download GnuCash file from S3 for /entry.')
            raise SystemExit
        logger.info('Attempting to read GnuCash book to create TransactionForm.')
        accounts = list_accounts(path_to_book)
        txn_form = cls()
        txn_form.debit.choices = accounts
        txn_form.credit.choices = accounts

        return txn_form


class DeleteTransactionForm(FlaskForm):
    del_transactions = SelectField('Select a Transaction to Delete',
                                   validators=[DataRequired()],
                                   validate_choice=True)
    submit = SubmitField('Delete')

    @classmethod
    def new(cls):
        """Instantiate a new DeleteTransactionForm."""
        global logger, path_to_book, book_name, s3_client, s3_bucket_name
        logger.info('Attempting to download GnuCash file from Scaleway S3 for /delete.')
        if downloaded := download_gnucash_file_from_scaleway_s3(book_name, path_to_book, s3_bucket_name, s3_client):
            logger.info('Successfully downloaded GnuCash file for /delete.')
        else:
            logger.critical('Failed to download GnuCash file for /delete.')
            raise SystemExit
        logger.info('Attempting to read GnuCash book to create DeleteTransactionForm.')
        book = open_book(path_to_book)
        transactions = last_n_transactions(book, 0)

        # List of summarized txns to display in dropdown box
        summaries = []
        for t in transactions:
            summaries.append(summarize_transaction(t))

        txn_form = cls()
        txn_form.del_transactions.choices = summaries

        return txn_form


class DeleteAccountForm(FlaskForm):
    del_account = SelectField('Select an Account to Delete',
                              validators=[DataRequired()],
                              validate_choice=True)
    submit = SubmitField('Delete')

    @classmethod
    def new(cls):
        """Instantiate a new DeleteAccountForm."""
        global path_to_book
        global logger
        logger.info('Attempting to read GnuCash book to create DeleteAccountForm.')
        book = open_book(path_to_book)
        account_names = sorted([acc.fullname for acc in book.accounts])

        del_acc_form = cls()
        del_acc_form.del_account.choices = account_names

        return del_acc_form


class AddAccountForm(FlaskForm):
    new_account = StringField('Name of your new account:',
                              validators=[DataRequired()])
    parent_account_select = SelectField('Parent Account for your new account:',
                                        validators=[DataRequired()],
                                        validate_choice=True)
    submit = SubmitField('Add')

    @classmethod
    def new(cls):
        """Instantiate a new AddAccountForm."""
        global path_to_book
        global logger
        logger.info('Attempting to read GnuCash book to create AddAccountForm.')
        book = open_book(path_to_book)
        account_names = sorted([acc.fullname for acc in book.accounts])
        add_acc_form = cls()
        add_acc_form.parent_account_select.choices = account_names

        return add_acc_form


app = Flask(__name__)
app.config['SECRET_KEY'] = env.get('FLASK_SECRET_KEY',
                                   'Mjpe[){i>"r3}]Fm+-{7#,m}qFtf!w)T')
bootstrap = Bootstrap(app)


@app.route('/')
def index():
    global logger
    logger.info('Rendering the index page')

    return render_template('index.html')


@app.route('/entry', methods=['GET', 'POST'])
def entry():
    global logger, path_to_book, s3_bucket_name, s3_client, book_name
    logger.info('Creating new form inside of the /entry route')
    form = TransactionForm.new()
    if form.validate_on_submit():
        # Add the transaction to the GnuCash book
        logger.info('Attempting to open book in /entry route')
        gnucash_book = open_book(path_to_book)
        descrip = form.description.data
        amount = form.amount.data
        credit = form.credit.data
        debit = form.debit.data
        added_txn = add_transaction(gnucash_book, descrip, amount, debit, credit)
        gnucash_book.close()

        # Upload the GnuCash book to Scaleway S3 and delete local copy
        if added_txn:
            upload_gnucash_file_to_s3_and_delete_local(path_to_book,
                                                       book_name,
                                                       s3_bucket_name,
                                                       s3_client)
        else:
            flash('Failed to add transaction to GnuCash book', 'danger')
        return redirect(url_for('entry'))
    return render_template('entry.html', form=form)


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    global logger, path_to_book, book_name, s3_client, s3_bucket_name
    logger.info('Creating new form inside of the /delete route')
    form = DeleteTransactionForm.new()
    if form.validate_on_submit():
        # Delete the transaction from the GnuCash book
        logger.info('Attempting to open book in /delete route')
        gnucash_book = open_book(path_to_book)
        txn_to_delete = form.del_transactions.data
        txn_deleted = delete_transaction(gnucash_book, txn_to_delete)
        gnucash_book.close()

        if txn_deleted:
            upload_gnucash_file_to_s3_and_delete_local(path_to_book, book_name, s3_bucket_name, s3_client)
        else:
            message = 'Transaction was NOT deleted from GnuCash file:\n'
            message += txn_to_delete
            flash(message, 'danger')

        return redirect(url_for('entry'))
    return render_template('delete_txn.html', form=form)


@app.route('/accounts', methods=['GET', 'POST'])
def accounts():
    global logger
    logger.info('Creating new form inside of the /accounts route')
    delete_form = DeleteAccountForm.new()
    add_form = AddAccountForm.new()
    if delete_form.validate_on_submit():
        # Delete the account from the GnuCash book
        logger.info('Attempting to open book in /accounts route')
        gnucash_book = open_book(path_to_book)
        acc_to_delete = delete_form.del_account.data
        acc_deleted = delete_account_with_inheritance(gnucash_book, acc_to_delete)
        gnucash_book.close()

        if acc_deleted:
            message = 'Account deleted from GnuCash file:\n'
            message += acc_to_delete
            flash(message, 'success')
        else:
            message = 'Account was NOT deleted from GnuCash file:\n'
            message += acc_to_delete
            flash(message, 'danger')

        return redirect(url_for('accounts'))
    elif add_form.validate_on_submit():
        logger.info('Attempting to open book in /accounts route')
        gnucash_book = open_book(path_to_book)
        acc_to_add = add_form.new_account.data
        parent_account = add_form.parent_account_select.data
        acc_added = add_account(gnucash_book, acc_to_add, parent_account)
        gnucash_book.close()

        if acc_added:
            message = f'Account "{acc_to_add}" added to GnuCash file:\n'
            flash(message, 'success')
        else:
            message = f'Account "{acc_to_add}" was NOT added to GnuCash file:\n'
            flash(message, 'danger')

        return redirect(url_for('accounts'))
    return render_template('accounts.html', delete_form=delete_form, add_form=add_form)


@app.route('/transactions')
def transactions():
    global path_to_book
    global logger
    logger.info('Attempting to open book inside transactions route')
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
    global logger
    logger.info('Attempting to open book inside of balances route.')
    book = open_book(path_to_book, readonly=True)
    accounts = []
    for acc in book.accounts:
        account = {}
        fn = acc.fullname.replace(':', ' ➔ ')
        bal = acc.get_balance()
        bal = f'${bal:,.2f}'
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
