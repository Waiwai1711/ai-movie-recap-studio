#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/opt/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "$BACKUP_DIR"

sqlite3 /opt/AI_Movie_Recap_Studio/storage/recap_studio.db ".backup '${BACKUP_DIR}/recap_studio_${TIMESTAMP}.db'"
find "$BACKUP_DIR" -type f -mtime +7 -delete
echo "Backup finished: ${BACKUP_DIR}/recap_studio_${TIMESTAMP}.db"
