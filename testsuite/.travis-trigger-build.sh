#!/bin/bash

log() {
  echo "$0: $1"
}

die() {
  echo "$0: $1" >&2
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
    branch="${TRAVIS_BRANCH}"
    if [ "${branch}" != "master" ]; then
      log "skipping non-master branch build."
      exit 0
    fi

    slug="${TRAVIS_REPO_SLUG}"
    commit_sha="${TRAVIS_COMMIT}"
    message="Running on upstream ${slug} commit \"${TRAVIS_COMMIT_MESSAGE}\""
  else
    slug="${TRAVIS_PULL_REQUEST_SLUG}"
    branch="${TRAVIS_PULL_REQUEST_BRANCH}"
    commit_sha="${TRAVIS_PULL_REQUEST_SHA}"
    message="Running on upstream PR ${TRAVIS_REPO_SLUG}#${TRAVIS_PULL_REQUEST}"
  fi

  env_base=$(sed 's/[\/-]/_/g' <<< "${TRAVIS_REPO_SLUG}" | tr '[:lower:]' '[:upper:]')
  body=$(jq -n --arg message "${message}" "{
          request: {
            message: \$message,
            branch: \"master\"
          },
          config: {
            merge_mode: \"deep_merge\",
            env: {
              global: [
                \"${env_base}_SLUG=${slug}\",
                \"${env_base}_BRANCH=${branch}\",
                \"${env_base}_COMMIT_SHA=${commit_sha}\"
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
