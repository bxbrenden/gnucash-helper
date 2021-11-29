FROM bxbrenden/docker-ide:0.1.0

LABEL "maintainer"="brendenahyde@gmail.com"

USER root

# Install app and dependencies
ENV LOG_DIR=/gnucash
RUN mkdir -p $LOG_DIR
ENV APP_DIR=/app
RUN mkdir -p $APP_DIR
WORKDIR $APP_DIR
ADD requirements.txt requirements.txt
RUN /home/brenden/.pyenv/shims/pip3 install -r requirements.txt
COPY templates/ templates/
COPY static/ static/
ADD gnucash_helper.py gnucash_helper.py
ADD app.py app.py

EXPOSE 8000

CMD ["/home/brenden/.pyenv/shims/gunicorn", "-b", "0.0.0.0:8000", "--worker-tmp-dir", "/dev/shm", "app:app"]
