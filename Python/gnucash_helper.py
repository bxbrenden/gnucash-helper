from decimal import Decimal
import os
from os import environ as env
import shlex
import subprocess
import sys

import piecash
from piecash import Transaction, Split, GnucashException
from piecash.core.factories import create_currency_from_ISO

def get_book_name_from_env():
    try:
        book_name = env['GNUCASH_BOOK_NAME']
    except KeyError as ke:
        print(f'Error: could not get GnuCash book name from env. var. {ke}.')
        sys.exit(1)
    else:
        return book_name


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
            transaction = Transaction(currency=usd,
                                      description=description,
                                      splits=[
                                          Split(value=amount, account=credit),
                                          Split(value=-amount, account=debit)
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

    except ValueError as ve:
        print('Failed to add the transaction with ValueError:')
        print(ve)
        return False


def get_gnucash_dir():
    '''Get the fully qualified path of the directory of your .gnucash file'''
    try:
        gnucash_dir = env['GNUCASH_DIR']
    except KeyError as ke:
        print('Error, could not get GnuCash dir. from env var')
        print('    Make sure to set $GNUCASH_DIR')
        sys.exit(1)
    else:
        return gnucash_dir


def get_git_user_name_and_email_from_env():
    try:
        git_user = env['GIT_USER']
        git_email = env['GIT_EMAIL']
    except KeyError as ke:
        print('Error: failed to source {ke} from env var. Make sure to set it')
        sys.exit(1)
    else:
        return (git_user, git_email)


def get_github_token_and_url_from_env():
    try:
        gh_token = env['GITHUB_TOKEN']
        gh_url = env['GITHUB_GNUCASH_URL']
    except KeyError as ke:
        print(f'Error: failed to source env var {ke}. Ensure it is set')
        sys.exit(1)
    else:
        return (gh_token, gh_url)


def run_shell_command(command_str):
    '''Run a shell comand using subprocess.run. Return completed command obj'''
    command = shlex.split(command_str)
    run = subprocess.run(command, capture_output=True)

    return run


def git_set_user_and_email(username, email):
    '''Set the user's name, e.g. "Brenden Hyde" and email address.
       This is used by git when writing commit messages for attribution.'''
    user_cmd = f'git config --global user.name {username}'
    email_cmd = f'git config --global user.email {email}'

    user_run = run_shell_command(user_cmd)
    email_run = run_shell_command(email_cmd)
    if user_run.returncode == 0 and email_run.returncode == 0:
        print('Successfully configured git user\'s name and email')
        return True
    elif user_run.returncode == 0 and email_run.returncode != 0:
        print('Error: git global config set for user\'s name but not email')
        return False
    elif user_run.returncode != 0 and email_run.returncode == 0:
        print('Error: git global config set for user\'s email but not name')
        return False
    else:
        print('Git global config of user\'s name and email is messed up!')
        return False


def git_ensure_cloned(gnucash_dir, gh_token, gh_url):
    '''Ensure the gnucash git repo is already present, and clone it if not.
       The `gh_url` var should be an HTTPS URL to your GnuCash GitHub repo.
       The `gh_token` var is a Personal Access Token from GitHub.'''
    repo_exists = os.path.exists(gnucash_dir)
    if repo_exists:
        return True
    else:
        clone_url = gh_url.replace('https://', f'https://{gh_token}@')
        print('Cloning GnuCash GitHub repo from URL:')
        print('    {clone_url}')
        cmd = f'git clone {clone_url}'
        run = run_shell_command(cmd)

        if run.returncode == 0:
            print('Successfully cloned the GnuCash GitHub repo.')
            return True
        else:
            print('Error: failed to clone the GnuCash GitHub repo:')
            print(run)
            return False


def git_pull(gnucash_dir):
    '''Run a `git pull` command in the directory with the GnuCash book.'''
    cmd = f'git -C {gnucash_dir} pull'
    run = run_shell_command(cmd)

    if run.returncode == 0:
        print('successfully ran `git pull`')
        return True
    else:
        print('Error: failed to run a `git pull` command.\
                See below for command output')
        print(run)
        return False


def git_add(gnucash_dir, gnucash_book):
    '''Run `git add {gnucash_book}` in the context of the GnuCash book directory.
       `gnucash_dir` should be a fully qualified path to your GnuCash dir'''
    cmd = f'git -C "{gnucash_dir}" add "{gnucash_book}"'
    run = run_shell_command(cmd)

    if run.returncode == 0:
        print(f'Successfully ran `git add {gnucash_book}` in GnuCash directory')
        return True
    else:
        print('Error: failed to run a `git add` command.\
                  See below for command output')
        print(run)
        return False


def git_commit(gnucash_dir, message):
    '''Run `git commit -m "{message}"` in the context of the GnuCash dir'''
    cmd = f'git -C {gnucash_dir} commit -m "{message}"'
    run = run_shell_command(cmd)

    if run.returncode == 0:
        print(f'Successfully ran the following git commit command:')
        print(f'    {cmd}')
        return True
    else:
        print('Error: failed to run a `git commit` command.\
                  See below for command output')
        print(run)
        return False


def git_push(gnucash_dir):
    '''Run a `git push` command in the context of the GnuCash directory'''
    cmd = f'git -C {gnucash_dir} push'
    run = run_shell_command(cmd)

    if run.returncode == 0:
        print('Successfully ran `git push`')
        return True
    else:
        print('Error: failed to run `git push`.\
                See below for command output')
        print(run)
        return False


def git_add_commit_and_push(gnucash_dir, gnucash_book, commit_message):
    '''Run `git add .`, `git commit -m "message"`, and `git push`,
       all in the context of the directory that contains your GnuCash file.'''
    added = git_add(gnucash_dir, gnucash_book)
    if added:
        committed = git_commit(gnucash_dir, commit_message)
        if committed:
            pushed = git_push(gnucash_dir)
            if pushed:
                return (True, None)
            else:
                failure = 'Git add and commit succeeded, but pushing failed'
                print(failure)
                return (False, failure)
        else:
            failure = 'Git add succeeded, but commit failed. Did not try a push'
            print(failure)
            return (False, failure)
    else:
        failure = 'Git add failed'
        print(failure)
        return (False, failure)
