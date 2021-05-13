FROM bxbrenden/docker-ide:latest

LABEL "maintainer"="brendenahyde@gmail.com"

USER root

# Install app and dependencies
RUN mkdir /GnuCash-Helper
WORKDIR /GnuCash-Helper
ADD requirements.txt requirements.txt
ADD gnucash_helper.py gnucash_helper.py
ADD app.py app.py
RUN pip3 install -r requirements.txt
COPY templates/ templates/
COPY static/ static/

# Make the dir where your GnuCash file will live inside the container
ENV GNUCASH_DIR=/gnucash
RUN mkdir $GNUCASH_DIR

# This is the name of your GnuCash file
ENV GNUCASH_FILE=budget.gnucash

# Number of transactions that will be visible in txn history
ENV NUM_TRANSACTIONS="200"

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "--worker-tmp-dir", "/dev/shm", "app:app"]
