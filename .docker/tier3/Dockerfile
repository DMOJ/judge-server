FROM dmoj/runtimes-tier3:wcipeg-runtimes

RUN mkdir /judge && cd /judge && \
	curl -L https://github.com/Xyene/judge/archive/wcipeg-judge.tar.gz | tar -xz --strip-components=1 && \
	pip3 install -e . && \
	. ~judge/.profile && \
	runuser -u judge -w PATH -- dmoj-autoconf -V > /judge-runtime-paths.yml && \
	echo '  crt_x86_in_lib32: true' >> /judge-runtime-paths.yml && \
	echo '  peg-g++-4.1.3: /usr/bin/peg-g++-4.1.3' >> /judge-runtime-paths.yml && \
	echo '  peg-g++-4.9.1: /usr/bin/peg-g++-4.9.1' >> /judge-runtime-paths.yml && \
	echo '  peg-gcc-4.7.2: /usr/bin/peg-gcc-4.7.2' >> /judge-runtime-paths.yml

ENTRYPOINT ["/judge/.docker/entry"]
