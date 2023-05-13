FROM debian:bookworm-20230502-slim

LABEL "maintainer"="brendenahyde@gmail.com"

USER root

# Install apt packages
RUN apt update && apt install -y python3-full python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install app and app dependencies
RUN mkdir /app
WORKDIR /app
ADD requirements.txt requirements.txt
RUN /usr/bin/python3 -m pip install --break-system-packages -r requirements.txt
COPY app/ app/
ADD gch.py gch.py
ADD config.py config.py
# This is a janky way to create a user DB _inside_ the container image with sqlite3.
#   It will result in annoyances because the user DB will not persist across containers.
#   That means you'll have to re-register every time the container restarts.
# COPY flask_db_init.sh flask_db_init.sh
# RUN chmod +x flask_db_init.sh && ./flask_db_init.sh

EXPOSE 8000

CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:8000", "--worker-tmp-dir", "/dev/shm", "gch:app"]
