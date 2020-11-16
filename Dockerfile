FROM debian:buster

COPY . /app

WORKDIR /app

RUN echo deb http://deb.debian.org/debian/ stretch main > /etc/apt/sources.list.d/stretch.list && \
#     sed -i "s@http://deb.debian.org@http://mirrors.aliyun.com@g" /etc/apt/sources.list && \
#     sed -i 's|security.debian.org/debian-security|mirrors.aliyun.com/debian-security|g' /etc/apt/sources.list && \
    echo 'APT::Default-Release "buster";' > /etc/apt/apt.conf.d/99stretch && \
#     printf '[global]\nindex-url = https://mirrors.aliyun.com/pypi/simple/\n[install]\ntrusted-host=mirrors.aliyun.com\n' > /etc/pip.conf && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl file gcc g++ python3-pip python3-dev python3-setuptools python3-wheel cython3 libseccomp-dev bzip2 gzip \
        python2 openjdk-11-jdk-headless fp-compiler && \
    apt-get install -y -t stretch --no-install-recommends openjdk-8-jdk-headless && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip3 install -e .

ENTRYPOINT ["/bin/bash"]
