import piecash
from piecash import GnucashException
import sys


def open_book(book_name, readonly=False, open_if_lock=True, do_backup=False):
    """Open a GnuCash book for reading and potentially writing."""
    try:
        book = piecash.open_book(book_name, readonly=readonly, open_if_lock=open_if_lock, do_backup=do_backup)
    except GnucashException as gce:
        print(f'Error while attempting to open GnuCash book "{book_name}"')
        print(gce)
        sys.exit(1)
    else:
        return book


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


def delete_transaction(book, txn):
    """Given an already open GnuCash book, delete the summarized transaction `txn` from the book."""
    guid = txn.split(',')[-1].replace('GUID: ', '')
    transactions = book.transactions
    for t in transactions:
        if t.guid == guid:
            print(f'Attempting to delete transaction {t} from book.')
            book.delete(t)
            print('Flushing book to ensure deletion takes hold.')
            book.flush()
            print('Saving GnuCash book after deletion + flush.')
            book.save()
            return True

    # If no txn had a matching GUID, return False, since no deletion occurred.
    return False


def delete_account(book, acct_fullname):
    """Delete a GnuCash account with the fullname."""
    print('Searching for account to delete from list of accounts.')
    account_to_delete = book.accounts.get(fullname=acct_fullname)

    if account_to_delete:
        print('Located account to delete.')
        try:
            print(f'Attempting to delete account {acct_fullname}')
            book.delete(account_to_delete)
            book.flush()
            book.save()
        except GnucashException as gce:
            print(f'Account deletion for {acct_fullname} failed with error: {gce}')
            return False
        else:
            print(f'Successfully deleted account {acct_fullname}.')
            return True
    else:
        print(f'No account called {acct_fullname} was found.')
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

    if join_at_index == 1:
        print(f'Searching for highest non-placeholder account in the {account_name} hierarchy')
    hierarchy = account_name.split(':')
    test_account_name = ':'.join(hierarchy[:join_at_index])
    test_account = book.accounts.get(fullname=test_account_name)
    if test_account is not None:
        if test_account.placeholder == 0:
            return test_account
        elif test_account.placeholder == 1:
            return get_highest_ancestor_acct(book, account_name, join_at_index+1)
    else:
        print(f'No account by the name of {test_account} was found in book {book}.')


def delete_account_with_inheritance(book, acct_fullname):
    """Delete an account from a GnuCash book and let an ancestor account inherit its txns."""
    print(f'Deleting account {acct_fullname} with inheritance')
    acct_to_delete = get_account(acct_fullname, book)

    # Determine which account should inherit the transactions
    inheriting_acct = get_highest_ancestor_acct(book, acct_fullname)
    print(f'The upmost account that is not a placeholder is: {inheriting_acct.fullname}')

    # Get all splits for the account that will be deleted
    del_splits = acct_to_delete.splits

    # Find the transactions that the splits were part of
    txns = []
    for ds in del_splits:
        txns.append(ds.transaction)

    # "Replay" those transactions by modifying splits to have the inheriting
    #    account in place of the soon-to-be deleted account
    print(f'Identifying splits that match account {acct_fullname}')
    for t in txns:
        for spl in t.splits:
            if spl.account.fullname == acct_fullname:
                print(f'Split {spl} matches account fullname {spl.account.fullname}')
                spl.account = inheriting_acct
                book.flush()
                book.save()

    deleted = delete_account(book, acct_fullname)

    if deleted:
        return True
    else:
        return False


def main():
    """Delete the 2600 account. Let Assets:Checking inherit its transactions."""
    BOOK = 'delete-acct.gnucash'
    DEL_ACCOUNT = 'Assets:Checking:Budget:Subscriptions:2600'
    book = open_book(BOOK)

    print(f'Attempting to delete account {DEL_ACCOUNT}')
    delete_account_with_inheritance(book, DEL_ACCOUNT)
    book.close()


if __name__ == '__main__':
    main()
