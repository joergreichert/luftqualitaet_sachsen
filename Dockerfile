FROM debian:jessie
ENV PG_VERSION 9.4
RUN apt-get update && apt-get install -y --no-install-recommends cython daemontools npm nodejs-legacy postgresql-client postgresql python-pip python-dev python-virtualenv virtualenvwrapper libpq-dev git make gcc

EXPOSE 8000:8000

ENV USER_NAME vagrant
RUN useradd -ms /bin/bash $USER_NAME
ENV HOME "/home/$USER_NAME"
ENV APP_DIR $HOME/app

USER vagrant

ADD . $APP_DIR
WORKDIR /$APP_DIR

USER root

RUN echo "local\tall\t\t${USER_NAME}\t\t\t\t\tmd5" >> /etc/postgresql/$PG_VERSION/main/pg_hba.conf

ENV VIRTUALENV "$APP_DIR/.virtualenvs" 

RUN chown -R $USER_NAME:$USER_NAME $HOME
RUN chown -R $USER_NAME:$USER_NAME $HOME /usr/local/lib/python2.7/dist-packages/

USER $USER_NAME

RUN mkdir -p $VIRTUALENV

ENV WORKON_HOME $VIRTUALENV
RUN echo "WORKON_HOME=$VIRTUALENV" >> $HOME/.bashrc
USER root

RUN  /bin/bash -c "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh && mkvirtualenv luftverschmutzung_sachsen && cd $APP_DIR && npm config set prefix '~/.npm-packages' && echo export PATH="$PATH:$HOME/.npm-packages/bin" >> ./.bashrc && source ./.bashrc && npm install -g bower && make install-dev"

USER postgres

RUN service postgresql start && make create-db && make migrate

USER root

ENTRYPOINT ["./docker-entrypoint.sh"]
