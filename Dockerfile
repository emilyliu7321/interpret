FROM debian:latest

MAINTAINER Jonathan Gordon <jgordon@isi.edu>

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8


# Install system dependencies.

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q -y --fix-missing
RUN apt-get upgrade -q -y --fix-missing

RUN apt-get install -q -y --fix-missing wget g++ bzip2 flex bison swi-prolog \
    libssl-dev zlib1g-dev

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


# Add the C&C pipeline and compile.

ADD ext /interpret/ext

RUN cd /interpret/ext/candc/ext && \
    tar -xjvf gsoap-2.8.16.tbz2 && \
    cd gsoap-2.8 && \
    ./configure --prefix=/interpret/ext/candc/ext && \
    make && \
    make install && \
    cd ../.. && \
    make && \
    make bin/t && \
    make bin/boxer && \
    make soap && \
    tar -xjvf models-1.02.tbz2


# Add the application code to the Docker image.

ADD app /interpret/app

ADD server /interpret


# Run our server.

EXPOSE 5000

WORKDIR /interpret
CMD ["./server"]
