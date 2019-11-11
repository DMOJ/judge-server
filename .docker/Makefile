GIT_TAG ?= master
TAG ?= latest

.PHONY: all judge-tier1 judge-tier2 judge-tier3

all: judge-tier1 judge-tier2 judge-tier3

judge-tier1:
	cd tier1 && docker build --build-arg TAG="${GIT_TAG}" -t dmoj/judge-tier1 -t dmoj/judge-tier1:$(TAG) .

judge-tier2:
	cd tier2 && docker build --build-arg TAG="${GIT_TAG}" -t dmoj/judge-tier2 -t dmoj/judge-tier2:$(TAG) .

judge-tier3:
	cd tier3 && docker build --build-arg TAG="${GIT_TAG}" -t dmoj/judge-tier3 -t dmoj/judge-tier3:$(TAG) .
