#!/usr/bin/env bash
# Commits the redrawn files. With nothing to commit it still makes an empty commit once the
# last commit is HEARTBEAT_DAYS old (default 30), so GitHub does not disable the schedule
# after 60 days without repository activity.
set -euo pipefail

heartbeat_days="${HEARTBEAT_DAYS:-30}"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

if [ -n "$(git status --porcelain)" ]; then
  git add -A assets README.md
  git commit -m "profile: redraw from hrabovskyi.online"
else
  age=$(( $(date +%s) - $(git log -1 --format=%ct) ))
  [ "$age" -lt $(( heartbeat_days * 86400 )) ] && exit 0
  git commit --allow-empty -m "profile: heartbeat, keeps the schedule enabled"
fi

git push
