GIT_TAG ?= master
TAG ?= latest

.PHONY: all image-tier1 image-tier2 image-tier3

all: image-tier1 image-tier2 image-tier3

image-tier1:
	cd tier1 && docker build --build-arg TAG="${GIT_TAG}" -t dmoj/judge-tier1 -t dmoj/judge-tier1:$(TAG) .

image-tier2:
	cd tier2 && docker build --build-arg TAG="${GIT_TAG}" -t dmoj/judge-tier2 -t dmoj/judge-tier2:$(TAG) .

image-tier3:
	cd tier3 && docker build --build-arg TAG="${GIT_TAG}" -t dmoj/judge-tier3 -t dmoj/judge-tier3:$(TAG) .
