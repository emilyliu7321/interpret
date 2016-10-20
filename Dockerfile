FROM debian:latest

MAINTAINER Jonathan Gordon <jgordon@isi.edu>

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8


# Install system dependencies.

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q -y --fix-missing
RUN apt-get upgrade -q -y

RUN apt-get install -q -y wget bzip2

RUN apt-get clean -q


# Install Miniconda.

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
         -O ~/miniconda.sh --quiet && \
    bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh

ENV PATH /opt/conda/bin:$PATH

RUN conda update -y conda

RUN conda install -y flask


# Add the application code to the Docker image.

ADD app/ /app/


# Run server.

EXPOSE 5000

WORKDIR /app
CMD ./app.py
