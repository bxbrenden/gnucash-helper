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
                           get_easy_button_values,\
                           write_easy_button_yml,\
                           validate_easy_button_schema

from datetime import datetime
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

from wtforms.fields import DateField

from wtforms.validators import DataRequired

book_name = get_book_name_from_env()
gnucash_dir = get_gnucash_dir()
path_to_book = gnucash_dir + '/' + book_name
book_exists = os.path.exists(path_to_book)
logger.info(f'At the global start, the book\'s existence is: {book_exists}')


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
    date = DateField('Date',
                     validators=[DataRequired()])
    submit = SubmitField('Submit')

    @classmethod
    def new(cls):
        """Instantiate a new TransactionForm."""
        global path_to_book
        global logger
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
        global path_to_book
        global logger
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


class AddEasyButton(FlaskForm):
    name = StringField('Name',
                       validators=[DataRequired()])
    debit = SelectField('From Account (Debit)',
                        validators=[DataRequired()],
                        validate_choice=True)
    credit = SelectField('To Account (Credit)',
                         validators=[DataRequired()],
                         validate_choice=True)
    descrip = TextAreaField('Description', validators=[DataRequired('The default description that appears every time you press the Easy Button')])
    emoji = SelectField('Emoji',
                        validators=[DataRequired()],
                        validate_choice=True)
    submit = SubmitField('Submit')

    @classmethod
    def new(cls):
        """Instantiate a new TransactionForm."""
        global path_to_book
        global logger
        logger.info('Attempting to read GnuCash book to create TransactionForm.')
        accounts = list_accounts(path_to_book)
        btn_form = cls()
        btn_form.debit.choices = accounts
        btn_form.credit.choices = accounts
        btn_form.emoji.choices = ['🎅', '🏇', '👌']

        return btn_form


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
    global logger
    logger.info('Creating new form inside of the /entry route')
    easy_btns = get_easy_button_values()
    print(f"easy buttons are: {easy_btns}")
    form = TransactionForm.new()
    if form.validate_on_submit():
        # Add the transaction to the GnuCash book
        logger.info('Attempting to open book in /entry route')
        gnucash_book = open_book(path_to_book)
        descrip = form.description.data
        amount = form.amount.data
        credit = form.credit.data
        debit = form.debit.data
        date = form.date.data
        time = datetime.utcnow().time()
        enter_datetime = datetime.combine(date, time)

        added_txn = add_transaction(gnucash_book, descrip, amount, debit, credit, enter_datetime)
        gnucash_book.close()

        if added_txn:
            flash(f'Transaction for {float(amount):.2f} saved to GnuCash file.',
                  'success')
        else:
            flash(f'Transaction for {float(amount):.2f} was not saved to GnuCash file.',
                  'danger')

        return redirect(url_for('entry'))
    return render_template('entry.html', form=form, easy_btns=easy_btns)


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    global logger
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
            message = 'Transaction deleted from GnuCash file:\n'
            message += txn_to_delete
            flash(message, 'success')
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


@app.route('/easy-buttons', methods=['GET', 'POST'])
def easy_buttons():
    global logger
    logger.info('Creating new form inside of the /easy-buttons route')
    existing_easy_btns = get_easy_button_values()
    if existing_easy_btns:
        logger.info(f"Current easy buttons are: {existing_easy_btns}")
    form = AddEasyButton.new()
    if form.validate_on_submit():
        name = form.name.data
        debit = form.debit.data
        credit = form.credit.data
        descrip = form.descrip.data
        emoji = form.emoji.data

        easy_btn_dict = {name: {'source': debit,
                                'dest': credit,
                                'descrip': descrip,
                                'emoji': emoji}}

        is_valid_btn = validate_easy_button_schema(easy_btn_dict)
        if is_valid_btn:
            # If there aren't any existing easy buttons, write a new file
            if not existing_easy_btns:
                written = write_easy_button_yml(easy_btn_dict)
            # Otherwise, extend the existing button list and write all that to a file
            else:
                new_easy_btns = existing_easy_btns | easy_btn_dict
                written = write_easy_button_yml(new_easy_btns)

        if written:
            flash(f'Easy button "{name}" added successfully.',
                  'success')
        else:
            flash(f'Easy button "{name}" was not saved successfully',
                  'danger')

        return redirect(url_for('easy_buttons'))
    return render_template('easy-buttons.html', form=form)


@app.errorhandler(404)
def page_nout_found(e):
    return render_template('404.html')


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html')
