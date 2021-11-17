# Delete Account Notes

## Steps to remove Imbalance Default
1. Specify which account you want to delete
2. Determine which account you want to inherit its transactions (not Imbalance!)
3. Find all splits for the account
4. For each split, find the transaction it's part of
5. Using the transaction from the split, get all splits
6. For each split in the transaction's splits, replace the deleted account with the inheriting account
7. Flush and save the book
8. Delete the account. Since it is empty, it won't have any transactions to inherit.

## Notes

Function signature for creating a piecash.Split:
```
Split(account, value, quantity=None, transaction=None, memo='',
      action='', reconcile_date=None, reconcile_state='n', lot=None)
```

**IMPORTANT!** splits are mutable, so you can just directly overwrite the account in the split to be the new name.
  That means there's no need to delete and recreate all the transactions; you can just change the existing ones.
  The only catch is that the new account can't be a placeholder.
