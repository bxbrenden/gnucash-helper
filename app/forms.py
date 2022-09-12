from app.gnucash_helper import list_accounts, get_book_name_from_env, \
    open_book, get_gnucash_dir, last_n_transactions, summarize_transaction, \
    get_easy_button_values, logger

from decimal import ROUND_HALF_UP
import os

from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, SubmitField, TextAreaField, \
    StringField

from wtforms.fields import DateField
from wtforms.validators import DataRequired


book_name = get_book_name_from_env()
gnucash_dir = get_gnucash_dir()
path_to_book = gnucash_dir + '/' + book_name


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
    descrip = TextAreaField('Description',
                            validators=[DataRequired()])
    emoji = TextAreaField('Emoji (limit: 1 character)',
                          validators=[DataRequired()])
    submit = SubmitField('Submit')

    @classmethod
    def new(cls):
        """Instantiate a new TransactionForm."""
        global path_to_book
        global logger
        logger.info('Attempting to read GnuCash book to create AddEasyButton form.')
        accounts = list_accounts(path_to_book)
        btn_form = cls()
        btn_form.debit.choices = accounts
        btn_form.credit.choices = accounts

        return btn_form


class DeleteEasyButton(FlaskForm):
    delete = SelectField('Select an Easy Button to Delete',
                         validators=[DataRequired()],
                         validate_choice=True)
    submit = SubmitField('Delete')

    @classmethod
    def new(cls):
        """Instantiate a new DeleteEasyButton form."""
        global path_to_book
        global logger
        logger.info('Attempting to read GnuCash book to create DeleteEasyButton form.')
        buttons = get_easy_button_values()

        # List of summarized txns to display in dropdown box
        summaries = []
        for b in buttons.keys():
            summaries.append(f'{b}  ({buttons[b]["emoji"]})')

        del_easy_form = cls()
        del_easy_form.delete.choices = summaries

        return del_easy_form
