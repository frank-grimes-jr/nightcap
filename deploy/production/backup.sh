#!/usr/bin/env bash
set -euo pipefail
umask 077
cd /opt/nightcap/deploy/production
# Root-owned 0600 file supplies RESTIC_REPOSITORY, RESTIC_PASSWORD_FILE,
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY for a private backup-only R2 bucket.
set -a
source /etc/nightcap-backup.env
set +a
dump=$(mktemp /var/tmp/nightcap-backup.XXXXXXXX.sql)
trap 'rm -f -- "$dump"' EXIT
# Finish the producer successfully before creating a restic snapshot. A failed
# or truncated dump must never look like a valid database backup.
docker compose exec -T db mariadb-dump --defaults-extra-file=/run/secrets/db_backup_config \
  --single-transaction --routines --events --hex-blob peq > "$dump"
test -s "$dump"
restic backup --stdin --stdin-filename peq.sql --tag nightcap-database < "$dump"
restic backup private data/server/quests data/server/plugins --tag nightcap-config
restic forget --tag nightcap-database --keep-daily 14 --keep-weekly 4 --prune
restic forget --tag nightcap-config --keep-daily 14 --keep-weekly 4 --prune
restic check
