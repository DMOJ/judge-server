FROM cgswong/min-jessie:latest
MAINTAINER Quantum <quantum@dmoj.ca>

RUN groupadd -r judge && useradd -r -g judge judge
RUN apt-get -y update && apt-get install -y --no-install-recommends python python2.7-dev python3 gcc g++ wget file && apt-get clean
RUN wget -q --no-check-certificate -O- https://bootstrap.pypa.io/get-pip.py | python && \
    pip install --no-cache-dir pika watchdog cython ansi2html && \
    rm -rf ~/.cache
RUN mkdir /problems

COPY . /judge
WORKDIR /judge

RUN python cptbox/build_cptbox.py && \
    python checkers/build_checker.py && \
    rm -rf checkers/build/ cptbox/build/
