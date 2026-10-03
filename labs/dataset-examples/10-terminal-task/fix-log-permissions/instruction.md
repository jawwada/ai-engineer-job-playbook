# Fix the log permissions for the nightly job

The nightly job `/opt/app/write_log.sh` runs as the system user `appsvc`. It appends a line to `/var/log/app/app.log` and, once that file passes 1 MB, rotates it to `/var/log/app/app.log.1`. Right now it fails with `Permission denied`.

Make the job work when it runs as `appsvc`:

- `appsvc` must be able to append to `/var/log/app/app.log` and to create and rename files in `/var/log/app`.
- Do not modify `/opt/app/write_log.sh`, and do not run the job as root.
- Nothing under `/var/log/app` may be writable by other users (no world-writable files or directories).
- The user `auditor` must still be able to read `/var/log/app/app.log` but must not be able to write to it.
