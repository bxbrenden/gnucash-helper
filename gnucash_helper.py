"""Utility functions for GnuCash Helper."""
import logging
import os
from os import environ as env
import sys

from botocore.exceptions import ClientError
import boto3
from flask import flash
import piecash
from piecash import Transaction, Split, GnucashException


def get_env_var(name):
    """Get the environment variable `name` from environment variable.

    Return the value of the `name` env var if found, None otherwise.
    """
    try:
        env_var = env[name]
    except KeyError as ke:
        print(f'Could not get env. var. "{ke}". Make sure it is set')
        sys.exit(1)
    else:
        return env_var


def configure_logging():
    """Set up logging for the module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s  %(name)s  %(levelname)s:%(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    if gnucash_dir := get_env_var('GNUCASH_DIR'):
        fh = logging.FileHandler(f'{gnucash_dir}/gnucash-helper.log', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = configure_logging()


def get_book_name_from_env():
    """Get the GnuCash book name from an environment variable."""
    try:
        book_name = env['GNUCASH_FILE']
    except KeyError as ke:
        logger.critical(f'Could not get GnuCash book name from env. var. {ke}.')
        sys.exit(1)
    else:
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
            logger.error(f'The length of splits was not 2 for transaction #{ind}. Skipping.')
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
    method from a GnuCash Account, e.g. book.accounts.get(fullname="Expenses:Food").
    `enter_datetime` should be of type datetime.datetime.
    """
    try:
        credit = get_account(credit_acct, book)
        debit = get_account(debit_acct, book)
        if credit and debit:
            usd = book.currencies(mnemonic='USD')
            logger.info('Creating a new transaction in the GnuCash book.')
            transaction = Transaction(currency=usd,
                                      description=description,
                                      enter_date=enter_datetime,
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
    except KeyError as ke:
        logger.critical(f'Error, could not get GnuCash directory {ke} from env var')
        logger.critical('Make sure to set $GNUCASH_DIR')
        sys.exit(1)
    else:
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
            logger.info(f'Attempting to delete transaction {t} from book.')
            book.delete(t)
            logger.info('Flushing book to ensure deletion takes hold.')
            book.flush()
            logger.info('Saving GnuCash book after deletion + flush.')
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
            return get_highest_ancestor_acct(book, account_name, join_at_index+1)
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


def get_scaleway_s3_client():
    """Get a boto3 s3 client to use with Scaleway Object Storage."""
    SCALEWAY_ACCESS_KEY_ID = get_env_var('SCALEWAY_ACCESS_KEY_ID')
    SCALEWAY_SECRET_ACCESS_KEY = get_env_var('SCALEWAY_SECRET_ACCESS_KEY')

    # static Scaleway settings (using NL region only)
    S3_REGION_NAME = 'nl-ams'
    S3_ENDPOINT_URL = 'https://s3.nl-ams.scw.cloud'

    s3 = boto3.client('s3',
                      region_name=S3_REGION_NAME,
                      endpoint_url=S3_ENDPOINT_URL,
                      aws_access_key_id=SCALEWAY_ACCESS_KEY_ID,
                      aws_secret_access_key=SCALEWAY_SECRET_ACCESS_KEY
                      )
    return s3


def download_gnucash_file_from_scaleway_s3(object_key, dest_path, bucket_name, s3_client):
    """Download the .gnucash file from Scaleway S3 (Object Storage) to the destination path.

       The s3_client object should be created using the function called
       get_scaleway_s3_client().

       The dest_path should be set to the fully qualified path where S3 will temporarily
       store the GnuCash file.

       The bucket_name param is the name of your Scaleway Object Storage bucket.

       the object_key param  is the object key / name in Scaleway Object Storage.
    """
    global logger
    try:
        s3_client.download_file(Bucket=bucket_name,
                                Key=object_key,
                                Filename=dest_path
                                )
        logger.info(f'Successfully downloaded GnuCash file {object_key} from S3.')
        return True
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'NoSuchKey':
            msg = 'Attempted to pull down GnuCash file from S3, but no such file.'
        else:
            msg = 'Attempted to pull down GnuCash file from S3, but unexpected error occurred: '
            msg += ce.response['Error']['Code'] + ' ' + ce.response['Error']['Message']
        logger.critical(msg)
        return False
    else:
        return False


def upload_gnucash_file_to_scaleway_s3(src_path, bucket_name, obj_key, s3_client):
    """Upload a GnuCash file to Scaleway Object Storage."""
    global logger
    try:
        s3_client.upload_file(Filename=src_path, Bucket=bucket_name, Key=obj_key)
    except ClientError as ce:
        msg = 'Failed to upload GnuCash file to S3 with error: '
        msg += ce.response['Error']['Code'] + ' ' + ce.response['Error']['Message']
        logger.critical(msg)
        return False
    else:
        return True


def delete_local_gnucash_file(file_path):
    """Delete the local copy of a GnuCash file after uploading to Scaleway S3."""
    global logger
    try:
        logger.info(f'Removing GnuCash file at path "{file_path}".')
        os.remove(file_path)
        return True
    except OSError as ose:
        msg = f'Failed to delete GnuCash file at path "{file_path}" with error:\n'
        msg += ose
        logger.error(msg)
        return False


def upload_gnucash_file_to_s3_and_delete_local(path_to_book,
                                               book_name,
                                               bucket_name,
                                               s3_client):
    """Upload GnuCash file to Scaleway S3 and delete the local copy.

       Return a two-tuple of booleans where index 0 is True when upload succeeds
       and where index 1 is True when deletion of local GnuCash file succeeds.
       in the /entry endpoint. This is tight coupling, but the whole app is, so...
    """
    global logger
    logger.info(f'Uploading GnuCash file {path_to_book} to Scaleway S3 bucket {bucket_name}.')
    uploaded = upload_gnucash_file_to_scaleway_s3(path_to_book,
                                                  bucket_name,
                                                  book_name,
                                                  s3_client)
    if uploaded:
        logger.info('Successfully uploaded GnuCash file to Scaleway S3.')
        logger.info(f'Attempting to delete local GnuCash file {path_to_book}.')
        if deleted := delete_local_gnucash_file(path_to_book):
            logger.info(f'Successfully deleted local GnuCash file {path_to_book}.')
            flash('Successfully saved GnuCash file to the cloud and cleaned up local data.',
                  'success')
        else:
            logger.error(f'Failed to delete local GnuCash file {path_to_book}.')
            flash('Successfully saved GnuCash file to the cloud but failed to clean up local data.',
                  'warning')
    else:
        logger.error('Failed to upload GnuCash file to Scaleway S3.')
        logger.info(f'Attempting to delete local GnuCash file {path_to_book}.')
        if deleted := delete_local_gnucash_file(path_to_book):
            logger.info(f'Successfully deleted local GnuCash file {path_to_book}.')
            flash('Failed to save GnuCash file to the cloud but successfully cleaned up local data',
                  'danger')
        else:
            logger.error(f'Failed to delete local GnuCash file {path_to_book}.')
            flash('Failed to save GnuCash file to the cloud and failed to clean up local data.',
                  'danger')
