#!/usr/bin/env bash
# Runs the bot's tests in throwaway containers and removes them after, whatever the result.
# Extra arguments filter the cases by name: ./scripts/test.sh notice
set -uo pipefail
cd "$(dirname "$0")/.."

compose=(docker compose -f docker-compose.test.yml)
"${compose[@]}" build --quiet migrator tests || exit 1
"${compose[@]}" run --rm --quiet-pull tests python tests/run.py "$@" 2>&1 \
  | grep -Ev '^ (Network|Container|Volume) '
status=${PIPESTATUS[0]}
"${compose[@]}" down -v --remove-orphans >/dev/null 2>&1
exit "$status"
