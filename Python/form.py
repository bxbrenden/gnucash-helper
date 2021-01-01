from gnucash_helper import list_accounts,\
                           get_book_name_from_env,\
                           open_book,\
                           get_account,\
                           add_transaction

from decimal import Decimal, ROUND_HALF_UP
from os import environ as env

from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import DecimalField,\
                    SelectField,\
                    StringField,\
                    SubmitField,\
                    TextAreaField

from wtforms.validators import DataRequired


class TransactionForm(FlaskForm):
    book_name = get_book_name_from_env()
    gnucash_book = open_book(book_name, readonly=True)
    accounts = [acc.fullname for acc in list_accounts(gnucash_book)]
    gnucash_book.close()
    debit = SelectField('Source Account (Debit)',
                        validators=[DataRequired()],
                        choices=accounts,
                        validate_choice=True)
    credit = SelectField('Destination Account (Credit)',
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
app.config['SECRET_KEY'] = env.get('FLASK_SECRET_KEY', 'SuperSecretKey123$')
bootstrap = Bootstrap(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = TransactionForm()
    if form.validate_on_submit():
        book_name = get_book_name_from_env()
        gnucash_book = open_book(book_name)
        descrip = form.description.data
        amount = form.amount.data
        credit = form.credit.data
        debit = form.debit.data
        added_txn = add_transaction(gnucash_book, descrip, amount, debit, credit)
        gnucash_book.close()
        if added_txn:
            flash(f'Transaction for ${float(form.amount.data):.2f} saved!')
        else:
            flash(f'Transaction failed!', 'error')
        return redirect(url_for('index'))
    return render_template('index.html', form=form)


@app.errorhandler(404)
def page_nout_found(e):
    return render_template('404.html')
