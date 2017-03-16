FROM debian:8.6

MAINTAINER Jonathan Gordon <jgordon@isi.edu>

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8


# Install basic system dependencies.

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -q -y --fix-missing && \
    apt-get install -q -y --fix-missing --no-install-recommends \
        bison bzip2 ca-certificates flex g++ libssl-dev make wget zlib1g-dev

RUN apt-get clean -q


# Install Miniconda.

RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh \
         -O /tmp/miniconda.sh -q && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh

ENV PATH /opt/conda/bin:$PATH

RUN conda update -y conda

RUN conda install -y flask beautifulsoup4 lxml


# Add the C&C pipeline and compile.

RUN apt-get install -q -y --fix-missing --no-install-recommends \
        swi-prolog

COPY ext /interpret/ext

WORKDIR /interpret/ext

RUN cd candc/ext && \
    tar -xjvf gsoap-2.8.16.tbz2 && \
    cd gsoap-2.8 && \
    ./configure --prefix=/interpret/ext/candc/ext && \
    make && \
    make install

RUN cd candc && \
    make && \
    make bin/t && \
    make bin/boxer && \
    make soap && \
    tar -xjvf models-1.02.tbz2


# Install Phillip.

RUN apt-get install -q -y --fix-missing --no-install-recommends \
        git graphviz liblpsolve55-dev lp-solve

ENV CPLUS_INCLUDE_PATH /usr/include/lpsolve:$CPLUS_INCLUDE_PATH
ENV LD_LIBRARY_PATH /usr/lib/lp_solve:$LD_LIBRARY_PATH

RUN git clone https://github.com/kazeto/phillip.git && \
    cd phillip && \
    2to3 -w tools/configure.py && \
    /bin/echo -e "\ny\nn" | python ./tools/configure.py && \
    make LDFLAGS="-lcolamd -llpsolve55 -ldl"

RUN 2to3 -w phillip/tools/util.py && \
    2to3 -w phillip/tools/graphviz.py


# Add the application code to the Docker image.

COPY app /interpret/app
COPY kb /interpret/kb
COPY server /interpret


# Run our server.

EXPOSE 5000

WORKDIR /interpret
CMD ["./server"]
