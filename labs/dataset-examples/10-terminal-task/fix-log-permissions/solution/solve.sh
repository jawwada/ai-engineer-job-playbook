#!/bin/bash
# Reference solution: the service account owns its log directory; others keep read-only access.
set -euo pipefail
chown -R appsvc:appsvc /var/log/app
chmod 755 /var/log/app
chmod 644 /var/log/app/app.log
