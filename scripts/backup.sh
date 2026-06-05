#!/bin/bash
# ── SQLite 数据库备份脚本 ──
# 用法: ./scripts/backup.sh [数据库路径] [备份目录]
#
# 默认配置:
#   DB_PATH=./data/interview.db
#   BACKUP_DIR=./backups
#   保留最近 30 天备份
#
# 定时执行 (crontab):
#   0 3 * * * /opt/tech-chat/scripts/backup.sh

set -euo pipefail

DB_PATH="${1:-./data/interview.db}"
BACKUP_DIR="${2:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

if [ ! -f "$DB_PATH" ]; then
    echo "[ERROR] Database not found: $DB_PATH"
    exit 1
fi

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/interview_$DATE.db"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backing up $DB_PATH → $BACKUP_FILE"

# SQLite online backup (no service interruption)
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Compress
gzip "$BACKUP_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Compressed: ${BACKUP_FILE}.gz ($(ls -lh "${BACKUP_FILE}.gz" | awk '{print $5}'))"

# Cleanup old backups
find "$BACKUP_DIR" -name "interview_*.db.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Cleaned up backups older than $RETENTION_DAYS days"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup complete"
