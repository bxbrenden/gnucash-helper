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
- `ENV GIT_USER` : Change "Pers Person" to your name as you'd like it to appear in your git commits.
- `ENV GIT_EMAIL` : Set your email address to the email you'd like to appear in your git commits.
- `ENV GITHUB_TOKEN`: Set the value to a [GitHub Personal Access Token](https://docs.github.com/en/free-pro-team@latest/github/authenticating-to-github/creating-a-personal-access-token). This personal access token only needs `repo` access.
- `ENV GITHUB_GNUCASH_URL`: Set this to the HTTPS URL of the GitHub repository containing your GnuCash file.
- `ENV CLONE_URL`: you construct this string as follows: `https://` + `<your GitHub Personal Access Token>` + `@github.com/<your GitHub account>/<your GnuCash git repo>` + `.git`. For example, if your Personal Access Token is `12345`, your user account is `bxbrenden`, and your git repo is called `my-gnucash`, your `CLONE_URL` would be: `https://12345@github.com/bxbrenden/my-gnucash.git`
- `ENV GNUCASH_BOOK_NAME`: This is the file name of your GnuCash file as it exists in your GitHub repository.
- `ENV GNUCASH_DIR`: You can leave this set to its default value. This is the name of the directory your GnuCash GitHub repository will be cloned to in the docker container.

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
sudo docker run -d -p 8000:8000 bxbrenden/gnucash-helper:latest
```
3. If successfully started, docker will print a long string to `STDOUT` (your terminal) representing the ID of your running container.
4. To ensure the container is running properly, you can run:
```bash
sudo docker logs --follow <container_ID>
```
