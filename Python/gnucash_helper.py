from decimal import Decimal
import sys

import piecash
from piecash import Transaction, Split, GnucashException
from piecash.core.factories import create_currency_from_ISO


def open_book(book_name, readonly=False):
    try:
        book = piecash.open_book(book_name, readonly=readonly)
    except GnucashException as gce:
        print(f'Error while attempting to open GnuCash book "{book_name}"')
        print(gce)
        sys.exit(1)
    else:
        return book


def list_accounts(book):
    '''List accounts in an existing book'''
    accounts = book.accounts

    return accounts


def get_account(account_name, book):
    '''Return a piecash Account object that matches `account_name`,
       or return None if no match is found.'''
    accounts = book.accounts
    search_name = account_name.lower()
    for account in accounts:
        if account.fullname.lower() == search_name:
            return account

    return None


def add_account(book, new_acct_name, parent, currency='USD'):
    '''Add a GnuCash account with name `new_acct_name` and a parent account of `parent`.
    Optionally set USD'''

    parent_account = book.accounts.get(fullname=parent)
    if parent_account:
        child_accts = [child.name.lower() for child in parent_account.children]
        if new_acct_name.lower() in child_accts:
            print(f'The {new_acct_name} account already exists as a child of your {parent} account. Skipping')
            return
    else:
        print(f'There was no parent account named "{parent}"')
        return

    USD = book.commodities.get(mnemonic='USD')
    if parent_account and USD:
        new_account = piecash.Account(name=new_acct_name,
                                      type='EXPENSE',
                                      parent=parent_account,
                                      commodity=USD)
        try:
            book.save()
        except GnucashException as gce:
            print('Encounted GnuCash Error while saving book:')
            print('\t' + gce)
            sys.exit(1)
        else:
            print(f'Successfully saved book with new account "{new_acct_name}", child of parent account "{parent}"')

    else:
        print(f'There was no parent account named "{parent}" or no commodity named "USD"')
        sys.exit(1)


def add_transaction(book, description, amount, debit_acct, credit_acct):
    '''Add a transaction to an existing book.
       `amount` should be a float out to 2 decimal places for the value of the transaction.
       `debit_acct` and `credit_acct` should be the names of the accounts as given by the .fullname
           method from a GnuCash Account, e.g. book.accounts.get(fullname="Expenses:Food")'''
    try:
        credit = get_account(credit_acct, book)
        debit = get_account(debit_acct, book)
        if credit and debit:
            #usd = create_currency_from_ISO('USD')
            usd = book.currencies(mnemonic='USD')
            value = Decimal(amount)
            transaction = Transaction(currency=usd,
                                      description=description,
                                      splits=[
                                          Split(value=value, account=credit),
                                          Split(value=-value, account=debit)
                                      ])
            book.save()
            return True

        elif credit and not debit:
            print(f'The debit account {debit_acct} was not found. Skipping.')
            return False

        elif debit and not credit:
            print(f'The credit account {credit_acct} was not found. Skipping.')
            return False

    except GnucashException as gce:
        print('Failed to add the transaction')
        return False
