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
COPY templates/ templates/
COPY static/ static/
ADD gnucash_helper.py gnucash_helper.py
ADD app.py app.py

EXPOSE 8000

CMD ["/usr/local/bin/gunicorn", "-b", "0.0.0.0:8000", "--worker-tmp-dir", "/dev/shm", "app:app"]
