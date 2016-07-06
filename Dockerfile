FROM cgswong/min-jessie:latest
MAINTAINER Quantum <quantum@dmoj.ca>

RUN groupadd -r judge && useradd -r -g judge judge
RUN apt-get -y update && apt-get install -y --no-install-recommends python python2.7-dev python3 gcc g++ wget file && apt-get clean
RUN wget -q --no-check-certificate -O- https://bootstrap.pypa.io/get-pip.py | python && \
    pip install --no-cache-dir pyyaml watchdog cython ansi2html termcolor && \
    rm -rf ~/.cache
RUN mkdir /problems

COPY . /judge
WORKDIR /judge

RUN env DMOJ_REDIST=1 python setup.py develop && rm -rf build/
