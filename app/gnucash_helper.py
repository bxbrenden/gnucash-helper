"""Utility functions for GnuCash Helper."""
import logging
from os import environ as env
import yaml
import sys

import piecash
from piecash import Transaction, Split, GnucashException
from voluptuous import Schema, Required, All, Length, MultipleInvalid


def configure_logging():
    """Set up logging for the module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s:%(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    try:
        log_dir = env['GCH_LOG_DIR']
        fh = logging.FileHandler(f'{log_dir}/gnucash-helper.log', encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except KeyError:
        # fh = logging.FileHandler('/app/gnucash-helper.log', encoding='utf-8')
        pass
    logger.addHandler(ch)

    return logger


logger = configure_logging()


def get_env_var(name):
    """Get the environment variable `name` from environment variable.

    Return the value of the `name` env var if found, None otherwise.
    """
    try:
        env_var = env[name]
    except KeyError as ke:
        logger.critical(f'Could not get env. var. "{ke}". Make sure it is set')
    else:
        return env_var


def validate_easy_button_schema(btns):
    """Given a dictionary of easy buttons, validate the schema and return True if valid else False."""
    global logger
    schema = Schema({Required(All(str, Length(min=1))): {Required('source'): All(str, Length(min=1)),
                     Required('dest'): All(str, Length(min=1)),
                     Required('descrip'): All(str, Length(min=1)),
                     Required('emoji'): All(str, Length(min=1))}})

    # Validate each button definition individually from easy-buttons.yml
    for k, v in btns.items():
        try:
            schema({k: v})
        except MultipleInvalid as invalid:
            logger.error(f'Easy Button schema validation failed: The button dict "{k}:{v}" failed with error: {invalid}')
            return False

    return True


def get_easy_button_values():
    """Get all the config info for easy buttons."""
    global logger
    easy_config_dir = env.get('EASY_CONFIG_DIR', '/app')
    try:
        with open(f'{easy_config_dir}/easy-buttons.yml', 'r') as easy:
            btns = yaml.safe_load(easy)

            if validate_easy_button_schema(btns):
                return btns
            else:
                logger.error("Schema validation failed for easy-buttons.yml")

    except FileNotFoundError:
        err = 'Failed to find easy button config. file. '
        err += f'Expected to find it at {easy_config_dir}/easy-buttons.yml.\n'
        err += 'This session will not use easy buttons.'
        logger.error(err)
    except PermissionError:
        err = f'Tried to open easy button config at {easy_config_dir}/'
        err += 'easy-buttons.yml, but permission denied.\n'
        err += 'This session will not use easy buttons.'
        logger.error(err)
    except yaml.YAMLError as exc:
        err = 'Failed to parse easy button config yaml file.\n'
        err += 'This session will not use easy buttons.\n'
        err += f'The error was:\n{exc}'
        logger.error(err)


def get_book_name_from_env():
    """Get the GnuCash book name from an environment variable."""
    try:
        book_name = env['GNUCASH_FILE']
    except KeyError:
        logger.error('Failed to get GNUCASH_FILE env. var. Defaulting to "budget.gnucash".')
        book_name = 'budget.gnucash'

    return book_name


def open_book(book_name, readonly=False, open_if_lock=True, do_backup=False):
    """Open a GnuCash book for reading and potentially writing."""
    try:
        book = piecash.open_book(book_name, readonly=readonly, open_if_lock=open_if_lock, do_backup=do_backup)
    except GnucashException as gce:
        logger.critical(f'Error while attempting to open GnuCash book "{book_name}"')
        logger.critical(gce)
        sys.exit(1)
    else:
        return book


def list_accounts(book):
    """List accounts in an existing book.

    `book` should be the fully qualified path to the GnuCash book.
    """
    book = open_book(book, readonly=True)
    accounts = sorted([x.fullname for x in book.accounts])
    book.close()

    return accounts


def get_account(account_name, book):
    """Return a piecash Account object that matches `account_name`.

    Return None if no match is found.
    """
    accounts = book.accounts
    search_name = account_name.lower()
    for account in accounts:
        if account.fullname.lower() == search_name:
            return account

    return None


def delete_account(book, acct_fullname):
    """Delete a GnuCash account with the fullname."""
    global logger
    logger.debug('Searching for account to delete from list of accounts.')
    account_to_delete = book.accounts.get(fullname=acct_fullname)

    if account_to_delete:
        logger.debug('Located account to delete.')
        try:
            logger.info(f'Attempting to delete account {acct_fullname}')
            book.delete(account_to_delete)
            book.flush()
            book.save()
        except GnucashException as gce:
            logger.error(f'Account deletion for {acct_fullname} failed with error: {gce}')
            return False
        else:
            logger.info(f'Successfully deleted account {acct_fullname}.')
            return True
    else:
        logger.error(f'No account called {acct_fullname} was found.')
        return False


def add_account(book, new_acct_name, parent, currency='USD'):
    """Add a GnuCash account with name `new_acct_name` and a parent account of `parent`.

    Optionally set USD
    """
    parent_account = book.accounts.get(fullname=parent)
    if parent_account:
        # Ensure no account already exists with the requested name
        child_accts = [child.name.lower() for child in parent_account.children]
        if new_acct_name.lower() in child_accts:
            logger.warning(f'The {new_acct_name} account already exists as a child of your {parent} account. Skipping')
            return False
        # Grab the account type of the parent account
        # To keep things simple, the child inherits the parent's account type
        parent_account_type = parent_account.type
    else:
        logger.error(f'There was no parent account named "{parent}"')
        return False

    commodity = book.commodities.get(mnemonic=currency)
    if parent_account and commodity and parent_account_type:
        new_account = piecash.Account(name=new_acct_name,
                                      type=parent_account_type,
                                      parent=parent_account,
                                      commodity=commodity)
        try:
            book.save()
        except GnucashException as gce:
            logger.critical('Encounted GnuCash Error while saving book:')
            logger.critical(gce)
            sys.exit(1)
        else:
            logger.info(f'Successfully saved book with new account "{new_acct_name}", child of parent account "{parent}"')
            return True

    else:
        logger.error(f'There was no parent account named "{parent}", no parent account type, or no commodity named "{currency}"')
        return False


def last_n_transactions(book, n=50):
    """Return the last `n` transactions from the GnuCash book `book`.

    The transactions are returned as a dict where the items are:
    - source: source account name
    - dest: destination account name
    - date: the enter date of the transaction (e.g. 2021-01-01)
    - amount: the amount of money
    - guid: the globally unique ID of the transaction
    - description: the transaction description
    """
    last_n = []
    # Return all transactions if n == 0
    if n != 0:
        transactions = [x for x in reversed(book.transactions[-n:])]
    elif n == 0:
        transactions = [x for x in reversed(book.transactions)]
    # Sort transactions by date
    transactions.sort(key=lambda x: x.enter_date, reverse=True)
    logger.debug(f'`n` was set to {n} for getting last transactions')
    logger.debug(f'There are {len(transactions)} transactions in the list')

    for ind, trans in enumerate(transactions):
        t = {}
        date = str(trans.enter_date.date())
        splits = trans.splits
        logger.debug(f'Txn #{ind}: the length of `splits` is: {len(splits)}')
        logger.debug('The splits are:')
        for split in splits:
            logger.debug(split)
        if len(splits) != 2:
            logger.debug(f'The length of splits was not 2 for transaction #{ind}. Skipping.')
            continue

        # figure out which split contains the debit acct in the transaction
        if splits[0].is_debit:
            source_acct = splits[1]
            dest_acct = splits[0]
        else:
            source_acct = splits[0]
            dest_acct = splits[1]

        descrip = trans.description
        amount = dest_acct.value
        # Get the GUID for the txn
        try:
            guid = trans.guid
        except AttributeError:
            logger.error(f'Failed to get transaction GUID for txn with description {descrip}.')
            raise SystemExit

        # make the amount positive for display's sake
        if amount.is_signed():
            amount = -amount
        amount = float(amount)

        t['date'] = date
        t['source'] = source_acct.account.fullname
        t['dest'] = dest_acct.account.fullname
        t['description'] = descrip
        t['amount'] = f'${amount:.2f}'
        t['guid'] = guid
        last_n.append(t)

    return last_n


def add_transaction(book, description, amount, debit_acct, credit_acct, enter_datetime):
    """Add a transaction to an existing book.

    `amount` should be a float out to 2 decimal places for the value of the transaction.
    `debit_acct` and `credit_acct` should be the names of the accounts as given by the .fullname
    `enter_datetime` should be of type datetime.datetime.
    method from a GnuCash Account, e.g. book.accounts.get(fullname="Expenses:Food").
    """
    try:
        credit = get_account(credit_acct, book)
        debit = get_account(debit_acct, book)
        if credit and debit:
            usd = book.currencies(mnemonic='USD')
            logger.info('Creating a new transaction in the GnuCash book.')
            transaction = Transaction(currency=usd,
                                      enter_date=enter_datetime,
                                      description=description,
                                      splits=[
                                          Split(value=amount, account=credit),
                                          Split(value=-amount, account=debit)
                                      ])
            logger.debug('Transaction successfully created.')
            logger.debug('Attempting to save transaction')
            book.save()
            logger.info('Successfully saved transaction')
            return True

        elif credit and not debit:
            logger.error(f'The debit account {debit_acct} was not found. Skipping.')
            return False

        elif debit and not credit:
            logger.error(f'The credit account {credit_acct} was not found. Skipping.')
            return False

    except GnucashException as gce:
        logger.error('Failed to add the transaction')
        logger.error(gce)
        return False

    except ValueError as ve:
        logger.error('Failed to add the transaction with ValueError:')
        logger.error(ve)
        return False


def get_gnucash_dir():
    """Get the fully qualified path of the directory of your .gnucash file."""
    try:
        gnucash_dir = env['GNUCASH_DIR']
    except KeyError:
        msg = 'Could not get GnuCash directory from GNUCASH_DIR env var.\n'
        msg += 'Defaulting gnucash_dir to "/app"'
        gnucash_dir = '/app'

    return gnucash_dir


def summarize_transaction(txn):
    """Given a transaction `txn`, return a shortened summary string for web forms."""
    global logger

    for key in ['description', 'source', 'dest', 'date', 'amount', 'guid']:
        if key not in txn.keys():
            logger.critical(f'Malformed transaction found while summarizing transaction {txn}')
            raise SystemExit

    # Create summary components
    desc_summ = txn['description'][:20]
    amount = txn['amount']
    date = txn['date']
    src_summ = txn['source'].split(':')[-1]
    dest_summ = txn['dest'].split(':')[-1]
    guid = txn['guid']

    summary = f'Txn: {desc_summ},Amount: {amount},Date: {date},Source: {src_summ},Dest: {dest_summ},GUID: {guid}'

    return summary


def delete_transaction(book, txn):
    """Given an already open GnuCash book, delete the summarized transaction `txn` from the book."""
    global logger

    guid = txn.split(',')[-1].replace('GUID: ', '')
    transactions = book.transactions
    for t in transactions:
        if t.guid == guid:
            logger.debug(f'Attempting to delete transaction {t} from book.')
            book.delete(t)
            logger.debug('Flushing book to ensure deletion takes hold.')
            book.flush()
            logger.debug('Saving GnuCash book after deletion + flush.')
            book.save()
            return True

    # If no txn had a matching GUID, return False, since no deletion occurred.
    return False


def get_highest_ancestor_acct(book, account_name, join_at_index=1):
    """Given a book and an account name, return the name of the upmost ancestor
       account that is not a placeholder account.

       For example, if I have an account which I want to delete called
       'Assets:Budget:Subscriptions:2600 Magazine', we want to find the
       highest-level (closest to the root of the account tree) account in
       the hierarchy.

       If `Assets` is not a placeholder, it is returned by this function.
       If `Assets` is a placeholder, `Budget` is checked for placeholder status.
       Whichever is the highest one that is not a placeholder is returned.

       Because this will be used recursively, the `join_at_index` value is used
       to tell the recursion where to stop. In our example above, the first time
       `get_highest_ancestor_acct` is called, it will start colon-joining things at
       at index 1 which returns the value `Assets`. If the `Assets` account is not a
       placeholder, it is returned.

       However, if it's not, we _recursively_ call `get_highest_ancestor_acct` with
       a `join_at_index` of 2. This tells the function that it can't re-check `Assets`,
       opting instead to see if `Assets:Budget` is a placeholder.
       """

    global logger
    logger.debug(f'Searching for highest non-placeholder account in the {account_name} hierarchy')
    hierarchy = account_name.split(':')
    test_account_name = ':'.join(hierarchy[:join_at_index])
    test_account = book.accounts.get(fullname=test_account_name)
    if test_account is not None:
        if test_account.placeholder == 0:
            return test_account
        elif test_account.placeholder == 1:
            return get_highest_ancestor_acct(book, account_name, join_at_index + 1)
    else:
        logger.error(f'No account by the name of {test_account} was found in book {book}.')


def delete_account_with_inheritance(book, acct_fullname):
    """Delete an account from a GnuCash book and let an ancestor account inherit its txns."""
    global logger
    logger.debug(f'Deleting account {acct_fullname} with inheritance')
    acct_to_delete = get_account(acct_fullname, book)

    # Determine which account should inherit the transactions
    inheriting_acct = get_highest_ancestor_acct(book, acct_fullname)
    logger.debug(f'The upmost account that is not a placeholder is: {inheriting_acct.fullname}')

    # Get all splits for the account that will be deleted
    del_splits = acct_to_delete.splits

    # Find the transactions that the splits were part of
    txns = []
    for ds in del_splits:
        txns.append(ds.transaction)

    # "Replay" those transactions by modifying splits to have the inheriting
    #    account in place of the soon-to-be deleted account
    logger.debug(f'Identifying splits that match account {acct_fullname}')
    for t in txns:
        for spl in t.splits:
            if spl.account.fullname == acct_fullname:
                logger.debug(f'Split {spl} matches due to account fullname {spl.account.fullname}')
                spl.account = inheriting_acct
                book.flush()
                book.save()

    deleted = delete_account(book, acct_fullname)

    if deleted:
        logger.info(f'Successfully deleted account {acct_fullname}.')
        return True
    else:
        logger.error(f'Failed to delete account {acct_fullname}.')
        return False


def write_easy_button_yml(btn_info):
    """Write the Easy Button info out to $EASY_CONFIG_DIR/easy-buttons.yml."""
    global logger
    write_dir = ""
    easy_conf_dir = env.get('EASY_CONFIG_DIR', None)
    gnucash_dir = env.get('GNUCASH_DIR', None)

    # Prefer the easy_conf_dir for writing the output yaml
    if easy_conf_dir:
        write_dir = easy_conf_dir
    elif gnucash_dir and not easy_conf_dir:
        write_dir = gnucash_dir
    else:
        write_dir = '/app'

    try:
        with open(write_dir + '/' + 'easy-buttons.yml', 'w') as yf:
            yf.write(yaml.dump(btn_info))
            return True
    except PermissionError:
        logger.error(f'Failed to write easy-buttons.yml to {easy_conf_dir}: permission denied.')
        return False
