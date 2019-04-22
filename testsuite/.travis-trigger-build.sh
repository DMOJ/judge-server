#!/bin/bash

die() {
  echo "$1" >&2
  exit 1
}

print_help_and_exit() {
  die "UPSTREAM_TRAVIS_TOKEN=xxxx $0 <upstream-slug>"
}

urlencode() {
  echo -ne "$1" | xxd -plain | tr -d '\n' | sed 's/\(..\)/%\1/g'
}

trigger_build() {
  local upstream_slug="$1"
  local slug=
  local branch=
  local commit_sha=
  local message=

  set -x

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

  body=$(jq -n --arg message "${message}" "{
          request: {
            message: \$message,
            branch: \"master\"
          },
          config: {
            merge_mode: \"deep_merge\",
            env: {
              global: [
                \"TESTSUITE_SLUG=$slug\",
                \"TESTSUITE_BRANCH=$branch\",
                \"TESTSUITE_COMMIT_SHA=$commit_sha\"
              ]
            }
          }
        }")

  set +x
  resp=$(curl -s -X POST \
          -H "Content-Type: application/json" \
          -H "Accept: application/json" \
          -H "Travis-API-Version: 3" \
          -H "Authorization: token ${UPSTREAM_TRAVIS_TOKEN}" \
          -d "${body}" \
          https://api.travis-ci.org/repo/$(urlencode "${upstream_slug}")/requests)
  set -x

  echo "Response from Travis API:"
  echo "${resp}"

  if [ "$(jq -r '.["@type"]' <<< "${resp}")" == "pending" ]; then
    echo "Success!"
  else
    die "Failed to schedule build :-("
  fi
}

trigger_build "$1"
