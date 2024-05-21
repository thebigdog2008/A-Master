FROM python:3.8-buster

# Install dependencies
RUN apt-get update
RUN apt-get install -y --no-install-recommends \
    build-essential \
    libcurl4-openssl-dev \
    libjpeg-dev \
    vim \
    ntp \
    libpq-dev
RUN apt-get install -y --no-install-recommends \
    git-core
RUN apt-get install -y --no-install-recommends \
    python3-dev \
    software-properties-common \
    python-setuptools
RUN apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    python-psycopg2
RUN apt-get install -y --no-install-recommends \
    python-gdal \
    gdal-bin \
    libgdal-dev \
    libgdal20 \
    libxml2-dev \
    libxslt-dev \
    xmlsec1

RUN pip install --upgrade \
    setuptools \
    pip \
    wheel

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /code
ENV VIRTUAL_ENV /usr/local


ADD . /code/

WORKDIR /code/

RUN mkdir -p /data/realtorx-logs/list_hub/
RUN chmod 777 /data/realtorx-logs/list_hub/

RUN pip install -r requirements.txt

CMD [ "gunicorn config.wsgi --bind 0.0.0.0:8080" ]
