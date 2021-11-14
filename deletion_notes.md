# Transactions

## Summary
As a user, I want to be able to delete transactions from the web app.

## Acceptance Criteria
- User is able to find a specific txn from a list
- User can choose to delete it and submit a form
- The transaction is then removed from the books

## Required Changes / Additions
- [x] New page for deletions (easier than changing the existing page)
- [] One or more of these:
  - [x] a drop-down for selecting transactions
  - a search bar for finding transactions
  - a list of txns, basically identical to `/transactions` but with check boxes for deletion
- [x] A new / changed Jinja2 template
- [x] Function in `gnucash_helper.py` for transaction deletion
- [x] new route in `app.py` for deletions, possibly `/delete`
