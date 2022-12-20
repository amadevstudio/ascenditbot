#!/bin/sh
set -e

while ! nc -z ${POSTGRES_SERVER} ${POSTGRES_PORT}; do sleep 1; done;

# Then exec the container's main process (what's set as CMD in the Dockerfile).
exec "$@"