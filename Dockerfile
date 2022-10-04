# pull base image
FROM python:3.8.2-slim-buster

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install  dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        autoconf \
        automake \
        libtool \
        build-essential \
        g++ \
        lsb-release \
        wget \
        automake libtool pkg-config libsqlite3-dev sqlite3 \
        libpq-dev \
        libcurl4-gnutls-dev \
        libproj-dev \
        libxml2-dev \
        libnetcdf-dev \
        libpoppler-dev \
        libspatialite-dev \
        libhdf4-alt-dev \
        libhdf5-serial-dev \
        libopenjp2-7-dev

# Install gdal, geos and proj
COPY ./build_deps.sh /
RUN /build_deps.sh

# Clean up
RUN apt-get update -y \
    && apt-get remove -y --purge build-essential wget \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# copy project
COPY . /usr/src/app/

# run docker-entrypoint.sh
ENTRYPOINT ["/usr/src/app/docker-entrypoint.sh"]