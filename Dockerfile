FROM debian:bullseye-20220801

LABEL "maintainer"="brendenahyde@gmail.com"

USER root

# Install apt packages
RUN apt update && apt install -y python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install app and app dependencies
RUN mkdir /app
WORKDIR /app
ADD requirements.txt requirements.txt
RUN /usr/bin/pip3 install -r requirements.txt
COPY app/ app/
ADD gch.py gch.py
ADD flask_db_init.sh flask_db_init.sh
ADD config.py config.py

# Configure the local sqlite3 DB to hold users.
# This file deletes itself after configuring the DB.
RUN ./flask_db_init.sh

EXPOSE 8000

CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:8000", "--worker-tmp-dir", "/dev/shm", "gch:app"]
