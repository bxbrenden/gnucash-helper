# GnuCash-Helper

GnuCash-Helper is a small Flask app for entering and viewing GnuCash transactions and account balances from a web browser.
Once your GnuCash file is configured in the _real_ GnuCash, GnuCash Helper can be run as a standalone tool for simple budgeting.
You can use [Syncthing](https://syncthing.net/) to ensure that your GnuCash file is synchronized from your server to your other devices.

## Requirements
### Hosting
It is recommended you run this program as a Docker container on port 8000 on a GNU/Linux-based distro behind an nginx reverse proxy with TLS.
Therefore, you should install `nginx` and `docker`.
Installation instructions for `nginx` and `docker` are beyond the scope of this readme.

### GnuCash File Format
GnuCash has several file formats available, including `sqlite3`, `postgresql`, and `xml`.
This project can only work with GnuCash files saved in  `sqlite3` format.
See the [official GnuCash page on formatting](https://www.gnucash.org/docs/v4/C/gnucash-guide/basics-files1.html) for instructions on saving your GnuCash file as `sqlite3`.

## Installation
You can download the latest docker image of GnuCash Helper by running the following command from your \*nix terminal:
```bash
docker pull bxbrenden/gnucash-helper:latest
```

## Running the Docker Container
This example run assumes that your environment meets these criteria:
- You have a Docker volume created with `docker volume create gnucash`
- You have `syncthing` installed and running
- `syncthing` is using a directory called `Sync` in your home directory
- The `Sync` directory in your home directory contains a file called `demo-budget.gnucash`
- The `demo-budget.gnucash` file in `Sync` is symlinked into the `gnucash` Docker volume

Example run:
```bash
docker run --restart unless-stopped -d -p 8000:8000 -v gnucash:/gnucash -e GNUCASH_FILE=demo-budget.gnucash -e GNUCASH_DIR=/gnucash -e NUM_TRANSACTIONS=1000  bxbrenden/gnucash-helper:0.1.0
```

## Configuration
There are only a few variable to configure, and they are all set in the `Dockerfile`:
- `ENV GNUCASH_FILE`: This is the file name of your GnuCash file as it exists on your server.
- `ENV GNUCASH_DIR`: You can leave this set to its default value. This is the name of the directory your GnuCash GitHub repository will be cloned to in the docker container.
- `ENV NUM_TRANSACTIONS`: The number of most recent transactions to display on the `Transactions` page

## Building the Docker Container
Once everything is configured in the `Dockerfile`, the next step is to build the container.

You can build the container from the root directory of this project with the following command (change `bxbrenden` to your DockerHub username if you intend to push it to DockerHub):
```bash
docker build -t bxbrenden/gnucash-helper:latest .
```
Afterwards, the `bxbrenden/gnucash-helper:latest` docker container will appear in your `sudo docker images` output.

## Running the Docker Container
Now that you have built the docker container, you can run it as follows:
1. Find the tag (it will be `latest` if you followed the previous section's instructions) for your docker container.
2. Using that tag, run the following command:
```bash
sudo docker run --reset unless-stopped -d -p 8000:8000 -v /path/to/Syncthing/folder bxbrenden/gnucash-helper:latest
```
3. If successfully started, docker will print a long string to `STDOUT` (your terminal) representing the ID of your running container.
4. To ensure the container is running properly, you can run:
```bash
sudo docker logs --follow <container_ID>
```

## Running the Docker Container Locally for Testing / Development
**Note**: All instructions in this section assume that "locally" means inside of a Docker container based on `bxbrenden/docker-ide`.

1. Ensure your python (pyenv) version is set to `3.9.8` with the `pyenv global 3.9.8` command.
2. Change directories to the `GnuCash-Helper` dir.
3. Run `pip install -r requirements.txt`
4. Run `sudo mkdir /gnucash && sudo chown -R brenden:brenden /gnucash`
5. Copy a demo GnuCash budget file to `/gnucash`
6. Set the following environment variables:
  - `GNUCASH_DIR` (`/gnucash`)
  - `GNUCASH_FILE` (usually set to `demo-budget.gnucash`)
  - `NUM_TRANSACTIONS` (`200` is fine)
7. Start the app with:
```
gunicorn -b 0.0.0.0:8000 --worker-tmp-dir /dev/shm app:app
```

Run these all in one shot with some assumptions that may only work for my system:
```
./run.sh
```

## License
This software is licensed under the `GNU Affero General Public License, Version 3`. Please see [LICENSE.md](https://github.com/bxbrenden/GnuCash-Helper/blob/main/LICENSE.md) or [The official site for this license](https://www.gnu.org/licenses/agpl-3.0.en.html) for more details.
