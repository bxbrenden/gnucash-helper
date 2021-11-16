# Feature: Manage Accounts

## Overview

As a user, I want to be able to add and delete accounts from the web UI instead of in GnuCash.

## Acceptance Criteria

One single tab in the navbar should be dedicated to this and called `Accounts` or `Manage Accounts`.
On the `Accounts` page, there should be two main sections:
1. A section to delete an existing account from a dropdown menu (and its submit button)
2. A section to create a new account (incl. submit button).
  - In this section, you choose its parent account from a dropdown menu.

## Required Changes / Additions
- [ ] A new Jinja2 template for the HTML page
- [ ] Two functions in `gnucash_helper.py`:
  - [x] Create account
  - [ ] Delete account
- [ ] Two new classes in `app.py`:
  - [ ] CreateAccountForm
  - [ ] DeleteAccountForm
- [ ] A new route in `app.py` called `/accounts`
