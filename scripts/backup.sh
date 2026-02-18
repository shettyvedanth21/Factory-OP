#!/bin/bash
#
# FactoryOps Database Backup Script
# 
# This script creates MySQL backups, uploads them to MinIO, and manages retention.
# Run via cron: 0 2 * * * /opt/factoryops/scripts/backup.sh
#

set -euo pipefail

# Configuration
BACKUP_DIR="/tmp/backups"
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-factoryops}"
MYSQL_DATABASE="${MYSQL_DATABASE:-factoryops}"
MINIO_ENDPOINT="${MINIO_ENDPOINT:-minio:9000}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY}"
MINIO_BUCKET="backups"
RETENTION_DAYS=30

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="mysql_${TIMESTAMP}.sql.gz"

# Get MySQL password from environment or Docker secret
if [ -f /run/secrets/mysql_password ]; then
    MYSQL_PASSWORD=$(cat /run/secrets/mysql_password)
else
    MYSQL_PASSWORD="${MYSQL_PASSWORD:-}"
fi

echo "[$(date)] Starting database backup..."

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Perform MySQL backup
echo "[$(date)] Dumping MySQL database..."
mysqldump -h "${MYSQL_HOST}" -P "${MYSQL_PORT}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --single-transaction \
    --quick \
    --lock-tables=false \
    --routines \
    --triggers \
    --events \
    "${MYSQL_DATABASE}" | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"

if [ ! -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    echo "[$(date)] ERROR: Backup file not created!"
    exit 1
fi

BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
echo "[$(date)] Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Upload to MinIO
echo "[$(date)] Uploading backup to MinIO..."
mc alias set minio "http://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" 2>/dev/null || true

# Create bucket if it doesn't exist
mc mb minio/${MINIO_BUCKET} --ignore-existing 2>/dev/null || true

# Upload the backup file
mc cp "${BACKUP_DIR}/${BACKUP_FILE}" "minio/${MINIO_BUCKET}/mysql/"

if [ $? -eq 0 ]; then
    echo "[$(date)] Backup uploaded to MinIO successfully"
else
    echo "[$(date)] ERROR: Failed to upload backup to MinIO!"
    rm -f "${BACKUP_DIR}/${BACKUP_FILE}"
    exit 1
fi

# Clean up local backup
rm -f "${BACKUP_DIR}/${BACKUP_FILE}"

# Clean up old backups from MinIO
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
mc ls minio/${MINIO_BUCKET}/mysql/ | while read -r line; do
    FILE_DATE=$(echo "$line" | awk '{print $6" "$7" "$8}')
    FILE_NAME=$(echo "$line" | awk '{print $8}')
    
    # Parse the date and compare with retention period
    FILE_EPOCH=$(date -d "$FILE_DATE" +%s 2>/dev/null || echo "0")
    CURRENT_EPOCH=$(date +%s)
    DAYS_OLD=$(( (CURRENT_EPOCH - FILE_EPOCH) / 86400 ))
    
    if [ "$DAYS_OLD" -gt "$RETENTION_DAYS" ]; then
        echo "[$(date)] Deleting old backup: ${FILE_NAME}"
        mc rm "minio/${MINIO_BUCKET}/mysql/${FILE_NAME}" || true
    fi
done

echo "[$(date)] Backup process completed successfully!"
