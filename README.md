# gnucash-helper
![gnucash-helper logo](https://github.com/bxbrenden/gnucash-helper/blob/main/static/gnucash-helper-bubble-logo_08-300x300.png)

gnucash-helper is a small Flask app for entering and viewing GnuCash transactions and account balances from a web browser.
Once your GnuCash file is configured in the _real_ GnuCash, GnuCash Helper can be run as a standalone tool for simple budgeting.

## Requirements

### Scaleway Object Storage
[Scaleway](https://www.scaleway.com/en/) is a cloud provider that offers services in France, Netherlands, and Poland.
In order to use `gnucash-helper` as-is, you will need to have a Scaleway account.
Starting in version `0.5.0`, `gnucash-helper` uses [Scaleway Object Storage](https://www.scaleway.com/en/object-storage/) (S3-compatible) to store its `.gnucash` files.
Using an S3 backend simplifies deployment because S3 serves as a single source of truth for the latest version of the file.
I realize it's not ideal for a FLOSS project to depend on a cloud provider, but managing Syncthing was proving too tiresome.

In order to configure Scaleway, follow their Object Storage [quickstart guide](https://www.scaleway.com/en/docs/storage/object/quickstart/).
**Note**: please make sure to set up your bucket in the `nl-ams` region, as this value is currently hard-coded in `gnucash-helper`.
**Additional Note**: Make sure to enable Object Versioning in the S3 bucket so each new write to your `.gnucash` file creates a new version within the bucket.

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

## Configuration
There are several variables to configure:
- `GNUCASH_FILE`: This is the file name of your GnuCash file as it exists on your server.
- `GNUCASH_DIR`: You can leave this set to its default value. This is the name of the directory your GnuCash GitHub repository will be cloned to in the docker container.
- `NUM_TRANSACTIONS`: The number of most recent transactions to display on the `Transactions` page
- `SCALEWAY_S3_BUCKET`: The name of the Scaleway Object Storage S3 bucket you created
- `SCALEWAY_ACCESS_KEY_ID`: The API access key ID from Scaleway's `Credentials` page
- `SCALEWAY_SECRET_ACCESS_KEY`: The API secret key from Scaleway's `Credentials` page (corresponding to access key ID)

## Building the Docker Container
Once everything is configured in the `Dockerfile`, the next step is to build the container.

You can build the container from the root directory of this project with the following command (change `bxbrenden` to your DockerHub username if you intend to push it to DockerHub):
```bash
docker build -t bxbrenden/gnucash-helper:latest .
```
Afterwards, the `bxbrenden/gnucash-helper:latest` docker container will appear in your `sudo docker images` output.

## Running the Docker Container
Now that you have built the docker container, you can run it as follows (chaning variables where needed):
1. Find the tag (it will be `latest` if you followed the previous section's instructions) for your docker container.
2. Using that tag, run the following command:
```bash
sudo docker run --reset unless-stopped -d -p 8000:8000 -e GNUCASH_DIR=/gnucash -e GNUCASH_FILE=demo-budget.gnucash -e NUM_TRANSACTIONS=1000 -e SCALEWAY_S3_BUCKET=my-unique-bucket -e SCALEWAY_ACCESS_KEY_ID=12345 -e SCALEWAY_SECRET_ACCESS_KEY=jkasdkfasdf bxbrenden/gnucash-helper:latest
```
3. If successfully started, docker will print a long string to `STDOUT` (your terminal) representing the ID of your running container.
4. To ensure the container is running properly, you can run:
```bash
sudo docker logs --follow <container_ID>
```

Alternatively, you can use `docker-compose` to run the container with an Envfile.
Use `Envfile.example` in this repo as a guide.
Copy `Envfile.example` to a file named `Envfile`, and substitute your own values in for each variable.
Once you've configured `Envfile`, you can run the container as follows:
```bash
docker-compose up -d
```
## License
This software is licensed under the `GNU Affero General Public License, Version 3`. Please see [LICENSE.md](https://github.com/bxbrenden/gnucash-helper/blob/main/LICENSE.md) or [The official site for this license](https://www.gnu.org/licenses/agpl-3.0.en.html) for more details.
