#!/bin/bash

# Usage: .travis-trigger-build.sh <upstream>

trigger_build() {
  local upstream_slug="$1"
  local slug=
  local branch=
  local commit_sha=
  local message=

  if [ "${TRAVIS_PULL_REQUEST}" == "false" ]; then
    slug="${TRAVIS_REPO_SLUG}"
    branch="${TRAVIS_BRANCH}"
    commit_sha="${TRAVIS_COMMIT}"
    message="testsuite: \"${TRAVIS_COMMIT_MESSAGE}\""
  else
    slug="${TRAVIS_PULL_REQUEST_SLUG}"
    branch="${TRAVIS_PULL_REQUEST_BRANCH}"
    commit_sha="${TRAVIS_PULL_REQUEST_SHA}"
    message="testsuite: Running on new tests from ${TRAVIS_REPO_SLUG}#${TRAVIS_PULL_REQUEST}"
  fi

  echo "slug=${slug}, branch=${branch}, commit=${commit_sha}, message=${message}"
}

trigger_build "$1"
