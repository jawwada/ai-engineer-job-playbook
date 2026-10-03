#!/bin/sh
# Nightly job: append a status line; rotate the log once it passes 1 MB.
set -eu
LOG=/var/log/app/app.log
if [ -f "$LOG" ] && [ "$(wc -c < "$LOG")" -gt 1048576 ]; then
  mv "$LOG" "$LOG.1"
fi
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) nightly job ok" >> "$LOG"
