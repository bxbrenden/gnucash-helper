# GnuCash-Helper
![GnuCash-Helper Logo](https://github.com/bxbrenden/gnucash-helper/blob/main/app/static/gnucash-helper-bubble-logo_08-300x300.png)

GnuCash-Helper is a personal finance app based on GnuCash.
It can be used as a standalone app and does not require GnuCash to work.

It uses `.gnucash` files behind the scenes, so you can easily export your data and import it to the GnuCash desktop app.


## Running
The easiest way to run GnuCash-Helper is via Docker.

If you're familiar with Ansible, see the `Ansible` section below to automate the deployment of GnuCash-Helper with Docker.

You can fetch the latest Docker image from Docker Hub with this command:
```
docker image pull bxbrenden/gnucash-helper:latest
```

Below is an example `docker run` command for running the container.
It assumes that your docker host has a file called `demo-budget.gnucash` in a directory called `/gnucash`.
This file is mounted into the container.
```bash
docker run -d --restart unless-stopped -p 8000:8000 -v /gnucash:/gnucash -e GNUCASH_FILE=demo-budget.gnucash -e GNUCASH_DIR=/gnucash -e NUM_TRANSACTIONS=10000 -e EASY_CONFIG_DIR=/gnucash bxbrenden/gnucash-helper:latest
```

If you're curious about the environment variables that GnuCash-Helper requires, see the `Configuration` section.


## Configuration
GnuCash-Helper needs a few environment variables set in order to run:
- `$GNUCASH_FILE`: This is the file name of your GnuCash file as it exists on your server / docker host.
- `$GNUCASH_DIR`: . This is the fully qualified path to the directory where your GnuCash file lives.
- `$NUM_TRANSACTIONS`: The number of most recent transactions to display on the `Transactions` page.
- `$EASY_CONFIG_DIR`: The directory where your Easy Button configuration file is saved. You should probably set this to the same value as `$GNUCASH_DIR`
- `$GCH_LOG_DIR=`: the directory where GnuCash-Helper will write its log file.


## GnuCash File Format
GnuCash-Helper uses GnuCash files as its backend for storing transaction / account info.
GnuCash has several file formats available, including `sqlite3`, `postgresql`, and `xml`.
This project can only work with GnuCash files saved in `sqlite3` format.

If you deploy the app via Ansible, there is already a `.gnucash` file included, so you don't need to make your own.

See the [official GnuCash page on formatting](https://www.gnucash.org/docs/v4/C/gnucash-guide/basics-files1.html) for instructions on saving your GnuCash file as `sqlite3`.


## Building the Docker Container
You can build the container from the root directory of this project with the following command:
```bash
docker build -t bxbrenden/gnucash-helper:latest .
```
Afterwards, the `bxbrenden/gnucash-helper:latest` docker container will appear in your `sudo docker images` output.


## Running the Docker Container Locally for Testing / Development
There is an example script called `run.sh` in the root directory of this repo which you can use an example for running the app locally for development.

This requires you to have Python and pyenv installed.


## License
This software is licensed under the `GNU Affero General Public License, Version 3`. Please see [LICENSE.md](https://github.com/bxbrenden/gnucash-helper/blob/main/LICENSE.md) or [The official site for this license](https://www.gnu.org/licenses/agpl-3.0.en.html) for more details.
