# GnuCash-Helper

GnuCash-Helper is a small Flask app for entering GnuCash transactions from a web browser.
It synchronizes the changes to a GnuCash file tracked in your GitHub account.

## Requirements
### Hosting
It is recommended you run this program as a Docker container on a GNU/Linux-based distro behind an nginx reverse proxy.
Therefore, you should install `nginx` and `docker`.
Installation instructions for `nginx` and `docker` are beyond the scope of this readme.

### GnuCash File Format
GnuCash has several file formats available, including `sqlite3`, `postgresql`, and `xml`.
This project can only work with GnuCash files saved in  `sqlite3` format.
See the [official GnuCash page on formatting](https://www.gnucash.org/docs/v4/C/gnucash-guide/basics-files1.html) for instructions on saving your GnuCash file as `sqlite3`.


## Configuration
All configuration is done in the Dockerfile.

Start by copying the [Dockerfile.example](https://github.com/bxbrenden/GnuCash-Helper/blob/main/Dockerfile.example) file to a new file called `Dockerfile`:
```bash
cp Dockerfile.example Dockerfile
``` 

Next, change the following variables:
- `ENV GIT_USER` : Change "Dude Dudeman" to your name as you'd like it to appear in your git commits.
- `ENV GIT_EMAIL` : Set your email address to the email you'd like to appear in your git commits.
- `ENV GITHUB_TOKEN`: Set the value to a [GitHub Personal Access Token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token). This personal access token only needs `repo` access.
- `ENV GITHUB_GNUCASH_URL`: Set this to the HTTPS URL of the GitHub repository containing your GnuCash file.
- `ENV CLONE_URL`: you construct this string as follows: `https://` + `<your GitHub Personal Access Token>` + `@github.com/<your GitHub account>/<your GnuCash git repo>` + `.git`. For example, if your Personal Access Token is `12345`, your user account is `bxbrenden`, and your git repo is called `my-gnucash`, your `CLONE_URL` would be: `https://12345@github.com/bxbrenden/my-gnucash.git`
