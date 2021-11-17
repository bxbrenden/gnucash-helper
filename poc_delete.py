from gnucash_helper import get_highest_ancestor_acct, delete_account, open_book

BOOK = 'delete-acct.gnucash'
DEL_ACCOUNT = 'Assets:Checking:Budget:Subscriptions:2600'
print(f'Attempting to delete account {DEL_ACCOUNT}')

book = open_book(BOOK)
accts = book.accounts

acct_to_delete = accts.get(fullname=DEL_ACCOUNT)

# Determine which account should inherit the transactions
inheriting_acct = get_highest_ancestor_acct(book, DEL_ACCOUNT)
print(f'The upmost account that is not a placeholder is: {inheriting_acct.fullname}')

# Get all splits for the account that will be deleted
del_splits = acct_to_delete.splits

# Find the transactions that the splits were part of
txns = []
for ds in del_splits:
    txns.append(ds.transaction)

# "Replay" those transactions by modifying splits to have the inheriting
#    account in place of the soon-to-be deleted account

for t in txns:
    for spl in t.splits:
        if spl.account.fullname == DEL_ACCOUNT:
            print(f'Split {spl} matches due to account fullname {spl.account.fullname}')
            spl.account = inheriting_acct
            book.flush()
            book.save()

deleted = delete_account(book, DEL_ACCOUNT)

if deleted:
    print(f'Successfully deleted account {DEL_ACCOUNT}')

book.close()
