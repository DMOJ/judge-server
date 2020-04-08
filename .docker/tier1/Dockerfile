FROM dmoj/runtimes-tier1

ARG TAG=master
RUN mkdir /judge && cd /judge && \
	curl -L https://github.com/DMOJ/judge/archive/"${TAG}".tar.gz | tar -xz --strip-components=1 && \
	pip3 install -e . && \
	runuser -u judge -w PATH -- bash --login -c 'dmoj-autoconf -V' > /judge-runtime-paths.yml && \
	echo '  crt_x86_in_lib32: true' >> /judge-runtime-paths.yml

ENTRYPOINT ["/judge/.docker/entry"]
