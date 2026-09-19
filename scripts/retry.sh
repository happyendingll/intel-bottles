#!/usr/bin/env bash
# Retry a non-build command once by default.

set -u

attempts="${RETRY_ATTEMPTS:-2}"
delay="${RETRY_DELAY_SECONDS:-15}"

if [ "$#" -eq 0 ]; then
  echo "usage: retry.sh command [args ...]" >&2
  exit 2
fi
if ! [[ "$attempts" =~ ^[1-9][0-9]*$ ]]; then
  echo "RETRY_ATTEMPTS must be a positive integer" >&2
  exit 2
fi
if ! [[ "$delay" =~ ^[0-9]+$ ]]; then
  echo "RETRY_DELAY_SECONDS must be a non-negative integer" >&2
  exit 2
fi

attempt=1
while true; do
  echo "==> attempt $attempt/$attempts: $*"
  "$@"
  status=$?
  if [ "$status" -eq 0 ]; then
    exit 0
  fi
  if [ "$attempt" -ge "$attempts" ]; then
    echo "command failed after $attempt attempt(s), exit $status" >&2
    exit "$status"
  fi
  echo "command failed with exit $status; retrying in ${delay}s" >&2
  sleep "$delay"
  attempt=$((attempt + 1))
done
