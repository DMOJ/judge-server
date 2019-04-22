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

api_call() {
  local upstream_slug="$1"
  local method="$2"
  local endpoint="$3"
  local body="$4"

  set +x
  curl -s -X "${method}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -H "Travis-API-Version: 3" \
    -H "Authorization: token ${UPSTREAM_TRAVIS_TOKEN}" \
    -d "${body}" \
    https://api.travis-ci.org/repo/$(urlencode "${upstream_slug}")"${endpoint}"
  set -x
}

poll_build_status() {
  local upstream_slug="$1"
  local request_id="$2"
  local status=
  local is_finished=

  read -r status is_finished <<<$(\
      api_call "${upstream_slug}" "GET" "/request/${request_id}" \
      | jq -r '.builds[0].state,.builds[0].finished_at != null' \
  )

  if [[ "${is_finished}" == "false" ]]; then
    return 1
  fi

  if [[ "${status}" != "passed" && "${status}" != "canceled" ]]; then
    die "Upstream build failed, status: ${status}"
  fi

  # Successful build!
  log "Upstream build completed with non-error status: ${status}"
  return 0
}

trigger_build() {
  local upstream_slug="$1"
  local slug=
  local branch=
  local commit_sha=
  local message=

  set -x

  if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
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

  local env_base=$(sed 's/[\/-]/_/g' <<< "${TRAVIS_REPO_SLUG}" \
                   | tr '[:lower:]' '[:upper:]')
  local body=$(jq -n --arg message "${message}" "{
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

  local status=
  local request_id=
  read -r status request_id <<<$(\
    api_call "${upstream_slug}" POST "/requests" "${body}" \
    | jq -r '.["@type"],.request.id' \
  )

  if [[ "${status}" != "pending" ]]; then
    die "Failed to schedule build :-("
  fi

  log "Waiting on request ${request_id} to complete..."
  until poll_build_status "${upstream_slug}" "${request_id}"; do
    sleep 5
  done
}

trigger_build "$1"
