# GnuCash-Helper

GnuCash-Helper is a small Flask app for entering GnuCash transactions from a web browser.
Once configured in the _real_ GnuCash, it can be used as a standalone tool or with [Syncthing](https://syncthing.net/).

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
Example run:
```bash
docker run -e "GNUCASH_FILE=your_gnucash_file.gnucash" --restart unless-stopped -d -p 8000:8000 -v "$(pwd)/Sync":/gnucash bxbrenden/gnucash-helper:latest
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

## License
This software is licensed under the `GNU Affero General Public License, Version 3`. Please see [LICENSE.md](https://github.com/bxbrenden/GnuCash-Helper/blob/main/LICENSE.md) or [The official site for this license](https://www.gnu.org/licenses/agpl-3.0.en.html) for more details.
