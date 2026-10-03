FROM python:3.12-slim

# Test dependency for the verifier (the tests themselves are not copied into the image).
RUN pip install --no-cache-dir pytest==8.3.3

# The broken state the agent must repair: a root-owned log directory the service account cannot write.
RUN useradd --system --user-group --shell /usr/sbin/nologin appsvc \
 && useradd --create-home --user-group auditor \
 && mkdir -p /var/log/app /opt/app \
 && echo "2026-09-30T23:59:59Z previous run" > /var/log/app/app.log \
 && chmod 755 /var/log/app \
 && chmod 644 /var/log/app/app.log

COPY app/write_log.sh /opt/app/write_log.sh
RUN chmod 755 /opt/app/write_log.sh

WORKDIR /root
