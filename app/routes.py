from datetime import datetime
import os
import urllib.parse

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.urls import url_parse

from app import app, db
from app.forms import AddAccountForm, AddEasyButton, DeleteTransactionForm,\
    DeleteAccountForm, DeleteEasyButton, TransactionForm, RegistrationForm,\
    LoginForm
from app.gnucash_helper import get_book_name_from_env, logger, open_book,\
    add_transaction, get_gnucash_dir, last_n_transactions, get_env_var,\
    delete_transaction, delete_account_with_inheritance, add_account,\
    get_easy_button_values, write_easy_button_yml, validate_easy_button_schema
from app.models import User


book_name = get_book_name_from_env()
gnucash_dir = get_gnucash_dir()
path_to_book = gnucash_dir + '/' + book_name
book_exists = os.path.exists(path_to_book)


@app.route('/')
def index():
    global logger
    logger.info('Rendering the index page')

    return render_template('index.html')


@app.route('/entry', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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


@app.route('/transactions/<account_name>')
@login_required
def filtered_transactions(account_name):
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

    # account_name is URL-encoded, need to decode it
    account_name = urllib.parse.unquote(account_name)
    filtered = []
    for t in transactions:
        if t['source'] == account_name or t['dest'] == account_name:
            filtered.append(t)

    return render_template('filtered_transactions.html',
                           transactions=filtered,
                           account_name=account_name)


@app.route('/balances')
@login_required
def balances():
    global path_to_book
    global logger
    logger.info('Attempting to open book inside of balances route.')
    book = open_book(path_to_book, readonly=True)
    accounts = []
    for acc in book.accounts:
        account = {}
        bal = acc.get_balance()
        bal = f'${bal:,.2f}'
        account['fullname'] = acc.fullname
        account['balance'] = bal
        accounts.append(account)
    accounts = sorted(accounts, key=lambda x: x['fullname'])
    book.close()

    return render_template('balances.html',
                           accounts=accounts)


@app.route('/easy-buttons', methods=['GET', 'POST'])
@login_required
def easy_buttons():
    global logger
    logger.info('Creating new form inside of the /easy-buttons route')
    existing_easy_btns = get_easy_button_values()
    if existing_easy_btns:
        logger.info(f"Current easy buttons are: {existing_easy_btns}")
    add_form = AddEasyButton.new()
    del_form = DeleteEasyButton.new()
    if add_form.validate_on_submit():
        name = add_form.name.data
        debit = add_form.debit.data
        credit = add_form.credit.data
        descrip = add_form.descrip.data
        emoji = add_form.emoji.data

        easy_btn_dict = {name: {'source': debit,
                                'dest': credit,
                                'descrip': descrip,
                                'emoji': emoji}}

        is_valid_btn = validate_easy_button_schema(easy_btn_dict)
        # Initialize the "written" variable as False by default
        written = False
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
            flash(f'Easy button "{name}" was not saved successfully. Did you accidentally add multiple characters? Only one emoji is allowed.',
                  'danger')

        return redirect(url_for('easy_buttons'))
    elif del_form.validate_on_submit():
        # No changes are written at first
        written = False
        delete = del_form.delete.data
        del_key = delete.split('  (')[0]
        current_btns = get_easy_button_values()
        if del_key in current_btns.keys():
            # Delete from the Yaml file and write / save it
            del current_btns[del_key]
            written = write_easy_button_yml(current_btns)
        else:
            logger.error('Tried to find key {del_key} in yaml, but not found.')
            written = False
        if written:
            flash(f'Easy button "{del_key}" deleted successfully.',
                  'success')
        else:
            flash(f'Easy button "{del_key}" was not deleted successfully.',
                  'danger')
        return redirect(url_for('easy_buttons'))
    return render_template('easy-buttons.html', add_form=add_form, del_form=del_form)


@app.route("/login", methods=["GET", "POST"])
def login():
    global logger
    if current_user.is_authenticated:
        return redirect(url_for('entry'))
    form = LoginForm()
    if form.validate_on_submit():
        logger.info('Login info was well-formed for login attempt.')
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            err = f"Invalid username or password for username {form.username.data}"
            flash(err, 'danger')
            logger.error(err)
            return redirect(url_for("login"))
        else:
            success = f'Successful login for user {form.username.data}'
            logger.info(success)
            flash(success, 'success')
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('entry')
            return redirect(next_page)
    user_list = User.query.all()
    if len(user_list) > 0:
        hide_registration_link = True
    else:
        hide_registration_link = False
    return render_template("login.html", form=form, hide_registration_link=hide_registration_link)


@app.route("/logout")
def logout():
    logout_user()

    return redirect(url_for('index'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    users_list = User.query.all()
    if len(users_list) > 0:
        flash('Only one user account is allowed to register. Log in with existing credentials.',
              'danger')
        return redirect(url_for('login'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Registration was successful! Welcome aboard, {form.username.data}!',
              'success')
    return render_template('register.html', form=form)


@app.errorhandler(404)
def page_nout_found(e):
    return render_template('404.html')


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html')
