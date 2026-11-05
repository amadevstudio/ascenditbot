#!/usr/bin/env bash
# The bot without Telegram, step by step, on a throwaway database: ./scripts/sim.sh -c "send /start" -c "tap 0,0"
# Actions: bot/tests/sim.py. A scenario file must be inside bot/ (it is mounted there): ./scripts/sim.sh tests/x.txt
set -uo pipefail
cd "$(dirname "$0")/.."

compose=(docker compose -f docker-compose.test.yml)
"${compose[@]}" build --quiet migrator tests || exit 1
"${compose[@]}" run --rm --quiet-pull tests python tests/sim.py "$@" 2>&1 \
  | grep -Ev '^ (Network|Container|Volume) '
status=${PIPESTATUS[0]}
"${compose[@]}" down -v --remove-orphans >/dev/null 2>&1
exit "$status"
