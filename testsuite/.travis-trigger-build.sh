#!/bin/bash

UPSTREAM_SLUG="$1"
UPSTREAM_TRAVIS_TOKEN="$2"

log() {
  echo "$0[${UPSTREAM_SLUG}]: $1"
}

die() {
  echo "$0[${UPSTREAM_SLUG}]: $1" >&2
  exit 1
}

print_help_and_exit() {
  echo "$0 <upstream slug> <upstream Travis token>"
  exit 0
}

urlencode() {
  echo -ne "$1" | xxd -plain | tr -d '\n' | sed 's/\(..\)/%\1/g'
}

api_call() {
  local method="$1"
  local endpoint="$2"
  local body="$3"

  curl -s -X "${method}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -H "Travis-API-Version: 3" \
    -H "Authorization: token ${UPSTREAM_TRAVIS_TOKEN}" \
    -d "${body}" \
    https://api.travis-ci.org/repo/$(urlencode "${UPSTREAM_SLUG}")"${endpoint}"
}

poll_build_status() {
  local request_id="$1"
  local status=
  local is_finished=

  read -r status is_finished <<<$(\
      api_call GET "/request/${request_id}" \
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
  local slug=
  local branch=
  local commit_sha=
  local message=

  if [[ "${TRAVIS_PULL_REQUEST}" == "false" ]]; then
    branch="${TRAVIS_BRANCH}"
    if [[ "${branch}" != "master" ]]; then
      log "Skipping non-master branch build."
      exit 0
    fi

    slug="${TRAVIS_REPO_SLUG}"
    commit_sha="${TRAVIS_COMMIT}"
    message="Running on upstream ${slug} commit \"${TRAVIS_COMMIT_MESSAGE}\""
  else
    branch="${TRAVIS_PULL_REQUEST_BRANCH}"
    slug="${TRAVIS_PULL_REQUEST_SLUG}"
    commit_sha="${TRAVIS_PULL_REQUEST_SHA}"
    message="Running on upstream PR ${TRAVIS_REPO_SLUG}#${TRAVIS_PULL_REQUEST}"
  fi

  local env_base=$(sed 's/[\/-]/_/g' <<< "${TRAVIS_REPO_SLUG}" \
                   | tr '[:lower:]' '[:upper:]')
  local body=$(jq -n --arg message "${message}" "{
    request: {
      message: \$message,
      branch: \"master\",
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
    }
  }")

  log "Scheduling upstream build for ${slug}, ${branch} branch @ ${commit_sha}"

  local status=
  local request_id=
  read -r status request_id <<<$(\
    api_call POST "/requests" "${body}" | jq -r '.["@type"],.request.id' \
  )

  if [[ "${status}" != "pending" ]]; then
    die "Failed to schedule build via request ${request_id}: ${status} :-("
  fi

  until poll_build_status "${request_id}"; do
    log "Waiting on request ${request_id} to complete..."
    sleep 30
  done
}

if [[ -z "${UPSTREAM_SLUG}" || -z "${UPSTREAM_TRAVIS_TOKEN}" ]]; then
  print_help_and_exit
fi

trigger_build
