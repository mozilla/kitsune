FROM          ubuntu:14.04
MAINTAINER    Mike Cooper <mcooper@mozilla.com>

RUN apt-get update -y
RUN apt-get install -y git \
    python-all \
    python-dev \
    python-pip \
    nodejs \
    nodejs-legacy \
    npm \
    libmysqlclient-dev # for MySQL-python \
    && apt-get clean

# configure git and install tc-vcs
RUN git config --global user.email "nobody@mozilla.com" && \
    git config --global user.name "mozilla"

# Set variable normally configured at login, by the shells parent process, these
# are taken from GNU su manual
ENV HOME /home/worker
ENV SHELL /bin/bash
ENV USER worker
ENV LOGNAME worker
ENV HOSTNAME taskcluster-worker

### add worker user and setup its workspace
RUN useradd -m worker
WORKDIR /home/worker
COPY checkout-pull-request /home/worker/bin/
USER worker
